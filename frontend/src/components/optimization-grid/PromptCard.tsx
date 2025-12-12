import React from "react";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import { FileText } from "lucide-react";

interface PromptCardProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  hasError?: boolean;
}

export const PromptCard: React.FC<PromptCardProps> = ({
  value,
  onChange,
  placeholder = "Enter your prompt to optimize...",
  hasError = false,
}) => {
  return (
    <div
      className={cn(
        "w-full bg-white text-meta-gray border-2 rounded-xl p-4 shadow-sm",
        "transition-all duration-200",
        hasError
          ? "border-red-500 bg-red-50 shadow-md"
          : value
          ? "border-meta-teal bg-meta-teal/5 shadow-md"
          : "border-dashed border-meta-gray-300 hover:border-meta-blue/30 hover:shadow-md"
      )}
    >
      <div className="flex items-center gap-2 mb-3">
        <FileText
          className={cn(
            "w-5 h-5",
            value ? "text-meta-teal" : "text-meta-gray/40 opacity-50"
          )}
        />
        <h3 className="text-sm font-medium">Your Prompt</h3>
        <span className="text-xs text-meta-gray/50 font-medium">
          (required)
        </span>
      </div>
      <Textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="min-h-[120px] bg-white border-meta-gray-300 focus:border-meta-blue resize-none"
        rows={5}
      />
      {hasError && (
        <p className="text-xs text-red-600 font-medium mt-2">
          Prompt is required
        </p>
      )}
    </div>
  );
};
