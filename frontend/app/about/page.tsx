import Link from "next/link";
import PublicLayout from "@/src/components/site/PublicLayout";

export const metadata = {
  title: "About Us — The Ed Psych Practice, London",
  description:
    "The Ed Psych Practice is an independent multidisciplinary team in Central London supporting children and young people since 2010.",
};

export default function AboutPage() {
  return (
    <PublicLayout>
      <section className="bg-gradient-to-br from-teal-50 to-white border-b border-slate-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <nav className="text-sm text-slate-500 mb-4" aria-label="Breadcrumb">
            <Link href="/" className="hover:text-primary">Home</Link>
            <span className="mx-2">/</span>
            <span className="text-slate-700 font-semibold">About Us</span>
          </nav>
          <h1 className="text-3xl sm:text-4xl font-black text-slate-900">About Us</h1>
        </div>
      </section>

      <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-6 text-slate-700 leading-relaxed">
        <p>
          We are an independent practice based in Central London, United Kingdom,
          consisting of educational psychologists, therapists, occupational
          therapists, specialist teachers and speech &amp; language therapists who
          work closely with families, nurseries, primary and secondary schools,
          colleges, paediatricians and other professionals. Together we support
          children and young people for whom there are concerns about learning,
          emotional well-being and developmental progress.
        </p>
        <p>
          The Ed Psych Practice was established in January 2010.
        </p>
        <p>
          Our philosophy is to provide in-depth, evidence-based assessments to
          support children and young people with a range of developmental needs
          across educational and home settings so that they can achieve.
        </p>

        <div className="pt-6">
          <Link href="/contact" className="ed-btn-primary px-6 py-3 rounded-lg font-bold">
            Get in touch →
          </Link>
        </div>
      </section>
    </PublicLayout>
  );
}
