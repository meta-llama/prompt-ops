import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold pointer-events-none",
  {
    variants: {
      variant: {
        // Neutral/default - uses semantic colors for dark mode
        default: "border-border bg-muted text-foreground",

        // Info - subtle blue (CSS vars flip the blue color)
        info: "border-meta-blue/30 bg-meta-blue/10 text-meta-blue",

        // Success - teal (CSS vars flip the teal color)
        success: "border-meta-teal/30 bg-meta-teal/10 text-meta-teal dark:text-meta-teal",

        // Warning - orange (CSS vars flip the orange color)
        warning: "border-meta-orange/30 bg-meta-orange/10 text-meta-orange-text",

        // Accent - solid blue background
        accent: "border-transparent bg-meta-blue text-white dark:text-meta-gray-900",

        // Purple - for special categories
        purple: "border-meta-purple/30 bg-meta-purple/10 text-meta-purple-text",

        // Destructive - red for errors
        destructive: "border-red-200 bg-red-50 text-red-700 dark:border-red-800 dark:bg-red-900/30 dark:text-red-400",

        // Outline - just a border, no fill
        outline: "border-border bg-transparent text-foreground",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
