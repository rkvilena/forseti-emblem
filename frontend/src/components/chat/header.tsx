/**
 * Header Component
 *
 * Application header with branding and controls.
 */

import { cn } from "@/lib/utils";
import { TrashIcon, SettingsIcon } from "./icons";
import { MainLogo } from "@/components/brand/main-logo";
import { useTheme } from "@/hooks/use-theme";

interface HeaderProps {
  /** Callback to clear chat */
  onClearChat?: () => void;
  /** Whether there are messages to clear */
  hasMessages?: boolean;
  className?: string;
}

export function Header({
  onClearChat,
  hasMessages = false,
  className,
}: HeaderProps) {
  const { theme, toggleTheme } = useTheme();

  return (
    <header
      className={cn(
        "flex items-center justify-between px-4 py-3",
        "bg-surface-elevated/80 backdrop-blur-lg",
        "border-b border-surface-border",
        "sticky top-0 z-10",
        className,
      )}
    >
      {/* Logo & Title */}
      <div className="flex items-center gap-3">
        <MainLogo />
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2">
        {hasMessages && onClearChat && (
          <button
            onClick={onClearChat}
            className="btn-icon"
            title="Clear conversation"
            aria-label="Clear conversation"
          >
            <TrashIcon className="w-5 h-5" />
          </button>
        )}
        <button
          onClick={toggleTheme}
          className="btn-icon"
          title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
          aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
        >
          <SettingsIcon className="w-5 h-5" />
        </button>
      </div>
    </header>
  );
}
