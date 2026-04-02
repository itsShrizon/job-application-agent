"use client";

import { useState } from "react";
import { toast } from "sonner";
import { refreshGitHub, type GitHubRefreshResult } from "@/lib/api";
import TopBar from "@/components/layout/TopBar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Github, RefreshCw, CheckCircle, FileText } from "lucide-react";

export default function GitHubPage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<GitHubRefreshResult | null>(null);

  const handleRefresh = async () => {
    setLoading(true);
    setResult(null);
    try {
      const res = await refreshGitHub();
      setResult(res);
      toast.success("GitHub projects refreshed.");
    } catch (e) {
      toast.error(`Failed to refresh GitHub: ${(e as Error).message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <TopBar title="GitHub Projects" />

      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-lg mx-auto space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Github className="h-5 w-5" />
                Refresh GitHub Projects
              </CardTitle>
              <CardDescription>
                Fetches your GitHub repositories and generates AI descriptions for use in CV generation.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button onClick={handleRefresh} disabled={loading} className="w-full">
                <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
                {loading ? "Refreshing..." : "Refresh GitHub Projects"}
              </Button>
            </CardContent>
          </Card>

          {result && (
            <Card className="border-green-500">
              <CardContent className="py-4 space-y-3">
                <div className="flex items-center gap-2 text-green-600">
                  <CheckCircle className="h-5 w-5" />
                  <span className="font-medium">Refresh successful</span>
                </div>
                {result.repo_count !== undefined && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Github className="h-4 w-4" />
                    <span>{result.repo_count} repositories fetched</span>
                  </div>
                )}
                {result.file_path && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <FileText className="h-4 w-4" />
                    <span className="font-mono text-xs">{result.file_path}</span>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
