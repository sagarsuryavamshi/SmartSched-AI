"use client";

import React, { useState } from "react";
import { usePathname } from "next/navigation";
import {
  Bell,
  CalendarDays,
  ChevronRight,
  LogIn,
  LogOut,
  Menu,
  ShieldCheck,
  User as UserIcon,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { useResources } from "@/context/ResourceContext";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

const ROUTE_LABELS: Record<string, string> = {
  "/": "Executive Dashboard",
  "/wizard": "10-Step Optimization Wizard",
  "/resources": "Academic Resource Management",
  "/model": "CSP Problem Formulation & Domain Explorer",
  "/solver": "Backtracking CSP Search Engine",
  "/genetic": "Genetic Algorithm & Metaheuristic Benchmarking",
  "/timetable": "Weekly Timetable Matrix",
  "/analytics": "Institutional Load & Utilization Analytics",
  "/analytics/benchmark": "Scientific Algorithm Benchmarking",
  "/reschedule": "What-If Rescheduling & Atomic Rollback",
  "/inspector": "Constraint Violation Diagnostics",
};

export function TopNav({ onOpenMobileMenu }: { onOpenMobileMenu?: () => void }) {
  const pathname = usePathname();
  const currentTitle = ROUTE_LABELS[pathname] || "SmartSched AI";
  const { user, login, logout, isAdmin } = useAuth();
  const { isLiveBackend } = useResources();

  const [isLoginOpen, setIsLoginOpen] = useState(false);
  const [isNotifOpen, setIsNotifOpen] = useState(false);
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [loginError, setLoginError] = useState<string | null>(null);
  const [loginLoading, setLoginLoading] = useState(false);

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError(null);
    setLoginLoading(true);
    const res = await login(username.trim(), password);
    setLoginLoading(false);
    if (res.success) {
      setIsLoginOpen(false);
      setPassword("");
    } else {
      setLoginError(res.message || "Authentication failed.");
    }
  };

  return (
    <>
      <header className="h-16 bg-white border-b border-slate-200 px-4 sm:px-6 flex items-center justify-between sticky top-0 z-20 shadow-sm">
        {/* Left: Mobile Menu + Breadcrumb */}
        <div className="flex items-center gap-2 text-sm min-w-0">
          {onOpenMobileMenu && (
            <button
              onClick={onOpenMobileMenu}
              className="md:hidden p-2 -ml-2 rounded-lg text-slate-600 hover:bg-slate-100"
              aria-label="Open navigation menu"
            >
              <Menu className="w-5 h-5" />
            </button>
          )}
          <Link href="/" className="hidden sm:inline text-slate-500 hover:text-slate-800 transition-colors font-medium">
            Operations
          </Link>
          <ChevronRight className="hidden sm:inline w-4 h-4 text-slate-400 shrink-0" />
          <span className="font-semibold text-navy-900 truncate">{currentTitle}</span>
        </div>

        {/* Right controls */}
        <div className="flex items-center gap-2 sm:gap-4 shrink-0">
          {/* Semester Badge */}
          <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-100 border border-slate-200 text-xs text-slate-700 font-medium">
            <CalendarDays className="w-3.5 h-3.5 text-primary" />
            <span>Fall Semester 2026-2027</span>
          </div>

          {/* Notifications Popover Trigger */}
          <div className="relative">
            <button
              onClick={() => setIsNotifOpen((prev) => !prev)}
              className="w-9 h-9 rounded-full hover:bg-slate-100 text-slate-500 hover:text-slate-800 flex items-center justify-center transition-colors relative"
              title="System status & notifications"
              aria-label="System status & notifications"
            >
              <Bell className="w-4 h-4" />
              <span
                className={`w-2 h-2 rounded-full absolute top-2 right-2 ring-2 ring-white ${
                  isLiveBackend ? "bg-emerald-500" : "bg-amber-500"
                }`}
              />
            </button>

            {isNotifOpen && (
              <div className="absolute right-0 mt-2 w-72 bg-white border border-slate-200 rounded-xl shadow-lg p-3 z-50 text-xs space-y-2">
                <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                  <span className="font-bold text-navy-900">System Diagnostics</span>
                  <button
                    onClick={() => setIsNotifOpen(false)}
                    className="text-[11px] text-slate-400 hover:text-slate-700"
                  >
                    Close
                  </button>
                </div>
                <div className="flex items-start gap-2 p-2 rounded-lg bg-slate-50">
                  {isLiveBackend ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  ) : (
                    <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                  )}
                  <div>
                    <div className="font-semibold text-navy-900">
                      {isLiveBackend ? "FastAPI Backend Connected" : "Offline / Fallback Mode"}
                    </div>
                    <div className="text-[11px] text-slate-500">
                      {isLiveBackend
                        ? "Live PostgreSQL / database synchronization active."
                        : "Backend unreachable. Viewing cached baseline state."}
                    </div>
                  </div>
                </div>
                <div className="flex items-start gap-2 p-2 rounded-lg bg-slate-50">
                  <ShieldCheck className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                  <div>
                    <div className="font-semibold text-navy-900">
                      {user ? `Signed in as ${user.username}` : "Guest Observer Session"}
                    </div>
                    <div className="text-[11px] text-slate-500">
                      {isAdmin
                        ? "Administrator privileges active for CRUD & optimization."
                        : "Sign in as Administrator to modify resources or run solvers."}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Auth Profile & Sign In / Out */}
          <div className="flex items-center gap-2 pl-2 border-l border-slate-200">
            {user ? (
              <>
                <div className="w-8 h-8 rounded-full bg-navy-900 text-white flex items-center justify-center font-bold text-xs uppercase">
                  {user.username.slice(0, 2)}
                </div>
                <div className="hidden sm:flex flex-col text-left">
                  <span className="text-xs font-semibold text-navy-900 leading-tight">{user.full_name}</span>
                  <span className="text-[10px] text-slate-500 uppercase font-mono">{user.role}</span>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={logout}
                  className="text-xs text-slate-500 hover:text-red-600 px-2"
                  title="Sign out"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span className="hidden md:inline ml-1">Sign Out</span>
                </Button>
              </>
            ) : (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsLoginOpen(true)}
                className="text-xs border-slate-300 text-navy-900"
              >
                <LogIn className="w-3.5 h-3.5 mr-1 text-primary" />
                <span>Sign In</span>
              </Button>
            )}
          </div>
        </div>
      </header>

      {/* Sign In Modal */}
      <Modal
        isOpen={isLoginOpen}
        onClose={() => setIsLoginOpen(false)}
        title="SmartSched AI Authentication"
        description="Sign in with your institutional Administrator or Observer account."
      >
        <form onSubmit={handleLoginSubmit} className="space-y-4 text-xs">
          {loginError && (
            <div className="p-2.5 rounded-lg bg-red-50 border border-red-200 text-red-800 font-medium">
              {loginError}
            </div>
          )}

          <div>
            <label className="block font-bold text-navy-900 mb-1">Username</label>
            <div className="relative">
              <UserIcon className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="admin or viewer"
                className="w-full pl-8 pr-3 py-2 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-primary/20"
              />
            </div>
          </div>

          <div>
            <label className="block font-bold text-navy-900 mb-1">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter account password"
              className="w-full px-3 py-2 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-primary/20"
            />
          </div>

          <div className="flex items-center justify-between pt-2">
            <Badge variant="info">RBAC Protected API</Badge>
            <div className="flex items-center gap-2">
              <Button type="button" variant="ghost" size="sm" onClick={() => setIsLoginOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary" size="sm" disabled={loginLoading}>
                {loginLoading ? "Signing In..." : "Sign In"}
              </Button>
            </div>
          </div>
        </form>
      </Modal>
    </>
  );
}
