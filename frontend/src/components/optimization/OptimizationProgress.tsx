import React from 'react';
import { Check, Hourglass } from 'lucide-react';

export type OptimizationStep = {
  id: string;
  label: string;
  completed: boolean;
  inProgress: boolean;
};

interface OptimizationProgressProps {
  steps: OptimizationStep[];
}

export const OptimizationProgress: React.FC<OptimizationProgressProps> = ({ steps }) => {
  return (
    <div className="bg-panel p-6 rounded-2xl border border-border">
      <div className="space-y-4">
        {steps.map((step) => (
          <div key={step.id} className="flex items-center gap-3">
            {step.completed ? (
              <div className="w-6 h-6 rounded-full bg-meta-blue flex items-center justify-center">
                <Check className="text-white dark:text-meta-gray-900" size={16} />
              </div>
            ) : step.inProgress ? (
              <div className="w-6 h-6 rounded-full bg-meta-blue flex items-center justify-center animate-pulse">
                <Hourglass className="text-white dark:text-meta-gray-900" size={16} />
              </div>
            ) : (
              <div className="w-6 h-6 flex items-center justify-center">
                <div className="w-3 h-3 bg-muted-foreground/30 rounded-full"></div>
              </div>
            )}
            <span className={`${step.completed ? 'text-foreground' : step.inProgress ? 'text-foreground' : 'text-muted-foreground'} font-medium`}>
              {step.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};
