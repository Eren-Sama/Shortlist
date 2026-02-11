"use client";

import { useEffect, useState, useMemo } from "react";
import { useAuth } from "@/components/auth-provider";
import { api, type AnalysisListItem, type FitnessListItem } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import {
  FileText,
  Plus,
  Clock,
  CheckCircle2,
  AlertCircle,
  GitBranch,
  FolderTree,
  Layers,
  ArrowRight,
  ClipboardCheck,
  Activity,
  BarChart3,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";

const statusConfig = {
  completed: { variant: "success" as const, icon: CheckCircle2, color: "text-ok" },
  processing: { variant: "info" as const, icon: Clock, color: "text-info" },
  pending: { variant: "warning" as const, icon: Clock, color: "text-warn" },
  failed: { variant: "error" as const, icon: AlertCircle, color: "text-danger" },
};

function MiniAreaChart({
  data,
  color = "#c8ff00",
  height = 48,
  width = 120,
}: {
  data: number[];
  color?: string;
  height?: number;
  width?: number;
}) {
  if (data.length < 2) return null;
  const max = Math.max(...data, 1);
  const pts = data.map((v, i) => ({
    x: (i / (data.length - 1)) * width,
    y: height - (v / max) * (height - 4) - 2,
  }));
  const line = pts.map((p, i) => `${i === 0 ? "M" : "L"}${p.x},${p.y}`).join(" ");
  const area = `${line} L${width},${height} L0,${height} Z`;
  return (
    <svg width={width} height={height} className="overflow-visible">
      <defs>
        <linearGradient id={`area-${color.replace("#", "")}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.2" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#area-${color.replace("#", "")})`} />
      <path d={line} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      {/* End dot */}
      <circle cx={pts[pts.length - 1].x} cy={pts[pts.length - 1].y} r="2.5" fill={color} />
    </svg>
  );
}

export default function DashboardPage() {
  const { user, session } = useAuth();
  const [analyses, setAnalyses] = useState<AnalysisListItem[]>([]);
  const [fitnessScores, setFitnessScores] = useState<FitnessListItem[]>([]);
  const [counts, setCounts] = useState({ analyses: 0, repos: 0, scaffolds: 0, portfolios: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!session?.access_token) {
      setLoading(false);
      return;
    }
    api.setToken(session.access_token);
    (async () => {
      try {
        const [aRes, rRes, sRes, pRes, fRes] = await Promise.allSettled([
          api.listAnalyses(8, 0),
          api.listRepoAnalyses(1, 0),
          api.listScaffolds(1, 0),
          api.listPortfolios(1, 0),
          api.listFitnessScores(5, 0),
        ]);
        if (aRes.status === "fulfilled") {
          setAnalyses(aRes.value.analyses);
          setCounts((c) => ({ ...c, analyses: aRes.value.total }));
        }
        if (rRes.status === "fulfilled") setCounts((c) => ({ ...c, repos: rRes.value.total }));
        if (sRes.status === "fulfilled") setCounts((c) => ({ ...c, scaffolds: sRes.value.total }));
        if (pRes.status === "fulfilled") setCounts((c) => ({ ...c, portfolios: pRes.value.total }));
        if (fRes.status === "fulfilled") setFitnessScores(fRes.value.scores);
      } catch { /* silent */ } finally {
        setLoading(false);
      }
    })();
  }, [session]);

  const displayName = user?.user_metadata?.full_name || user?.email?.split("@")[0] || "there";
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";

  /* Synthetic chart data from analyses timestamps */
  const activityData = useMemo(() => {
    if (analyses.length < 2) return [0, 1, 0, 2, 1, 3, 2];
    const now = Date.now();
    const buckets = Array(7).fill(0);
    analyses.forEach((a) => {
      const age = now - new Date(a.created_at).getTime();
      const day = Math.min(6, Math.floor(age / (1000 * 60 * 60 * 24)));
      buckets[6 - day]++;
    });
    return buckets;
  }, [analyses]);

  const totalItems = counts.analyses + counts.repos + counts.scaffolds + counts.portfolios;
  const completedAnalyses = analyses.filter((a) => a.status === "completed").length;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3 animate-reveal">
        <div className="min-w-0">
          <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-muted mb-1">Dashboard</p>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-primary">
            {greeting}, <span className="text-accent">{displayName}</span>
          </h1>
        </div>
        <Link href="/dashboard/analyze">
          <Button className="gap-2">
            <Plus className="h-4 w-4" /> <span className="hidden sm:inline">New Analysis</span><span className="sm:hidden">New</span>
          </Button>
        </Link>
      </div>

      <div className="grid grid-cols-12 gap-4">
        {[
          { key: "analyses", label: "Analyses", icon: FileText, color: "#c8ff00", bg: "rgba(200,255,0,0.06)" },
          { key: "repos", label: "Repos Scored", icon: GitBranch, color: "#60a5fa", bg: "rgba(96,165,250,0.06)" },
          { key: "scaffolds", label: "Scaffolds", icon: FolderTree, color: "#c084fc", bg: "rgba(192,132,252,0.06)" },
          { key: "portfolios", label: "Portfolios", icon: Layers, color: "#34d399", bg: "rgba(52,211,153,0.06)" },
        ].map((s, i) => (
          <div
            key={s.key}
            className={cn(
              "col-span-6 sm:col-span-6 lg:col-span-3 animate-reveal",
              `d${i + 1}`,
              "group relative overflow-hidden rounded-2xl border border-edge/70 bg-surface/80 p-5 transition-all hover:border-edge-strong"
            )}
          >
            {/* Corner accent glow */}
            <div className="absolute -top-8 -right-8 h-24 w-24 rounded-full transition-opacity opacity-0 group-hover:opacity-100" style={{ background: `radial-gradient(circle, ${s.bg.replace('0.06', '0.12')}, transparent 70%)` }} />
            <div className="relative">
              <div className="flex items-center justify-between mb-4">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl" style={{ background: s.bg }}>
                  <s.icon className="h-4 w-4" style={{ color: s.color }} />
                </div>
                <MiniAreaChart data={activityData} color={s.color} height={28} width={64} />
              </div>
              <p className="text-[28px] font-bold text-primary leading-none tabular-nums">
                {loading ? <span className="inline-block h-7 w-16 rounded-lg bg-raised animate-pulse" /> : counts[s.key as keyof typeof counts]}
              </p>
              <p className="mt-1 text-[11px] font-medium text-muted tracking-wide">{s.label}</p>
            </div>
          </div>
        ))}

        <div className="col-span-12 lg:col-span-8 animate-reveal d5 rounded-2xl border border-edge/70 bg-surface/80 p-6">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-2.5">
              <Activity className="h-4 w-4 text-accent" />
              <h2 className="text-[14px] font-semibold text-primary">Recent Activity</h2>
            </div>
            <span className="text-[10px] font-mono text-muted tracking-wide">LAST 7 DAYS</span>
          </div>
          {/* Activity bars — horizontal week chart */}
          <div className="flex items-end gap-[6px] h-[110px]">
            {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((day, i) => {
              const val = activityData[i] || 0;
              const max = Math.max(...activityData, 1);
              const pct = Math.max(8, (val / max) * 100);
              const isToday = i === new Date().getDay() - 1 || (i === 6 && new Date().getDay() === 0);
              return (
                <div key={day} className="flex-1 flex flex-col items-center gap-2">
                  <div className="w-full relative" style={{ height: "80px" }}>
                    <div
                      className={cn(
                        "absolute bottom-0 w-full rounded-t-md transition-all duration-500",
                        isToday ? "bg-accent" : "bg-accent/20"
                      )}
                      style={{ height: `${pct}%` }}
                    />
                  </div>
                  <span className={cn("text-[10px] font-mono", isToday ? "text-accent" : "text-muted")}>
                    {day}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        <div className="col-span-12 lg:col-span-4 animate-reveal d6 rounded-2xl border border-edge/70 bg-surface/80 p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2.5">
              <Zap className="h-4 w-4 text-accent" />
              <h2 className="text-[14px] font-semibold text-primary">Pipeline</h2>
            </div>
            {!loading && (() => {
              const steps = [counts.analyses, fitnessScores.length, counts.repos, counts.scaffolds, counts.portfolios];
              const done = steps.filter(Boolean).length;
              return (
                <span className="text-[10px] font-mono text-muted tabular-nums">{done}/{steps.length}</span>
              );
            })()}
          </div>
          {/* Steps */}
          <div className="space-y-0.5">
            {[
              { label: "Analyze JD", count: counts.analyses, icon: FileText, color: "#c8ff00", href: "/dashboard/analyze" },
              { label: "Score Resume", count: fitnessScores.length, icon: ClipboardCheck, color: "#34d399", href: "/dashboard/fitness" },
              { label: "Score Repos", count: counts.repos, icon: GitBranch, color: "#60a5fa", href: "/dashboard/repo" },
              { label: "Build Project", count: counts.scaffolds, icon: FolderTree, color: "#c084fc", href: "/dashboard/scaffold" },
              { label: "Ship Portfolio", count: counts.portfolios, icon: Layers, color: "#f59e0b", href: "/dashboard/portfolio" },
            ].map((step, i) => {
              const done = step.count > 0;
              return (
                <Link key={step.label} href={step.href}>
                  <div className="group flex items-center gap-3 rounded-xl px-2 py-2.5 transition-colors hover:bg-white/[0.03]">
                    {/* Step number */}
                    <div
                      className={cn(
                        "flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-[10px] font-bold tabular-nums transition-all duration-300",
                        done
                          ? "bg-white/[0.07] text-primary"
                          : "bg-white/[0.03] text-muted/40"
                      )}
                    >
                      {done ? (
                        <svg className="h-3 w-3" viewBox="0 0 12 12" fill="none"><path d="M2.5 6L5 8.5L9.5 3.5" stroke={step.color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
                      ) : (
                        <span>{i + 1}</span>
                      )}
                    </div>
                    {/* Label */}
                    <span className={cn("flex-1 text-[12px] font-medium truncate", done ? "text-primary" : "text-muted/50")}>{step.label}</span>
                    {/* Count */}
                    {done ? (
                      <span className="text-[10px] font-semibold tabular-nums text-muted">{step.count}</span>
                    ) : (
                      <span className="text-[10px] text-muted/30">—</span>
                    )}
                  </div>
                </Link>
              );
            })}
          </div>
          {/* Segmented progress */}
          {!loading && (() => {
            const steps = [counts.analyses, fitnessScores.length, counts.repos, counts.scaffolds, counts.portfolios];
            const done = steps.filter(Boolean).length;
            return (
              <div className="mt-4 pt-4 border-t border-white/[0.04]">
                <div className="flex gap-1">
                  {steps.map((s, i) => (
                    <div
                      key={i}
                      className={cn(
                        "h-1 flex-1 rounded-full transition-all duration-500",
                        s > 0 ? "bg-accent/70" : "bg-white/[0.06]"
                      )}
                    />
                  ))}
                </div>
              </div>
            );
          })()}
        </div>

        <div className="col-span-12 lg:col-span-7 animate-reveal d7 rounded-2xl border border-edge/70 bg-surface/80 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2.5">
              <BarChart3 className="h-4 w-4 text-info" />
              <h2 className="text-[14px] font-semibold text-primary">Recent Analyses</h2>
            </div>
            {analyses.length > 0 && (
              <Link href="/dashboard/projects" className="text-[11px] font-medium text-accent/70 hover:text-accent transition">
                View all →
              </Link>
            )}
          </div>

          {loading && (
            <div className="space-y-2.5">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-[56px] rounded-xl bg-raised/40 animate-pulse" />
              ))}
            </div>
          )}

          {!loading && analyses.length === 0 && (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-accent/[0.06] mb-3">
                <FileText className="h-5 w-5 text-accent/50" />
              </div>
              <p className="text-[13px] font-medium text-secondary">No analyses yet</p>
              <p className="text-[11px] text-muted mt-0.5 mb-4">Analyze a JD to see results here</p>
              <Link href="/dashboard/analyze">
                <Button variant="secondary" size="sm" className="gap-1.5">
                  <Plus className="h-3.5 w-3.5" /> Start Analysis
                </Button>
              </Link>
            </div>
          )}

          {!loading && analyses.length > 0 && (
            <div className="space-y-1.5">
              {analyses.slice(0, 6).map((analysis) => {
                const status = statusConfig[analysis.status as keyof typeof statusConfig] || statusConfig.pending;
                const StatusIcon = status.icon;
                return (
                  <Link key={analysis.id} href={`/dashboard/results/${analysis.id}`}>
                    <div className="group flex items-center gap-3.5 rounded-xl px-3.5 py-3 transition-colors hover:bg-raised/60">
                      <div className={cn("flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-surface border border-edge/50")}>
                        <StatusIcon className={cn("h-3.5 w-3.5", status.color)} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-[13px] font-medium text-primary truncate">{analysis.role}</p>
                        <p className="text-[10px] text-muted font-mono">
                          {analysis.company_type.replace("_", " ")} · {new Date(analysis.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                        </p>
                      </div>
                      <Badge variant={status.variant} className="text-[9px] shrink-0">{analysis.status}</Badge>
                      <ArrowRight className="h-3 w-3 text-muted/0 group-hover:text-muted transition-all" />
                    </div>
                  </Link>
                );
              })}
            </div>
          )}
        </div>

        <div className="col-span-12 lg:col-span-5 animate-reveal d8 rounded-2xl border border-edge/70 bg-surface/80 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2.5">
              <ClipboardCheck className="h-4 w-4 text-accent" />
              <h2 className="text-[14px] font-semibold text-primary">Resume Fitness</h2>
            </div>
            <Link href="/dashboard/fitness" className="text-[11px] font-medium text-accent/70 hover:text-accent transition">
              Score now →
            </Link>
          </div>

          {loading && (
            <div className="space-y-3">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-[52px] rounded-xl bg-raised/40 animate-pulse" />
              ))}
            </div>
          )}

          {!loading && fitnessScores.length === 0 && (
            <div className="flex flex-col items-center justify-center py-10 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-accent/[0.06] mb-3">
                <ClipboardCheck className="h-5 w-5 text-accent/50" />
              </div>
              <p className="text-[13px] font-medium text-secondary">No fitness scores yet</p>
              <p className="text-[11px] text-muted mt-0.5 mb-4">Score your resume against a JD</p>
              <Link href="/dashboard/fitness">
                <Button variant="secondary" size="sm" className="gap-1.5">
                  <ClipboardCheck className="h-3.5 w-3.5" /> Score Resume
                </Button>
              </Link>
            </div>
          )}

          {!loading && fitnessScores.length > 0 && (
            <div className="space-y-2">
              {fitnessScores.slice(0, 5).map((score) => {
                const verdictColors: Record<string, { dot: string; bg: string }> = {
                  strong_fit: { dot: "bg-ok", bg: "bg-ok/10" },
                  good_fit: { dot: "bg-accent", bg: "bg-accent/10" },
                  partial_fit: { dot: "bg-warn", bg: "bg-warn/10" },
                  weak_fit: { dot: "bg-danger", bg: "bg-danger/10" },
                };
                const vc = verdictColors[score.verdict] || verdictColors.partial_fit;
                return (
                  <div key={score.id} className="group flex items-center gap-3 rounded-xl px-3 py-2.5 transition-colors hover:bg-raised/40">
                    <div className={cn("flex h-9 w-9 shrink-0 items-center justify-center rounded-lg", vc.bg)}>
                      <span className="text-[14px] font-bold text-primary tabular-nums">{score.fitness_score}</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-[12px] font-medium text-primary truncate">Fitness Score</p>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className={cn("h-1.5 w-1.5 rounded-full", vc.dot)} />
                        <span className="text-[10px] text-muted capitalize">{(score.verdict || "").replace("_", " ")}</span>
                        <span className="text-[10px] text-muted">· {new Date(score.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric" })}</span>
                      </div>
                    </div>
                    <span className="text-[18px] font-bold tabular-nums" style={{ color: score.fitness_score >= 80 ? "#22c55e" : score.fitness_score >= 60 ? "#c8ff00" : score.fitness_score >= 40 ? "#f59e0b" : "#ef4444" }}>
                      {score.fitness_score}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
