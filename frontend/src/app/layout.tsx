import type { Metadata, Viewport } from "next";
import "@/styles/globals.css";
import { nocturneSerif } from "@/styles/fonts";

export const metadata: Metadata = {
  title: "Forsetiemblem - Fire Emblem Chapter Assistant",
  description: "AI-powered assistant for Fire Emblem chapter information. Ask questions about storylines, characters, and strategies.",
  keywords: ["Fire Emblem", "RAG", "AI Assistant", "Gaming", "Strategy"],
  authors: [{ name: "Forsetiemblem" }],
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  themeColor: "#0d1117",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning className={`dark ${nocturneSerif.variable}`}>
      <body className="min-h-screen bg-surface-base antialiased">
        {children}
      </body>
    </html>
  );
}
