"use client";

import Link from "next/link";
import { useState } from "react";
import PublicLayout from "@/src/components/site/PublicLayout";
import { reportClientError } from "@/src/lib/logger";

type Status = "idle" | "sending" | "sent" | "error";

export default function ContactPage() {
  const [form, setForm] = useState({ name: "", email: "", mobile: "", message: "" });
  const [status, setStatus] = useState<Status>("idle");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const onChange =
    (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
      setForm((f) => ({ ...f, [k]: e.target.value }));

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErrorMsg(null);
    if (!form.name.trim() || !form.email.trim() || !form.message.trim()) {
      setErrorMsg("Please fill in your name, email and message.");
      return;
    }
    setStatus("sending");
    try {
      // Stub for now — sends to client-error sink (which the user will wire to a real endpoint later).
      await new Promise((r) => setTimeout(r, 400));
      setStatus("sent");
      setForm({ name: "", email: "", mobile: "", message: "" });
    } catch (err) {
      reportClientError(err, { form: "contact" });
      setStatus("error");
      setErrorMsg("Something went wrong. Please call us on +44 (0) 78 3344 7356.");
    }
  }

  return (
    <PublicLayout>
      <section className="bg-gradient-to-br from-teal-50 to-white border-b border-slate-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <nav className="text-sm text-slate-500 mb-4" aria-label="Breadcrumb">
            <Link href="/" className="hover:text-primary">Home</Link>
            <span className="mx-2">/</span>
            <span className="text-slate-700 font-semibold">Contact Us</span>
          </nav>
          <h1 className="text-3xl sm:text-4xl font-black text-slate-900">Contact Us</h1>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 grid md:grid-cols-2 gap-10">
        {/* form */}
        <div className="bg-white rounded-xl p-6 sm:p-8 border border-slate-100 shadow-sm">
          <h2 className="text-xl font-bold text-slate-900 mb-5">Keen to get in touch?</h2>
          <form onSubmit={onSubmit} className="space-y-4">
            <input
              type="text"
              placeholder="Name*"
              value={form.name}
              onChange={onChange("name")}
              className="w-full px-4 py-3 border border-slate-200 rounded-lg focus:outline-none focus:border-primary"
              required
            />
            <input
              type="email"
              placeholder="Email*"
              value={form.email}
              onChange={onChange("email")}
              className="w-full px-4 py-3 border border-slate-200 rounded-lg focus:outline-none focus:border-primary"
              required
            />
            <input
              type="tel"
              placeholder="Mobile"
              value={form.mobile}
              onChange={onChange("mobile")}
              className="w-full px-4 py-3 border border-slate-200 rounded-lg focus:outline-none focus:border-primary"
            />
            <textarea
              placeholder="Message*"
              rows={6}
              value={form.message}
              onChange={onChange("message")}
              className="w-full px-4 py-3 border border-slate-200 rounded-lg focus:outline-none focus:border-primary"
              required
            />
            {errorMsg && <p className="text-sm text-red-600">{errorMsg}</p>}
            {status === "sent" && (
              <p className="text-sm text-emerald-600 font-semibold">
                Thanks — we&apos;ll be in touch shortly.
              </p>
            )}
            <button
              type="submit"
              disabled={status === "sending"}
              className="ed-btn-primary px-6 py-3 rounded-lg font-bold disabled:opacity-60"
            >
              {status === "sending" ? "Sending…" : "SEND"}
            </button>
          </form>
        </div>

        {/* office details */}
        <div className="space-y-6">
          <div className="bg-white rounded-xl p-6 sm:p-8 border border-slate-100 shadow-sm">
            <h2 className="text-xl font-bold text-slate-900 mb-4">Our Office</h2>
            <address className="not-italic text-slate-700 leading-relaxed mb-4">
              The Ed Psych Practice
              <br />
              23 Harcourt Street
              <br />
              London W1H 4HJ
              <br />
              United Kingdom
            </address>
            <div className="space-y-2 text-sm">
              <p>
                <strong>Enquiries &amp; Appointments</strong>
              </p>
              <p>
                Phone:{" "}
                <a href="tel:+447833447356" className="text-primary font-semibold hover:underline">
                  +44 (0) 78 3344 7356
                </a>
              </p>
              <p>
                Email:{" "}
                <a
                  href="mailto:office@theedpsych.com"
                  className="text-primary font-semibold hover:underline"
                >
                  office@theedpsych.com
                </a>
              </p>
              <p className="pt-3">
                <a
                  href="https://citipark.co.uk/car-parks/london/bell-street"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary font-semibold hover:underline"
                >
                  Click here for nearest parking
                </a>{" "}
                <span className="text-slate-500">(outside congestion zone)</span>
              </p>
            </div>
          </div>

          <div className="bg-white rounded-xl overflow-hidden border border-slate-100 shadow-sm">
            <iframe
              title="Map to 23 Harcourt Street, London W1H 4HJ"
              src="https://maps.google.com/maps?ll=51.519792,-0.164659&z=16&t=m&hl=en-GB&gl=GB&mapclient=embed&q=23%20Harcourt%20St%20London%20W1H%204HJ%20UK&output=embed"
              className="w-full h-72 border-0"
              loading="lazy"
            />
          </div>
        </div>
      </section>
    </PublicLayout>
  );
}
