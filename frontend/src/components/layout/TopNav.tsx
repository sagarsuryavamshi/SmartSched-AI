"use client";

import React from "react";
import { usePathname } from "next/navigation";
import { Bell, CalendarDays, ExternalLink, ChevronRight } from "lucide-react";
import Link from "next/link";

const ROUTE_LABELS: Record<string, string> = {
  "/": "Executive Dashboard",
  "/wizard": "10-Step Optimization Wizard",
  "/resources": "Academic Resource Management",
  "/model": "CSP Problem Formulation & Domain Explorer",
  "/solver": "Backtracking CSP Search Engine",
  "/genetic": "Genetic Algorithm & Metaheuristic Benchmarking",
  "/timetable": "Weekly Timetable Matrix",
  "/analytics": "Institutional Load & Utilization Analytics",
  "/reschedule": "What-If Rescheduling & Atomic Rollback",
  "/inspector": "Constraint Violation Diagnostics",
};

export function TopNav() {
  const pathname = usePathname();
  const currentTitle = ROUTE_LABELS[pathname] || "SmartSched AI";

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between sticky top-0 z-20 shadow-sm">
      {/* Breadcrumb / Page Context */}
      <div className="flex items-center gap-2 text-sm">
        <Link href="/" className="text-slate-500 hover:text-slate-800 transition-colors font-medium">
          Operations
        </Link>
        <ChevronRight className="w-4 h-4 text-slate-400" />
        <span className="font-semibold text-navy-900 truncate">{currentTitle}</span>
      </div>

      {/* Right controls */}
      <div className="flex items-center gap-4">
        {/* Semester Badge */}
        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-100 border border-slate-200 text-xs text-slate-700 font-medium">
          <CalendarDays className="w-3.5 h-3.5 text-primary" />
          <span>Fall Semester 2026-2027</span>
        </div>

        {/* Link to Streamlit App */}
        <a
          href="http://localhost:8501"
          target="_blank"
          rel="noopener noreferrer"
          className="hidden lg:flex items-center gap-1.5 text-xs text-slate-600 hover:text-primary transition-colors px-2.5 py-1.5 rounded-md hover:bg-slate-50 border border-slate-200"
          title="Open currently running Streamlit app in background"
        >
          <span>Streamlit Runtime</span>
          <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
        </a>

        {/* Notifications */}
        <button
          className="w-9 h-9 rounded-full hover:bg-slate-100 text-slate-500 hover:text-slate-800 flex items-center justify-center transition-colors relative"
          title="System notifications"
        >
          <Bell className="w-4 h-4" />
          <span className="w-2 h-2 rounded-full bg-primary absolute top-2 right-2 ring-2 ring-white" />
        </button>

        {/* User Profile */}
        <div className="flex items-center gap-3 pl-2 border-l border-slate-200">
          <div className="w-8 h-8 rounded-full bg-navy-900 text-white flex items-center justify-center font-bold text-xs">
            AD
          </div>
          <div className="hidden sm:flex flex-col text-left">
            <span className="text-xs font-semibold text-navy-900 leading-tight">Academic Dean</span>
            <span className="text-[10px] text-slate-500">Administrator</span>
          </div>
        </div>
      </div>
    </header>
  );
}
