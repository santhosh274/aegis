import { useCallback, useEffect, useRef, useState } from "react";
import { streamPost, type PipelineEvent } from "../api/client";
import { useAegisStore } from "../store/useAegisStore";

export interface PipelineRun {
  events: PipelineEvent[];
  running: boolean;
  error: string | null;
  /** Run a POST + SSE stream. Returns the collected events for the caller. */
  run: (path: string, body: Record<string, unknown>) => Promise<PipelineEvent[]>;
  /** Abort a live stream (EventSource cleanup guarantee). */
  stop: () => void;
  clear: () => void;
}

/** Find the last event whose data carries the given root key. */
export function extractEventData<T>(
  events: PipelineEvent[],
  key: string
): T | null {
  for (let i = events.length - 1; i >= 0; i--) {
    const d = events[i].data;
    if (d && key in d && d[key] !== undefined && d[key] !== null) {
      return d[key] as T;
    }
  }
  return null;
}

export function usePipelineRun(): PipelineRun {
  const [events, setEvents] = useState<PipelineEvent[]>([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const pushEvents = useAegisStore((s) => s.pushEvents);
  const clearPipeline = useAegisStore((s) => s.clearPipeline);
  const alive = useRef(true);

  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
      abortRef.current?.abort();
    };
  }, []);

  const run = useCallback(
    async (path: string, body: Record<string, unknown>) => {
      clearPipeline();
      setEvents([]);
      setError(null);
      setRunning(true);
      abortRef.current?.abort();
      const ac = new AbortController();
      abortRef.current = ac;

      const collected: PipelineEvent[] = [];
      try {
        await streamPost(
          path,
          body,
          {
            onEvent: (ev) => {
              collected.push(ev);
              if (alive.current) {
                setEvents([...collected]);
                pushEvents([ev]);
              }
            },
            onError: (e) => {
              if (alive.current) setError(e.message);
            },
          },
          ac.signal
        );
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        if (alive.current) setError(msg);
        if (alive.current) pushEvents([failedEvent(msg)]);
      } finally {
        if (alive.current) setRunning(false);
        abortRef.current = null;
      }
      return collected;
    },
    [clearPipeline, pushEvents]
  );

  const stop = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  const clear = useCallback(() => {
    setEvents([]);
    setError(null);
    clearPipeline();
  }, [clearPipeline]);

  return { events, running, error, run, stop, clear };
}

function failedEvent(message: string): PipelineEvent {
  return {
    phase: "report",
    status: "failed",
    message,
    timestamp: new Date().toISOString(),
  };
}