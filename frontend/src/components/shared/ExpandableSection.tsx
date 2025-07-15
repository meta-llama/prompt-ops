import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ExpandableSectionProps {
  title: string;
  children: React.ReactNode;
  defaultExpanded?: boolean;
  className?: string;
  headerClassName?: string;
  contentClassName?: string;
  icon?: React.ReactNode;
}

export const ExpandableSection: React.FC<ExpandableSectionProps> = ({
  title,
  children,
  defaultExpanded = false,
  className,
  headerClassName,
  contentClassName,
  icon
}) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  return (
    <div className={cn("border border-facebook-border rounded-2xl overflow-hidden shadow-lg backdrop-blur-xl bg-white/90", className)}>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className={cn(
          "w-full p-4 bg-white/90 hover:bg-facebook-gray",
          "flex items-center justify-between",
          "text-left font-bold text-facebook-text",
          "transition-all duration-300 transform hover:scale-105",
          headerClassName
        )}
      >
        <div className="flex items-center gap-3">
          {icon && <span className="text-facebook-blue">{icon}</span>}
          <span>{title}</span>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-5 h-5 text-facebook-blue" />
        ) : (
          <ChevronDown className="w-5 h-5 text-facebook-blue" />
        )}
      </button>

      {isExpanded && (
        <div className={cn(
          "p-4 bg-facebook-gray/50 border-t border-facebook-border",
          contentClassName
        )}>
          {children}
        </div>
      )}
    </div>
  );
};
