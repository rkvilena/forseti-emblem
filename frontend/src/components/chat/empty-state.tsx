/**
 * EmptyState Component
 * 
 * Shown when no messages exist in the chat.
 * Provides guidance and example questions.
 */

import { cn } from "@/lib/utils";
import { SwordIcon, BookIcon, MapIcon } from "./icons";

const EXAMPLE_QUESTIONS = [
  {
    icon: SwordIcon,
    text: "What happens in Chapter 1 of Fire Emblem?",
    category: "Story",
  },
  {
    icon: BookIcon,
    text: "Who are the main characters in the prologue?",
    category: "Characters",
  },
  {
    icon: MapIcon,
    text: "What are the objectives in Chapter 5?",
    category: "Strategy",
  },
];

interface EmptyStateProps {
  onSelectQuestion?: (question: string) => void;
  className?: string;
}

export function EmptyState({ onSelectQuestion, className }: EmptyStateProps) {
  return (
    <div className={cn(
      "flex flex-col items-center justify-center h-full px-4 py-12",
      className
    )}>
      {/* Logo/Title */}
      <div className="text-center mb-8">
        {/* Emblem Icon */}
        <div className="relative inline-flex items-center justify-center mb-4">
          <div className="absolute inset-0 bg-gradient-to-br from-primary-500/20 to-accent-500/20 blur-2xl" />
          <div className="relative w-20 h-20 rounded-full bg-gradient-to-br from-primary-600 to-primary-800 flex items-center justify-center border border-primary-500/30 shadow-glow-primary">
            <span className="text-3xl font-display text-white">F</span>
          </div>
        </div>
        
        <h1 className="text-3xl font-display font-semibold text-gradient mb-2">
          Forsetiemblem
        </h1>
        <p className="text-text-secondary max-w-md">
          Your AI companion for Fire Emblem chapter knowledge. Ask anything about 
          chapters, characters, storylines, and strategies.
        </p>
      </div>

      {/* Example Questions */}
      <div className="w-full max-w-2xl">
        <p className="text-sm text-text-muted mb-4 text-center">
          Try asking about:
        </p>
        <div className="grid gap-3 sm:grid-cols-3">
          {EXAMPLE_QUESTIONS.map((question, index) => {
            const Icon = question.icon;
            return (
              <button
                key={index}
                onClick={() => onSelectQuestion?.(question.text)}
                className={cn(
                  "group relative p-4 rounded-xl text-left",
                  "bg-surface-elevated border border-surface-border",
                  "hover:border-primary-500/50 hover:shadow-glow-primary/50",
                  "transition-all duration-300",
                  "ember-glow"
                )}
              >
                <div className="flex items-center gap-2 mb-2">
                  <Icon className="w-4 h-4 text-accent-500" />
                  <span className="text-xs font-medium text-accent-500">
                    {question.category}
                  </span>
                </div>
                <p className="text-sm text-text-secondary group-hover:text-text-primary transition-colors">
                  {question.text}
                </p>
              </button>
            );
          })}
        </div>
      </div>

      {/* Disclaimer */}
      <p className="mt-8 text-xs text-text-muted text-center max-w-md">
        Powered by RAG (Retrieval-Augmented Generation) for accurate Fire Emblem information.
        Results are based on available chapter data.
      </p>
    </div>
  );
}
