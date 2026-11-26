"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Sparkles,
  BookOpen,
  Cpu,
  Dna,
  Grid,
  BarChart3,
  RefreshCw,
  ShieldAlert,
  ChevronLeft,
  ChevronRight,
  GraduationCap,
  Layers,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface NavItem {
  title: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
}

interface NavGroup {
  group: string;
  items: NavItem[];
}

const NAV_GROUPS: NavGroup[] = [
  {
    group: "Operations",
    items: [
      { title: "Dashboard", href: "/", icon: LayoutDashboard },
      { title: "10-Step Wizard", href: "/wizard", icon: Sparkles, badge: "Guided" },
    ],
  },
  {
    group: "Academic Resources",
    items: [
      { title: "Resource Management", href: "/resources", icon: BookOpen },
      { title: "CSP Model Explorer", href: "/model", icon: Layers },
    ],
  },
  {
    group: "Optimization Engines",
    items: [
      { title: "Backtracking CSP", href: "/solver", icon: Cpu },
      { title: "Genetic Algorithm", href: "/genetic", icon: Dna },
    ],
  },
  {
    group: "Timetable & Analytics",
    items: [
      { title: "Timetable Grid", href: "/timetable", icon: Grid },
      { title: "Analytics & Load", href: "/analytics", icon: BarChart3 },
      { title: "What-If Rescheduling", href: "/reschedule", icon: RefreshCw },
      { title: "Violation Inspector", href: "/inspector", icon: ShieldAlert },
    ],
  },
];

export function Sidebar({
  collapsed,
  setCollapsed,
  mobileOpen = false,
  setMobileOpen,
}: {
  collapsed: boolean;
  setCollapsed: (v: boolean) => void;
  mobileOpen?: boolean;
  setMobileOpen?: (v: boolean) => void;
}) {
  const pathname = usePathname();

  return (
    <aside
      className={cn(
        "h-screen bg-navy-900 text-white flex flex-col transition-all duration-200 z-40 select-none border-r border-navy-800",
        "fixed inset-y-0 left-0 md:sticky md:top-0",
        mobileOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0",
        collapsed ? "w-20" : "w-64"
      )}
    >
      {/* Brand Header */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-navy-800">
        <Link href="/" className="flex items-center gap-3 overflow-hidden">
          <div className="w-10 h-10 rounded-lg bg-primary flex items-center justify-center shrink-0 shadow-md">
            <GraduationCap className="w-6 h-6 text-white" />
          </div>
          {!collapsed && (
            <div className="flex flex-col truncate">
              <span className="font-bold text-base tracking-tight text-white leading-tight">
                SmartSched<span className="text-primary-subtle font-extrabold ml-0.5">AI</span>
              </span>
              <span className="text-[10px] text-slate-400 font-medium uppercase tracking-wider">
                University Platform
              </span>
            </div>
          )}
        </Link>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="w-7 h-7 rounded-md bg-navy-800 hover:bg-navy-700 text-slate-400 hover:text-white flex items-center justify-center transition-colors"
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Nav List */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
        {NAV_GROUPS.map((grp) => (
          <div key={grp.group} className="space-y-1">
            {!collapsed && (
              <h3 className="px-3 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                {grp.group}
              </h3>
            )}
            <div className="space-y-1 pt-1">
              {grp.items.map((item) => {
                const Icon = item.icon;
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setMobileOpen && setMobileOpen(false)}
                    className={cn(
                      "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all group",
                      isActive
                        ? "bg-primary text-white shadow-sm"
                        : "text-slate-300 hover:bg-navy-800 hover:text-white"
                    )}
                    title={collapsed ? item.title : undefined}
                  >
                    <Icon className={cn("w-5 h-5 shrink-0", isActive ? "text-white" : "text-slate-400 group-hover:text-white")} />
                    {!collapsed && (
                      <span className="flex-1 truncate">{item.title}</span>
                    )}
                    {!collapsed && item.badge && (
                      <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded bg-primary-subtle text-primary shrink-0">
                        {item.badge}
                      </span>
                    )}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Footer Info */}
      {!collapsed && (
        <div className="p-4 border-t border-navy-800 bg-navy-900/60">
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <div className="flex flex-col text-xs">
              <span className="font-semibold text-slate-300">FastAPI Ready</span>
              <span className="text-[10px] text-slate-400">CSP & GA Active</span>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
}
