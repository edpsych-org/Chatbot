"use client";

import Link from "next/link";
import { useState } from "react";
import PublicLayout from "@/src/components/site/PublicLayout";

type Service = {
  id: string;
  label: string;
  blurb: string;
  items: string[];
};

const SERVICES: Service[] = [
  {
    id: "educational-psychology",
    label: "Educational Psychology",
    blurb:
      "Consultation, assessment and problem-solving for children and young people with a range of developmental issues.",
    items: [
      "Consultation, advice, and problem solving for children and young people with a range of developmental issues",
      "In-depth psychological assessment of learning needs",
      "Dyslexia assessments",
      "Specific learning difficulty assessment",
      "Disability Student Allowance (DSA) assessments and reports",
      "Exam access arrangement assessments",
      "Gifted and Talented, MENSA testing",
      "Managing children / young people with Autistic Spectrum Disorder, ADHD and Learning Difficulties",
      "Behaviour management at home and school",
      "Supporting and understanding emotional issues in children and young people",
      "Parenting education",
      "Assessments for emotional difficulties",
      "Counselling and therapeutic support for children, young people, adults and families",
      "Social skills training for children and young people",
      "Managing anxiety in children and young people",
      "Setting up learning support systems in nurseries, schools and colleges for students with special educational and additional needs",
      "Bespoke training to school staff on topics such as autism, developing meta-cognitive skills, reading comprehension, developing language skills, working with EAL learners and supporting working memory",
      "Supporting English as an Additional Language (EAL) learners",
      "Intelligence / cognitive assessments",
    ],
  },
  {
    id: "occupational-therapy",
    label: "Occupational Therapy",
    blurb:
      "Helping children build the motor, sensory and self-care skills they need to participate fully at home and at school.",
    items: [
      "Assessment of fine and gross motor skills",
      "Sensory processing and integration assessment and therapy",
      "Handwriting assessment and support",
      "Self-care and daily-living skills (dressing, eating, organisation)",
      "Visual perceptual and visual-motor assessment",
      "Classroom-based observations and recommendations",
      "Individual and group therapy programmes",
      "Parent and teacher coaching",
    ],
  },
  {
    id: "speech-language-therapy",
    label: "Speech & Language Therapy",
    blurb:
      "Assessment and intervention across speech, receptive and expressive language, social communication and voice.",
    items: [
      "Full speech, language and communication assessment",
      "Receptive and expressive language intervention",
      "Social communication and pragmatic language support",
      "Speech sound / articulation therapy",
      "Stammering assessment and therapy",
      "Voice assessment and therapy",
      "Language support for bilingual / EAL children",
      "Therapy to support literacy and narrative skills",
    ],
  },
  {
    id: "counselling-therapy",
    label: "Counselling & Therapy",
    blurb:
      "Mental-health support for children, adolescents and families — integrative, age-appropriate and compassionate.",
    items: [
      "Individual counselling for children, adolescents and young adults",
      "Cognitive Behavioural Therapy (CBT)",
      "Art therapy",
      "Music therapy",
      "Play-based therapeutic approaches",
      "Parent-infant psychotherapy",
      "Family therapy",
      "Post-diagnosis parental support",
    ],
  },
  {
    id: "specialist-teaching",
    label: "Specialist Teaching",
    blurb:
      "Targeted, evidence-based teaching for learners with dyslexia and related specific learning difficulties.",
    items: [
      "Structured, multi-sensory literacy programmes",
      "Maths support for children with dyscalculia / number difficulties",
      "Study skills and exam preparation",
      "Individualised learning plans",
      "School liaison and reasonable-adjustment advice",
      "Exam access-arrangement evidence",
    ],
  },
  {
    id: "reflective-parenting",
    label: "Reflective Parenting Session",
    blurb:
      "A reflective space to think about your child's development, behaviour and your relationship together.",
    items: [
      "Individual or couple sessions with a qualified professional",
      "Focus on understanding your child's needs and responses",
      "Practical strategies tailored to your family",
      "Useful around key transitions (nursery, school, teens)",
      "Supportive, non-judgemental and confidential",
    ],
  },
];

export default function ServicesPage() {
  const [active, setActive] = useState<string>(SERVICES[0].id);
  const current = SERVICES.find((s) => s.id === active)!;

  return (
    <PublicLayout>
      <section className="bg-gradient-to-br from-teal-50 to-white border-b border-slate-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <nav className="text-sm text-slate-500 mb-4" aria-label="Breadcrumb">
            <Link href="/" className="hover:text-primary">Home</Link>
            <span className="mx-2">/</span>
            <span className="text-slate-700 font-semibold">Services</span>
          </nav>
          <h1 className="text-3xl sm:text-4xl font-black text-slate-900">Services</h1>
          <p className="mt-3 text-slate-600 max-w-3xl">
            Our multidisciplinary team offers tailored assessments and therapeutic
            services for children, adolescents and young adults.
          </p>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid md:grid-cols-[260px,1fr] gap-8">
          <aside>
            <ul className="space-y-1 bg-white rounded-xl p-2 border border-slate-100 shadow-sm">
              {SERVICES.map((s) => (
                <li key={s.id}>
                  <button
                    onClick={() => setActive(s.id)}
                    className={`w-full text-left px-3 py-2.5 rounded-lg text-sm font-semibold transition-colors ${
                      active === s.id
                        ? "bg-primary text-white"
                        : "text-slate-700 hover:bg-teal-50"
                    }`}
                  >
                    {s.label}
                  </button>
                </li>
              ))}
            </ul>
          </aside>

          <div className="bg-white rounded-xl p-6 sm:p-8 border border-slate-100 shadow-sm">
            <h2 className="text-2xl font-bold text-slate-900 mb-2">{current.label}</h2>
            <p className="text-slate-600 mb-6">{current.blurb}</p>
            <ul className="space-y-2">
              {current.items.map((item) => (
                <li key={item} className="flex gap-2 text-slate-700">
                  <span className="text-primary font-bold mt-0.5">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
            <div className="mt-8 pt-6 border-t border-slate-100 flex flex-wrap gap-3">
              <Link href="/contact" className="ed-btn-primary px-5 py-2.5 rounded-lg font-bold text-sm">
                Request an assessment
              </Link>
              <a
                href="tel:+447833447356"
                className="px-5 py-2.5 rounded-lg font-bold text-sm bg-white border border-primary text-primary hover:bg-teal-50"
              >
                Call +44 (0) 78 3344 7356
              </a>
            </div>
          </div>
        </div>
      </section>
    </PublicLayout>
  );
}
