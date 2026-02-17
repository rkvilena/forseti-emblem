/**
 * EmptyState Component
 *
 * Shown when no messages exist in the chat.
 * Provides welcome message and usage hints.
 */

import { cn } from "@/lib/utils";
import { MainLogo } from "@/components/brand/main-logo";

interface EmptyStateProps {
  className?: string;
}

export function EmptyState({ className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center h-full px-4 py-12",
        className,
      )}
    >
      {/* Logo */}
      <MainLogo className="mb-6 text-3xl" />

      {/* Welcome Message */}
      <div className="text-center max-w-md">
        <div className="flex items-center justify-center gap-2 mb-3"></div>
        <p className="text-sm text-text-muted mb-4">
          Retrieval Augmented Generation (RAG) based site to answer questions
          regarding chapters in mainline Fire Emblem series.
        </p>
      </div>
    </div>
  );
}
