import React from "react";
import { Card } from "@/components/ui/Card";
import { cn } from "@/lib/utils";

interface KpiCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ComponentType<{ className?: string }>;
  trend?: {
    value: string;
    positive: boolean;
  };
  accent?: "blue" | "purple" | "green" | "amber" | "slate";
}

export function KpiCard({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  accent = "blue",
}: KpiCardProps) {
  const accents = {
    blue: "bg-blue-50 text-blue-700 border-blue-100",
    purple: "bg-purple-50 text-purple-700 border-purple-100",
    green: "bg-emerald-50 text-emerald-700 border-emerald-100",
    amber: "bg-amber-50 text-amber-700 border-amber-100",
    slate: "bg-slate-50 text-slate-700 border-slate-100",
  };

  return (
    <Card className="flex items-center justify-between p-5">
      <div className="space-y-1">
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">{title}</p>
        <p className="text-2xl font-bold text-navy-900 tracking-tight">{value}</p>
        {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
        {trend && (
          <p className={cn("text-xs font-medium", trend.positive ? "text-emerald-600" : "text-amber-600")}>
            {trend.value}
          </p>
        )}
      </div>
      <div className={cn("w-12 h-12 rounded-xl flex items-center justify-center border shrink-0", accents[accent])}>
        <Icon className="w-6 h-6" />
      </div>
    </Card>
  );
}
