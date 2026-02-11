"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

const COMPANY_TYPES = [
  { value: "startup", label: "Startup", desc: "Speed, shipping, full-stack" },
  { value: "mid_level", label: "Mid-Level", desc: "Clean code, testing, quality" },
  { value: "faang", label: "FAANG", desc: "Scale, system design, DSA" },
  { value: "research", label: "Research", desc: "Novel methods, rigor" },
  { value: "enterprise", label: "Enterprise", desc: "Security, reliability" },
];

export default function AnalyzePage() {
  const router = useRouter();
  const [jdText, setJdText] = useState("");
  const [role, setRole] = useState("");
  const [companyType, setCompanyType] = useState("startup");
  const [geography, setGeography] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const result = await api.analyzeJD({
        jd_text: jdText,
        role,
        company_type: companyType,
        geography: geography || undefined,
      });
      router.push(`/dashboard/results/${result.analysis_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <div className="animate-reveal">
        <h1 className="text-2xl font-bold tracking-tight">Analyze Job Description</h1>
        <p className="mt-1 text-sm text-secondary">
          Paste a JD and our AI pipeline will extract skills, expectations, and generate
          tailored project ideas.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* JD Text */}
        <Card className="animate-reveal d1">
          <CardHeader>
            <CardTitle>Job Description</CardTitle>
            <CardDescription>
              Paste the full job description text (50–15,000 characters)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <textarea
              required
              minLength={50}
              maxLength={15000}
              rows={12}
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              placeholder="Paste the complete job description here..."
              className="w-full rounded-lg px-4 py-3 text-sm resize-y"
            />
            <p className="mt-2 text-xs text-muted font-mono">
              {jdText.length} / 15,000
            </p>
          </CardContent>
        </Card>

        {/* Role & Company */}
        <Card className="animate-reveal d2">
          <CardHeader>
            <CardTitle>Context</CardTitle>
            <CardDescription>
              Help the AI understand the target role and company
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-muted">
                Target Role
              </label>
              <input
                type="text"
                required
                minLength={2}
                maxLength={200}
                value={role}
                onChange={(e) => setRole(e.target.value)}
                placeholder="e.g., Senior Backend Engineer"
                className="w-full rounded-lg px-4 py-2.5 text-sm"
              />
            </div>

            <div>
              <label className="mb-2 block text-xs font-medium uppercase tracking-wider text-muted">
                Company Type
              </label>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5">
                {COMPANY_TYPES.map((ct) => (
                  <button
                    key={ct.value}
                    type="button"
                    onClick={() => setCompanyType(ct.value)}
                    className={`rounded-lg border p-3 text-left text-sm transition ${
                      companyType === ct.value
                        ? "border-accent bg-accent-dim text-accent"
                        : "border-edge text-secondary hover:border-edge-strong hover:text-primary"
                    }`}
                  >
                    <div className="font-medium">{ct.label}</div>
                    <div className="mt-0.5 text-xs opacity-60">{ct.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-muted">
                Geography <span className="normal-case tracking-normal">(optional)</span>
              </label>
              <input
                type="text"
                maxLength={100}
                value={geography}
                onChange={(e) => setGeography(e.target.value)}
                placeholder="e.g., US, India, Remote"
                className="w-full rounded-lg px-4 py-2.5 text-sm"
              />
            </div>
          </CardContent>
        </Card>

        {error && (
          <div className="rounded-lg border border-danger/30 bg-danger-dim px-4 py-3 text-sm text-danger">
            {error}
          </div>
        )}

        <Button type="submit" size="lg" loading={loading} className="w-full animate-reveal d3">
          {loading ? "Analyzing with AI Pipeline..." : "Analyze JD & Generate Projects"}
        </Button>
      </form>
    </div>
  );
}
