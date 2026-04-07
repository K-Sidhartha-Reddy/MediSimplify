"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import DashboardShell from "@/components/dashboard-shell";
import { getReportById } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Report } from "@/lib/types";

export default function ReportDetailsPage() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const { token, ready } = useAuth();
  const [report, setReport] = useState<Report | null>(null);

  useEffect(() => {
    if (!ready) return;
    if (!token) {
      router.push("/login");
      return;
    }

    const reportId = params.id;
    if (!reportId) return;

    const load = async () => {
      const data = await getReportById(token, reportId);
      setReport(data);
    };

    void load();
  }, [ready, token, params.id, router]);

  if (!report) {
    return <div className="grid min-h-screen place-items-center text-slate-400">Loading report...</div>;
  }

  return (
    <DashboardShell title={report.file_name} subtitle="Detailed report simplification output">
      <div className="space-y-6">
        <div className="glass-card p-6">
          <h2 className="text-lg font-semibold">Original extracted text</h2>
          <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-slate-200">
            {report.extracted_text}
          </p>
        </div>

        <div className="glass-card border-blue-500/40 p-6">
          <h2 className="text-lg font-semibold">Simplified explanation</h2>
          <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-blue-100">
            {report.simplified_text}
          </p>
        </div>

        <div className="glass-card p-6">
          <h2 className="text-lg font-semibold">Important medical terms</h2>
          <div className="mt-3 flex flex-wrap gap-2">
            {report.important_terms.length ? (
              report.important_terms.map((term) => (
                <span
                  key={term}
                  className="rounded-full border border-slate-600 bg-slate-800 px-3 py-1 text-xs"
                >
                  {term}
                </span>
              ))
            ) : (
              <p className="text-sm text-slate-300">No key terms found.</p>
            )}
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}
