/**
 * Header Component
 * 
 * Application header with branding and controls.
 */

import { cn } from "@/lib/utils";
import { TrashIcon, SettingsIcon, SparkleIcon } from "./icons";

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
  className 
}: HeaderProps) {
  return (
    <header
      className={cn(
        "flex items-center justify-between px-4 py-3",
        "bg-surface-elevated/80 backdrop-blur-lg",
        "border-b border-surface-border",
        "sticky top-0 z-10",
        className
      )}
    >
      {/* Logo & Title */}
      <div className="flex items-center gap-3">
        <div className="relative">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary-600 to-primary-800 flex items-center justify-center border border-primary-500/30">
            <span className="text-lg font-display font-bold text-white">F</span>
          </div>
          {/* Sparkle decoration */}
          <SparkleIcon className="absolute -top-1 -right-1 w-4 h-4 text-accent-400 animate-pulse-slow" />
        </div>
        <div>
          <h1 className="text-lg font-display font-semibold text-text-primary">
            Forsetiemblem
          </h1>
          <p className="text-xs text-text-muted">
            Fire Emblem Chapter Assistant
          </p>
        </div>
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
          className="btn-icon"
          title="Settings"
          aria-label="Settings"
        >
          <SettingsIcon className="w-5 h-5" />
        </button>
      </div>
    </header>
  );
}
