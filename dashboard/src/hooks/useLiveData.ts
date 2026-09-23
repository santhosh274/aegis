import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, connectFindingsWs } from "../api/client";
import { useAegisStore } from "../store/useAegisStore";

/**
 * Mounted once in the app shell. Keeps the Zustand store in sync with:
 *  - the live finding feed (WebSocket push, falls back to polling)
 *  - the active-run status flags (polled every 2.5s)
 *  - scope settings (React Query cache, writes on change)
 */
export function useLiveData() {
  const setScope = useAegisStore((s) => s.setScope);
  const setStatus = useAegisStore((s) => s.setStatus);
  const upsertFindings = useAegisStore((s) => s.upsertFindings);
  const replaceFindings = useAegisStore((s) => s.replaceFindings);
  const scope = useAegisStore((s) => s.scope);

  const findingsQuery = useQuery({
    queryKey: ["findings"],
    queryFn: api.getFindings,
    refetchInterval: 15_000,
    refetchIntervalInBackground: true,
  });

  const settingsQuery = useQuery({
    queryKey: ["settings"],
    queryFn: api.getSettings,
    refetchInterval: 10_000,
    refetchIntervalInBackground: true,
  });

  useQuery({
    queryKey: ["status"],
    queryFn: api.getStatus,
    refetchInterval: 2_500,
    refetchIntervalInBackground: true,
  });

  // Scope → store for the persistent banner + settings page.
  useEffect(() => {
    if (settingsQuery.data) setScope(settingsQuery.data);
  }, [settingsQuery.data, setScope]);

  // Polled findings → store baseline.
  useEffect(() => {
    if (findingsQuery.data) replaceFindings(findingsQuery.data);
  }, [findingsQuery.data, replaceFindings]);

  // Re-publish the settings whenever the scope store is mutated (e.g. Settings page).
  const saveSettingsAndRefresh = async (body: Parameters<typeof api.saveSettings>[0]) => {
    const saved = await api.saveSettings(body);
    setScope(saved);
    settingsQuery.refetch();
    return saved;
  };

  return { saveSettingsAndRefresh, scope, refetchFindings: findingsQuery.refetch };
}

/** Standalone WebSocket effect for live finding pushes. */
export function useFindingsSocket() {
  const upsertFindings = useAegisStore((s) => s.upsertFindings);
  useEffect(() => {
    const disconnect = connectFindingsWs({
      onMessage: (msg) => {
        if (msg.type === "hello") {
          upsertFindings(msg.findings);
        } else if (msg.type === "finding") {
          upsertFindings([msg.finding]);
        }
      },
    });
    return disconnect;
  }, [upsertFindings]);
}