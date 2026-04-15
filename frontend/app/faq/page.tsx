import Link from "next/link";
import PublicLayout from "@/src/components/site/PublicLayout";

export const metadata = {
  title: "Frequently Asked Questions — The Ed Psych Practice",
  description:
    "Answers to common questions about educational psychology, speech & language therapy and occupational therapy assessments at The Ed Psych Practice.",
};

type Faq = { q: string; a: string };

const FAQS: Faq[] = [
  {
    q: "What should I do if I am concerned about my child's progress at school?",
    a: "Start by speaking to the class teacher or SENCO. If you are still worried after that conversation, contact us to arrange a consultation or a full assessment — we can often clarify what is going on and suggest the next steps.",
  },
  {
    q: "What will a full assessment by an Educational Psychologist, Occupational Therapist, Counselling Therapist or Speech Therapist include?",
    a: "A full assessment typically involves reviewing background information, direct work with the child using standardised tools, conversations with parents/carers (and, where useful, school staff), and a written report with findings and recommendations.",
  },
  {
    q: "Do I need to let the school know that my child is going to see an independent professional?",
    a: "It isn't required, but we strongly encourage it. Schools are an important part of the picture and are usually keen to work with us. With your permission we can share the report so that recommendations can be used to support your child day-to-day.",
  },
  {
    q: "Why would my child need an assessment by an Educational Psychologist (EP)?",
    a: "An EP assessment can help where there are concerns about learning, attention, memory, cognition, emotional well-being or progress compared to peers — and is often used to guide dyslexia diagnosis, exam access arrangements and Education, Health & Care Plans.",
  },
  {
    q: "Why would my child need an assessment by a Speech and Language Therapist?",
    a: "A speech & language therapy assessment looks at how your child understands language, uses language and produces speech sounds. It is indicated where there are worries about talking, listening, following instructions, social communication or stammering.",
  },
  {
    q: "My child is due to be seen for a speech and language therapy assessment. What will the assessment involve?",
    a: "The therapist will use play-based and standardised activities appropriate to your child's age to look at understanding, expression, speech sounds and social communication. Parents are usually asked to share developmental history and current concerns.",
  },
  {
    q: "What is a multi-disciplinary assessment?",
    a: "Two or more professionals (for example an Educational Psychologist and a Speech & Language Therapist) see your child and share findings. This is particularly helpful when several areas — learning, language, attention and sensory — may be interacting.",
  },
  {
    q: "How often should an EP assessment be carried out?",
    a: "There is no fixed rule. As a guide, cognitive assessments are usually considered valid for around two to three years. A re-assessment is sensible if circumstances change, at key transitions, or when evidence is needed for access arrangements.",
  },
  {
    q: "What does an EP assessment involve?",
    a: "Direct 1:1 work with your child using standardised tests of cognition, literacy and attention, observations, conversations with parents and sometimes teachers, and a written report with recommendations you can share with school.",
  },
  {
    q: "Where will my child be assessed?",
    a: "Assessments usually take place at our practice in Marylebone. In some cases — particularly for school-age children — we can carry out observations and assessments on school premises, and we also offer remote assessment where appropriate.",
  },
  {
    q: "What is the assessment procedure at the practice?",
    a: "After you get in touch we will send a short questionnaire and agree an appointment. The assessment itself typically runs across one or two sessions, followed by a feedback conversation and a detailed written report within a couple of weeks.",
  },
  {
    q: "Will I get a report?",
    a: "Yes. Every assessment is accompanied by a detailed written report with findings, diagnosis where appropriate, and concrete recommendations for home and school.",
  },
  {
    q: "How are SLT and OT assessments carried out?",
    a: "Both use age-appropriate standardised tools alongside observation and parent interview. Speech & language work covers understanding, expression, speech sounds and social communication; occupational therapy looks at motor skills, sensory processing and daily-living skills.",
  },
  {
    q: "Do I need a referral from my GP for an assessment with an EP, SLT or OT?",
    a: "No — you can contact us directly. If your child is already under the care of a paediatrician or CAMHS team, it is helpful for us to know that when we speak.",
  },
  {
    q: "Where do the ongoing SLT and OT sessions take place?",
    a: "Ongoing therapy sessions usually happen at our practice in Marylebone, or at your child's school where that is more practical. Some sessions can be delivered online.",
  },
  {
    q: "How many sessions will my child need and how long will they last?",
    a: "This depends entirely on the child and the goals. After assessment we agree a therapy plan with you — typically sessions are 45–60 minutes, weekly, in blocks that we review together.",
  },
  {
    q: "What is Occupational Therapy in children and young people?",
    a: "Paediatric occupational therapy supports the skills children need to do the things expected of them day to day — handwriting, self-care, concentration and play. It often involves sensory-processing work as well as motor-skill and cognitive-strategy teaching.",
  },
];

export default function FaqPage() {
  return (
    <PublicLayout>
      <section className="bg-gradient-to-br from-teal-50 to-white border-b border-slate-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <nav className="text-sm text-slate-500 mb-4" aria-label="Breadcrumb">
            <Link href="/" className="hover:text-primary">Home</Link>
            <span className="mx-2">/</span>
            <span className="text-slate-700 font-semibold">FAQs</span>
          </nav>
          <h1 className="text-3xl sm:text-4xl font-black text-slate-900">
            Frequently Asked Questions
          </h1>
          <p className="mt-3 text-slate-600 max-w-3xl">
            A few of the questions parents, schools and professionals ask most
            often. Can&apos;t see what you&apos;re looking for?{" "}
            <Link href="/contact" className="text-primary font-semibold hover:underline">
              Get in touch
            </Link>{" "}
            and we&apos;ll help.
          </p>
        </div>
      </section>

      <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-3">
        {FAQS.map((item, i) => (
          <details
            key={i}
            className="group bg-white border border-slate-200 rounded-xl overflow-hidden"
          >
            <summary className="flex items-center justify-between cursor-pointer px-5 py-4 font-semibold text-slate-900 hover:bg-teal-50 list-none">
              <span className="pr-4">{item.q}</span>
              <span className="flex-shrink-0 w-7 h-7 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold transition-transform group-open:rotate-45">
                +
              </span>
            </summary>
            <div className="px-5 pb-5 text-slate-700 leading-relaxed">{item.a}</div>
          </details>
        ))}
      </section>
    </PublicLayout>
  );
}
