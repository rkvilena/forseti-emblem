"use client";

import { Sidebar } from "@/components/chat";
import { MainLogo } from "@/components/brand/main-logo";
import { SITES } from "@/components/prop/sites";

export default function AboutPage() {
  return (
    <div className="relative isolate flex h-screen max-h-screen overflow-hidden bg-surface-base parchment-bg">
      <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-1/4 -right-1/4 w-1/2 h-1/2 bg-brand-teal/5 rounded-full blur-3xl" />
        <div className="absolute -bottom-1/4 -left-1/4 w-1/2 h-1/2 bg-brand-green/5 rounded-full blur-3xl" />
      </div>

      <div className="relative z-10 parchment-panel">
        <Sidebar hasMessages={false} />
      </div>

      <main className="relative z-10 flex-1 flex flex-col min-w-0">
        <div className="flex-1 flex flex-col min-h-0 px-6 py-8 overflow-y-auto">
          <div className="max-w-5xl w-full mx-auto flex flex-col items-center text-center gap-6 flex-1">
            <MainLogo className="text-2xl lg:text-5xl" />
            <div className="w-full max-w-5xl grid grid-cols-1 lg:grid-cols-2 gap-6 text-md text-justify lg:text-lg">
              <p className="text-text-secondary">
                Forseti Emblem is a fansite that I created with the idea of
                helping Fire Emblem players who needs more information regarding
                each chapters of the games. This site covers pretty much every
                chapters of the mainline games. Currently users has limit of 15
                request per day, so please be patient if you want to ask about
                multiple chapters at once.
              </p>
              <p className="text-text-secondary">
                The source I pulled for feeding this site is from
                <a
                  className="text-brand-gold hover:text-brand-blue hover:underline transition-colors"
                  href="https://fireemblem.fandom.com/"
                >
                  {" "}
                  Fire Emblem wiki
                </a>{" "}
                because it provided a clean API to be processed instead of
                Serenes Forest (there's a possiblity that Serenes Forest
                actually provided an API but so far I haven't found it). My
                original plan actually to provide chapters information and
                character growth rates, but the latter has a complex structure
                that quite differs for each games, so I think Serenes Forest
                actually covers it pretty well. Here's the example of&nbsp;
                <a
                  className="text-brand-gold hover:text-brand-blue hover:underline transition-colors"
                  href="https://serenesforest.net/thracia-776/characters/growth-rates/"
                >
                  Thracia 776 growth rates pages
                </a>
                .
              </p>
              <p className="text-text-secondary">
                This sites uses retrieval-augmented generation to ground its
                answers in curated chapters information (so no data actually
                feeded to the LLM, it's actually LLM understanding information
                chapters as a separate context). Fire Emblem Wiki has a chapter
                information box that always exist, and that's the information
                the LLM will use to assist you. Aside from the information box,
                each chapters has no consistency of the information (strategy,
                item list, etc), so this information box is the only reliable
                one.
              </p>
              <p className="text-text-secondary">
                This project is not really intended for public use, as the
                actual purpose is to train myself in creating a AI-integrated
                website. But if you has something to discuss with me regarding
                this project, feel free to contact me through my email on my
                personal site.
              </p>
            </div>

            <div className="mt-8 lg:mt-auto flex items-center justify-center gap-6">
              {SITES.map((site) => {
                const Icon = site.Icon;
                return (
                  <a
                    key={site.label}
                    href={site.href}
                    target="_blank"
                    rel="noreferrer"
                    className="group inline-flex items-center justify-center rounded-full border border-brand-gold/70 bg-surface-elevated/80 px-4 py-2 text-sm text-text-secondary hover:bg-surface-muted/80 hover:text-text-primary transition-colors"
                  >
                    <Icon className="w-5 h-5 mr-2 text-brand-green group-hover:text-brand-lime transition-colors" />
                    <span>{site.label}</span>
                  </a>
                );
              })}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
