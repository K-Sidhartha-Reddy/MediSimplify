"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import DashboardShell from "@/components/dashboard-shell";
import { getReports } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Report } from "@/lib/types";

export default function DashboardResultPage() {
  const router = useRouter();
  const { token, ready } = useAuth();
  const [latestReport, setLatestReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!ready) return;
    if (!token) {
      router.push("/login");
      return;
    }

    const loadLatest = async () => {
      setLoading(true);
      try {
        const data = await getReports(token);
        setLatestReport(data[0] ?? null);
      } finally {
        setLoading(false);
      }
    };

    void loadLatest();
  }, [ready, token, router]);

  return (
    <DashboardShell
      activeTab="result"
      title="Simplified Results"
      subtitle="See your latest AI-simplified explanation and key medical terms in one focused view."
    >
      {loading ? (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-8 text-center text-sm text-slate-400">
          Loading latest result...
        </div>
      ) : !latestReport ? (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-8 text-center text-sm text-slate-400">
          No saved reports yet. Upload one from the Upload & OCR page.
        </div>
      ) : (
        <section className="space-y-5 rounded-2xl border border-slate-800 bg-slate-900/50 p-8">
          <div className="flex items-center justify-between gap-3">
            <h3 className="text-lg font-semibold text-white">Latest simplified output</h3>
            <span className="rounded-full border border-emerald-500/40 bg-emerald-500/10 px-3 py-1 text-xs text-emerald-300">
              {new Date(latestReport.created_at).toLocaleString()}
            </span>
          </div>

          <div>
            <p className="mb-2 text-xs uppercase tracking-wide text-slate-400">File</p>
            <p className="rounded-lg border border-slate-700 bg-slate-900/60 p-3 text-sm text-slate-200">
              {latestReport.file_name}
            </p>
          </div>

          <div>
            <p className="mb-2 text-xs uppercase tracking-wide text-slate-400">Simplified explanation</p>
            <div className="rounded-lg border border-blue-500/30 bg-blue-500/10 p-4 text-sm text-blue-100">
              {latestReport.simplified_text}
            </div>
          </div>

          <div>
            <p className="mb-2 text-xs uppercase tracking-wide text-slate-400">Important medical terms</p>
            <div className="flex flex-wrap gap-2">
              {latestReport.important_terms.length ? (
                latestReport.important_terms.map((term) => (
                  <span key={term} className="rounded-full border border-slate-600 bg-slate-900/70 px-3 py-1 text-xs">
                    {term}
                  </span>
                ))
              ) : (
                <p className="text-sm text-slate-300">No key terms detected.</p>
              )}
            </div>
          </div>
        </section>
      )}
    </DashboardShell>
  );
}
