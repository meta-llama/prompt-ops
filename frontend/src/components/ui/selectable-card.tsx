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
          ? "border-[#4da3ff] bg-[#4da3ff]/10"
          : "border-white/[0.1] bg-white/[0.03] hover:border-white/[0.2]",
        className
      )}
    >
      {/* Selection indicator */}
      {selected && showCheckmark && (
        <div className="absolute top-3 right-3 w-6 h-6 bg-[#4da3ff] rounded-full flex items-center justify-center">
          <Check className="w-4 h-4 text-white" />
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
            ? "bg-[#4da3ff] text-white"
            : "bg-white/[0.08] text-white/60"
        )}
      >
        {icon}
      </div>

      {/* Content */}
      <h4 className="font-semibold text-white mb-2">{title}</h4>
      {description && (
        <p className="text-sm text-white/60 mb-3">{description}</p>
      )}

      {/* Additional content */}
      {children}
    </button>
  );
};
