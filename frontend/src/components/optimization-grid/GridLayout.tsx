import React from "react";
import { cn } from "@/lib/utils";

interface GridLayoutProps {
  children: React.ReactNode;
  maxWidth?: string;
  gap?: string;
  className?: string;
}

export const GridLayout: React.FC<GridLayoutProps> = ({
  children,
  maxWidth = "max-w-md",
  gap = "gap-2",
  className,
}) => {
  return (
    <div className={cn("w-full flex justify-center px-4 pb-6", className)}>
      <div className={cn("w-full", maxWidth, "space-y-2", gap)}>{children}</div>
    </div>
  );
};
