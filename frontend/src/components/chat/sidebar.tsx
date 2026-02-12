"use client";

/**
 * Sidebar Component
 *
 * Collapsible sidebar with logo, question recommendations, and action buttons.
 * Expands on hover, collapses when not hovered.
 */

import { useState } from "react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { MainLogo, MainLogoIcon } from "@/components/brand/main-logo";
import { useTheme } from "@/hooks/use-theme";
import { useTextSize } from "@/hooks/use-text-size";
import {
  SwordIcon,
  BookIcon,
  SettingsIcon,
  SunIcon,
  MoonIcon,
  TrashIcon,
} from "./icons";
import { usePathname } from "next/navigation";

const PAGES = [
  {
    href: "/",
    label: "Chat",
    icon: SwordIcon,
  },
  {
    href: "/chapters",
    label: "Chapters",
    icon: BookIcon,
  },
];

interface SidebarProps {
  onSelectQuestion?: (question: string) => void;
  onClearChat?: () => void;
  hasMessages?: boolean;
  className?: string;
}

export function Sidebar({
  onSelectQuestion,
  onClearChat,
  hasMessages = false,
  className,
}: SidebarProps) {
  const [isHovered, setIsHovered] = useState(false);
  const { theme, toggleTheme } = useTheme();
  const pathname = usePathname();
  useTextSize();

  return (
    <aside
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className={cn(
        "flex flex-col h-full",
        "bg-surface-elevated border-r-4 border-brand-gold/70",
        "transition-all duration-300 ease-out",
        isHovered ? "w-64" : "w-16",
        className,
      )}
    >
      {/* Top: Logo */}
      <div
        className={cn(
          "flex items-center h-16 px-3 border-b-2 border-brand-gold/50",
          isHovered ? "justify-start" : "justify-center",
        )}
      >
        {isHovered ? (
          <MainLogo className="animate-fade-in" />
        ) : (
          <MainLogoIcon />
        )}
      </div>

      <div className="flex-1 overflow-y-auto py-4">
        <div className={cn("px-2 mb-2", isHovered ? "block" : "hidden")}>
          <p className="text-xs text-text-muted px-2 mb-2">Pages</p>
        </div>
        <nav className="flex flex-col gap-1 px-2">
          {PAGES.map((page) => {
            const Icon = page.icon;
            const isActive = pathname === page.href;
            return (
              <Link
                key={page.href}
                href={page.href}
                className={cn(
                  "group flex items-center gap-3 rounded-md",
                  "text-text-secondary hover:text-text-primary",
                  "hover:bg-surface-muted/50",
                  "transition-all duration-200",
                  isHovered ? "px-3 py-2.5" : "px-0 py-2.5 justify-center",
                  isActive && "bg-surface-muted/60 text-text-primary",
                )}
                onClick={(event) => {
                  if (page.href === "/" && pathname === "/") {
                    event.preventDefault();
                  }
                }}
              >
                <Icon className="w-5 h-5 flex-shrink-0 text-brand-green" />
                {isHovered && (
                  <span className="text-sm truncate animate-fade-in">
                    {page.label}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Bottom: Settings & Theme Toggle */}
      <div className="border-t-2 border-brand-gold/50 p-2 flex flex-col gap-1">
        <button
          onClick={onClearChat}
          disabled={!hasMessages}
          className={cn(
            "flex items-center gap-3 rounded-md",
            "text-text-secondary hover:text-text-primary",
            "hover:bg-surface-muted/50",
            "transition-all duration-200",
            isHovered ? "px-3 py-2.5" : "px-0 py-2.5 justify-center",
            !hasMessages &&
              "opacity-40 cursor-not-allowed hover:bg-transparent",
          )}
          title={hasMessages ? "Clear chat" : "No messages to clear"}
          aria-label="Clear chat"
        >
          <TrashIcon className="w-5 h-5 flex-shrink-0" />
          {isHovered && (
            <span className="text-sm animate-fade-in">Clear Chat</span>
          )}
        </button>

        <Link
          href="/settings"
          className={cn(
            "flex items-center gap-3 rounded-md",
            "text-text-secondary hover:text-text-primary",
            "hover:bg-surface-muted/50",
            "transition-all duration-200",
            isHovered ? "px-3 py-2.5" : "px-0 py-2.5 justify-center",
          )}
          title="Settings"
        >
          <SettingsIcon className="w-5 h-5 flex-shrink-0" />
          {isHovered && (
            <span className="text-sm animate-fade-in">Settings</span>
          )}
        </Link>

        <button
          onClick={toggleTheme}
          className={cn(
            "flex items-center gap-3 rounded-md",
            "text-text-secondary hover:text-text-primary",
            "hover:bg-surface-muted/50",
            "transition-all duration-200",
            isHovered ? "px-3 py-2.5" : "px-0 py-2.5 justify-center",
          )}
          title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
        >
          {theme === "dark" ? (
            <SunIcon className="w-5 h-5 flex-shrink-0" />
          ) : (
            <MoonIcon className="w-5 h-5 flex-shrink-0" />
          )}
          {isHovered && (
            <span className="text-sm animate-fade-in">
              {theme === "dark" ? "Light Mode" : "Dark Mode"}
            </span>
          )}
        </button>
      </div>
    </aside>
  );
}
