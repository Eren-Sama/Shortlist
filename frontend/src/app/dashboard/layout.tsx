"use client";

import { useAuth } from "@/components/auth-provider";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { useEffect, useState, useRef } from "react";
import {
  FileText,
  Code2,
  GitBranch,
  FolderTree,
  LogOut,
  LayoutDashboard,
  Layers,
  User,
  ClipboardCheck,
  ChevronDown,
  Menu,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";
import { motion, AnimatePresence } from "framer-motion";

const navSections = [
  {
    label: "General",
    items: [
      { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
      { href: "/dashboard/analyze", label: "Analyze JD", icon: FileText },
      { href: "/dashboard/projects", label: "Projects", icon: Code2 },
    ],
  },
  {
    label: "Tools",
    items: [
      { href: "/dashboard/repo", label: "Repo Scorer", icon: GitBranch },
      { href: "/dashboard/scaffold", label: "Scaffold", icon: FolderTree },
      { href: "/dashboard/portfolio", label: "Portfolio", icon: Layers },
      { href: "/dashboard/fitness", label: "Fitness", icon: ClipboardCheck },
    ],
  },
  {
    label: "Account",
    items: [
      { href: "/dashboard/profile", label: "Profile", icon: User },
    ],
  },
];

function UserDropdown({
  initials,
  displayName,
  email,
  onSignOut,
}: {
  initials: string;
  displayName: string;
  email: string;
  onSignOut: () => void;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2 rounded-lg px-2 py-1.5 transition hover:bg-raised"
      >
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-accent/20 to-accent/5 text-[11px] font-bold text-accent border border-accent/10">
          {initials}
        </div>
        <ChevronDown className={cn(
          "h-3 w-3 text-muted transition-transform duration-200",
          open && "rotate-180"
        )} />
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, scale: 0.92, y: -4 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.92, y: -4 }}
            transition={{ duration: 0.18, ease: [0.16, 1, 0.3, 1] }}
            className="absolute right-0 top-full z-50 mt-2 w-56 origin-top-right overflow-hidden rounded-xl border border-edge/80 bg-surface/95 shadow-[0_16px_48px_rgba(0,0,0,0.5)] backdrop-blur-2xl"
          >
            <div className="border-b border-edge/50 px-4 py-3">
              <p className="truncate text-[13px] font-medium text-primary">{displayName}</p>
              <p className="truncate text-[11px] text-muted">{email}</p>
            </div>
            <div className="py-1.5">
              <Link
                href="/dashboard/profile"
                onClick={() => setOpen(false)}
                className="flex items-center gap-2.5 px-4 py-2 text-[13px] text-secondary hover:bg-white/[0.04] hover:text-primary transition"
              >
                <User className="h-3.5 w-3.5" />
                Profile
              </Link>
              <button
                onClick={() => { setOpen(false); onSignOut(); }}
                className="flex w-full items-center gap-2.5 px-4 py-2 text-[13px] text-secondary hover:bg-white/[0.04] hover:text-danger transition"
              >
                <LogOut className="h-3.5 w-3.5" />
                Sign out
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, session, loading, signOut } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Set API token globally for all dashboard pages
  useEffect(() => {
    if (session?.access_token) {
      api.setToken(session.access_token);
    }
  }, [session]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-root">
        <div className="h-6 w-6 rounded-full border-2 border-accent border-t-transparent animate-spin" />
      </div>
    );
  }

  if (!user) {
    router.push("/");
    return null;
  }

  const handleSignOut = async () => {
    await signOut();
    router.push("/");
  };

  const initials = user.user_metadata?.full_name
    ? user.user_metadata.full_name
        .split(" ")
        .map((w: string) => w[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : user.email?.slice(0, 2).toUpperCase() ?? "U";

  const displayName =
    user.user_metadata?.full_name || user.email?.split("@")[0] || "User";

  return (
    <div className="flex min-h-screen bg-root">
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside
        className={cn(
          "fixed left-0 top-0 z-50 flex h-screen w-60 flex-col border-r border-edge bg-surface/80 backdrop-blur-xl transition-transform duration-300 lg:translate-x-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {/* Brand */}
        <div className="flex items-center justify-between px-5 py-5 border-b border-edge/50">
          <div className="flex items-center gap-2.5">
            <div className="relative h-2.5 w-2.5">
              <div className="absolute inset-0 rounded-[3px] bg-accent" />
              <div className="absolute inset-0 rounded-[3px] bg-accent blur-[4px] opacity-50" />
            </div>
            <Link
              href="/"
              className="text-[11px] font-bold uppercase tracking-[0.2em] text-primary transition hover:text-accent"
            >
              Shortlist
            </Link>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="rounded-lg p-1.5 text-muted hover:text-primary hover:bg-raised transition lg:hidden"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Nav sections */}
        <nav className="flex-1 overflow-y-auto px-3 py-2 space-y-5">
          {navSections.map((section) => (
            <div key={section.label}>
              <p className="mb-1.5 px-3 text-[10px] font-bold uppercase tracking-[0.18em] text-muted/60">
                {section.label}
              </p>
              <div className="space-y-0.5">
                {section.items.map((item) => {
                  const isActive =
                    pathname === item.href ||
                    (item.href !== "/dashboard" &&
                      pathname.startsWith(item.href));
                  return (
                    <Link key={item.href} href={item.href} onClick={() => setSidebarOpen(false)}>
                      <div
                        className={cn(
                          "flex items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] font-medium transition-all duration-200",
                          isActive
                            ? "bg-accent/[0.08] text-accent border border-accent/10 shadow-[0_0_12px_rgba(200,255,0,0.04)]"
                            : "text-secondary hover:text-primary hover:bg-raised border border-transparent"
                        )}
                      >
                        <item.icon className="h-4 w-4" />
                        {item.label}
                      </div>
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>
      </aside>

      <div className="w-full lg:ml-60">
        {/* Top bar */}
        <header className="sticky top-0 z-30 flex items-center border-b border-edge/50 bg-root/80 backdrop-blur-xl px-4 py-3 sm:px-6 md:px-8">
          {/* Mobile hamburger */}
          <button
            onClick={() => setSidebarOpen(true)}
            className="rounded-lg p-2 text-muted hover:text-primary hover:bg-raised transition lg:hidden"
          >
            <Menu className="h-5 w-5" />
          </button>
          <div className="flex-1" />
          <div className="flex items-center gap-3">
            <UserDropdown
              initials={initials}
              displayName={displayName}
              email={user.email ?? ""}
              onSignOut={handleSignOut}
            />
          </div>
        </header>

        {/* Page content */}
        <main className="p-4 sm:p-6 md:p-8">{children}</main>
      </div>
    </div>
  );
}
