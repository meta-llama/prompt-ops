import React from 'react';
import { Check, Hourglass } from 'lucide-react';
import type { OptimizationStep } from '@/types';

export type { OptimizationStep } from '@/types';

interface OptimizationProgressProps {
  steps: OptimizationStep[];
}

export const OptimizationProgress: React.FC<OptimizationProgressProps> = ({ steps }) => {
  return (
    <div className="glass-panel p-6">
      <div className="space-y-4">
        {steps.map((step) => (
          <div key={step.id} className="flex items-center gap-3">
            {step.completed ? (
              <div className="w-6 h-6 rounded-full bg-[#4da3ff] flex items-center justify-center">
                <Check className="text-white" size={16} />
              </div>
            ) : step.inProgress ? (
              <div className="w-6 h-6 rounded-full bg-[#4da3ff] flex items-center justify-center animate-pulse">
                <Hourglass className="text-white" size={16} />
              </div>
            ) : (
              <div className="w-6 h-6 flex items-center justify-center">
                <div className="w-3 h-3 bg-white/20 rounded-full"></div>
              </div>
            )}
            <span className={`${step.completed ? 'text-white' : step.inProgress ? 'text-white' : 'text-white/50'} font-medium`}>
              {step.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};
