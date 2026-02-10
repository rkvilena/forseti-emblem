"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/chat";
import { MainLogo } from "@/components/brand/main-logo";
import { useTextSize, type TextSize } from "@/hooks/use-text-size";

const OPTIONS: { value: TextSize; label: string }[] = [
  { value: "sm", label: "Small" },
  { value: "md", label: "Default" },
  { value: "lg", label: "Large" },
  { value: "xl", label: "Extra large" },
];

export default function SettingsPage() {
  const { textSize, setTextSize } = useTextSize();
  const [value, setValue] = useState<TextSize>(textSize);

  useEffect(() => {
    setValue(textSize);
  }, [textSize]);

  return (
    <div className="relative isolate flex h-screen max-h-screen overflow-hidden bg-surface-base">
      <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-1/4 -right-1/4 w-1/2 h-1/2 bg-brand-teal/5 rounded-full blur-3xl" />
        <div className="absolute -bottom-1/4 -left-1/4 w-1/2 h-1/2 bg-brand-green/5 rounded-full blur-3xl" />
        <div className="absolute inset-0 flex items-center justify-center">
          <MainLogo
            variant="watermark"
            className="opacity-[0.12] scale-[1.35]"
          />
        </div>
      </div>

      <div className="relative z-10">
        <Sidebar hasMessages={false} />
      </div>

      <main className="relative z-10 flex-1 flex flex-col min-w-0">
        <div className="flex-1 flex flex-col min-h-0 px-6 py-8">
          <div className="max-w-3xl w-full mx-auto space-y-6">
            <header className="space-y-1">
              <h1 className="text-2xl font-semibold">Settings</h1>
              <p className="text-sm text-muted-foreground">
                Adjust how text appears across Forsetiemblem.
              </p>
            </header>

            <section className="border border-brand-gold/70 bg-surface-elevated shadow-sm p-4 flex flex-col gap-3">
              <div className="flex items-center justify-between gap-4 flex-wrap">
                <div className="space-y-1">
                  <h2 className="text-base font-semibold">Text size</h2>
                  <p className="text-xs text-muted-foreground max-w-md">
                    Choose how large text should appear by default. Components
                    that specify their own size may differ slightly.
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <label
                    htmlFor="text-size"
                    className="text-xs text-muted-foreground"
                  >
                    Size
                  </label>
                  <select
                    id="text-size"
                    value={value}
                    onChange={(event) => {
                      const next = event.target.value as TextSize;
                      setValue(next);
                      setTextSize(next);
                    }}
                    className="border border-brand-gold/70 bg-surface-elevated px-3 py-1.5 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-brand-teal focus:ring-offset-2 focus:ring-offset-surface-base"
                  >
                    {OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </section>
          </div>
        </div>
      </main>
    </div>
  );
}
