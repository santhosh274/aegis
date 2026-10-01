import { useState } from "react";
import { Trash2 } from "lucide-react";
import { Button } from "./ui/button";
import { api, type Finding } from "../api/client";
import { useAegisStore } from "../store/useAegisStore";
import { useQueryClient } from "@tanstack/react-query";

/**
 * Deletes a finding record: removes its JSON files on disk and any matching
 * verification-history rows, then syncs the store and query cache.
 */
export function DeleteFindingButton({
  finding,
  variant = "ghost",
  size = "sm",
  label = "Delete",
  showLabel = false,
  className,
  onDeleted,
}: {
  finding: Pick<Finding, "id" | "title" | "target">;
  variant?: "ghost" | "destructive" | "outline";
  size?: "sm" | "icon";
  label?: string;
  showLabel?: boolean;
  className?: string;
  onDeleted?: () => void;
}) {
  const removeFinding = useAegisStore((s) => s.removeFinding);
  const queryClient = useQueryClient();
  const [busy, setBusy] = useState(false);

  const handleClick = async (e: React.MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    const ok = window.confirm(
      `Delete finding "${finding.title}" for ${finding.target}?\n\nThis also removes its verification-history rows and cannot be undone.`
    );
    if (!ok) return;
    setBusy(true);
    try {
      await api.deleteFinding(finding.id);
      removeFinding(finding.id);
      queryClient.invalidateQueries({ queryKey: ["findings"] });
      queryClient.invalidateQueries({ queryKey: ["verify-history"] });
      onDeleted?.();
    } catch (err) {
      window.alert(err instanceof Error ? err.message : "Delete failed.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Button
      size={size}
      variant={variant}
      className={className}
      onClick={handleClick}
      disabled={busy}
      aria-label={`delete finding ${finding.title}`}
      title="Delete finding and its history"
    >
      <Trash2 />
      {showLabel && !busy && <span>{label}</span>}
      {showLabel && busy && "Deleting…"}
    </Button>
  );
}