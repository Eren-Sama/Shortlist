"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FolderTree, Boxes, Shield, TestTubeDiagonal } from "lucide-react";

const COMMON_STACKS = [
  "Python",
  "FastAPI",
  "Django",
  "React",
  "Next.js",
  "Node.js",
  "Express",
  "TypeScript",
  "PostgreSQL",
  "MongoDB",
  "Redis",
  "Docker",
  "Go",
  "Rust",
  "GraphQL",
  "Tailwind CSS",
];

export default function ScaffoldPage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [selectedStack, setSelectedStack] = useState<string[]>([]);
  const [customTech, setCustomTech] = useState("");
  const [includeDocker, setIncludeDocker] = useState(true);
  const [includeCi, setIncludeCi] = useState(true);
  const [includeTests, setIncludeTests] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const toggleStack = (tech: string) => {
    setSelectedStack((prev) =>
      prev.includes(tech) ? prev.filter((t) => t !== tech) : [...prev, tech]
    );
  };

  const addCustomTech = () => {
    const trimmed = customTech.trim();
    if (trimmed && !selectedStack.includes(trimmed)) {
      setSelectedStack((prev) => [...prev, trimmed]);
      setCustomTech("");
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !description.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const result = await api.generateScaffold({
        project_title: title.trim(),
        project_description: description.trim(),
        tech_stack: selectedStack,
        include_docker: includeDocker,
        include_ci: includeCi,
        include_tests: includeTests,
      });

      const scaffoldId = (result.generation_metadata as Record<string, string>)
        .scaffold_id;
      if (scaffoldId) {
        router.push(`/dashboard/scaffold/${scaffoldId}`);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to generate scaffold"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <div className="animate-reveal">
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight flex items-center gap-2">
          <FolderTree className="h-5 w-5 text-ok" />
          Scaffold Generator
        </h1>
        <p className="mt-1 text-sm text-secondary">
          Generate a production-ready project structure with boilerplate code,
          tests, Docker, and CI/CD.
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
            placeholder="e.g., Real-time Analytics Dashboard"
            className="w-full rounded-lg px-4 py-2.5 text-sm"
            required
            minLength={3}
            maxLength={200}
          />
        </div>

        {/* Project Description */}
        <div className="animate-reveal d2">
          <label className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-muted">
            Project Description
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe what this project does, its key features, and target audience..."
            rows={4}
            className="w-full rounded-lg px-4 py-2.5 text-sm resize-y"
            required
            minLength={20}
            maxLength={2000}
          />
        </div>

        {/* Tech Stack Selection */}
        <div className="animate-reveal d3">
          <label className="mb-2 block text-xs font-medium uppercase tracking-wider text-muted">
            Tech Stack
          </label>
          <div className="flex flex-wrap gap-2">
            {COMMON_STACKS.map((tech) => (
              <button
                key={tech}
                type="button"
                onClick={() => toggleStack(tech)}
                className={`rounded-lg border px-3 py-1 text-xs font-medium transition ${
                  selectedStack.includes(tech)
                    ? "border-accent bg-accent-dim text-accent"
                    : "border-edge bg-well text-secondary hover:border-edge-strong"
                }`}
              >
                {tech}
              </button>
            ))}
          </div>
          <div className="mt-2 flex gap-2">
            <input
              type="text"
              value={customTech}
              onChange={(e) => setCustomTech(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addCustomTech())}
              placeholder="Add custom technology..."
              className="flex-1 rounded-lg px-3 py-1.5 text-sm"
            />
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={addCustomTech}
            >
              Add
            </Button>
          </div>
          {selectedStack.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {selectedStack.map((tech) => (
                <Badge key={tech} variant="accent" className="gap-1">
                  {tech}
                  <button
                    type="button"
                    onClick={() => toggleStack(tech)}
                    className="ml-1 text-xs opacity-60 hover:opacity-100"
                  >
                    \u00d7
                  </button>
                </Badge>
              ))}
            </div>
          )}
        </div>

        {/* Options */}
        <div className="grid gap-3 sm:grid-cols-3 animate-reveal d4">
          <label className="flex items-center gap-3 rounded-lg border border-edge p-3 cursor-pointer hover:border-edge-strong transition">
            <input
              type="checkbox"
              checked={includeDocker}
              onChange={(e) => setIncludeDocker(e.target.checked)}
              className="h-4 w-4 rounded"
            />
            <div>
              <div className="flex items-center gap-1.5 text-sm font-medium text-primary">
                <Boxes className="h-3.5 w-3.5" /> Docker
              </div>
              <span className="text-xs text-muted">
                Dockerfile + Compose
              </span>
            </div>
          </label>
          <label className="flex items-center gap-3 rounded-lg border border-edge p-3 cursor-pointer hover:border-edge-strong transition">
            <input
              type="checkbox"
              checked={includeCi}
              onChange={(e) => setIncludeCi(e.target.checked)}
              className="h-4 w-4 rounded"
            />
            <div>
              <div className="flex items-center gap-1.5 text-sm font-medium text-primary">
                <Shield className="h-3.5 w-3.5" /> CI/CD
              </div>
              <span className="text-xs text-muted">
                GitHub Actions workflow
              </span>
            </div>
          </label>
          <label className="flex items-center gap-3 rounded-lg border border-edge p-3 cursor-pointer hover:border-edge-strong transition">
            <input
              type="checkbox"
              checked={includeTests}
              onChange={(e) => setIncludeTests(e.target.checked)}
              className="h-4 w-4 rounded"
            />
            <div>
              <div className="flex items-center gap-1.5 text-sm font-medium text-primary">
                <TestTubeDiagonal className="h-3.5 w-3.5" /> Tests
              </div>
              <span className="text-xs text-muted">
                Test suite + config
              </span>
            </div>
          </label>
        </div>

        {error && (
          <div className="rounded-lg border border-danger/30 bg-danger-dim px-4 py-3 text-sm text-danger">
            {error}
          </div>
        )}

        <Button
          type="submit"
          size="lg"
          className="w-full"
          disabled={loading || !title.trim() || description.length < 20}
          loading={loading}
        >
          <FolderTree className="h-4 w-4" />
          {loading ? "Generating scaffold..." : "Generate Project Scaffold"}
        </Button>
      </form>

      {/* Info Card */}
      <Card className="animate-reveal d5">
        <CardHeader>
          <CardTitle className="text-base">What gets generated?</CardTitle>
          <CardDescription>
            A complete, production-ready project structure ready to clone and
            build.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm text-secondary">
            <li className="flex items-start gap-2">
              <span className="font-mono text-accent text-xs">01</span>
              <span>
                <strong className="text-primary">Project structure</strong> {"\u2014"} Clean folder layout following
                best practices for your stack
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="font-mono text-accent text-xs">02</span>
              <span>
                <strong className="text-primary">Boilerplate code</strong> {"\u2014"} Working entry points, routes,
                models, and config files
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="font-mono text-accent text-xs">03</span>
              <span>
                <strong className="text-primary">DevOps</strong> {"\u2014"} Dockerfile, docker-compose, CI/CD
                pipeline, and .gitignore
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="font-mono text-accent text-xs">04</span>
              <span>
                <strong className="text-primary">Tests</strong> {"\u2014"} Test suite skeleton with realistic test
                cases
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="font-mono text-accent text-xs">05</span>
              <span>
                <strong className="text-primary">README</strong> {"\u2014"} Comprehensive documentation with setup
                instructions and architecture overview
              </span>
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
