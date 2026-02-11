/**
 * EmptyState Component
 *
 * Shown when no messages exist in the chat.
 * Provides welcome message and usage hints.
 */

import { cn } from "@/lib/utils";
import { MainLogo } from "@/components/brand/main-logo";
import { SparkleIcon } from "./icons";

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
      <MainLogo className="mb-6" />

      {/* Welcome Message */}
      <div className="text-center max-w-md">
        <div className="flex items-center justify-center gap-2 mb-3">
          <SparkleIcon className="w-5 h-5 text-brand-green" />
          <h2 className="text-lg font-medium text-text-primary">
            How can I help you?
          </h2>
        </div>
        <p className="text-sm text-text-muted mb-4">
          Ask me anything about Fire Emblem chapters, characters, story events,
          or battle strategies.
        </p>
        <p className="text-xs text-text-muted">
          Try selecting a suggested question below or type your own message.
        </p>
      </div>
    </div>
  );
}
