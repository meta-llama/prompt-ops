import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-full font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed [&_svg]:pointer-events-none [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        // Filled variants - solid background, white text, darker on hover
        filled: "bg-meta-blue text-white hover:bg-meta-blue-800",
        filledTeal: "bg-meta-teal text-white hover:bg-meta-teal-800",
        filledDestructive: "bg-red-500 text-white hover:bg-red-600",

        // Outlined variants - border with matching text, darker border on hover
        outlined: "border-2 border-meta-blue text-meta-blue bg-transparent hover:border-meta-blue-800 hover:text-meta-blue-800",
        outlinedGray: "border-2 border-meta-gray-300 text-meta-gray bg-transparent hover:border-meta-gray-600 hover:text-meta-gray",
        outlinedDestructive: "border-2 border-red-500 text-red-500 bg-transparent hover:border-red-600 hover:text-red-600",

        // Ghost variant - no background or border, just text
        ghost: "text-meta-gray hover:bg-meta-gray-100 hover:text-meta-gray",

        // Link variant
        link: "text-meta-blue underline-offset-4 hover:underline",
      },
      size: {
        // Medium - standard size
        medium: "h-10 px-5 py-2 text-sm [&_svg]:size-4",

        // Large - taller with bigger text and icons
        large: "h-12 px-8 py-3 text-lg [&_svg]:size-5",

        // Icon only
        icon: "h-10 w-10 [&_svg]:size-4",
        iconLarge: "h-12 w-12 [&_svg]:size-5",
      },
    },
    defaultVariants: {
      variant: "filled",
      size: "medium",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
