/**
 * TypingIndicator Component
 * 
 * Animated dots indicating the assistant is typing.
 */

import { cn } from "@/lib/utils";

interface TypingIndicatorProps {
  className?: string;
}

export function TypingIndicator({ className }: TypingIndicatorProps) {
  return (
    <div className={cn("flex items-center gap-1.5 py-1", className)}>
      <span className="sr-only">Assistant is typing...</span>
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className={cn(
            "w-2 h-2 rounded-full bg-brand-gold",
            "animate-bounce"
          )}
          style={{
            animationDelay: `${i * 150}ms`,
            animationDuration: "0.6s",
          }}
        />
      ))}
    </div>
  );
}
