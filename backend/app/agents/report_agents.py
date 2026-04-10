"""
Report Agents — Multi-agent debate pipeline for the Psychologist Reports Workspace.

Architecture:
  BackgroundSummaryAgent uses a 3-stage internal pipeline:
    1. DataAnalystAgent    — extracts every usable data point from raw parent JSON
    2. ClinicalInterpreter — interprets the data through a clinical developmental lens
    3. ReportSynthesizer   — writes the final professional report, reconciling the two views

  IQScoreExtractorAgent  : raw PDF/OCR text -> structured scores JSON
  CognitiveReportAgent   : structured scores -> narrative markdown (also multi-stage)
  UnifiedInsightsAgent   : background + cognitive markdowns -> bridging narrative

Each agent inherits from BaseAgent and uses Groq/Ollama via call_llm / call_llm_json.
"""

import asyncio
import json
import logging
from typing import Optional

from app.agents.base import BaseAgent
from app.core.config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# 1. Background Summary Agent — Multi-agent debate pipeline
# ============================================================================
class BackgroundSummaryAgent(BaseAgent):
    """
    Multi-agent pipeline that produces a clinical-grade background summary.

    Stage 1 — Data Analyst: extracts and structures every data point from raw JSON
    Stage 2 — Clinical Interpreter: reads the analyst's output and produces clinical
              interpretations, inferences, and developmental observations
    Stage 3 — Report Synthesizer: reads BOTH outputs and writes the final polished
              report in professional educational psychology style
    """

    def __init__(self):
        super().__init__(
            name="BackgroundSummaryAgent",
            timeout=90.0,
            max_tokens=3000,
        )

    async def generate(self, context_data: dict, student_name: str) -> str:
        try:
            user_profile = context_data.get("user_profile", {}) or {}
            assessment_data = context_data.get("assessment_data", {}) or {}
            completed_qa_pairs = context_data.get("completed_qa_pairs", []) or []

            profile_json = json.dumps(user_profile, indent=2, default=str)
            assessment_json = json.dumps(assessment_data, indent=2, default=str)
            qa_json = json.dumps(completed_qa_pairs, indent=2, default=str)

            first_name = student_name.split()[0] if student_name else "the child"

            raw_data_block = f"""User Profile:
{profile_json}

Assessment Responses:
{assessment_json}

Completed Q&A Pairs:
{qa_json}"""
            # Truncate raw data to fit within Groq free tier token limits
            raw_data_block = raw_data_block[:4000]

            # ── STAGE 1: Data Analyst ──
            logger.info(f"[BackgroundSummaryAgent] Stage 1/3: Data Analyst for {student_name}")
            analyst_output = await self._run_data_analyst(
                raw_data_block, student_name, first_name
            )
            if not analyst_output:
                analyst_output = f"Raw data available for {student_name}. Data extraction inconclusive — proceed with direct interpretation of source material."
            # Truncate to stay within Groq TPM limits
            analyst_output = analyst_output[:3000]

            # Wait for Groq rate limit (skipped for OpenAI)
            if settings.USE_GROQ:
                logger.info(f"[BackgroundSummaryAgent] Stage 1 complete, waiting 35s for Groq rate limit...")
                await asyncio.sleep(35)

            # ── STAGE 2: Clinical Interpreter ──
            logger.info(f"[BackgroundSummaryAgent] Stage 2/3: Clinical Interpreter for {student_name}")
            interpreter_output = await self._run_clinical_interpreter(
                analyst_output, student_name, first_name
            )
            if not interpreter_output:
                interpreter_output = f"Clinical interpretation unavailable — synthesizer should work directly from analyst output."
            interpreter_output = interpreter_output[:3000]

            # Wait for Groq rate limit (skipped for OpenAI)
            if settings.USE_GROQ:
                logger.info(f"[BackgroundSummaryAgent] Stage 2 complete, waiting 35s for Groq rate limit...")
                await asyncio.sleep(35)

            # ── STAGE 3: Report Synthesizer ──
            logger.info(f"[BackgroundSummaryAgent] Stage 3/3: Report Synthesizer for {student_name}")
            final_report = await self._run_report_synthesizer(
                analyst_output, interpreter_output,
                student_name, first_name
            )

            if final_report and len(final_report.strip()) > 0:
                return final_report.strip()

            return "Unable to generate background summary: the synthesis pipeline returned no content. Please try again or start with a blank editor."

        except Exception as e:
            logger.error(f"[BackgroundSummaryAgent] pipeline failed: {e}", exc_info=True)
            return f"Unable to generate background summary: {str(e)}"

    async def _run_data_analyst(
        self, raw_data: str, student_name: str, first_name: str
    ) -> Optional[str]:
        prompt = f"""You are a data extraction specialist working within an educational psychology team. Your job is to read raw questionnaire data and extract EVERY usable observation, fact, and data point — no matter how small.

CHILD: {student_name}

RAW QUESTIONNAIRE DATA:
{raw_data}

Extract and organise ALL data points under these categories. For each, list every specific observation you can find — exact words the parent used, specific examples, frequencies, durations, contexts:

HEALTH & DEVELOPMENTAL HISTORY:
- Age, gender (if stated)
- Developmental milestones mentioned
- Medical history, medications, diagnoses
- Birth history, neonatal complications
- Current health, sensory concerns (vision, hearing)

FAMILIAL HISTORY:
- Family history of SpLD (dyslexia, dyscalculia, dyspraxia)
- Family history of ADHD, ASD, or other neurodevelopmental conditions
- Learning difficulties in siblings or parents
- Any noted hereditary patterns

LINGUISTIC HISTORY:
- First language, additional languages spoken at home
- Speech and language therapy history
- Language development milestones
- Current expressive and receptive language observations

EDUCATION HISTORY:
- Schools attended, year group
- SEND support received, EHCPs, IEPs
- Previous assessments (educational psychology, speech & language, occupational therapy)
- Interventions tried and their outcomes
- Attendance patterns

CURRENT SITUATION:
- Home life, family structure, living situation
- Current concerns, reason for referral
- Emotional presentation, social functioning, behavioural presentation
- Current coping strategies, interests, and strengths
- Any recent changes or stressors

TEST CONDITIONS:
- Where the assessment took place
- Rapport and engagement during assessment
- Any factors that may have affected validity (fatigue, anxiety, medication, illness)
- Observations of the child during testing

IMPORTANT: Extract the ACTUAL data. If a parent answered "often" to a question about focus difficulties, record "Parent reported focus difficulties occur 'often'". If the data for a category is thin, still extract what exists — even a single data point matters. Do NOT write "no data available" — instead note what CAN be inferred from adjacent responses. Be concise — use short bullet points, not long paragraphs.

TONE: Always extract and highlight STRENGTHS and POSITIVE observations alongside any difficulties. Note interests, talents, supportive relationships, positive coping strategies, and areas where the child is thriving. Every child has strengths — make sure they are captured."""

        return await self.call_llm(prompt, max_tokens=1500, temperature=0.2)

    async def _run_clinical_interpreter(
        self, analyst_output: str,
        student_name: str, first_name: str
    ) -> Optional[str]:
        prompt = f"""You are a senior clinical educational psychologist reviewing extracted data about {student_name}. A data analyst has organised the raw questionnaire responses below. Provide CLINICAL INTERPRETATION — what does this mean developmentally and educationally?

DATA ANALYST'S EXTRACTION:
{analyst_output}

For each domain below, provide your clinical interpretation. Think like a psychologist in a case conference — what patterns do you see? What do these observations suggest? What would you want to investigate further?

DEVELOPMENTAL & HEALTH INTERPRETATION:
- What does the available health and developmental information tell us about {first_name}'s developmental trajectory?
- Are there any red flags or protective factors in the birth, medical, or developmental history?
- What is the likely impact of any health or developmental factors on current functioning?

FAMILIAL RISK INTERPRETATION:
- Is there a familial loading for SpLD, ADHD, ASD, or other neurodevelopmental conditions?
- What does the family history suggest about genetic or hereditary risk?
- How should familial factors inform diagnostic hypotheses?

LINGUISTIC DEVELOPMENT INTERPRETATION:
- What does the linguistic history suggest about {first_name}'s language development?
- Are there indicators of speech, language, or communication needs?
- Could bilingualism or EAL status be a factor in the presenting concerns?
- How might linguistic history interact with literacy development?

EDUCATIONAL HISTORY INTERPRETATION:
- What does {first_name}'s educational trajectory reveal about the nature and persistence of difficulties?
- Have previous interventions been appropriate and effective?
- What do patterns of SEND support, school changes, or assessment history suggest?
- Are there indicators of unmet needs within the educational setting?

CURRENT PRESENTATION INTERPRETATION:
- What does the current home, social, emotional, and behavioural presentation suggest about {first_name}'s needs?
- Are there signs of anxiety, low self-esteem, emotional dysregulation, or social communication difficulties?
- What strengths, interests, and protective factors are evident?
- What environmental or contextual factors are influencing the current picture?

KEY CLINICAL HYPOTHESES:
- List 2-4 clinical hypotheses that could explain the overall pattern
- Note which require further investigation through direct assessment

Be bold in your interpretations. Draw on your clinical knowledge to connect dots the raw data alone cannot. Where data is sparse, use what IS available to make reasonable clinical inferences. Be concise — focus on key clinical observations.

CRITICAL TONE REQUIREMENT: This report will be read by PARENTS. Adopt a STRENGTHS-BASED, empathetic tone throughout. Lead each section with positives before discussing areas of difficulty. Frame difficulties as "areas for development" or "areas where support would be beneficial" — NEVER use deficit-focused or negative language. Highlight the child's resilience, effort, and potential. Even when noting clinical concerns, balance them with protective factors and strengths. Parents should feel understood and hopeful after reading this report, not distressed.

NEVER CRITICISE PARENTS OR SCHOOLS: Do NOT imply that parents have been neglectful, unsupportive, or have failed their child. Do NOT suggest schools have been inadequate, incompetent, or have missed things. If interventions were delayed or support was limited, frame it neutrally — e.g., "Further assessment was sought to better understand {first_name}'s needs" rather than "The school failed to identify..." or "Despite parents not seeking help earlier...". Acknowledge the efforts parents and schools have already made. Frame gaps in support as systemic or as opportunities for enhanced provision, NEVER as failures by individuals or institutions."""

        return await self.call_llm(prompt, max_tokens=1500, temperature=0.4)

    async def _run_report_synthesizer(
        self, analyst_output: str, interpreter_output: str,
        student_name: str, first_name: str
    ) -> Optional[str]:
        prompt = f"""You are a Chartered Educational Psychologist writing the BACKGROUND INFORMATION section of a Confidential Diagnostic Assessment Report for {student_name}. Synthesise the analyst extraction and clinical interpretation below into a polished, publishable report section.

ANALYST EXTRACTION:
{analyst_output}

CLINICAL INTERPRETATION:
{interpreter_output}

Write in authoritative third-person clinical prose. NEVER say "data was insufficient" or "no information was available" — these are BANNED. If information is limited, frame gaps as areas for direct assessment. Use varied phrasing: "{first_name} was described as...", "Concerns were raised regarding...", "{first_name} presents with...", "Parental accounts indicate...". Each subsection: 3-6 sentences of substantive professional clinical prose.

CRITICAL TONE: This report is read by PARENTS. Use a STRENGTHS-BASED, warm, and empathetic tone. Lead each subsection with POSITIVE observations before discussing areas of difficulty. Frame challenges constructively — use "areas where support would be beneficial" rather than deficit language. Highlight {first_name}'s strengths, interests, resilience, and positive qualities throughout. Parents should feel that their child is understood and valued, not labelled negatively. NEVER use blunt negative statements like "{first_name} struggles with..." or "{first_name} has poor..." — instead use "{first_name} would benefit from additional support with..." or "An area for development is...".

NEVER CRITICISE PARENTS OR SCHOOLS: Do NOT imply parents were neglectful, unsupportive, or slow to act. Do NOT suggest schools failed, missed signs, or provided inadequate support. Acknowledge the efforts parents and schools have ALREADY made. If support was delayed, frame neutrally — "Further assessment was sought to clarify {first_name}'s needs" NOT "The school failed to identify...". Frame gaps as opportunities for enhanced provision, not failures.

Use EXACTLY these headings and structure:

## BACKGROUND INFORMATION

### Health and developmental history
Cover birth history, developmental milestones, medical history, medications, diagnoses, and current health status.

### Familial history of SpLD or other developmental conditions
Cover family history of specific learning difficulties (dyslexia, dyscalculia, dyspraxia), ADHD, ASD, or other neurodevelopmental conditions in parents, siblings, or extended family.

### Linguistic history
Cover first language, additional languages, speech and language development, any speech and language therapy, and current communication profile.

### Education history
Cover schools attended, year group, SEND support, EHCPs, previous assessments, interventions tried, and their outcomes.

### Current Situation
Cover current home life, family structure, reason for referral, current emotional, social, and behavioural presentation, interests, strengths, and any recent changes or stressors.

## TEST CONDITIONS
Describe the assessment conditions including where the assessment took place, rapport established, {first_name}'s engagement and presentation during assessment, and any factors that may have affected the validity of results.

Prose only, no bullets/lists/tables. Do NOT mention AI. Use {first_name} naturally. Begin directly with ## BACKGROUND INFORMATION."""

        return await self.call_llm(prompt, max_tokens=2500, temperature=0.3)


# ============================================================================
# 2. IQ Score Extractor Agent
# ============================================================================
class IQScoreExtractorAgent(BaseAgent):
    """Extracts structured scores from raw IQ test PDF text (OCR or text layer)."""

    def __init__(self):
        super().__init__(
            name="IQScoreExtractorAgent",
            timeout=60.0,
            max_tokens=3000,
        )

    async def extract(self, raw_text: str) -> dict:
        """
        Parse a block of raw IQ-test PDF text into a structured scores dict.

        Returns a dict matching the schema below (organised by test battery):
          {
            "test_batteries": [...],
            "full_scale_iq": {score, percentile, confidence_interval, classification},
            "notes": string | null
          }

        On failure returns {"error": "..."} so the API layer can decide what to do.
        """
        try:
            if not raw_text or not raw_text.strip():
                return {"error": "No text was extracted from the uploaded PDF."}

            snippet = raw_text[:12000]

            prompt = f"""You are extracting structured data from a UK educational psychology assessment report. The report may contain ANY combination of standardised test batteries. Common ones include WISC-VUK, WPPSI-IV, BAS3, KABC-II, WIAT-IIIUK, YARC, WRAT-5, TOWRE-2, CTOPP-2, PhAB-2, BPVS-3, Beery VMI, DTVP-3, BRIEF-2, Conners, and others — but do NOT limit yourself to this list. Extract ALL test batteries and scores found in the text.

RAW REPORT TEXT:
\"\"\"
{snippet}
\"\"\"

Return a SINGLE JSON object matching EXACTLY this schema:

{{
  "test_batteries": [
    {{
      "battery_name": string,
      "test_date": string | null,
      "administered_by": string | null,
      "composites": [
        {{
          "name": string,
          "score": number | null,
          "percentile": number | null,
          "confidence_interval": string | null,
          "classification": string | null
        }}
      ],
      "subtests": [
        {{
          "name": string,
          "score": number | null,
          "percentile": number | null,
          "scaled_score": number | null,
          "confidence_interval": string | null
        }}
      ]
    }}
  ],
  "full_scale_iq": {{
    "score": number | null,
    "percentile": number | null,
    "confidence_interval": string | null,
    "classification": string | null
  }},
  "notes": string | null
}}

Instructions:
- Create one entry in "test_batteries" for EACH distinct test battery found in the report
- Use the battery_name EXACTLY as it appears in the report (e.g., "WISC-VUK", "BAS3", "WIAT-IIIUK")
- "composites" holds index/composite-level scores (e.g., VCI, VSI, FRI for WISC-VUK; Verbal Ability for BAS3; Phonological Awareness for CTOPP-2)
- "subtests" holds individual subtest-level scores within each battery (e.g., Similarities, Block Design; or Word Reading, Spelling)
- "full_scale_iq" should contain the overall cognitive ability score if one exists (FSIQ, GCA, etc.)
- "scaled_score" is for subtest-level scaled scores (typically 1-19 scale); use null if not present

Strict rules:
- Only extract values that are EXPLICITLY present in the text.
- Use null for any field you cannot find. DO NOT invent, guess, or interpolate scores.
- "confidence_interval" should be a string like "95-105" or "90% CI 95-105" if stated; otherwise null.
- "classification" should be the descriptive band exactly as stated in the report (e.g. "Average", "Low Average") if present; otherwise null.
- "test_batteries" should be an array containing one entry per battery found (possibly empty if no scores found).
- Return JSON only — no prose, no markdown code fence."""

            result = await self.call_llm_json(prompt, max_tokens=3000, temperature=0.1)
            if result is None:
                return {"error": "The language model failed to return valid JSON. Please review the PDF manually."}
            return result
        except Exception as e:
            logger.error(f"[IQScoreExtractorAgent] extraction failed: {e}", exc_info=True)
            return {"error": f"Unable to extract scores: {str(e)}"}


# ============================================================================
# 3. Cognitive Report Agent — Multi-stage
# ============================================================================
class CognitiveReportAgent(BaseAgent):
    """Turns structured cognitive scores into a narrative clinical report using multi-stage pipeline."""

    def __init__(self):
        super().__init__(
            name="CognitiveReportAgent",
            timeout=90.0,
            max_tokens=3000,
        )

    async def generate(self, parsed_scores: dict, student_name: str) -> str:
        try:
            scores_json = json.dumps(parsed_scores, indent=2, default=str)
            first_name = student_name.split()[0] if student_name else "the child"

            # Stage 1: Score Interpreter — classify each score clinically
            logger.info(f"[CognitiveReportAgent] Stage 1/2: Score Interpreter for {student_name}")
            interpretation = await self._interpret_scores(scores_json, student_name, first_name)
            if not interpretation:
                interpretation = "Score interpretation unavailable — proceed with direct analysis."

            # Wait for Groq rate limit (skipped for OpenAI)
            if settings.USE_GROQ:
                await asyncio.sleep(20)

            # Stage 2: Report Writer — produce the final clinical narrative
            logger.info(f"[CognitiveReportAgent] Stage 2/2: Report Writer for {student_name}")
            report = await self._write_report(
                scores_json, interpretation, student_name, first_name
            )

            if report and len(report.strip()) > 0:
                return report.strip()

            return "Unable to generate cognitive report: the language model returned no content. Please try again or start with a blank editor."
        except Exception as e:
            logger.error(f"[CognitiveReportAgent] generation failed: {e}", exc_info=True)
            return f"Unable to generate cognitive report: {str(e)}"

    async def _interpret_scores(
        self, scores_json: str, student_name: str, first_name: str
    ) -> Optional[str]:
        prompt = f"""You are a psychometrics specialist working within the UK Educational Psychology framework. Analyse these cognitive test scores for {student_name} and provide clinical classification for each.

SCORES:
{scores_json}

First, identify WHICH test batteries and subtests are present in the data. Different students receive different assessments. Common UK batteries include (but are not limited to):
- Cognitive: WISC-VUK, WPPSI-IV, BAS3, KABC-II, Leiter-3
- Attainments: WIAT-IIIUK, YARC, WRAT-5, BPVS-3
- Reading efficiency: TOWRE-2, YARC
- Phonological: CTOPP-2, PhAB-2
- Other: BRIEF-2, Conners, DTVP-3, Beery VMI, etc.

For each score/subtest/composite ACTUALLY PRESENT in the data, provide:
1. The UK classification band using standard bands ("Extremely Low" <70, "Very Low" 70-79, "Low Average" 80-89, "Average" 90-109, "High Average" 110-119, "Superior" 120-129, "Very Superior" 130+)
2. The percentile rank interpretation
3. Whether this represents a significant strength or weakness relative to the overall profile
4. What this score means functionally — how would it manifest in a classroom?

Do NOT list or comment on tests that are NOT in the data.

Then provide:
- PROFILE ANALYSIS: Is the profile flat or scattered? What is the significance of the scatter?
- PATTERN RECOGNITION: Do the scores suggest any specific conditions (e.g., SpLD, processing difficulties)?
- STRENGTH-WEAKNESS ANALYSIS: What are the clear strengths to build on and areas where support would be beneficial?

CRITICAL TONE: Always lead with STRENGTHS. Identify and emphasise what the child does WELL before discussing areas of difficulty. Frame lower scores as "areas for development" or "areas where support would be beneficial" — NEVER use deficit language like "poor", "weak", or "failed". Even scores in the Low or Very Low range should be contextualised with empathy and hope."""

        return await self.call_llm(prompt, max_tokens=3000, temperature=0.2)

    async def _write_report(
        self, scores_json: str, interpretation: str,
        student_name: str, first_name: str
    ) -> Optional[str]:
        prompt = f"""You are a Chartered Educational Psychologist writing the COGNITIVE ASSESSMENT section of a confidential diagnostic assessment report for {student_name}.

RAW SCORES:
{scores_json}

PSYCHOMETRIC INTERPRETATION:
{interpretation}

Write the final published report section in the style of a senior UK educational psychologist. This section will be read by parents, SENCOs, and potentially tribunals.

IMPORTANT: Different students receive different test batteries. You MUST adapt the report structure to match ONLY the tests actually present in the scores data. Do NOT include sections for tests that were not administered.

Use this ADAPTIVE heading structure — include each section ONLY if the relevant test data exists in the scores:

## MAIN BODY OF REPORT
Write a brief introductory paragraph stating which standardised assessments were actually administered during this assessment and the purpose of each.

## COGNITIVE PROFILE
Include this section ONLY if a cognitive/IQ test was administered (e.g., WISC-VUK, WPPSI-IV, BAS3, KABC-II).
Write an introductory paragraph naming the specific cognitive test used and its purpose.

For each cognitive index/composite found in the data, create a ### subsection using the EXACT test name and index name as it appears in the data (e.g., "### WISC-VUK Verbal Comprehension Index (VCI)" or "### BAS3 Verbal Ability"). For each:
- State the composite score, percentile rank, and UK classification band
- Explain what the index measures
- Describe {first_name}'s performance and functional classroom implications

Then include a ### subsection for the Full-Scale/General Ability score (e.g., "### WISC-VUK Full-Scale IQ: General Ability Level" or "### BAS3 General Conceptual Ability (GCA)"):
- State the overall score, percentile, confidence interval, and classification
- Provide profile scatter analysis and interpretability

## ATTAINMENTS
Include this section ONLY if attainment tests were administered (e.g., WIAT-IIIUK, YARC, WRAT-5).
Write an introductory paragraph naming the specific attainment test(s) used.

For each attainment subtest found in the data, create a ### subsection using the EXACT test name as it appears in the data (e.g., "### WIAT IIIUK Word Reading" or "### YARC Reading Accuracy"). For each:
- State the standard score, percentile rank, and UK classification band
- Describe what was assessed and {first_name}'s performance
- Provide functional implications for the classroom

If TOWRE-2 data is present, include "### Test of Word Reading Efficiency - Second Edition (TOWRE-2)" with scores and interpretation.

## PHONOLOGICAL PROCESSING
Include this section ONLY if phonological tests were administered (e.g., CTOPP-2, PhAB-2).
Write an introductory paragraph naming the specific phonological test used.

For each phonological composite/subtest found in the data, create a ### subsection (e.g., "### Phonological Awareness", "### Rapid Naming"). For each:
- State the composite score, percentile rank, and UK classification band
- Explain what the skill measures and its importance for literacy
- Describe {first_name}'s performance and functional implications

SKIP any major section (COGNITIVE PROFILE, ATTAINMENTS, PHONOLOGICAL PROCESSING) entirely if no data exists for it. Do NOT write "this test was not administered" — simply omit the section.

FORMAT RULES:
- Reference SPECIFIC numeric scores, percentiles, and UK classification bands throughout
- Use standard UK interpretive bands (Extremely Low, Very Low, Low Average, Average, High Average, Superior, Very Superior)
- Professional clinical prose — no bullet lists, no tables
- Do NOT invent scores not in the data
- Do NOT mention AI or "this report"
- Use {first_name} naturally throughout
- Begin directly with "## MAIN BODY OF REPORT" — no preamble

CRITICAL TONE: This report is read by PARENTS. Use a STRENGTHS-BASED tone throughout. For EVERY section, lead with {first_name}'s strengths and what they do well BEFORE discussing areas of difficulty. Frame lower scores empathetically — e.g., "This is an area where {first_name} would benefit from targeted support" rather than "{first_name} performed poorly". Use language like "an area for development", "would benefit from support", "emerging skill". NEVER use blunt negative phrases like "struggled", "failed", "poor performance", "deficient", or "impaired". Celebrate strengths genuinely — if a child has a strong VCI but lower PSI, lead with the verbal strength as a genuine asset. Parents should feel their child is understood, valued, and that there is a clear path forward.

NEVER CRITICISE PARENTS OR SCHOOLS: Do NOT imply parents were neglectful or slow to act. Do NOT suggest schools failed, missed signs, or provided inadequate support. Acknowledge efforts already made by families and educators. Frame any gaps in provision neutrally as opportunities for enhanced support, not as failures by anyone."""

        return await self.call_llm(prompt, max_tokens=3000, temperature=0.3)


# ============================================================================
# 4. Unified Insights Agent — Multi-stage debate
# ============================================================================
class UnifiedInsightsAgent(BaseAgent):
    """Cross-references background summary and cognitive report through debate."""

    def __init__(self):
        super().__init__(
            name="UnifiedInsightsAgent",
            timeout=90.0,
            max_tokens=3000,
        )

    async def synthesize(
        self,
        background_summary: str,
        cognitive_report: str,
        student_name: str,
    ) -> str:
        try:
            first_name = student_name.split()[0] if student_name else "the child"

            # Stage 1: Pattern Analyst — find convergences and divergences
            logger.info(f"[UnifiedInsightsAgent] Stage 1/2: Pattern Analyst for {student_name}")
            analysis = await self._analyse_patterns(
                background_summary, cognitive_report, student_name, first_name
            )
            if not analysis:
                analysis = "Pattern analysis unavailable — proceed with direct synthesis."

            # Wait for Groq rate limit (skipped for OpenAI)
            if settings.USE_GROQ:
                await asyncio.sleep(20)

            # Stage 2: Synthesizer — write the final unified report
            logger.info(f"[UnifiedInsightsAgent] Stage 2/2: Synthesis Writer for {student_name}")
            report = await self._write_synthesis(
                background_summary, cognitive_report, analysis,
                student_name, first_name
            )

            if report and len(report.strip()) > 0:
                return report.strip()

            return "Unable to generate unified insights: the synthesis pipeline returned no content. Please try again or start with a blank editor."
        except Exception as e:
            logger.error(f"[UnifiedInsightsAgent] synthesis failed: {e}", exc_info=True)
            return f"Unable to generate unified insights: {str(e)}"

    async def _analyse_patterns(
        self, background: str, cognitive: str,
        student_name: str, first_name: str
    ) -> Optional[str]:
        prompt = f"""You are a clinical case analyst. You have two independent data sources about {student_name}. Find every connection, contradiction, and pattern between them.

SOURCE 1 — BACKGROUND INFORMATION (from parent questionnaire — includes Health and developmental history, Familial history of SpLD, Linguistic history, Education history, Current Situation, and TEST CONDITIONS):
{background}

SOURCE 2 — COGNITIVE ASSESSMENT (from standardised testing — may include COGNITIVE PROFILE, ATTAINMENTS, and/or PHONOLOGICAL PROCESSING sections depending on which tests were administered):
{cognitive}

Analyse (adapt to whichever test batteries are present in Source 2 — do NOT assume specific tests):
CONVERGENCES: Where do observations from the BACKGROUND INFORMATION (particularly Health and developmental history, Familial history of SpLD, and Linguistic history) CONFIRM what the cognitive, attainment, or phonological scores show? Be specific — which background observation maps to which score or index?
DIVERGENCES: Where do the BACKGROUND INFORMATION sections CONTRADICT or are not fully explained by the assessment data? What might explain this?
HIDDEN PATTERNS: What emerges from reading the BACKGROUND INFORMATION and the cognitive sections together that neither source reveals alone? Pay particular attention to how familial and linguistic history interact with any phonological or attainment findings.
DIAGNOSTIC IMPLICATIONS: What conditions or profiles does the combined evidence point toward? Consider SpLD diagnoses, ADHD, ASD, or processing difficulties in light of the cognitive-attainment discrepancy patterns present.
PROTECTIVE FACTORS & STRENGTHS: Strengths that can be leveraged in intervention planning, drawn from both the background history and the cognitive strengths evident in the assessment data. Include interests, supportive relationships, and areas of resilience.
RISK FACTORS: Any safeguarding, mental health, or urgent educational concerns emerging from the Current Situation or TEST CONDITIONS sections? Frame these sensitively.

TONE: Lead with strengths and protective factors. Frame difficulties as areas for support, not deficits. This analysis feeds the final parent-facing report — ensure a balanced, hopeful perspective."""

        return await self.call_llm(prompt, max_tokens=1500, temperature=0.4)

    async def _write_synthesis(
        self, background: str, cognitive: str, analysis: str,
        student_name: str, first_name: str
    ) -> Optional[str]:
        prompt = f"""You are a Chartered Educational Psychologist writing the UNIFIED INSIGHTS AND RECOMMENDATIONS section of a confidential diagnostic assessment report for {student_name}.

You have the background summary, cognitive report, and an internal pattern analysis from your team.

PATTERN ANALYSIS:
{analysis}

Write the final published section using EXACTLY these headings:

## Convergent Findings
Cross-reference the BACKGROUND INFORMATION subsections with whatever cognitive, attainment, and phonological assessment sections are present in the cognitive report. Where do parent-reported observations align with and are corroborated by the standardised assessment results? Reference specific details from both sources — for example, how familial history maps onto phonological or reading scores, or how reported difficulties align with specific subtest performance. Explain why each convergence is clinically significant. Use the ACTUAL test names from the cognitive report (not assumed ones).

## Divergent Findings and Areas for Further Investigation
Where observations from the BACKGROUND INFORMATION appear to diverge from, or are not fully explained by, the assessment data. Frame these professionally as areas requiring further exploration rather than contradictions. Where relevant, consider whether cognitive index scatter or attainment subtest variability might account for apparent inconsistencies. Suggest what further investigation would help resolve each divergence.

## Integrated Formulation
A clinical formulation that draws together all the evidence — from the BACKGROUND INFORMATION sections through to whatever cognitive, attainment, and phonological data is available — into a coherent narrative about {first_name}'s needs. What is the emerging picture of this child? What are the primary areas of need? What cognitive-attainment discrepancy patterns, if present, are clinically meaningful? What strengths can be built upon?

## Recommendations
Concrete, specific, clinically grounded recommendations organised as:
- Recommendations for school (classroom strategies, accommodations, SEND support — including any SpLD-specific provisions supported by the assessment profiles)
- Recommendations for home (parental strategies, environmental modifications, and ways to support areas of difficulty identified through the assessment)
- Recommendations for intervention (where phonological, literacy, or numeracy difficulties are indicated by the assessment scores, specify the type of structured, evidence-based intervention recommended, its frequency, and the professional best placed to deliver it)
- Recommendations for further assessment (any additional diagnostic conclusions or referrals that follow from the cognitive-attainment discrepancy analysis)
Write these as flowing prose paragraphs, not bullet lists.

FORMAT RULES:
- Professional clinical prose throughout
- Reference specific details from both the BACKGROUND INFORMATION and cognitive report sections using the ACTUAL test names present
- Do NOT rehash either source — synthesise and add clinical value
- Do NOT mention AI, data analysis tools, or "this report"
- Use {first_name} naturally throughout
- Begin directly with "## Convergent Findings" — no preamble

CRITICAL TONE: This section is read by PARENTS. Use a STRENGTHS-BASED, warm, and empathetic tone throughout ALL subsections. Lead every section with positives before discussing areas of need. In Convergent Findings, highlight where strengths are confirmed across sources. In Divergent Findings, frame as "areas warranting further exploration" not problems. In Integrated Formulation, present a balanced picture emphasising {first_name}'s potential and the supports that will help them thrive. In Recommendations, frame as empowering actions the family and school can take — use hopeful, solution-focused language. NEVER use deficit language like "poor", "weak", "deficient", "impaired", or "failed". Instead use "area for development", "would benefit from support", "emerging skill". Parents should finish reading this report feeling understood, hopeful, and empowered to support their child.

NEVER CRITICISE PARENTS OR SCHOOLS: Do NOT imply parents were neglectful, unsupportive, or slow to seek help. Do NOT suggest schools failed to identify needs, provided inadequate support, or missed warning signs. Acknowledge and appreciate the efforts parents and schools have already made. In Recommendations, frame school actions as "building on existing provision" and parent actions as "complementing the support already being provided at home". If earlier intervention could have helped, frame as "with the benefit of this assessment, further targeted support can now be put in place" — NEVER blame anyone for delays."""

        return await self.call_llm(prompt, max_tokens=3000, temperature=0.3)
