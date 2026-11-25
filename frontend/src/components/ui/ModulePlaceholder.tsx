import React from "react";
import { Code2, Sparkles } from "lucide-react";
import { Card } from "@/components/ui/Card";

interface ModulePlaceholderProps {
  title: string;
  moduleKey: string;
  description: string;
  existingPythonFile: string;
  expectedApiRoute: string;
  icon: React.ComponentType<{ className?: string }>;
}

export function ModulePlaceholder({
  title,
  moduleKey,
  description,
  existingPythonFile,
  expectedApiRoute,
  icon: Icon,
}: ModulePlaceholderProps) {
  return (
    <div className="space-y-6">
      <Card className="border-blue-100 bg-gradient-to-r from-blue-50/50 to-white p-6">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-xl bg-primary text-white flex items-center justify-center shrink-0 shadow-sm">
            <Icon className="w-6 h-6" />
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-navy-900">{title}</h2>
              <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-blue-100 text-blue-800">
                Phase 8 Stage 1 Architecture Ready
              </span>
            </div>
            <p className="text-sm text-slate-600">{description}</p>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <div className="flex items-center gap-2 mb-3 text-navy-900 font-bold text-sm">
            <Code2 className="w-4 h-4 text-primary" />
            <span>Underlying Python Service Integration</span>
          </div>
          <p className="text-xs text-slate-500 mb-3">
            In Stage 2, this UI view will connect to the existing Python algorithm without altering any core logic.
          </p>
          <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 font-mono text-xs text-slate-700 space-y-1.5">
            <div><span className="text-slate-400">Python Source:</span> {existingPythonFile}</div>
            <div><span className="text-slate-400">Streamlit View:</span> src/frontend/{moduleKey}_view.py</div>
            <div><span className="text-slate-400">Target Endpoint:</span> {expectedApiRoute}</div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center gap-2 mb-3 text-navy-900 font-bold text-sm">
            <Sparkles className="w-4 h-4 text-accent-purple" />
            <span>Planned Next.js Features</span>
          </div>
          <ul className="text-xs text-slate-600 space-y-2 list-disc list-inside">
            <li>Asynchronous REST & WebSocket telemetry connection</li>
            <li>Optimistic UI caching with TanStack React Query</li>
            <li>Micro-interactions, accessible modal dialogs, and instant validation</li>
            <li>Export stream handlers directly to client PDF / CSV download</li>
          </ul>
        </Card>
      </div>
    </div>
  );
}
