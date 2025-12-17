import * as React from "react";
import { CheckCircle, ChevronDown, ChevronUp } from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "./badge";
import type { WizardSectionStatus } from "@/types";

export type { WizardSectionStatus } from "@/types";

export interface WizardSectionProps {
  id: string;
  title: string;
  icon: React.ReactNode;
  status: WizardSectionStatus;
  collapsed: boolean;
  onToggle: () => void;
  children: React.ReactNode;
  className?: string;
}

/**
 * A collapsible section component for wizard/form flows.
 * Displays a header with status indicator, icon, and title.
 * Content is shown/hidden based on collapsed state.
 */
export const WizardSection: React.FC<WizardSectionProps> = ({
  id,
  title,
  icon,
  status,
  collapsed,
  onToggle,
  children,
  className,
}) => {
  const statusStyles = {
    complete: "bg-meta-teal/10 text-meta-teal",
    incomplete: "bg-meta-orange/10 text-meta-orange",
    empty: "bg-meta-blue/10 text-meta-blue",
  };

  return (
    <div className={cn("space-y-4", className)}>
      {/* Section Header */}
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-4 bg-muted rounded-xl border border-border hover:border-meta-blue/30 transition-colors"
        aria-expanded={!collapsed}
        aria-controls={`wizard-section-content-${id}`}
      >
        <div className="flex items-center space-x-3">
          <div
            className={cn(
              "w-10 h-10 rounded-xl flex items-center justify-center",
              statusStyles[status]
            )}
          >
            {status === "complete" ? (
              <CheckCircle className="w-5 h-5" />
            ) : (
              icon
            )}
          </div>
          <h3 className="text-lg font-bold text-foreground">{title}</h3>
          {status === "complete" && <Badge variant="success">Complete</Badge>}
          {status === "incomplete" && (
            <Badge variant="warning">In Progress</Badge>
          )}
        </div>
        {collapsed ? (
          <ChevronDown className="w-5 h-5 text-muted-foreground" />
        ) : (
          <ChevronUp className="w-5 h-5 text-muted-foreground" />
        )}
      </button>

      {/* Section Content */}
      {!collapsed && (
        <div
          id={`wizard-section-content-${id}`}
          className="pl-4 space-y-4"
        >
          {children}
        </div>
      )}
    </div>
  );
};
