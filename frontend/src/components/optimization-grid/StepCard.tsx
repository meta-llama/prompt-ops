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
    "bg-white text-facebook-text rounded-xl p-4",
    "transition-all duration-200",
    "cursor-pointer",
    "border-2",
    "hover:scale-[1.02]",
    "shadow-sm",
    className
  );

  const statusClasses = {
    empty:
      "border-dashed border-facebook-border hover:border-facebook-blue/30 hover:shadow-md",
    active: "border-solid border-facebook-blue shadow-lg",
    completed: "border-solid border-green-500 bg-green-50 shadow-md",
    error: "border-solid border-red-500 bg-red-50 shadow-md",
  };

  const iconClasses = {
    empty: "opacity-50 text-facebook-text/40",
    active: "text-facebook-blue",
    completed: "text-green-600",
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
          <CheckCircle className="w-5 h-5 text-green-600" />
        )}
        {status === "error" && errorCount && (
          <div className="flex items-center gap-1 bg-red-100 px-2 py-1 rounded-full border border-red-200">
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
            <span className="text-xs text-facebook-text/60 mt-0.5">
              {subtitle}
            </span>
          )}
          <span className="text-xs text-facebook-text/50 mt-1 font-medium">
            {required ? "(required)" : "(optional)"}
          </span>
        </div>
      </div>

      {/* Active pulse animation with Facebook blue gradient */}
      {status === "active" && (
        <div
          className="absolute inset-0 rounded-xl animate-pulse opacity-30"
          style={{
            background:
              "linear-gradient(135deg, hsl(var(--facebook-blue)), hsl(var(--facebook-blue-light)))",
          }}
        />
      )}
    </button>
  );
};
