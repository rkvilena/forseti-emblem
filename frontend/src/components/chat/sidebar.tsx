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
  SparkleIcon,
  InfoIcon,
  MenuIcon,
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
  {
    href: "/about",
    label: "About",
    icon: SparkleIcon,
  },
  {
    href: "/disclaimer",
    label: "Disclaimer",
    icon: InfoIcon,
  },
];

interface SidebarProps {
  onClearChat?: () => void;
  hasMessages?: boolean;
  className?: string;
}

export function Sidebar({
  onClearChat,
  hasMessages = false,
  className,
}: SidebarProps) {
  const [isHovered, setIsHovered] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const { theme, toggleTheme } = useTheme();
  const pathname = usePathname();
  useTextSize();

  return (
    <>
      {!isMobileOpen && (
        <button
          type="button"
          onClick={() => setIsMobileOpen(true)}
          className="lg:hidden fixed top-4 left-4 z-40 rounded-md border border-brand-gold/70 bg-surface-elevated/90 p-2 text-text-secondary hover:text-text-primary hover:bg-surface-muted/80 transition-colors"
          aria-label="Open sidebar"
        >
          <MenuIcon className="w-5 h-5" />
        </button>
      )}

      {isMobileOpen && (
        <div
          className="lg:hidden fixed inset-0 z-30 bg-black/40"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      <aside
        className={cn(
          "lg:hidden fixed inset-y-0 left-0 z-40 w-64",
          "bg-surface-elevated border-r-4 border-brand-gold/70",
          "transition-transform duration-300 ease-out",
          isMobileOpen ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex flex-col h-full">
          <div className="flex items-center h-16 px-3 border-b-2 border-brand-gold/50 justify-between">
            <MainLogo className="animate-fade-in" />
            <button
              type="button"
              onClick={() => setIsMobileOpen(false)}
              className="text-xs text-text-secondary hover:text-text-primary"
              aria-label="Close sidebar"
            >
              Close
            </button>
          </div>

          <div className="flex-1 overflow-y-auto py-4">
            <div className="px-2 mb-2">
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
                      "px-3 py-2.5",
                      isActive && "bg-surface-muted/60 text-text-primary",
                    )}
                    onClick={(event) => {
                      if (page.href === "/" && pathname === "/") {
                        event.preventDefault();
                        return;
                      }
                      setIsMobileOpen(false);
                    }}
                  >
                    <Icon className="w-5 h-5 flex-shrink-0 text-brand-green" />
                    <span className="text-sm truncate animate-fade-in">
                      {page.label}
                    </span>
                  </Link>
                );
              })}
            </nav>
          </div>

          <div className="border-t-2 border-brand-gold/50 p-2 flex flex-col gap-1">
            <button
              onClick={() => {
                onClearChat?.();
                setIsMobileOpen(false);
              }}
              disabled={!hasMessages}
              className={cn(
                "flex items-center gap-3 rounded-md",
                "text-text-secondary hover:text-text-primary",
                "hover:bg-surface-muted/50",
                "transition-all duration-200",
                "px-3 py-2.5",
                !hasMessages &&
                  "opacity-40 cursor-not-allowed hover:bg-transparent",
              )}
              title={hasMessages ? "Clear chat" : "No messages to clear"}
              aria-label="Clear chat"
            >
              <TrashIcon className="w-5 h-5 flex-shrink-0" />
              <span className="text-sm animate-fade-in">Clear Chat</span>
            </button>

            <Link
              href="/settings"
              className={cn(
                "flex items-center gap-3 rounded-md",
                "text-text-secondary hover:text-text-primary",
                "hover:bg-surface-muted/50",
                "transition-all duration-200",
                "px-3 py-2.5",
              )}
              title="Settings"
              onClick={() => setIsMobileOpen(false)}
            >
              <SettingsIcon className="w-5 h-5 flex-shrink-0" />
              <span className="text-sm animate-fade-in">Settings</span>
            </Link>

            <button
              onClick={toggleTheme}
              className={cn(
                "flex items-center gap-3 rounded-md",
                "text-text-secondary hover:text-text-primary",
                "hover:bg-surface-muted/50",
                "transition-all duration-200",
                "px-3 py-2.5",
              )}
              title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
            >
              {theme === "dark" ? (
                <SunIcon className="w-5 h-5 flex-shrink-0" />
              ) : (
                <MoonIcon className="w-5 h-5 flex-shrink-0" />
              )}
              <span className="text-sm animate-fade-in">
                {theme === "dark" ? "Light Mode" : "Dark Mode"}
              </span>
            </button>
          </div>
        </div>
      </aside>

      <aside
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        className={cn(
          "hidden lg:flex flex-col h-full",
          "bg-surface-elevated border-r-4 border-brand-gold/70",
          "transition-all duration-300 ease-out",
          isHovered ? "w-64" : "w-16",
          className,
        )}
      >
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
    </>
  );
}
