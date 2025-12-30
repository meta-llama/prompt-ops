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
      "bg-blue-500/10 border-blue-400/30",
    title: "text-blue-300",
    icon: <Info className="w-5 h-5 text-blue-400" />,
  },
  warning: {
    container:
      "bg-yellow-500/10 border-yellow-400/30",
    title: "text-yellow-300",
    icon: (
      <AlertTriangle className="w-5 h-5 text-yellow-400" />
    ),
  },
  success: {
    container:
      "bg-green-500/10 border-green-400/30",
    title: "text-green-300",
    icon: <CheckCircle className="w-5 h-5 text-green-400" />,
  },
  error: {
    container:
      "bg-red-500/10 border-red-400/30",
    title: "text-red-300",
    icon: <AlertCircle className="w-5 h-5 text-red-400" />,
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
          <div className="text-sm text-white/70">{children}</div>
        </div>
      </div>
    </div>
  );
};
