import * as React from "react";
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

export interface SelectableCardProps {
  selected: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  title: string;
  description?: string;
  /** Optional badge to show in the top-right corner */
  badge?: React.ReactNode;
  /** Additional content to render below the description */
  children?: React.ReactNode;
  className?: string;
  /** Whether to show a checkmark when selected */
  showCheckmark?: boolean;
}

/**
 * A selectable card component for use in multi-select or single-select lists.
 * Displays an icon, title, optional description, and optional additional content.
 */
export const SelectableCard: React.FC<SelectableCardProps> = ({
  selected,
  onClick,
  icon,
  title,
  description,
  badge,
  children,
  className,
  showCheckmark = true,
}) => {
  return (
    <button
      onClick={onClick}
      className={cn(
        "relative p-6 rounded-xl border-2 text-left transition-colors w-full",
        selected
          ? "border-meta-blue dark:border-meta-blue-light bg-meta-blue/5 dark:bg-meta-blue/10"
          : "border-border bg-card hover:border-muted-foreground/50",
        className
      )}
    >
      {/* Selection indicator */}
      {selected && showCheckmark && (
        <div className="absolute top-3 right-3 w-6 h-6 bg-meta-blue dark:bg-meta-blue-light rounded-full flex items-center justify-center">
          <Check className="w-4 h-4 text-white dark:text-meta-gray-900" />
        </div>
      )}

      {/* Badge */}
      {badge && !selected && (
        <div className="absolute top-3 right-3">{badge}</div>
      )}

      {/* Icon */}
      <div
        className={cn(
          "w-12 h-12 rounded-lg flex items-center justify-center mb-4",
          selected
            ? "bg-meta-blue dark:bg-meta-blue-light text-white dark:text-meta-gray-900"
            : "bg-muted text-muted-foreground"
        )}
      >
        {icon}
      </div>

      {/* Content */}
      <h4 className="font-semibold text-foreground mb-2">{title}</h4>
      {description && (
        <p className="text-sm text-muted-foreground mb-3">{description}</p>
      )}

      {/* Additional content */}
      {children}
    </button>
  );
};
