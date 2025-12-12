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
    <div className="bg-white p-6 rounded-2xl border border-meta-gray-300/50">
      <div className="space-y-4">
        {steps.map((step) => (
          <div key={step.id} className="flex items-center gap-3">
            {step.completed ? (
              <div className="w-6 h-6 rounded-full bg-meta-blue flex items-center justify-center">
                <Check className="text-white" size={16} />
              </div>
            ) : step.inProgress ? (
              <div className="w-6 h-6 rounded-full bg-meta-blue flex items-center justify-center animate-pulse">
                <Hourglass className="text-white" size={16} />
              </div>
            ) : (
              <div className="w-6 h-6 flex items-center justify-center">
                <div className="w-3 h-3 bg-meta-gray-300 rounded-full"></div>
              </div>
            )}
            <span className={`${step.completed ? 'text-meta-gray' : step.inProgress ? 'text-meta-gray' : 'text-meta-gray/50'} font-medium`}>
              {step.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};
