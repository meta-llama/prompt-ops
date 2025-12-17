import * as React from "react";
import { AlertCircle, CheckCircle, Info, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";
import type { InfoBoxVariant } from "@/types";

export type { InfoBoxVariant } from "@/types";

export interface InfoBoxProps {
  variant: InfoBoxVariant;
  title?: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

const variantStyles: Record<
  InfoBoxVariant,
  { container: string; title: string; icon: React.ReactNode }
> = {
  info: {
    container:
      "bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800",
    title: "text-blue-900 dark:text-blue-300",
    icon: <Info className="w-5 h-5 text-blue-600 dark:text-blue-400" />,
  },
  warning: {
    container:
      "bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800",
    title: "text-yellow-900 dark:text-yellow-300",
    icon: (
      <AlertTriangle className="w-5 h-5 text-yellow-600 dark:text-yellow-400" />
    ),
  },
  success: {
    container:
      "bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800",
    title: "text-green-900 dark:text-green-300",
    icon: <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />,
  },
  error: {
    container:
      "bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800",
    title: "text-red-900 dark:text-red-300",
    icon: <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400" />,
  },
};

/**
 * A styled info/alert box component for displaying messages, tips, or warnings.
 * Supports info, warning, success, and error variants.
 */
export const InfoBox: React.FC<InfoBoxProps> = ({
  variant,
  title,
  icon,
  children,
  className,
}) => {
  const styles = variantStyles[variant];
  const displayIcon = icon ?? styles.icon;

  return (
    <div
      className={cn(
        "rounded-xl p-4 border",
        styles.container,
        className
      )}
    >
      <div className="flex items-start space-x-3">
        <div className="flex-shrink-0 mt-0.5">{displayIcon}</div>
        <div className="flex-1 min-w-0">
          {title && (
            <h4 className={cn("font-semibold mb-1", styles.title)}>{title}</h4>
          )}
          <div className="text-sm text-muted-foreground">{children}</div>
        </div>
      </div>
    </div>
  );
};
