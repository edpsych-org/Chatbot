import Link from "next/link";
import PublicLayout from "@/src/components/site/PublicLayout";

export const metadata = {
  title: "Information for Schools — The Ed Psych Practice",
  description:
    "Services, training and consultancy for nurseries, primary schools, secondary schools, sixth-form colleges and special schools, plus international support.",
};

const SECTIONS = [
  {
    heading: "Services for Schools",
    body: (
      <>
        <p>
          A range of services are available for independent and state schools
          including nurseries, primary and secondary schools, sixth-form colleges
          and special schools. To make sure we provide a service tailored to your
          requirements, we will be happy to meet you to discuss the needs of your
          educational establishment.
        </p>
        <ul className="mt-4 space-y-1.5">
          <li>• Consultations with SENCOs and senior leadership</li>
          <li>• Early intervention programmes</li>
          <li>• Group intervention (social skills, literacy, emotional regulation)</li>
          <li>• Bespoke training for teaching staff</li>
          <li>• Policy development and coaching</li>
          <li>• Individual pupil assessments on school premises</li>
        </ul>
      </>
    ),
  },
  {
    heading: "Examples Of Work Carried Out",
    body: (
      <>
        <p>
          Our team of professionals are experienced and are able to deliver a high
          quality of services that are research and evidence based. This can range
          from individual work or group work with children and young people, family
          work and school staff support through training. The support we offer is
          based on the needs of the school.
        </p>
        <ul className="mt-4 space-y-1.5">
          <li>• Whole-class observation and feedback</li>
          <li>• Targeted group interventions run over a term or half-term</li>
          <li>• 1:1 assessment reports to inform Education, Health &amp; Care Plans</li>
          <li>• Staff INSET sessions on autism, ADHD, dyslexia, working memory</li>
          <li>• Reflective supervision for pastoral teams</li>
        </ul>
      </>
    ),
  },
  {
    heading: "International Services",
    body: (
      <>
        <p>
          The Ed Psych Practice provides an international service where a therapist
          or multi-disciplinary team will travel to your home or school in most
          places around the world. Our international service has proved to be a
          popular choice for parents living in countries where services for
          children with special needs may not be particularly well developed, or
          for expatriate families keen to maintain appropriate support for their
          child while abroad. Our therapists ensure that each child&apos;s needs are
          managed in a holistic manner.
        </p>
      </>
    ),
  },
];

export default function SchoolsPage() {
  return (
    <PublicLayout>
      <section className="bg-gradient-to-br from-teal-50 to-white border-b border-slate-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <nav className="text-sm text-slate-500 mb-4" aria-label="Breadcrumb">
            <Link href="/" className="hover:text-primary">Home</Link>
            <span className="mx-2">/</span>
            <span className="text-slate-700 font-semibold">Schools</span>
          </nav>
          <h1 className="text-3xl sm:text-4xl font-black text-slate-900">
            Information for Schools
          </h1>
        </div>
      </section>

      <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-8">
        {SECTIONS.map((s) => (
          <div
            key={s.heading}
            className="bg-white rounded-xl p-6 sm:p-8 border border-slate-100 shadow-sm"
          >
            <h2 className="text-xl sm:text-2xl font-bold text-primary mb-4">
              {s.heading}
            </h2>
            <div className="text-slate-700 leading-relaxed">{s.body}</div>
          </div>
        ))}

        <div className="text-center pt-4">
          <Link href="/contact" className="ed-btn-primary px-6 py-3 rounded-lg font-bold">
            Discuss your school&apos;s needs →
          </Link>
        </div>
      </section>
    </PublicLayout>
  );
}
