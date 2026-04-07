import { BookOpen, Sparkles } from "lucide-react";
import ClickSpark from "./ClickSpark";
import StarBorder from "./StarBorder";
import type { UploadResponse } from "@/lib/types";

export default function ResultPanel({ result }: { result: UploadResponse | null }) {
  if (!result) {
    return (
      <StarBorder
        as="div"
        className="w-full"
        color="#06b6d4"
        speed="7s"
        innerClassName="!rounded-2xl !border-slate-700/70 !bg-gradient-to-br !from-slate-900/50 !to-slate-900/30 !p-8 !text-left !backdrop-blur"
      >
        <div className="flex flex-col items-center justify-center space-y-4 py-12">
          <div className="rounded-lg bg-slate-800/50 p-3">
            <BookOpen className="text-slate-500" size={32} />
          </div>
          <div className="text-center">
            <StarBorder as="h3" color="#06b6d4" speed="7s" className="text-lg font-semibold">
              Latest result
            </StarBorder>
            <p className="mt-3 text-sm text-slate-400">Upload a report to see extracted and simplified text.</p>
          </div>
        </div>
      </StarBorder>
    );
  }

  return (
    <ClickSpark sparkColor="#06b6d4" sparkSize={6} sparkCount={10} duration={500}>
      <StarBorder
        as="div"
        className="w-full"
        color="#06b6d4"
        speed="7s"
        innerClassName="!space-y-5 !rounded-2xl !border-slate-700/70 !bg-gradient-to-br !from-slate-900/50 !to-slate-900/30 !p-8 !text-left !backdrop-blur"
      >
        <div className="space-y-2">
          <div className="flex items-center justify-between gap-3">
            <StarBorder as="h3" color="#06b6d4" speed="7s" className="text-lg font-semibold">
              Simplified output
            </StarBorder>
            <span className="inline-flex items-center gap-1 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-300">
              <div className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
              {result.saved ? "Saved" : "Preview"}
            </span>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <BookOpen size={14} className="text-slate-500" />
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Original text</p>
          </div>
          <div className="max-h-32 overflow-y-auto rounded-lg border border-slate-700 bg-slate-900/50 p-4 text-sm leading-relaxed text-slate-300">
            {result.extracted_text || "No text could be extracted."}
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Sparkles size={14} className="text-blue-400" />
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Simplified explanation</p>
          </div>
          <div className="rounded-lg border border-blue-500/20 bg-blue-500/5 p-4 text-sm leading-7 whitespace-pre-wrap text-blue-100">
            {result.simplified_text}
          </div>
        </div>

        {result.important_terms.length > 0 && (
          <div className="space-y-3 border-t border-slate-700 pt-4">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Key medical terms</p>
            <div className="flex flex-wrap gap-2">
              {result.important_terms.map((term) => (
                <span
                  key={term}
                  className="inline-flex items-center rounded-full border border-slate-600 bg-slate-800/50 px-3 py-1 text-xs font-medium text-slate-200 backdrop-blur"
                >
                  {term}
                </span>
              ))}
            </div>
          </div>
        )}

        <div className="flex items-center justify-between border-t border-slate-700 pt-4 text-xs text-slate-500">
          <span>Processed</span>
          <span>{new Date(result.created_at).toLocaleString()}</span>
        </div>
      </StarBorder>
    </ClickSpark>
  );
}
