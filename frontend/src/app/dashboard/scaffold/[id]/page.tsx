"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api, type ScaffoldResponse, type GeneratedFile } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  ArrowLeft,
  FolderTree,
  FileCode,
  Copy,
  Check,
  ChevronDown,
  ChevronRight,
} from "lucide-react";

const LANG_COLORS: Record<string, string> = {
  python: "text-warn",
  javascript: "text-warn",
  typescript: "text-info",
  go: "text-info",
  rust: "text-danger",
  java: "text-danger",
  html: "text-warn",
  css: "text-info",
  markdown: "text-secondary",
  yaml: "text-info",
  json: "text-ok",
  sql: "text-ok",
  dockerfile: "text-info",
  shell: "text-accent",
  text: "text-muted",
};

function FileCard({
  file,
  defaultOpen = false,
}: {
  file: GeneratedFile;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    await navigator.clipboard.writeText(file.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const langColor = LANG_COLORS[file.language] || LANG_COLORS.text;

  return (
    <div className="overflow-hidden rounded-lg border border-edge">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center gap-3 px-4 py-3 text-left hover:bg-raised transition"
      >
        {open ? (
          <ChevronDown className="h-4 w-4 text-muted" />
        ) : (
          <ChevronRight className="h-4 w-4 text-muted" />
        )}
        <FileCode className={`h-4 w-4 ${langColor}`} />
        <span className="flex-1 font-mono text-sm text-primary">
          {file.path}
        </span>
        <Badge variant="default" className="text-[10px]">
          {file.language}
        </Badge>
      </button>

      {open && (
        <div className="border-t border-edge">
          {file.description && (
            <div className="border-b border-edge px-4 py-2 text-xs text-muted">
              {file.description}
            </div>
          )}
          <div className="relative">
            <button
              onClick={copy}
              className="absolute right-2 top-2 rounded p-1.5 text-muted transition hover:bg-raised hover:text-primary"
              title="Copy file content"
            >
              {copied ? (
                <Check className="h-3.5 w-3.5 text-ok" />
              ) : (
                <Copy className="h-3.5 w-3.5" />
              )}
            </button>
            <pre className="max-h-96 overflow-auto bg-well p-4 text-xs text-secondary font-mono">
              <code>{file.content}</code>
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ScaffoldResultPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [data, setData] = useState<ScaffoldResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [allOpen, setAllOpen] = useState(false);

  useEffect(() => {
    api
      .getScaffold(id)
      .then(setData)
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Failed to load")
      )
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <div className="h-6 w-6 rounded-full border-2 border-accent border-t-transparent animate-spin" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="space-y-4">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4" /> Back
        </Button>
        <Card>
          <CardContent className="py-8 text-center text-danger">
            {error || "Scaffold not found"}
          </CardContent>
        </Card>
      </div>
    );
  }

  const processingMs = data.generation_metadata?.processing_time_ms as
    | number
    | undefined;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center gap-4 animate-reveal">
        <Button variant="ghost" size="sm" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex-1">
          <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight">
            <FolderTree className="h-5 w-5 text-ok" />
            {data.project_name}
          </h1>
          <p className="mt-1 text-sm text-secondary">
            <span className="font-mono text-xs text-muted">{data.files.length} files</span>
            {processingMs && <span className="font-mono text-xs text-muted"> \u00b7 {(processingMs / 1000).toFixed(1)}s</span>}
          </p>
        </div>
      </div>

      {/* File Tree */}
      {data.file_tree && (
        <Card className="animate-reveal d1">
          <CardHeader>
            <CardTitle className="text-base">Project Structure</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="overflow-auto rounded-lg bg-well p-4 text-xs text-secondary font-mono">
              {data.file_tree}
            </pre>
          </CardContent>
        </Card>
      )}

      {/* File List */}
      <div className="animate-reveal d2">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-bold tracking-tight">Generated Files</h2>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setAllOpen(!allOpen)}
          >
            {allOpen ? "Collapse All" : "Expand All"}
          </Button>
        </div>
        <div className="space-y-2">
          {data.files.map((file, i) => (
            <FileCard
              key={file.path}
              file={file}
              defaultOpen={allOpen || i === 0}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
