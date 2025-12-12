import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold pointer-events-none",
  {
    variants: {
      variant: {
        // Neutral/default - gray tones
        default: "border-meta-gray-300 bg-meta-gray-100 text-meta-gray",

        // Info - subtle blue for informational badges
        info: "border-meta-blue/30 bg-meta-blue/10 text-meta-blue",

        // Success - teal for completed/positive states
        success: "border-meta-teal/30 bg-meta-teal/10 text-meta-teal-800",

        // Warning - orange for in-progress/attention states
        warning: "border-meta-orange/30 bg-meta-orange/10 text-meta-orange-800",

        // Accent - solid blue for highlighted/recommended
        accent: "border-transparent bg-meta-blue text-white",

        // Purple - for special categories
        purple: "border-meta-purple/30 bg-meta-purple/10 text-meta-purple-800",

        // Destructive - red for errors
        destructive: "border-red-200 bg-red-50 text-red-700",

        // Outline - just a border, no fill
        outline: "border-meta-gray-300 bg-transparent text-meta-gray",
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
