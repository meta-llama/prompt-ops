import React from 'react';
import { Check } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Step {
  id: string;
  title: string;
  description?: string;
}

interface StepIndicatorProps {
  steps: Step[] | string[];
  currentStep: number;
  className?: string;
  variant?: 'horizontal' | 'vertical';
}

export const StepIndicator: React.FC<StepIndicatorProps> = ({
  steps,
  currentStep,
  className,
  variant = 'horizontal'
}) => {
  const stepItems = steps.map((step, index) => {
    if (typeof step === 'string') {
      return { id: `step-${index}`, title: step };
    }
    return step;
  });

  const isStepComplete = (index: number) => index < currentStep;
  const isStepActive = (index: number) => index === currentStep;

  if (variant === 'vertical') {
    return (
      <div className={cn("flex flex-col", className)}>
        {stepItems.map((step, index) => (
          <React.Fragment key={step.id}>
            <div className="flex items-center mb-4">
              {/* Step Circle */}
              <div
                className={cn(
                  "relative flex items-center justify-center",
                  "w-10 h-10 rounded-full border-2",
                  "transition-all duration-300",
                  isStepComplete(index) && "bg-meta-teal border-meta-teal",
                  isStepActive(index) && "bg-orange-400 border-orange-400",
                  !isStepComplete(index) && !isStepActive(index) && "bg-white border-gray-300"
                )}
              >
                {isStepComplete(index) ? (
                  <Check className="w-5 h-5 text-white" />
                ) : (
                  <span
                    className={cn(
                      "text-sm font-semibold",
                      isStepActive(index) ? "text-white" : "text-gray-500"
                    )}
                  >
                    {index + 1}
                  </span>
                )}
              </div>

              {/* Step Label */}
              <div className="ml-3">
                <p
                  className={cn(
                    "text-sm font-medium",
                    isStepComplete(index) || isStepActive(index)
                      ? "text-gray-900"
                      : "text-gray-500"
                  )}
                >
                  {step.title}
                </p>
                {step.description && (
                  <p className="text-xs text-gray-500 mt-1">{step.description}</p>
                )}
              </div>
            </div>

            {/* Connector Line */}
            {index < stepItems.length - 1 && (
              <div
                className={cn(
                  "w-0.5 h-8 ml-5",
                  isStepComplete(index) ? "bg-meta-teal" : "bg-meta-gray-300",
                  "transition-colors duration-300"
                )}
              />
            )}
          </React.Fragment>
        ))}
      </div>
    );
  }

  // Horizontal layout - single line with text wrapping
  return (
    <div
      className={cn(
        "flex items-start justify-center w-full",
        "px-4 py-2",
        className
      )}
    >
      {stepItems.map((step, index) => (
        <React.Fragment key={step.id}>
          {/* Step Container */}
          <div className="flex flex-col items-center min-w-0 flex-1 max-w-[140px]">
            {/* Step Circle */}
            <div
              className={cn(
                "relative flex items-center justify-center",
                "w-8 h-8 rounded-full border-2 mb-2",
                "transition-all duration-300 shrink-0",
                isStepComplete(index) && "bg-meta-teal border-meta-teal",
                isStepActive(index) && "bg-meta-blue border-meta-blue",
                !isStepComplete(index) && !isStepActive(index) && "bg-white border-gray-300"
              )}
            >
              {isStepComplete(index) ? (
                <Check className="w-4 h-4 text-white" />
              ) : (
                <span
                  className={cn(
                    "text-xs font-semibold",
                    isStepActive(index) ? "text-white" : "text-gray-500"
                  )}
                >
                  {index + 1}
                </span>
              )}
            </div>

            {/* Step Label - allows text wrapping */}
            <div className="text-center w-full">
              <p
                className={cn(
                  "text-xs font-medium leading-tight",
                  "break-words hyphens-auto",
                  isStepComplete(index) || isStepActive(index)
                    ? "text-meta-gray"
                    : "text-meta-gray-300"
                )}
                style={{ wordBreak: 'break-word' }}
              >
                {step.title}
              </p>
            </div>
          </div>

          {/* Connector Line */}
          {index < stepItems.length - 1 && (
            <div
              className={cn(
                "h-0.5 mt-4 mx-1 flex-1 min-w-[12px] max-w-[24px]",
                isStepComplete(index) ? "bg-meta-teal" : "bg-meta-gray-300",
                "transition-colors duration-300"
              )}
            />
          )}
        </React.Fragment>
      ))}
    </div>
  );
};
