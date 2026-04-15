"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import PublicLayout from "@/src/components/site/PublicLayout";

function dashboardHrefFor(role?: string): string {
  const r = (role || "").toUpperCase();
  if (r === "PSYCHOLOGIST") return "/psychologist/dashboard";
  if (r === "ADMIN") return "/admin/dashboard";
  return "/dashboard";
}

export default function HomePage() {
  const [dashboardHref, setDashboardHref] = useState<string | null>(null);

  useEffect(() => {
    try {
      const token = localStorage.getItem("access_token");
      if (!token) return;
      const raw = localStorage.getItem("user");
      const role = raw ? JSON.parse(raw)?.role : undefined;
      setDashboardHref(dashboardHrefFor(role));
    } catch {
      /* ignore */
    }
  }, []);

  return (
    <PublicLayout>
      {dashboardHref && (
        <div className="bg-emerald-50 border-b border-emerald-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2.5 text-sm text-emerald-800 flex items-center justify-between gap-4">
            <span>Welcome back — you&apos;re signed in.</span>
            <Link href={dashboardHref} className="font-semibold hover:underline">
              Go to your dashboard →
            </Link>
          </div>
        </div>
      )}

      {/* Hero */}
      <section className="bg-gradient-to-br from-teal-50 via-white to-emerald-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24">
          <div className="max-w-3xl">
            <p className="text-sm font-bold text-primary uppercase tracking-wider mb-3">
              Welcome to The Ed Psych Practice
            </p>
            <h1 className="text-3xl sm:text-5xl font-black text-slate-900 leading-tight mb-6">
              In-depth, evidence-based assessments and therapy to support{" "}
              <span className="text-primary">children and young people</span>.
            </h1>
            <p className="text-lg text-slate-600 mb-8 leading-relaxed">
              A multidisciplinary private practice in Marylebone, Central London —
              educational psychologists, speech &amp; language therapists, occupational
              therapists, counsellors, and specialist teachers working together for
              each child&apos;s needs.
            </p>
            <div className="flex flex-wrap gap-3">
              <Link href="/contact" className="ed-btn-primary px-6 py-3 rounded-lg font-bold">
                Contact Us
              </Link>
              <Link
                href="/services"
                className="px-6 py-3 rounded-lg font-bold bg-white border-2 border-primary text-primary hover:bg-teal-50"
              >
                Explore Services
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Welcome body */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 mb-6">
          Educational Psychologists in London
        </h2>
        <div className="prose max-w-none text-slate-700 space-y-4">
          <p>
            Our team is dedicated to enhancing the academic performance and
            psychological well-being of children, adolescents, and young adults in
            London. We are a multidisciplinary practice with a strong team of
            educational psychologists, neurodevelopmental paediatricians, speech
            &amp; language therapists, and occupational therapists. Our mental health
            professionals also offer art therapy, music therapy, psychotherapy,
            cognitive behavioural therapy, and post-diagnosis parental support.
          </p>
          <p>
            Our practice is located in Marylebone, Central London, where all
            assessments and therapy sessions take place. We also offer our services
            online. Depending on the child&apos;s needs, we can conduct school-based
            observations and assessments, and we collaborate with families, schools,
            and local authorities to achieve the most beneficial outcomes for the
            child.
          </p>
        </div>

        <div className="mt-8 flex flex-wrap gap-6 text-sm">
          <span>
            <strong>Email:</strong>{" "}
            <a href="mailto:office@theedpsych.com" className="text-primary hover:underline">
              office@theedpsych.com
            </a>
          </span>
          <span>
            <strong>Phone:</strong>{" "}
            <a href="tel:+447833447356" className="text-primary hover:underline">
              +44 (0) 7833 447 356
            </a>
          </span>
        </div>
      </section>

      {/* Services we offer */}
      <section className="bg-slate-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <h2 className="text-2xl sm:text-3xl font-bold text-center text-slate-900 mb-10">
            Services we offer
          </h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-100">
              <h3 className="text-xl font-bold text-primary mb-4">For Individuals</h3>
              <ul className="space-y-2 text-slate-700">
                <li>• Educational Psychology</li>
                <li>• Occupational Therapy</li>
                <li>• Speech &amp; Language Therapy</li>
                <li>• Counselling &amp; Therapy</li>
                <li>• Specialist Teaching</li>
              </ul>
              <Link
                href="/services"
                className="inline-block mt-6 font-bold text-primary hover:underline"
              >
                Read More →
              </Link>
            </div>
            <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-100">
              <h3 className="text-xl font-bold text-primary mb-4">For Schools</h3>
              <ul className="space-y-2 text-slate-700">
                <li>• Consultations</li>
                <li>• Early Intervention</li>
                <li>• Group Intervention</li>
                <li>• Training</li>
                <li>• Policy Development and Coaching</li>
              </ul>
              <Link
                href="/schools"
                className="inline-block mt-6 font-bold text-primary hover:underline"
              >
                Read More →
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Book an Appointment */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <h2 className="text-2xl sm:text-3xl font-bold text-center text-slate-900 mb-10">
          Book an Appointment
        </h2>
        <div className="grid md:grid-cols-3 gap-6">
          {[
            {
              icon: "phone-appointment.png",
              title: "Talk to us",
              body: (
                <>
                  Call us on{" "}
                  <a href="tel:+447833447356" className="text-primary font-semibold">
                    (0) 78 3344 7356
                  </a>{" "}
                  or{" "}
                  <a href="tel:+447990538654" className="text-primary font-semibold">
                    (0) 79 9053 8654
                  </a>{" "}
                  and let us know about the issues you are dealing with.
                </>
              ),
            },
            {
              icon: "calendar-appointment.png",
              title: "Book availability",
              body: (
                <>
                  Get availability of highly experienced psychologists &amp;
                  therapists suitable for your needs and book the appointment for
                  you.
                </>
              ),
            },
            {
              icon: "meet-appointment.png",
              title: "Meet the practitioner",
              body: (
                <>
                  Meet the practitioner and start the road to self-improvement. Have
                  any concerns?{" "}
                  <Link href="/contact" className="text-primary font-semibold">
                    Contact us
                  </Link>{" "}
                  so that we can assist.
                </>
              ),
            },
          ].map((step) => (
            <div key={step.title} className="text-center p-6">
              <img
                src={`/images/appointment/${step.icon}`}
                alt=""
                className="w-16 h-16 mx-auto mb-4 object-contain"
              />
              <h3 className="font-bold text-slate-900 mb-2">{step.title}</h3>
              <p className="text-sm text-slate-600 leading-relaxed">{step.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Registered with */}
      <section className="bg-slate-50 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-center text-lg font-bold text-slate-700 mb-8 uppercase tracking-wider">
            Practitioners Registered With
          </h2>
          <div className="flex flex-wrap justify-center items-center gap-8">
            {["bps", "hcpc", "rcot", "rcslt", "baat", "bamt", "patoss"].map((c) => (
              <img
                key={c}
                src={`/images/certified/${c}.png`}
                alt={`${c.toUpperCase()} certification`}
                className="h-12 sm:h-14 w-auto"
              />
            ))}
          </div>
        </div>
      </section>
    </PublicLayout>
  );
}
