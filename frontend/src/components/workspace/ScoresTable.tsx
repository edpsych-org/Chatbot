"use client";

import type { ParsedScores, TestBattery, FullScaleIQ } from "./types";

interface ScoresTableProps {
  scores: ParsedScores | null;
  confidence: number;
  editable?: boolean;
  onScoresChange?: (scores: ParsedScores) => void;
}

function formatValue(v: unknown): string {
  if (v === null || v === undefined || v === "") return "—";
  if (typeof v === "object") {
    // Handle full_scale_iq object
    const obj = v as Record<string, unknown>;
    if (obj.score !== null && obj.score !== undefined) return String(obj.score);
    return "—";
  }
  return String(v);
}

function getFSIQScore(fsiq: FullScaleIQ | number | string | null | undefined): string {
  if (!fsiq) return "—";
  if (typeof fsiq === "number" || typeof fsiq === "string") return String(fsiq);
  if (typeof fsiq === "object" && fsiq.score != null) return String(fsiq.score);
  return "—";
}

function getFSIQDetails(fsiq: FullScaleIQ | number | string | null | undefined): {
  percentile: string;
  classification: string;
  ci: string;
} {
  const empty = { percentile: "—", classification: "—", ci: "—" };
  if (!fsiq || typeof fsiq !== "object") return empty;
  return {
    percentile: fsiq.percentile != null ? String(fsiq.percentile) : "—",
    classification: fsiq.classification || "—",
    ci: fsiq.confidence_interval || "—",
  };
}

export default function ScoresTable({
  scores,
  editable = false,
  onScoresChange,
}: ScoresTableProps) {
  if (!scores) {
    return (
      <div className="p-6 rounded-xl bg-slate-50 border border-slate-200 text-center text-sm text-slate-500">
        No scores available yet.
      </div>
    );
  }

  const batteries: TestBattery[] = scores.test_batteries || [];
  const legacySubtests = Array.isArray(scores.subtests) ? scores.subtests : [];
  const fsiqScore = getFSIQScore(scores.full_scale_iq);
  const fsiqDetails = getFSIQDetails(scores.full_scale_iq);

  return (
    <div className="space-y-4">
      {/* Overall Score */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-5 rounded-2xl bg-gradient-to-br from-teal-50 to-teal-50 border border-teal-100">
        <div>
          <p className="text-xs font-semibold text-teal-700 uppercase tracking-wide">
            Overall Ability Score
          </p>
          <p className="mt-1 text-4xl font-extrabold text-slate-900">
            {fsiqScore}
          </p>
          <div className="mt-2 flex flex-wrap gap-3 text-xs text-slate-600">
            {fsiqDetails.classification !== "—" && (
              <span><span className="font-semibold">Classification:</span> {fsiqDetails.classification}</span>
            )}
            {fsiqDetails.percentile !== "—" && (
              <span><span className="font-semibold">Percentile:</span> {fsiqDetails.percentile}</span>
            )}
            {fsiqDetails.ci !== "—" && (
              <span><span className="font-semibold">95% CI:</span> {fsiqDetails.ci}</span>
            )}
          </div>
        </div>
      </div>

      {/* Test Batteries (new format) */}
      {batteries.map((battery, bIdx) => (
        <div key={bIdx} className="space-y-2">
          <h3 className="text-sm font-bold text-slate-700 px-1">
            {battery.battery_name}
            {battery.test_date && <span className="ml-2 text-xs font-normal text-slate-500">({battery.test_date})</span>}
          </h3>

          {/* Composites — only show columns that have data */}
          {battery.composites && battery.composites.length > 0 && (() => {
            const hasPercentile = battery.composites!.some(c => c.percentile != null);
            const hasClassification = battery.composites!.some(c => c.classification != null);
            const hasCI = battery.composites!.some(c => c.confidence_interval != null);
            return (
              <div className="overflow-x-auto rounded-xl border border-slate-200">
                <table className="w-full text-sm">
                  <thead className="bg-slate-50">
                    <tr className="text-left text-xs font-bold text-slate-600 uppercase tracking-wide">
                      <th className="px-4 py-3">Index / Composite</th>
                      <th className="px-4 py-3">Score</th>
                      {hasPercentile && <th className="px-4 py-3">Percentile</th>}
                      {hasClassification && <th className="px-4 py-3">Classification</th>}
                      {hasCI && <th className="px-4 py-3">95% CI</th>}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {battery.composites!.map((comp, cIdx) => (
                      <tr key={cIdx} className="hover:bg-slate-50">
                        <td className="px-4 py-3 font-medium text-slate-800">{comp.name || "—"}</td>
                        <td className="px-4 py-3 text-slate-700">{formatValue(comp.score)}</td>
                        {hasPercentile && <td className="px-4 py-3 text-slate-700">{formatValue(comp.percentile)}</td>}
                        {hasClassification && <td className="px-4 py-3 text-slate-700">{comp.classification || "—"}</td>}
                        {hasCI && <td className="px-4 py-3 text-slate-700">{comp.confidence_interval || "—"}</td>}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            );
          })()}

          {/* Subtests within battery — only show columns that have data */}
          {battery.subtests && battery.subtests.length > 0 && (() => {
            const hasScaledScore = battery.subtests!.some(s => s.scaled_score != null);
            const hasPercentile = battery.subtests!.some(s => s.percentile != null);
            return (
              <div className="overflow-x-auto rounded-xl border border-slate-200">
                <table className="w-full text-sm">
                  <thead className="bg-slate-50">
                    <tr className="text-left text-xs font-bold text-slate-600 uppercase tracking-wide">
                      <th className="px-4 py-3">Subtest</th>
                      <th className="px-4 py-3">Score</th>
                      {hasScaledScore && <th className="px-4 py-3">Scaled Score</th>}
                      {hasPercentile && <th className="px-4 py-3">Percentile</th>}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {battery.subtests!.map((sub, sIdx) => (
                      <tr key={sIdx} className="hover:bg-slate-50">
                        <td className="px-4 py-3 font-medium text-slate-800">{sub.name || "—"}</td>
                        <td className="px-4 py-3 text-slate-700">{formatValue(sub.score)}</td>
                        {hasScaledScore && <td className="px-4 py-3 text-slate-700">{formatValue(sub.scaled_score)}</td>}
                        {hasPercentile && <td className="px-4 py-3 text-slate-700">{formatValue(sub.percentile)}</td>}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            );
          })()}
        </div>
      ))}

      {/* Legacy flat subtests (backward compatibility) */}
      {batteries.length === 0 && legacySubtests.length > 0 && (
        <div className="overflow-x-auto rounded-xl border border-slate-200">
          <table className="w-full text-sm">
            <thead className="bg-slate-50">
              <tr className="text-left text-xs font-bold text-slate-600 uppercase tracking-wide">
                <th className="px-4 py-3">Test / Subtest</th>
                <th className="px-4 py-3">Score</th>
                <th className="px-4 py-3">Percentile</th>
                <th className="px-4 py-3">95% CI</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {legacySubtests.map((row, idx) => (
                <tr key={idx} className="hover:bg-slate-50">
                  <td className="px-4 py-3 font-medium text-slate-800">{formatValue(row.name)}</td>
                  <td className="px-4 py-3 text-slate-700">{formatValue(row.score)}</td>
                  <td className="px-4 py-3 text-slate-700">{formatValue(row.percentile)}</td>
                  <td className="px-4 py-3 text-slate-700">{formatValue(row.confidence_interval)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {batteries.length === 0 && legacySubtests.length === 0 && (
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-sm text-slate-500">
          No subtest scores found. You can generate the report from the PDF text directly.
        </div>
      )}

      {scores.notes && (
        <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-sm text-amber-800">
          <span className="font-semibold">Notes:</span> {scores.notes}
        </div>
      )}
    </div>
  );
}
