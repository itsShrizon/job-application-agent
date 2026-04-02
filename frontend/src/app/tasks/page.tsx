"use client";

import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";
import { getTask, type TaskStatus } from "@/lib/api";
import TopBar from "@/components/layout/TopBar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Trash2, Plus, RefreshCw } from "lucide-react";

const STORAGE_KEY = "cv_generator_task_ids";

function statusColor(status: TaskStatus["status"]) {
  switch (status) {
    case "completed": return "bg-green-500 text-white";
    case "failed": return "bg-red-500 text-white";
    case "running": return "bg-blue-500 text-white";
    default: return "bg-muted text-muted-foreground";
  }
}

function statusProgress(status: TaskStatus["status"]) {
  switch (status) {
    case "completed": return 100;
    case "failed": return 100;
    case "running": return 60;
    default: return 20;
  }
}

interface TaskEntry {
  taskId: string;
  status: TaskStatus | null;
  loading: boolean;
  error: string | null;
}

export default function TasksPage() {
  const [taskIds, setTaskIds] = useState<string[]>([]);
  const [tasks, setTasks] = useState<Record<string, TaskEntry>>({});
  const [newTaskId, setNewTaskId] = useState("");
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        setTaskIds(JSON.parse(stored));
      } catch {
        // ignore
      }
    }
  }, []);

  const saveIds = (ids: string[]) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(ids));
    setTaskIds(ids);
  };

  const fetchTask = useCallback(async (taskId: string) => {
    setTasks((prev) => ({
      ...prev,
      [taskId]: { ...(prev[taskId] ?? { taskId, status: null, error: null }), loading: true },
    }));
    try {
      const status = await getTask(taskId);
      setTasks((prev) => ({
        ...prev,
        [taskId]: { taskId, status, loading: false, error: null },
      }));
    } catch (e) {
      setTasks((prev) => ({
        ...prev,
        [taskId]: { taskId, status: null, loading: false, error: (e as Error).message },
      }));
    }
  }, []);

  const fetchAll = useCallback(() => {
    taskIds.forEach(fetchTask);
  }, [taskIds, fetchTask]);

  useEffect(() => {
    if (taskIds.length === 0) return;
    fetchAll();
  }, [taskIds, fetchAll]);

  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      const runningIds = taskIds.filter((id) => {
        const t = tasks[id];
        return !t?.status || t.status.status === "pending" || t.status.status === "running";
      });
      runningIds.forEach(fetchTask);
    }, 3000);
    return () => clearInterval(interval);
  }, [autoRefresh, taskIds, tasks, fetchTask]);

  const addTask = () => {
    const id = newTaskId.trim();
    if (!id) return;
    if (taskIds.includes(id)) {
      toast.warning("Task ID already in list.");
      return;
    }
    saveIds([id, ...taskIds]);
    setNewTaskId("");
    fetchTask(id);
  };

  const removeTask = (taskId: string) => {
    saveIds(taskIds.filter((id) => id !== taskId));
    setTasks((prev) => {
      const next = { ...prev };
      delete next[taskId];
      return next;
    });
  };

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <TopBar
        title="Tasks"
        actions={
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAutoRefresh((v) => !v)}
          >
            <RefreshCw className={`h-4 w-4 mr-1 ${autoRefresh ? "text-green-500" : ""}`} />
            {autoRefresh ? "Auto-refresh ON" : "Auto-refresh OFF"}
          </Button>
        }
      />

      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-2xl mx-auto space-y-4">
          {/* Add task */}
          <div className="flex gap-2">
            <Input
              placeholder="Enter task ID..."
              value={newTaskId}
              onChange={(e) => setNewTaskId(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && addTask()}
              className="flex-1"
            />
            <Button onClick={addTask}>
              <Plus className="h-4 w-4 mr-1" /> Add
            </Button>
          </div>

          {taskIds.length === 0 ? (
            <p className="text-center text-muted-foreground py-12">
              No tasks tracked. Task IDs are stored in your browser.
            </p>
          ) : (
            taskIds.map((taskId) => {
              const entry = tasks[taskId];
              const status = entry?.status;
              return (
                <Card key={taskId}>
                  <CardContent className="py-4 space-y-3">
                    <div className="flex items-start justify-between gap-4">
                      <div className="space-y-1 flex-1 min-w-0">
                        <p className="font-mono text-sm truncate">{taskId}</p>
                        <div className="flex items-center gap-2">
                          {entry?.loading && !status ? (
                            <Badge variant="secondary">Loading...</Badge>
                          ) : entry?.error ? (
                            <Badge className="bg-red-500 text-white">Error</Badge>
                          ) : status ? (
                            <Badge className={statusColor(status.status)}>
                              {status.status}
                            </Badge>
                          ) : (
                            <Badge variant="secondary">Unknown</Badge>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => fetchTask(taskId)}
                          disabled={entry?.loading}
                        >
                          <RefreshCw className={`h-4 w-4 ${entry?.loading ? "animate-spin" : ""}`} />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeTask(taskId)}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    </div>

                    {status && (
                      <Progress
                        value={statusProgress(status.status)}
                        className={
                          status.status === "failed"
                            ? "[&>div]:bg-red-500"
                            : status.status === "completed"
                            ? "[&>div]:bg-green-500"
                            : ""
                        }
                      />
                    )}

                    {entry?.error && (
                      <p className="text-xs text-red-500">{entry.error}</p>
                    )}

                    {status?.error && (
                      <p className="text-xs text-red-500">Task error: {status.error}</p>
                    )}

                    {status?.result !== undefined && status.status === "completed" && (
                      <pre className="text-xs bg-muted p-2 rounded overflow-auto max-h-24">
                        {JSON.stringify(status.result, null, 2)}
                      </pre>
                    )}
                  </CardContent>
                </Card>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
