"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/auth-provider";
import { api } from "@/lib/api";
import type { PortfolioResponse } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Layers } from "lucide-react";

const COMMON_ROLES = [
  "Full-Stack Engineer",
  "Frontend Engineer",
  "Backend Engineer",
  "DevOps / SRE",
  "Data Engineer",
  "ML Engineer",
  "Mobile Developer",
];

export default function PortfolioPage() {
  const { session } = useAuth();
  const router = useRouter();

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [techInput, setTechInput] = useState("");
  const [techStack, setTechStack] = useState<string[]>([]);
  const [features, setFeatures] = useState("");
  const [repoScore, setRepoScore] = useState("");
  const [targetRole, setTargetRole] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const addTech = (tech: string) => {
    const trimmed = tech.trim();
    if (trimmed && !techStack.includes(trimmed)) {
      setTechStack([...techStack, trimmed]);
    }
    setTechInput("");
  };

  const removeTech = (tech: string) => {
    setTechStack(techStack.filter((t) => t !== tech));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    if (session?.access_token) {
      api.setToken(session.access_token);
    }

    try {
      const payload: Parameters<typeof api.optimizePortfolio>[0] = {
        project_title: title,
        project_description: description,
        tech_stack: techStack,
      };

      if (features.trim()) {
        payload.key_features = features
          .split("\n")
          .map((f) => f.trim())
          .filter(Boolean);
      }
      if (repoScore) {
        payload.repo_score = parseFloat(repoScore);
      }
      if (targetRole) {
        payload.target_role = targetRole;
      }

      const result: PortfolioResponse = await api.optimizePortfolio(payload);
      const portfolioId = result.generation_metadata?.portfolio_id;

      if (portfolioId) {
        router.push(`/dashboard/portfolio/${portfolioId}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Portfolio generation failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <div className="animate-reveal">
        <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
          <Layers className="h-5 w-5 text-warn" />
          Portfolio Optimizer
        </h1>
        <p className="mt-1 text-sm text-secondary">
          Generate a polished README, ATS resume bullets, demo script, and
          LinkedIn post for your project.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Project Title */}
        <div className="animate-reveal d1">
          <label className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-muted">
            Project Title
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. Shortlist — AI Portfolio Architect"
            required
            minLength={3}
            maxLength={200}
            className="w-full rounded-lg px-4 py-2.5 text-sm"
          />
        </div>

        {/* Description */}
        <div className="animate-reveal d2">
          <label className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-muted">
            Project Description
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe what the project does, the problem it solves, and who it's for..."
            required
            minLength={20}
            rows={4}
            className="w-full rounded-lg px-4 py-2.5 text-sm resize-y"
          />
        </div>

        {/* Tech Stack */}
        <div className="animate-reveal d3">
          <label className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-muted">
            Tech Stack
          </label>
          <div className="mb-3 flex flex-wrap gap-2">
            {techStack.map((tech) => (
              <span
                key={tech}
                className="inline-flex items-center gap-1 rounded-lg bg-accent-dim border border-accent/20 px-3 py-1 text-sm text-accent"
              >
                {tech}
                <button
                  type="button"
                  onClick={() => removeTech(tech)}
                  className="ml-1 text-accent/60 hover:text-danger"
                >
                  &times;
                </button>
              </span>
            ))}
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              value={techInput}
              onChange={(e) => setTechInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  addTech(techInput);
                }
              }}
              placeholder="Type and press Enter..."
              className="flex-1 rounded-lg px-4 py-2 text-sm"
            />
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => addTech(techInput)}
            >
              Add
            </Button>
          </div>
        </div>

        {/* Key Features */}
        <div className="animate-reveal d4">
          <label className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-muted">
            Key Features{" "}
            <span className="normal-case tracking-normal text-muted">(one per line, optional)</span>
          </label>
          <textarea
            value={features}
            onChange={(e) => setFeatures(e.target.value)}
            placeholder={"Real-time notifications\nRole-based auth\nCI/CD pipeline"}
            rows={3}
            className="w-full rounded-lg px-4 py-2.5 text-sm resize-y"
          />
        </div>

        {/* Target Role */}
        <div className="animate-reveal d5">
          <label className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-muted">
            Target Role{" "}
            <span className="normal-case tracking-normal text-muted">(optional — tailors tone)</span>
          </label>
          <div className="mb-2 flex flex-wrap gap-2">
            {COMMON_ROLES.map((role) => (
              <button
                key={role}
                type="button"
                onClick={() =>
                  setTargetRole(targetRole === role ? "" : role)
                }
                className={`rounded-lg border px-3 py-1 text-xs font-medium transition ${
                  targetRole === role
                    ? "border-accent bg-accent-dim text-accent"
                    : "border-edge bg-well text-secondary hover:border-edge-strong"
                }`}
              >
                {role}
              </button>
            ))}
          </div>
          <input
            type="text"
            value={targetRole}
            onChange={(e) => setTargetRole(e.target.value)}
            placeholder="Or type a custom role..."
            maxLength={200}
            className="w-full rounded-lg px-4 py-2 text-sm"
          />
        </div>

        {/* Repo Score */}
        <div className="animate-reveal d6">
          <label className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-muted">
            Repo Score{" "}
            <span className="normal-case tracking-normal text-muted">(0-10, optional)</span>
          </label>
          <input
            type="number"
            step="0.1"
            min="0"
            max="10"
            value={repoScore}
            onChange={(e) => setRepoScore(e.target.value)}
            placeholder="e.g. 7.5"
            className="w-32 rounded-lg px-4 py-2 text-sm font-mono"
          />
        </div>

        {/* Error */}
        {error && (
          <div className="rounded-lg border border-danger/30 bg-danger-dim px-4 py-3 text-sm text-danger">
            {error}
          </div>
        )}

        {/* Submit */}
        <Button
          type="submit"
          size="lg"
          className="w-full"
          disabled={loading || !title || description.length < 20}
          loading={loading}
        >
          {loading ? "Generating Portfolio Materials..." : "Generate Portfolio Materials"}
        </Button>
      </form>
    </div>
  );
}
