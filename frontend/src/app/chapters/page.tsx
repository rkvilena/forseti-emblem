"use client";

import { useEffect, useState } from "react";
import apiClient from "@/lib/api-client";
import type { ChapterListResponse } from "@/types";
import { Sidebar } from "@/components/chat";
import { MainLogo } from "@/components/brand/main-logo";
import { DISCLAIMER_TEXT } from "@/components/prop/sites";

export default function ChaptersPage() {
  const [data, setData] = useState<ChapterListResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    let isMounted = true;

    apiClient
      .listChapters()
      .then((response) => {
        if (!isMounted) return;
        setData(response);
      })
      .catch((err) => {
        if (!isMounted) return;
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load documented chapters.",
        );
      })
      .finally(() => {
        if (!isMounted) return;
        setIsLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const groups = data?.games ?? [];

  return (
    <div className="relative isolate flex h-screen max-h-screen overflow-hidden bg-surface-base">
      <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-1/4 -right-1/4 w-1/2 h-1/2 bg-brand-teal/5 rounded-full blur-3xl" />
        <div className="absolute -bottom-1/4 -left-1/4 w-1/2 h-1/2 bg-brand-green/5 rounded-full blur-3xl" />
        {groups.length > 0 && (
          <div className="absolute inset-0 flex items-center justify-center">
            <MainLogo
              variant="watermark"
              className="opacity-[0.12] scale-[1.35]"
            />
          </div>
        )}
      </div>

      <div className="relative z-30">
        <Sidebar hasMessages={false} />
      </div>

      <main className="relative z-10 flex-1 flex flex-col min-w-0">
        <div className="flex-1 flex flex-col min-h-0 px-6 py-8">
          <div className="max-w-5xl w-full mx-auto space-y-6">
            <header className="space-y-1">
              <h1 className="text-2xl font-semibold">Documented Chapters</h1>
              <p className="text-sm text-muted-foreground">
                All chapters that have been ingested into the database, grouped
                by game.
              </p>
            </header>

            {isLoading ? (
              <p className="text-sm text-muted-foreground">Loading...</p>
            ) : error ? (
              <p className="text-sm text-destructive">{error}</p>
            ) : groups.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No chapters have been ingested yet.
              </p>
            ) : (
              <div className="grid gap-6 md:grid-cols-2">
                {groups.map((group) => {
                  const gameName = group.game ?? "Unknown game";

                  return (
                    <section
                      key={gameName}
                      className="border border-brand-gold/70 bg-surface-elevated shadow-sm p-4 flex flex-col gap-3"
                    >
                      <h2 className="text-lg font-semibold text-foreground">
                        {gameName}
                      </h2>
                      <hr className="border-brand-gold/70" />
                      <ul className="space-y-1 text-sm text-muted-foreground">
                        {group.chapters.map((chapter) => {
                          const baseTitle =
                            chapter.infobox_title || chapter.title;
                          const fullTitle = chapter.title;
                          let displayTitle = baseTitle;

                          const parenIndex = fullTitle.indexOf(" (");
                          if (
                            parenIndex !== -1 &&
                            fullTitle !== baseTitle &&
                            parenIndex < fullTitle.length - 2
                          ) {
                            const suffix = fullTitle.slice(parenIndex);
                            displayTitle = `${baseTitle}${suffix}`;
                          }

                          return (
                            <li key={chapter.id} className="leading-snug">
                              {displayTitle}
                            </li>
                          );
                        })}
                      </ul>
                    </section>
                  );
                })}
              </div>
            )}
            <footer className="pt-4 text-xs text-text-muted text-center lg:fixed lg:bottom-4 lg:left-0 lg:right-0 lg:pt-0 lg:px-6">
              {DISCLAIMER_TEXT}
            </footer>
          </div>
        </div>
      </main>
    </div>
  );
}
