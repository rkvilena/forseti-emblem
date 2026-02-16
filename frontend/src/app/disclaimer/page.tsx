"use client";

import { Sidebar } from "@/components/chat";
import { MainLogo } from "@/components/brand/main-logo";
import { DISCLAIMER_TEXT } from "@/components/prop/sites";

export default function DisclaimerPage() {
  return (
    <div className="relative isolate flex h-screen max-h-screen overflow-hidden bg-surface-base parchment-bg">
      <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-1/4 -right-1/4 w-1/2 h-1/2 bg-brand-teal/5 rounded-full blur-3xl" />
        <div className="absolute -bottom-1/4 -left-1/4 w-1/2 h-1/2 bg-brand-green/5 rounded-full blur-3xl" />
      </div>

      <div className="relative z-30 parchment-panel">
        <Sidebar hasMessages={false} />
      </div>

      <main className="relative z-10 flex-1 flex flex-col min-w-0">
        <div className="flex-1 flex flex-col min-h-0 px-6 py-8 overflow-y-auto">
          <div className="max-w-4xl w-full mx-auto flex flex-col items-center lg:items-start gap-6">
            <MainLogo className="text-2xl lg:text-5xl" />
            <h1 className="text-2xl font-semibold">Project Disclaimer</h1>
            <p className="text-text-secondary">
              Forseti Emblem is a non-commercial, open-source technical
              demonstration developed for portfolio purposes.
            </p>
            <ul className="list-disc pl-6 space-y-3 text-text-secondary">
              <li>
                <span className="font-semibold">Data Source:</span> Textual
                content is retrieved from the{" "}
                <a
                  className="text-brand-gold hover:text-brand-blue hover:underline transition-colors"
                  href="https://fireemblem.fandom.com/"
                >
                  Fire Emblem Wiki
                </a>{" "}
                via the MediaWiki API, utilized under the CC BY-SA 3.0 license.
              </li>
              <li>
                <span className="font-semibold">Ownership:</span> Fire Emblem
                and all associated characters, names, and lore are the
                intellectual property of Nintendo and Intelligent Systems. This
                project is not affiliated with, endorsed by, or sponsored by
                Nintendo.
              </li>
              <li>
                <span className="font-semibold">Purpose:</span> This site serves
                as a showcase of Retrieval-Augmented Generation (RAG)
                architecture and vector database implementation. It is not
                intended to replace official sources or generate revenue.
              </li>
              <li>
                <span className="font-semibold">Compliance:</span> If you are a
                rights holder and have concerns regarding data usage or would
                like content removed from the live demonstration, please reach
                out via email or open an issue on GitHub. I am committed to
                maintaining a respectful and compliant technical showcase.
                Please contact{" "}
                <a
                  className="text-brand-gold hover:text-brand-blue hover:underline transition-colors"
                  href="mailto:rkvilena11@gmail.com"
                >
                  rkvilena11@gmail.com
                </a>{" "}
                or{" "}
                <a
                  className="text-brand-gold hover:text-brand-blue hover:underline transition-colors"
                  href="https://github.com/rkvilena/forseti-emblem"
                >
                  the repository code of this project
                </a>
              </li>
            </ul>
            <p className="text-text-secondary">
              This project is built with deep respect for the creators of the
              Fire Emblem series and the community contributors at Fandom. As
              this is a personal educational experiment, I am happy to adjust or
              remove content to remain in good standing with rights holders or
              community guidelines.
            </p>
            <footer className="mt-8 text-xs text-text-muted text-center lg:fixed lg:bottom-4 lg:left-0 lg:right-0 lg:mt-0 lg:px-6">
              {DISCLAIMER_TEXT}
            </footer>
          </div>
        </div>
      </main>
    </div>
  );
}
