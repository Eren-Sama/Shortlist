"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/auth-provider";
import { api, type AnalysisListItem } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { Code2, ArrowRight } from "lucide-react";

export default function ProjectsPage() {
  const { session } = useAuth();
  const [analyses, setAnalyses] = useState<AnalysisListItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!session?.access_token) {
      setLoading(false);
      return;
    }
    api.setToken(session.access_token);
    api
      .listAnalyses(50, 0)
      .then((data) => {
        setAnalyses(data.analyses.filter((a) => a.status === "completed"));
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [session]);

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <div className="h-6 w-6 rounded-full border-2 border-accent border-t-transparent animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="animate-reveal">
        <h1 className="text-2xl font-bold tracking-tight">Your Projects</h1>
        <p className="mt-1 text-sm text-secondary">
          Completed analyses ready for capstone generation
        </p>
      </div>

      {analyses.length === 0 ? (
        <Card className="animate-reveal d1">
          <CardContent className="py-12 text-center">
            <Code2 className="mx-auto mb-4 h-12 w-12 text-muted" />
            <h3 className="mb-2 text-lg font-semibold">No completed analyses</h3>
            <p className="mb-6 text-sm text-secondary">
              Analyze a JD first to generate project ideas
            </p>
            <Link href="/dashboard/analyze">
              <Button>Analyze a JD</Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {analyses.map((a, i) => (
            <Link key={a.id} href={`/dashboard/results/${a.id}`}>
              <Card className={`h-full cursor-pointer transition hover:border-edge-strong animate-reveal d${Math.min(i + 1, 8)}`}>
                <CardContent className="flex items-center justify-between py-5">
                  <div>
                    <h3 className="font-semibold text-primary">{a.role}</h3>
                    <div className="mt-1.5 flex items-center gap-2">
                      <Badge className="capitalize">
                        {a.company_type.replace("_", " ")}
                      </Badge>
                      {a.geography && (
                        <span className="text-xs text-muted">
                          {a.geography}
                        </span>
                      )}
                    </div>
                  </div>
                  <ArrowRight className="h-4 w-4 text-muted" />
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
