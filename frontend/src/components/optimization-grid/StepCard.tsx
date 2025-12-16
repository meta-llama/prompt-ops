import React from "react";
import { CheckCircle, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

export type StepStatus = "empty" | "active" | "completed" | "error";

export interface StepCardProps {
  id: string;
  icon: React.ReactNode;
  title: string;
  subtitle?: string;
  status: StepStatus;
  required: boolean;
  aspectRatio?: string;
  onClick: () => void;
  errorCount?: number;
  className?: string;
}

export const StepCard: React.FC<StepCardProps> = ({
  icon,
  title,
  subtitle,
  status,
  required,
  aspectRatio,
  onClick,
  errorCount,
  className,
}) => {
  const baseClasses = cn(
    "relative flex flex-col items-center justify-center",
    "w-full",
    "bg-white text-meta-gray rounded-xl p-4",
    "transition-all duration-200",
    "cursor-pointer",
    "border-2",
    "hover:border-meta-blue/30",
    "shadow-sm",
    className
  );

  const statusClasses = {
    empty:
      "border-dashed border-meta-gray-300 hover:border-meta-blue/30 hover:shadow-md",
    active: "border-solid border-meta-blue",
    completed: "border-solid border-meta-teal bg-meta-teal/5 shadow-md",
    error: "border-solid border-red-500 bg-red-50 shadow-md",
  };

  const iconClasses = {
    empty: "opacity-50 text-meta-gray/40",
    active: "text-meta-blue",
    completed: "text-meta-teal",
    error: "text-red-600",
  };

  return (
    <button
      onClick={onClick}
      className={cn(baseClasses, statusClasses[status])}
      style={aspectRatio ? { aspectRatio } : undefined}
      data-test={`step-card-${title.toLowerCase().replace(/\s+/g, "-")}`}
    >
      {/* Status badge */}
      <div className="absolute top-2 right-2">
        {status === "completed" && (
          <CheckCircle className="w-5 h-5 text-meta-teal" />
        )}
        {status === "error" && errorCount && (
          <div className="flex items-center gap-1 bg-red-100 px-2 py-1 rounded-md border border-red-200">
            <AlertCircle className="w-4 h-4 text-red-600" />
            <span className="text-xs text-red-600 font-medium">
              {errorCount}
            </span>
          </div>
        )}
      </div>

      {/* Main content */}
      <div className="flex flex-col items-center gap-2 relative z-[2]">
        <div className={cn("w-6 h-6", iconClasses[status])}>{icon}</div>

        <div className="flex flex-col items-center">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium capitalize">{title}</span>
          </div>
          {subtitle && (
            <span className="text-xs text-meta-gray/60 mt-0.5">
              {subtitle}
            </span>
          )}
          <span className="text-xs text-meta-gray/50 mt-1 font-medium">
            {required ? "(required)" : "(optional)"}
          </span>
        </div>
      </div>

    </button>
  );
};
