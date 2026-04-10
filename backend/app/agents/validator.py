"""
Input Validator Agent
Checks if parent responses are detailed enough for meaningful assessment.
Uses fast heuristics first, LLM only for borderline cases.
"""

import re
import logging
from typing import Optional
from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)

# Responses that are too vague to be useful
INSUFFICIENT_PATTERNS = [
    r"^(yes|no|ok|okay|ya|yep|nope|nah|sure|fine|good|bad|idk|dunno|maybe)\.?$",
    r"^(i\s*don'?t\s*know|not\s*sure|nothing|none|na|n/?a)\.?$",
    r"^[\s\W]*$",  # only whitespace/punctuation
]

INSUFFICIENT_COMPILED = [re.compile(p, re.IGNORECASE) for p in INSUFFICIENT_PATTERNS]

# ── Relevance-checking word sets ──────────────────────────────────────────────
# Generic child / education / parenting words — if ANY of these appear the input
# is almost certainly on-topic regardless of category.
CHILD_EDUCATION_WORDS = {
    "child", "children", "kid", "kids", "son", "daughter", "boy", "girl",
    "student", "learner", "pupil", "toddler", "teen", "teenager", "baby",
    "school", "class", "classroom", "teacher", "tutor", "homework", "lesson",
    "lessons", "grade", "grades", "exam", "exams", "test", "tests",
    "learn", "learning", "study", "studying", "read", "reading", "write",
    "writing", "math", "maths", "science", "english", "subject",
    "focus", "attention", "concentrate", "concentration", "distract", "distracted",
    "friend", "friends", "peer", "peers", "bully", "bullying", "social",
    "behavior", "behaviour", "behave", "misbehave", "tantrum", "tantrums",
    "feel", "feeling", "feelings", "emotion", "emotions", "emotional",
    "angry", "anger", "anxious", "anxiety", "sad", "sadness", "happy", "upset",
    "cry", "crying", "worried", "worry", "scared", "fear",
    "parent", "parenting", "mom", "mum", "dad", "father", "mother",
    "sibling", "brother", "sister", "family",
    "therapist", "therapy", "counselor", "counsellor", "psychologist",
    "diagnosis", "adhd", "asd", "autism", "dyslexia", "iep", "504",
    "special", "needs", "support", "accommodation",
    "play", "playing", "recess", "sport", "sports",
    "struggle", "struggling", "difficult", "difficulty", "challenge",
    "improve", "improving", "progress", "regression",
    "he", "she", "him", "her", "his", "they", "them", "their",
}

# Per-category keyword sets — extra topic-specific words
CATEGORY_KEYWORDS = {
    "attention": {
        "focus", "attention", "concentrate", "distract", "distracted", "fidget",
        "fidgeting", "squirm", "hyperactive", "impulsive", "impulse", "wander",
        "daydream", "daydreaming", "zone", "zoning", "task", "off-task",
        "listen", "listening", "forgetful", "forget", "careless", "rushing",
        "sit", "sitting", "still", "restless", "calm", "patient", "impatient",
    },
    "social": {
        "friend", "friends", "peer", "peers", "social", "interact", "interaction",
        "play", "share", "sharing", "cooperate", "cooperation", "turn", "turns",
        "conflict", "argue", "arguing", "fight", "fighting", "bully", "bullying",
        "shy", "withdrawn", "lonely", "group", "team", "include", "exclude",
        "empathy", "kind", "kindness", "communicate", "communication", "talk",
    },
    "emotional": {
        "feel", "feeling", "feelings", "emotion", "emotional", "mood", "moods",
        "angry", "anger", "anxious", "anxiety", "sad", "sadness", "happy",
        "upset", "cry", "crying", "tantrum", "meltdown", "frustrated",
        "frustration", "worried", "worry", "scared", "fear", "overwhelmed",
        "calm", "regulate", "regulation", "self-control", "cope", "coping",
        "sensitive", "irritable", "confident", "confidence", "self-esteem",
    },
    "academic": {
        "read", "reading", "write", "writing", "math", "maths", "spell",
        "spelling", "homework", "assignment", "test", "exam", "grade", "grades",
        "score", "scores", "subject", "class", "lesson", "learn", "learning",
        "study", "studying", "tutor", "tutoring", "comprehension", "fluency",
        "vocabulary", "science", "english", "history", "project", "report",
        "performance", "achievement", "behind", "ahead", "struggle", "pass", "fail",
    },
    "behavioral": {
        "behavior", "behaviour", "behave", "misbehave", "tantrum", "tantrums",
        "defiant", "defiance", "oppose", "oppositional", "aggressive", "aggression",
        "hit", "hitting", "kick", "kicking", "bite", "biting", "throw",
        "rule", "rules", "consequence", "consequences", "discipline", "timeout",
        "comply", "compliance", "refuse", "refusing", "listen", "obey",
        "disruptive", "outburst", "impulse", "impulsive", "destructive",
    },
}

# Friendly relevance prompts per category
RELEVANCE_PROMPTS = {
    "attention": "I'd love to hear more about {student_name}'s experience with this. Could you share something specific about how they handle focusing or paying attention?",
    "social": "I'd love to hear more about {student_name}'s experience with this. Could you share something specific about how they interact with other children?",
    "emotional": "I'd love to hear more about {student_name}'s experience with this. Could you share something specific about how they handle their emotions?",
    "academic": "I'd love to hear more about {student_name}'s experience with this. Could you share something specific about how they manage schoolwork or learning?",
    "behavioral": "I'd love to hear more about {student_name}'s experience with this. Could you share something specific about their behaviour at home or school?",
    "general": "I'd love to hear more about {student_name}'s experience with this. Could you share something related to their day-to-day life at home or school?",
}

# Common English words used to detect gibberish
# If a message has very few real words, it's likely nonsense
COMMON_WORDS = {
    "i", "he", "she", "we", "they", "it", "my", "his", "her", "our", "the", "a", "an",
    "is", "are", "was", "were", "has", "have", "had", "do", "does", "did", "will", "would",
    "can", "could", "should", "not", "no", "yes", "and", "or", "but", "in", "on", "at",
    "to", "for", "with", "from", "by", "about", "up", "out", "of", "that", "this", "what",
    "when", "where", "how", "who", "which", "very", "really", "much", "more", "also",
    "just", "like", "time", "been", "being", "some", "than", "then", "them", "their",
    "there", "these", "those", "so", "if", "all", "any", "each", "every", "both",
    "school", "class", "teacher", "homework", "child", "kid", "son", "daughter",
    "student", "learn", "learning", "read", "reading", "write", "writing", "math",
    "help", "need", "problem", "issue", "hard", "easy", "difficult", "focus", "attention",
    "behavior", "behaviour", "friend", "friends", "social", "emotional", "feel", "feeling",
    "think", "know", "understand", "work", "home", "sometimes", "often", "always", "never",
    "because", "since", "well", "good", "bad", "better", "worse", "gets", "get", "got",
    "make", "makes", "made", "go", "goes", "going", "come", "comes", "say", "says", "said",
    "see", "seen", "take", "takes", "give", "want", "wants", "need", "needs", "try", "tries",
    "seem", "seems", "lot", "many", "few", "still", "keep", "keeps", "day", "days",
    "year", "years", "old", "new", "first", "last", "long", "short", "big", "small",
    "him", "able", "unable", "sit", "sitting", "play", "playing", "talk", "talking",
}

# Follow-up prompts keyed by assessment category
FOLLOW_UP_PROMPTS = {
    "attention": "Could you give an example of when {student_name} has trouble focusing? For instance, during homework, in class, or during activities?",
    "social": "Could you describe a specific situation where you noticed this with {student_name}'s social interactions?",
    "emotional": "Can you share a bit more about what {student_name} does or says when they feel this way?",
    "academic": "Could you tell me more about which subjects or tasks {student_name} finds most challenging?",
    "behavioral": "Can you give me an example of a recent situation where this behaviour occurred with {student_name}?",
    "general": "Could you share a bit more detail? Even a short example would help me understand {student_name}'s situation better.",
}


class InputValidatorAgent(BaseAgent):
    """Validates whether parent input is detailed enough for assessment."""

    def __init__(self):
        super().__init__(name="InputValidator", timeout=8.0, max_tokens=150)

    async def validate(
        self,
        user_input: str,
        category: str = "general",
        student_name: str = "your child",
        question_context: Optional[str] = None,
    ) -> dict:
        """
        Validate input sufficiency.
        Returns: {
            "is_sufficient": bool,
            "feedback": str | None,  # message to show user if insufficient
            "confidence": float
        }
        """
        text = user_input.strip()

        # Empty input
        if not text:
            return {
                "is_sufficient": False,
                "feedback": "It looks like your message was empty. Could you share your thoughts?",
                "confidence": 1.0,
            }

        # Check against insufficient patterns
        for pattern in INSUFFICIENT_COMPILED:
            if pattern.match(text):
                prompt = FOLLOW_UP_PROMPTS.get(category, FOLLOW_UP_PROMPTS["general"])
                return {
                    "is_sufficient": False,
                    "feedback": prompt.replace("{student_name}", student_name),
                    "confidence": 0.95,
                }

        # Very short input (< 4 words) - likely insufficient
        word_count = len(text.split())
        if word_count < 4:
            prompt = FOLLOW_UP_PROMPTS.get(category, FOLLOW_UP_PROMPTS["general"])
            return {
                "is_sufficient": False,
                "feedback": f"Thanks for that! {prompt.replace('{student_name}', student_name)}",
                "confidence": 0.8,
            }

        # Gibberish / nonsense detection
        if self._is_gibberish(text):
            return {
                "is_sufficient": False,
                "feedback": "I didn't quite understand that. Could you describe your thoughts in a sentence or two?",
                "confidence": 0.9,
            }

        # ── Strict relevance checks ─────────────────────────────────────

        # 1. Excessive length check — real answers are typically under 100 words
        if word_count > 100:
            # Check if it looks like a copy-paste (very long, impersonal)
            if self._is_copy_paste(text):
                return {
                    "is_sufficient": False,
                    "feedback": f"That looks like it might be copied text. Could you describe {student_name}'s experience in your own words instead?",
                    "confidence": 0.9,
                }

        # 2. Keyword-based irrelevance (zero overlap with child/education topics)
        if self._is_irrelevant(text, category):
            prompt = RELEVANCE_PROMPTS.get(category, RELEVANCE_PROMPTS["general"])
            return {
                "is_sufficient": False,
                "feedback": prompt.replace("{student_name}", student_name),
                "confidence": 0.75,
            }

        # 3. LLM-based relevance check for longer inputs (>30 words)
        #    Short personal answers are trusted; longer ones get verified
        if word_count > 30 and question_context:
            llm_result = await self._llm_relevance_check(text, question_context, student_name)
            if llm_result is not None and not llm_result:
                prompt = RELEVANCE_PROMPTS.get(category, RELEVANCE_PROMPTS["general"])
                return {
                    "is_sufficient": False,
                    "feedback": prompt.replace("{student_name}", student_name),
                    "confidence": 0.85,
                }

        # 4-8 words - borderline, accept but note it's brief
        if word_count < 8:
            return {
                "is_sufficient": True,
                "feedback": None,
                "confidence": 0.7,
            }

        # 8+ words - sufficient
        return {
            "is_sufficient": True,
            "feedback": None,
            "confidence": 0.95,
        }

    @staticmethod
    def _is_gibberish(text: str) -> bool:
        """Detect gibberish/random keyboard mashing."""
        words = re.findall(r"[a-zA-Z']+", text.lower())
        if not words:
            return True

        # Check what fraction of words are recognizable English
        real_word_count = sum(1 for w in words if w in COMMON_WORDS or len(w) <= 2)
        ratio = real_word_count / len(words)

        # If less than 30% of words are recognizable, it's likely gibberish
        if ratio < 0.3:
            return True

        # Check for excessive consonant clusters (keyboard mashing signature)
        consonant_heavy = 0
        for word in words:
            if len(word) >= 4:
                vowels = sum(1 for c in word if c in "aeiou")
                if vowels / len(word) < 0.15:
                    consonant_heavy += 1
        if len(words) > 0 and consonant_heavy / len(words) > 0.5:
            return True

        # Check for repeated random capitalization patterns
        alpha_chars = [c for c in text if c.isalpha()]
        if len(alpha_chars) > 10:
            upper_ratio = sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars)
            # Normal text has <15% uppercase; random mashing has ~50%
            if upper_ratio > 0.4:
                return True

        return False

    @staticmethod
    def _is_copy_paste(text: str) -> bool:
        """
        Detect copy-pasted content (Wikipedia articles, news, essays, etc.)
        Real parent answers are personal and conversational. Copy-paste text is:
        - Very long (100+ words)
        - Lacks personal pronouns about a child (my, his, her, their child/son/daughter)
        - Contains formal/encyclopedic markers
        """
        words = text.lower().split()
        word_count = len(words)

        if word_count < 50:
            return False

        text_lower = text.lower()

        # Personal child references — parents almost always use these
        personal_child_refs = [
            "my child", "my son", "my daughter", "my kid",
            "his ", "her ", "he ", "she ", "they ",
            "my boy", "my girl", "our child", "our son", "our daughter",
        ]
        has_personal_ref = any(ref in text_lower for ref in personal_child_refs)

        # Encyclopedic/formal markers — strong signal of copy-paste
        formal_markers = [
            "wikipedia", "encyclopedia", "according to", "citation",
            "references", "published", "founded in", "established in",
            "million", "billion", "organization", "organisation",
            "government", "corporation", "company", "technology",
            "www.", "http", ".com", ".org", ".net",
            "article", "journal", "research shows", "studies have",
            "[edit]", "[citation", "isbn", "doi:",
        ]
        formal_count = sum(1 for marker in formal_markers if marker in text_lower)

        # Sentence count — copy-paste text tends to have many sentences
        sentences = re.split(r'[.!?]+', text)
        sentence_count = len([s for s in sentences if s.strip()])

        # Decision logic:
        # 1. Very long + no personal refs = very likely copy-paste
        if word_count > 80 and not has_personal_ref:
            return True

        # 2. Contains formal/encyclopedic markers
        if formal_count >= 2:
            return True

        # 3. Extremely long regardless (200+ words) — no assessment answer needs this
        if word_count > 200:
            return True

        # 4. Many sentences (10+) without personal refs
        if sentence_count >= 10 and not has_personal_ref:
            return True

        return False

    async def _llm_relevance_check(
        self, text: str, question: str, student_name: str
    ) -> Optional[bool]:
        """
        Use LLM to check if the response is relevant to the assessment question.
        Returns True if relevant, False if not, None if LLM call failed.
        """
        # Truncate very long input to save tokens
        truncated = text[:500] if len(text) > 500 else text

        prompt = f"""You are validating a parent's response in a child educational assessment.

QUESTION ASKED: "{question}"

PARENT'S RESPONSE: "{truncated}"

Is this response a genuine, personal answer about their child that relates to the question?
A valid answer talks about the child's specific experiences, behaviors, or situations.
An INVALID answer is: copied text, random content, off-topic text, Wikipedia articles, news, jokes, or anything not about the child.

Reply with ONLY one word: YES or NO"""

        try:
            result = await self.call_llm(
                prompt,
                format_json=False,
                max_tokens=5,
                temperature=0.1,
            )
            if result:
                answer = result.strip().upper()
                if "YES" in answer:
                    return True
                if "NO" in answer:
                    return False
        except Exception as e:
            logger.warning(f"[InputValidator] LLM relevance check failed: {e}")

        return None  # LLM failed — don't block the user

    @staticmethod
    def _is_irrelevant(text: str, category: str) -> bool:
        """
        Detect clearly off-topic input using keyword overlap.

        Strategy: be very generous — only flag input that has ZERO overlap with
        both the broad child/education word list AND the category-specific list.
        Short inputs (< 8 words) are given the benefit of the doubt and always
        accepted, since brevity doesn't imply irrelevance.
        """
        words = set(re.findall(r"[a-zA-Z']+", text.lower()))

        # Short responses are hard to judge — let them through
        if len(words) < 8:
            return False

        # Accept if ANY word matches the broad child/education set
        if words & CHILD_EDUCATION_WORDS:
            return False

        # Accept if ANY word matches category-specific keywords
        cat_keywords = CATEGORY_KEYWORDS.get(category)
        if cat_keywords and (words & cat_keywords):
            return False

        # Also accept if the union of ALL category keywords has a match
        # (covers cases where the category label is wrong or "general")
        all_category_words: set[str] = set()
        for kw_set in CATEGORY_KEYWORDS.values():
            all_category_words |= kw_set
        if words & all_category_words:
            return False

        # No relevant signal at all — flag as irrelevant
        return True
