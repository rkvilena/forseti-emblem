import { cn } from "@/lib/utils";

interface MainLogoProps {
  className?: string;
  /** Visual style: normal for sidebar, watermark for background */
  variant?: "default" | "watermark";
}

/**
 * Main Logo - Full "FORSETI EMBLEM" text with gradient
 */
export function MainLogo({ className, variant = "default" }: MainLogoProps) {
  const isWatermark = variant === "watermark";

  return (
    <span
      className={cn(
        "font-brand relative inline-block select-none whitespace-nowrap bg-gradient-to-r from-brand-lime to-brand-blue bg-clip-text text-transparent px-1",
        isWatermark ? "text-4xl sm:text-5xl" : "text-xl",
        className,
      )}
      style={{ lineHeight: 1.1 }}
    >
      FORSETI EMBLEM
    </span>
  );
}

/**
 * Logo Icon - Compact "FE" for collapsed sidebar
 */
export function MainLogoIcon({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "font-brand relative inline-block select-none text-2xl bg-gradient-to-r from-brand-lime to-brand-blue bg-clip-text text-transparent px-1",
        className,
      )}
      style={{ lineHeight: 1.1 }}
    >
      FE
    </span>
  );
}
