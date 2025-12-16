import * as React from "react";
import { cn } from "@/lib/utils";

export interface SectionTitleProps {
  title: string;
  subtitle?: string;
  className?: string;
  /** Whether to center the text (default: true) */
  centered?: boolean;
}

/**
 * A consistent section title component for wizard/form sections.
 * Displays a large title with an optional subtitle.
 */
export const SectionTitle: React.FC<SectionTitleProps> = ({
  title,
  subtitle,
  className,
  centered = true,
}) => {
  return (
    <div className={cn(centered && "text-center", "mb-6", className)}>
      <h2 className="text-2xl md:text-3xl font-normal text-foreground mb-4 tracking-tight">
        {title}
      </h2>
      {subtitle && (
        <p className="text-muted-foreground text-lg">{subtitle}</p>
      )}
    </div>
  );
};
