"use client";

import { useState, useEffect, use } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import {
  getJob,
  generateCV,
  generateCover,
  cvDownloadUrl,
  coverDownloadUrl,
  type Job,
} from "@/lib/api";
import TopBar from "@/components/layout/TopBar";
import TaskPoller from "@/components/TaskPoller";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { ArrowLeft, Download, FileText, Mail, ExternalLink, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";

function scoreBadge(score: number | null) {
  if (score === null) return <Badge variant="secondary">Not scored</Badge>;
  const val = score.toFixed(1) + "%";
  if (score >= 70) return <Badge className="bg-green-500 text-white">{val}</Badge>;
  if (score >= 40) return <Badge className="bg-yellow-500 text-white">{val}</Badge>;
  return <Badge className="bg-red-500 text-white">{val}</Badge>;
}

const TEMPLATES = [
  { id: "t1", label: "Template 1", desc: "Classic single-column" },
  { id: "t2", label: "Template 2", desc: "Modern two-column" },
  { id: "t3", label: "Template 3", desc: "Minimal clean" },
] as const;

type TemplateId = "t1" | "t2" | "t3";

export default function JobDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();

  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedTemplate, setSelectedTemplate] = useState<TemplateId>("t1");

  const [cvTaskId, setCvTaskId] = useState<string | null>(null);
  const [coverTaskId, setCoverTaskId] = useState<string | null>(null);
  const [cvLoading, setCvLoading] = useState(false);
  const [coverLoading, setCoverLoading] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const j = await getJob(id);
        setJob(j);
      } catch (e) {
        toast.error(`Failed to load job: ${(e as Error).message}`);
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  const handleGenerateCV = async () => {
    if (!job) return;
    setCvLoading(true);
    try {
      const task = await generateCV({ job_id: job.job_id, template: selectedTemplate });
      setCvTaskId(task.task_id);
      toast.info("CV generation started.");
    } catch (e) {
      toast.error(`Failed to generate CV: ${(e as Error).message}`);
    } finally {
      setCvLoading(false);
    }
  };

  const handleGenerateCover = async () => {
    if (!job) return;
    setCoverLoading(true);
    try {
      const task = await generateCover({ job_id: job.job_id });
      setCoverTaskId(task.task_id);
      toast.info("Cover letter generation started.");
    } catch (e) {
      toast.error(`Failed to generate cover letter: ${(e as Error).message}`);
    } finally {
      setCoverLoading(false);
    }
  };

  const refreshJob = async () => {
    try {
      const j = await getJob(id);
      setJob(j);
    } catch {
      // silent
    }
  };

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <TopBar
        title={loading ? "Job Details" : (job?.title ?? "Job Details")}
        actions={
          <Button variant="ghost" size="sm" onClick={() => router.back()}>
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back
          </Button>
        }
      />

      {cvTaskId && (
        <TaskPoller
          taskId={cvTaskId}
          label="CV Generation"
          onComplete={() => { setCvTaskId(null); refreshJob(); }}
          onError={() => setCvTaskId(null)}
        />
      )}
      {coverTaskId && (
        <TaskPoller
          taskId={coverTaskId}
          label="Cover Letter"
          onComplete={() => { setCoverTaskId(null); refreshJob(); }}
          onError={() => setCoverTaskId(null)}
        />
      )}

      <div className="flex-1 overflow-auto p-6">
        {loading ? (
          <div className="space-y-4 max-w-4xl mx-auto">
            <Skeleton className="h-8 w-64" />
            <Skeleton className="h-4 w-48" />
            <Skeleton className="h-48 w-full" />
          </div>
        ) : !job ? (
          <p className="text-muted-foreground text-center py-12">Job not found.</p>
        ) : (
          <div className="max-w-4xl mx-auto space-y-6">
            {/* Header Card */}
            <Card>
              <CardHeader>
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <CardTitle className="text-xl">{job.title}</CardTitle>
                    <p className="text-muted-foreground mt-1">{job.company_name}</p>
                  </div>
                  {scoreBadge(job.relevance_score)}
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Location</span>
                    <p className="font-medium">{job.location || "—"}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Work Type</span>
                    <p className="font-medium capitalize">{job.work_type || "—"}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Status</span>
                    <p className="font-medium capitalize">{job.status}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Deadline</span>
                    <p className="font-medium">{job.deadline || "—"}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Posted</span>
                    <p className="font-medium">{job.posted_date || "—"}</p>
                  </div>
                  {job.url && (
                    <div>
                      <span className="text-muted-foreground">URL</span>
                      <p>
                        <a
                          href={job.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary hover:underline flex items-center gap-1"
                        >
                          Open <ExternalLink className="h-3 w-3" />
                        </a>
                      </p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Description */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Description</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="max-h-72 overflow-y-auto text-sm whitespace-pre-wrap text-muted-foreground leading-relaxed">
                  {job.description_text || "No description available."}
                </div>
              </CardContent>
            </Card>

            <Separator />

            {/* CV Generation */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <FileText className="h-4 w-4" /> Generate CV
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-3 gap-3">
                  {TEMPLATES.map((t) => (
                    <button
                      key={t.id}
                      onClick={() => setSelectedTemplate(t.id)}
                      className={cn(
                        "border rounded-lg p-3 text-left transition-colors",
                        selectedTemplate === t.id
                          ? "border-primary bg-primary/5 ring-1 ring-primary"
                          : "hover:bg-accent"
                      )}
                    >
                      <p className="font-medium text-sm">{t.label}</p>
                      <p className="text-xs text-muted-foreground mt-0.5">{t.desc}</p>
                    </button>
                  ))}
                </div>
                <div className="flex items-center gap-3">
                  <Button onClick={handleGenerateCV} disabled={cvLoading || !!cvTaskId}>
                    {cvLoading || cvTaskId ? "Generating..." : "Generate CV"}
                  </Button>
                  {job.cv_generated && (
                    <>
                      <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200 hover:bg-green-50 h-8 gap-1.5 px-3">
                        <CheckCircle2 className="h-4 w-4 text-green-600" />
                        CV Generated
                      </Badge>
                      <a
                        href={cvDownloadUrl(job.job_id)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 h-8 px-2.5 text-sm font-medium rounded-lg border border-border bg-background hover:bg-muted transition-colors ml-auto"
                      >
                        <Download className="h-4 w-4" /> Download CV
                      </a>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Cover Letter */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Mail className="h-4 w-4" /> Generate Cover Letter
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-3">
                  <Button onClick={handleGenerateCover} disabled={coverLoading || !!coverTaskId}>
                    {coverLoading || coverTaskId ? "Generating..." : "Generate Cover Letter"}
                  </Button>
                  {job.cover_generated && (
                    <>
                      <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200 hover:bg-green-50 h-8 gap-1.5 px-3">
                        <CheckCircle2 className="h-4 w-4 text-green-600" />
                        Cover Generated
                      </Badge>
                      <a
                        href={coverDownloadUrl(job.job_id)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 h-8 px-2.5 text-sm font-medium rounded-lg border border-border bg-background hover:bg-muted transition-colors ml-auto"
                      >
                        <Download className="h-4 w-4" /> Download Cover
                      </a>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
