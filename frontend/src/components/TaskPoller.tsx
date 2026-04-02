"use client";

import { useEffect, useRef } from "react";
import { toast } from "sonner";
import { getTask } from "@/lib/api";

interface TaskPollerProps {
  taskId: string;
  label?: string;
  onComplete?: (result: unknown) => void;
  onError?: (error: string) => void;
}

export default function TaskPoller({ taskId, label = "Task", onComplete, onError }: TaskPollerProps) {
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const toastIdRef = useRef<string | number | null>(null);

  useEffect(() => {
    if (!taskId) return;

    toastIdRef.current = toast.loading(`${label} running...`, { id: taskId });

    const poll = async () => {
      try {
        const task = await getTask(taskId);

        if (task.status === "completed") {
          clearInterval(intervalRef.current!);
          toast.success(`${label} completed.`, { id: taskId });
          onComplete?.(task.result);
        } else if (task.status === "failed") {
          clearInterval(intervalRef.current!);
          toast.error(`${label} failed: ${task.error ?? "Unknown error"}`, { id: taskId });
          onError?.(task.error ?? "Unknown error");
        }
      } catch {
        clearInterval(intervalRef.current!);
        toast.error(`Failed to poll ${label} status.`, { id: taskId });
      }
    };

    poll();
    intervalRef.current = setInterval(poll, 3000);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [taskId, label, onComplete, onError]);

  return null;
}
