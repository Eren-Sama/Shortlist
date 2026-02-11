"use client";

import { useEffect, useState, use } from "react";
import { useAuth } from "@/components/auth-provider";
import { api } from "@/lib/api";
import type { PortfolioRecord } from "@/lib/api";
import {
  FileText,
  Briefcase,
  Video,
  Linkedin,
  Copy,
  Check,
  ChevronDown,
  ChevronRight,
} from "lucide-react";

export default function PortfolioResultPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { session } = useAuth();
  const [record, setRecord] = useState<PortfolioRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copiedField, setCopiedField] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(["readme", "bullets", "demo", "linkedin"])
  );

  useEffect(() => {
    if (!session?.access_token) return;
    api.setToken(session.access_token);

    const fetchData = async () => {
      try {
        const data = await api.getPortfolio(id);
        setRecord(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load portfolio");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id, session]);

  const copyToClipboard = async (text: string, field: string) => {
    await navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 2000);
  };

  const toggleSection = (section: string) => {
    const next = new Set(expandedSections);
    if (next.has(section)) {
      next.delete(section);
    } else {
      next.add(section);
    }
    setExpandedSections(next);
  };

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="text-center">
          <div className="mx-auto h-6 w-6 rounded-full border-2 border-accent border-t-transparent animate-spin" />
          <p className="mt-4 text-muted text-sm">Loading portfolio...</p>
        </div>
      </div>
    );
  }

  if (error || !record) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="rounded-lg border border-danger/30 bg-danger-dim p-6 text-center">
          <p className="text-danger">{error || "Portfolio not found"}</p>
        </div>
      </div>
    );
  }

  const CopyButton = ({ text, field }: { text: string; field: string }) => (
    <button
      onClick={() => copyToClipboard(text, field)}
      className="flex items-center gap-1 rounded-lg bg-raised px-3 py-1.5 text-xs text-muted transition hover:bg-edge hover:text-primary"
      title="Copy to clipboard"
    >
      {copiedField === field ? (
        <>
          <Check className="h-3 w-3 text-ok" /> Copied!
        </>
      ) : (
        <>
          <Copy className="h-3 w-3" /> Copy
        </>
      )}
    </button>
  );

  const SectionHeader = ({
    icon: Icon,
    title,
    section,
    color,
  }: {
    icon: React.ElementType;
    title: string;
    section: string;
    color: string;
  }) => (
    <button
      onClick={() => toggleSection(section)}
      className="flex w-full items-center gap-3 text-left"
    >
      {expandedSections.has(section) ? (
        <ChevronDown className="h-4 w-4 text-muted" />
      ) : (
        <ChevronRight className="h-4 w-4 text-muted" />
      )}
      <Icon className={`h-5 w-5 ${color}`} />
      <h2 className="text-lg font-semibold tracking-tight">{title}</h2>
    </button>
  );

  return (
    <div className="mx-auto max-w-4xl space-y-8">
      {/* Header */}
      <div className="animate-reveal">
        <h1 className="text-2xl font-bold tracking-tight">{record.project_title}</h1>
        <div className="mt-2 flex flex-wrap items-center gap-2">
          {record.tech_stack?.map((tech) => (
            <span
              key={tech}
              className="rounded-lg border border-accent/20 bg-accent-dim px-2.5 py-0.5 text-xs text-accent"
            >
              {tech}
            </span>
          ))}
          {record.target_role && (
            <span className="rounded-lg border border-info/20 bg-info-dim px-2.5 py-0.5 text-xs text-info">
              {record.target_role}
            </span>
          )}
          {record.processing_time_ms && (
            <span className="font-mono text-xs text-muted">
              {(record.processing_time_ms / 1000).toFixed(1)}s
            </span>
          )}
        </div>
      </div>

      {/* README Section */}
      <section className="rounded-xl border border-edge bg-surface p-6 animate-reveal d1">
        <div className="flex items-start justify-between">
          <SectionHeader
            icon={FileText}
            title="README.md"
            section="readme"
            color="text-ok"
          />
          {record.readme_markdown && (
            <CopyButton text={record.readme_markdown} field="readme" />
          )}
        </div>
        {expandedSections.has("readme") && record.readme_markdown && (
          <div className="mt-4 rounded-lg bg-well p-6">
            <pre className="whitespace-pre-wrap font-mono text-sm leading-relaxed text-secondary">
              {record.readme_markdown}
            </pre>
          </div>
        )}
      </section>

      {/* Resume Bullets Section */}
      <section className="rounded-xl border border-edge bg-surface p-6 animate-reveal d2">
        <SectionHeader
          icon={Briefcase}
          title="Resume Bullets"
          section="bullets"
          color="text-warn"
        />
        {expandedSections.has("bullets") && record.resume_bullets && (
          <div className="mt-4 space-y-3">
            {record.resume_bullets.map((b, i) => (
              <div
                key={i}
                className="flex items-start justify-between gap-4 rounded-lg border border-edge bg-well p-4"
              >
                <div className="flex-1">
                  <p className="text-sm text-primary">{b.bullet}</p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {b.keywords?.map((kw) => (
                      <span
                        key={kw}
                        className="rounded bg-warn-dim px-2 py-0.5 text-xs text-warn"
                      >
                        {kw}
                      </span>
                    ))}
                    <span
                      className={`rounded px-2 py-0.5 text-xs ${
                        b.impact_type === "quantitative"
                          ? "bg-ok-dim text-ok"
                          : b.impact_type === "qualitative"
                            ? "bg-info-dim text-info"
                            : "bg-accent-dim text-accent"
                      }`}
                    >
                      {b.impact_type}
                    </span>
                  </div>
                </div>
                <CopyButton text={b.bullet} field={`bullet-${i}`} />
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Demo Script Section */}
      <section className="rounded-xl border border-edge bg-surface p-6 animate-reveal d3">
        <SectionHeader
          icon={Video}
          title="Demo Script"
          section="demo"
          color="text-danger"
        />
        {expandedSections.has("demo") && record.demo_script && (
          <div className="mt-4 space-y-4">
            {/* Hook */}
            <div className="rounded-lg border border-edge bg-well p-4">
              <p className="text-xs font-medium uppercase tracking-wider text-danger">
                Opening Hook
              </p>
              <p className="mt-1 text-sm text-primary">
                {record.demo_script.opening_hook}
              </p>
            </div>

            {/* Duration */}
            <p className="font-mono text-xs text-muted">
              Total Duration: {record.demo_script.total_duration_seconds}s
            </p>

            {/* Steps */}
            <div className="space-y-2">
              {record.demo_script.steps?.map((step, i) => (
                <div
                  key={i}
                  className="flex gap-3 rounded-lg border border-edge bg-well p-4"
                >
                  <div className="shrink-0">
                    <span className="inline-block rounded-lg bg-raised px-2 py-0.5 font-mono text-xs text-muted">
                      {step.timestamp}
                    </span>
                  </div>
                  <div>
                    <p className="text-xs font-medium uppercase tracking-wider text-muted">
                      {step.action}
                    </p>
                    <p className="mt-1 text-sm text-secondary">
                      {step.narration}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            {/* CTA */}
            <div className="rounded-lg border border-edge bg-well p-4">
              <p className="text-xs font-medium uppercase tracking-wider text-danger">
                Closing CTA
              </p>
              <p className="mt-1 text-sm text-primary">
                {record.demo_script.closing_cta}
              </p>
            </div>

            {/* Copy full script */}
            <div className="flex justify-end">
              <CopyButton
                text={`Opening: ${record.demo_script.opening_hook}\n\n${
                  record.demo_script.steps
                    ?.map(
                      (s) =>
                        `[${s.timestamp}] ${s.action}\n  "${s.narration}"`
                    )
                    .join("\n\n") ?? ""
                }\n\nClosing: ${record.demo_script.closing_cta}`}
                field="demo-full"
              />
            </div>
          </div>
        )}
      </section>

      {/* LinkedIn Post Section */}
      <section className="rounded-xl border border-edge bg-surface p-6 animate-reveal d4">
        <div className="flex items-start justify-between">
          <SectionHeader
            icon={Linkedin}
            title="LinkedIn Post"
            section="linkedin"
            color="text-info"
          />
          {record.linkedin_post && (
            <CopyButton
              text={`${record.linkedin_post.hook}\n\n${record.linkedin_post.body}\n\n${record.linkedin_post.hashtags?.join(" ") ?? ""}\n\n${record.linkedin_post.call_to_action}`}
              field="linkedin-full"
            />
          )}
        </div>
        {expandedSections.has("linkedin") && record.linkedin_post && (
          <div className="mt-4 rounded-lg bg-well p-6">
            {/* Hook */}
            <p className="text-base font-semibold text-primary">
              {record.linkedin_post.hook}
            </p>

            {/* Body */}
            <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-secondary">
              {record.linkedin_post.body}
            </p>

            {/* Hashtags */}
            {record.linkedin_post.hashtags &&
              record.linkedin_post.hashtags.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {record.linkedin_post.hashtags.map((tag) => (
                    <span
                      key={tag}
                      className="text-sm text-info"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}

            {/* CTA */}
            <p className="mt-3 text-sm font-medium text-muted">
              {record.linkedin_post.call_to_action}
            </p>
          </div>
        )}
      </section>
    </div>
  );
}
