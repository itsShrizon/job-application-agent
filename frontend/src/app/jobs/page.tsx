"use client";

import { useState, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import {
  getJobs,
  scoreJobs,
  scrapeJobs,
  deleteJob,
  deleteAllJobs,
  type Job,
  type JobsQueryParams,
} from "@/lib/api";
import TopBar from "@/components/layout/TopBar";
import TaskPoller from "@/components/TaskPoller";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Search, ChevronLeft, ChevronRight, Trash2 } from "lucide-react";

const PAGE_SIZE = 25;

function scoreBadge(score: number | null) {
  if (score === null) return <Badge variant="secondary">—</Badge>;
  const val = score.toFixed(0) + "%";
  if (score >= 70)
    return <Badge className="bg-green-500 text-white hover:bg-green-600">{val}</Badge>;
  if (score >= 40)
    return <Badge className="bg-yellow-500 text-white hover:bg-yellow-600">{val}</Badge>;
  return <Badge className="bg-red-500 text-white hover:bg-red-600">{val}</Badge>;
}

const SORT_OPTIONS = [
  { value: "relevance_score", label: "Score" },
  { value: "posted_date", label: "Posted Date" },
  { value: "deadline", label: "Deadline" },
  { value: "title", label: "Title" },
];

const STATUS_OPTIONS = [
  { value: "all", label: "All Statuses" },
  { value: "new", label: "New" },
  { value: "applied", label: "Applied" },
  { value: "rejected", label: "Rejected" },
];

const DEADLINE_OPTIONS = [
  { value: "24h", label: "24 Hours" },
  { value: "7d", label: "7 Days" },
  { value: "30d", label: "30 Days" },
  { value: "anytime", label: "Anytime" },
];

const WORK_TYPE_OPTIONS = [
  { value: "onsite", label: "On-site" },
  { value: "hybrid", label: "Hybrid" },
  { value: "remote", label: "Remote" },
];

interface ScrapeForm {
  deadline: string;
  location: string;
  role: string;
  work_type: string;
  limit: string;
}

export default function JobsPage() {
  const router = useRouter();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);

  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");
  const [minScore, setMinScore] = useState("");
  const [sort, setSort] = useState("relevance_score");
  const [order, setOrder] = useState<"asc" | "desc">("desc");

  const [scrapeOpen, setScrapeOpen] = useState(false);
  const [scrapeForm, setScrapeForm] = useState<ScrapeForm>({
    deadline: "7d",
    location: "",
    role: "",
    work_type: "",
    limit: "500",
  });
  const [scrapeLoading, setScrapeLoading] = useState(false);

  const [scoreTaskId, setScoreTaskId] = useState("");
  const [scrapeTaskId, setScrapeTaskId] = useState("");

  const loadJobs = useCallback(async () => {
    setLoading(true);
    try {
      const params: JobsQueryParams = {
        offset,
        limit: PAGE_SIZE,
        sort,
        order,
      };
      if (search) params.search = search;
      if (status !== "all") params.status = status;
      if (minScore) params.min_score = parseFloat(minScore);
      const res = await getJobs(params);
      setJobs(res.jobs);
      setTotal(res.total);
    } catch (e) {
      toast.error(`Failed to load jobs: ${(e as Error).message}`);
    } finally {
      setLoading(false);
    }
  }, [offset, sort, order, search, status, minScore]);

  const handleDeleteJob = async (jobId: string) => {
    if (!confirm("Are you sure you want to delete this job? This action cannot be undone.")) return;
    try {
      await deleteJob(jobId);
      toast.success("Job completely deleted");
      loadJobs();
    } catch (e) {
      toast.error(`Failed to delete job: ${(e as Error).message}`);
    }
  };

  const handleDeleteAllJobs = async () => {
    if (!confirm("Are you ABSOLUTELY sure you want to delete ALL jobs? This action CANNOT be undone.")) return;
    try {
      const res = await deleteAllJobs();
      toast.success(res.message || "All jobs deleted");
      loadJobs();
    } catch (e) {
      toast.error(`Failed to delete all jobs: ${(e as Error).message}`);
    }
  };

  useEffect(() => {
    loadJobs();
  }, [loadJobs]);

  const handleScrape = async () => {
    if (!scrapeForm.location.trim()) {
      toast.error("Location is required.");
      return;
    }
    setScrapeLoading(true);
    try {
      const body = {
        deadline: scrapeForm.deadline,
        location: scrapeForm.location,
        ...(scrapeForm.role ? { role: scrapeForm.role } : {}),
        ...(scrapeForm.work_type ? { work_type: scrapeForm.work_type } : {}),
        limit: parseInt(scrapeForm.limit) || 500,
      };
      const task = await scrapeJobs(body);
      setScrapeTaskId(task.task_id ?? "");
      setScrapeOpen(false);
      toast.info("Scrape started.");
    } catch (e) {
      toast.error(`Scrape failed: ${(e as Error).message}`);
    } finally {
      setScrapeLoading(false);
    }
  };

  const handleScore = async () => {
    try {
      const task = await scoreJobs();
      setScoreTaskId(task.task_id ?? "");
      toast.info("Scoring started.");
    } catch (e) {
      toast.error(`Failed to start scoring: ${(e as Error).message}`);
    }
  };

  const totalPages = Math.ceil(total / PAGE_SIZE);
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <TopBar
        title="Jobs"
        actions={
          <>
            <Button variant="outline" size="sm" onClick={handleScore}>
              Score All
            </Button>
            <Button size="sm" onClick={() => setScrapeOpen(true)}>
              Scrape Jobs
            </Button>
            <Button variant="destructive" size="sm" onClick={handleDeleteAllJobs}>
              Delete All
            </Button>
          </>
        }
      />

      {scoreTaskId && (
        <TaskPoller
          taskId={scoreTaskId}
          label="Scoring"
          onComplete={() => { setScoreTaskId(""); loadJobs(); }}
          onError={() => setScoreTaskId("")}
        />
      )}
      {scrapeTaskId && (
        <TaskPoller
          taskId={scrapeTaskId}
          label="Scrape"
          onComplete={() => { setScrapeTaskId(""); loadJobs(); }}
          onError={() => setScrapeTaskId("")}
        />
      )}

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3 px-6 py-3 border-b bg-muted/30">
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search..."
            className="pl-8 h-9 w-56"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setOffset(0); }}
          />
        </div>

        <Select value={status} onValueChange={(v) => { setStatus(v ?? "all"); setOffset(0); }}>
          <SelectTrigger className="h-9 w-40">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {STATUS_OPTIONS.map((o) => (
              <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Input
          placeholder="Min score (0-1)"
          className="h-9 w-36"
          value={minScore}
          onChange={(e) => { setMinScore(e.target.value); setOffset(0); }}
        />

        <Select value={sort} onValueChange={(v) => { setSort(v ?? "relevance_score"); setOffset(0); }}>
          <SelectTrigger className="h-9 w-40">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {SORT_OPTIONS.map((o) => (
              <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={order} onValueChange={(v) => { setOrder((v ?? "desc") as "asc" | "desc"); setOffset(0); }}>
          <SelectTrigger className="h-9 w-32">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="desc">Descending</SelectItem>
            <SelectItem value="asc">Ascending</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto">
        <Table>
          <TableHeader className="sticky top-0 bg-background z-10">
            <TableRow>
              <TableHead>Title</TableHead>
              <TableHead>Company</TableHead>
              <TableHead>Location</TableHead>
              <TableHead>Work Type</TableHead>
              <TableHead>Score</TableHead>
              <TableHead>Deadline</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              Array.from({ length: 8 }).map((_, i) => (
                <TableRow key={i}>
                  {Array.from({ length: 8 }).map((__, j) => (
                    <TableCell key={j}>
                      <Skeleton className="h-4 w-full" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : jobs.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} className="text-center py-12 text-muted-foreground">
                  No jobs found.
                </TableCell>
              </TableRow>
            ) : (
              jobs.map((job) => (
                <TableRow key={job.job_id}>
                  <TableCell className="font-medium max-w-48 truncate">{job.title}</TableCell>
                  <TableCell className="max-w-36 truncate">{job.company_name}</TableCell>
                  <TableCell className="max-w-28 truncate">{job.location}</TableCell>
                  <TableCell>{job.work_type}</TableCell>
                  <TableCell>{scoreBadge(job.relevance_score)}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">{job.deadline}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className="capitalize">{job.status}</Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => router.push(`/jobs/${job.job_id}`)}
                      >
                        View
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="text-destructive hover:bg-destructive/10 hover:text-destructive h-8 w-8"
                        onClick={() => handleDeleteJob(job.job_id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between px-6 py-3 border-t text-sm text-muted-foreground">
        <span>
          {total === 0 ? "No results" : `${offset + 1}–${Math.min(offset + PAGE_SIZE, total)} of ${total}`}
        </span>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
            disabled={offset === 0}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span>Page {currentPage} of {Math.max(1, totalPages)}</span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setOffset(offset + PAGE_SIZE)}
            disabled={offset + PAGE_SIZE >= total}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Scrape Dialog */}
      <Dialog open={scrapeOpen} onOpenChange={setScrapeOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Scrape Jobs</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-2">
            <div className="grid gap-1.5">
              <Label>Deadline</Label>
              <Select
                value={scrapeForm.deadline}
                onValueChange={(v) => setScrapeForm((f) => ({ ...f, deadline: v ?? f.deadline }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {DEADLINE_OPTIONS.map((o) => (
                    <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-1.5">
              <Label>Location <span className="text-destructive">*</span></Label>
              <Input
                placeholder="e.g. London"
                value={scrapeForm.location}
                onChange={(e) => setScrapeForm((f) => ({ ...f, location: e.target.value }))}
              />
            </div>
            <div className="grid gap-1.5">
              <Label>Role (optional)</Label>
              <Input
                placeholder="e.g. Software Engineer"
                value={scrapeForm.role}
                onChange={(e) => setScrapeForm((f) => ({ ...f, role: e.target.value }))}
              />
            </div>
            <div className="grid gap-1.5">
              <Label>Work Type (optional)</Label>
              <Select
                value={scrapeForm.work_type || "any"}
                onValueChange={(v) => setScrapeForm((f) => ({ ...f, work_type: !v || v === "any" ? "" : v }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Any" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="any">Any</SelectItem>
                  {WORK_TYPE_OPTIONS.map((o) => (
                    <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-1.5">
              <Label>Limit</Label>
              <Input
                type="number"
                value={scrapeForm.limit}
                onChange={(e) => setScrapeForm((f) => ({ ...f, limit: e.target.value }))}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setScrapeOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleScrape} disabled={scrapeLoading}>
              {scrapeLoading ? "Starting..." : "Start Scrape"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
