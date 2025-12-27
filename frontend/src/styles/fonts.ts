import localFont from "next/font/local";

export const nocturneSerif = localFont({
  src: [
    {
      path: "../assets/fonts/fonnts.com-nocturneserif-semibolditalic.otf",
      weight: "600",
      style: "italic",
    },
  ],
  variable: "--font-brand",
  display: "swap",
});
