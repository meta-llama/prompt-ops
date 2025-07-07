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
    <div className="bg-white/80 backdrop-blur-xl p-6 rounded-xl border border-facebook-border shadow-lg">
      <div className="space-y-4">
        {steps.map((step) => (
          <div key={step.id} className="flex items-center gap-3">
            {step.completed ? (
              <div className="w-6 h-6 rounded-full bg-facebook-blue flex items-center justify-center">
                <Check className="text-white" size={16} />
              </div>
            ) : step.inProgress ? (
              <div className="w-6 h-6 rounded-full bg-facebook-blue flex items-center justify-center animate-pulse">
                <Hourglass className="text-white" size={16} />
              </div>
            ) : (
              <div className="w-6 h-6 flex items-center justify-center">
                <div className="w-3 h-3 bg-facebook-border rounded-full"></div>
              </div>
            )}
            <span className={`${step.completed ? 'text-facebook-text' : step.inProgress ? 'text-facebook-text' : 'text-facebook-text/50'} font-medium`}>
              {step.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};
