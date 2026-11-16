"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import apiClient from "@/lib/api-client";
import { Sidebar } from "@/components/chat";
import { MainLogo } from "@/components/brand/main-logo";

export default function ChaptersPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const {
    data,
    error,
    isLoading,
  } = useQuery({
    queryKey: ["chapters"],
    queryFn: () => apiClient.listChapters(),
  });

  const groups = useMemo(() => data?.games ?? [], [data]);

  const normalizedQuery = searchTerm.trim().toLowerCase();

  const filteredGroups = useMemo(() => {
    if (!normalizedQuery) {
      return groups;
    }

    return groups
      .map((group) => {
        const gameName = group.game ?? "Unknown game";
        const gameMatches = gameName.toLowerCase().includes(normalizedQuery);
        const chapters = gameMatches
          ? group.chapters
          : group.chapters.filter(
              (chapter) =>
                chapter.title.toLowerCase().includes(normalizedQuery) ||
                (chapter.infobox_title ?? "")
                  .toLowerCase()
                  .includes(normalizedQuery),
            );

        return { ...group, chapters };
      })
      .filter((group) => group.chapters.length > 0);
  }, [groups, normalizedQuery]);

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

      <main className="relative z-10 flex-1 flex flex-col min-w-0 overflow-y-auto">
        <div className="flex-1 flex flex-col min-h-0 px-6 py-8">
          <div className="max-w-5xl w-full mx-auto space-y-6">
            <header className="space-y-1">
              <h1 className="text-2xl font-semibold">Documented Chapters</h1>
              <p className="text-sm text-muted-foreground">
                All chapters that have been ingested into the database, grouped
                by game.
              </p>
            </header>

            {!isLoading && !error && groups.length > 0 && (
              <div>
                <label htmlFor="chapter-search" className="sr-only">
                  Search chapters
                </label>
                <input
                  id="chapter-search"
                  type="search"
                  value={searchTerm}
                  onChange={(event) => setSearchTerm(event.target.value)}
                  placeholder="Search by game or chapter name..."
                  className="w-full border border-brand-gold/70 bg-surface-elevated px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-brand-teal/60"
                />
              </div>
            )}

            {isLoading ? (
              <p className="text-sm text-muted-foreground">Loading...</p>
            ) : error ? (
              <p className="text-sm text-destructive">
                {error instanceof Error
                  ? error.message
                  : "Failed to load documented chapters."}
              </p>
            ) : groups.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No chapters have been ingested yet.
              </p>
            ) : filteredGroups.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No chapters match &ldquo;{searchTerm.trim()}&rdquo;.
              </p>
            ) : (
              <div className="grid gap-6 md:grid-cols-2 pb-6">
                {filteredGroups.map((group) => {
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
                              {chapter.source_url ? (
                                <a
                                  href={chapter.source_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-foreground transition-colors hover:text-brand-gold focus-visible:text-brand-gold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold/70 focus-visible:ring-offset-2 focus-visible:ring-offset-surface-elevated"
                                >
                                  {displayTitle}
                                </a>
                              ) : (
                                displayTitle
                              )}
                            </li>
                          );
                        })}
                      </ul>
                    </section>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
