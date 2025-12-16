import * as React from "react";
import { useState, useEffect, useRef } from "react";
import { Target, Brain, Globe, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

export type RoleType = "target" | "optimizer" | "both";

export interface RoleBadgeProps {
  role: RoleType;
  /** If true, clicking the badge shows a dropdown to change the role */
  interactive?: boolean;
  /** Callback when role changes (only used when interactive=true) */
  onRoleChange?: (role: RoleType) => void;
  /** Roles available in the dropdown (only used when interactive=true) */
  availableRoles?: RoleType[];
  className?: string;
}

const roleConfig: Record<
  RoleType,
  {
    icon: React.ReactNode;
    label: string;
    className: string;
    interactiveClassName: string;
  }
> = {
  target: {
    icon: <Target className="w-3 h-3" />,
    label: "Target",
    className: "bg-meta-teal/10 text-meta-teal-800 border-meta-teal/30",
    interactiveClassName:
      "bg-green-100 text-green-800 border-green-200 hover:bg-green-200 dark:bg-green-900/30 dark:text-green-300 dark:border-green-800 dark:hover:bg-green-900/50",
  },
  optimizer: {
    icon: <Brain className="w-3 h-3" />,
    label: "Optimizer",
    className: "bg-meta-purple/10 text-meta-purple-800 border-meta-purple/30",
    interactiveClassName:
      "bg-purple-100 text-purple-800 border-purple-200 hover:bg-purple-200 dark:bg-purple-900/30 dark:text-purple-300 dark:border-purple-800 dark:hover:bg-purple-900/50",
  },
  both: {
    icon: (
      <div className="flex items-center space-x-0.5">
        <Target className="w-2.5 h-2.5" />
        <Brain className="w-2.5 h-2.5" />
      </div>
    ),
    label: "Target + Optimizer",
    className: "bg-meta-blue/10 text-meta-blue border-meta-blue/30",
    interactiveClassName:
      "bg-blue-100 text-blue-800 border-blue-200 hover:bg-blue-200 dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-800 dark:hover:bg-blue-900/50",
  },
};

/**
 * A badge component that displays a role (target, optimizer, or both).
 * Can be static or interactive with a dropdown to change roles.
 */
export const RoleBadge: React.FC<RoleBadgeProps> = ({
  role,
  interactive = false,
  onRoleChange,
  availableRoles = [],
  className,
}) => {
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setShowDropdown(false);
      }
    };

    if (showDropdown) {
      document.addEventListener("mousedown", handleClickOutside);
      return () =>
        document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [showDropdown]);

  const config = roleConfig[role];
  const hasDropdownOptions = interactive && availableRoles.length > 0;

  // Static badge (non-interactive)
  if (!interactive) {
    return (
      <div
        className={cn(
          "inline-flex items-center space-x-1 px-2 py-1 rounded-md text-xs font-medium border",
          config.className,
          className
        )}
      >
        {config.icon}
        <span>{config.label}</span>
      </div>
    );
  }

  // Interactive badge with dropdown
  return (
    <div className={cn("relative", className)} ref={dropdownRef}>
      <button
        onClick={() => hasDropdownOptions && setShowDropdown(!showDropdown)}
        className={cn(
          "inline-flex items-center space-x-1 px-2 py-1 rounded-md text-xs font-medium border transition-colors",
          config.interactiveClassName,
          hasDropdownOptions ? "cursor-pointer" : "cursor-default opacity-75"
        )}
        title={
          hasDropdownOptions
            ? "Click to change role"
            : "No other roles available"
        }
      >
        {config.icon}
        <span>{config.label}</span>
        {hasDropdownOptions && <ChevronDown className="w-3 h-3" />}
      </button>

      {showDropdown && hasDropdownOptions && (
        <div className="absolute top-full left-0 mt-1 bg-card border border-border rounded-xl z-50 min-w-40 shadow-lg">
          <div className="py-1">
            {availableRoles.map((availableRole) => {
              const roleConf = roleConfig[availableRole];
              return (
                <button
                  key={availableRole}
                  onClick={() => {
                    onRoleChange?.(availableRole);
                    setShowDropdown(false);
                  }}
                  className="flex items-center space-x-2 w-full px-3 py-2 text-sm text-foreground hover:bg-muted transition-colors first:rounded-t-lg last:rounded-b-lg"
                >
                  {roleConf.icon}
                  <span>{roleConf.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
