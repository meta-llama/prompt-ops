import React, { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import {
  Check,
  Settings,
  Zap,
  Target,
  ChevronDown,
  ChevronUp,
  HelpCircle,
  AlertCircle,
  Clock,
  BarChart3,
  Sparkles,
  Cpu,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { SectionTitle } from "@/components/ui/section-title";
import { getStatusColor, getSpeedColor, getQualityColor } from "@/lib/status-colors";
import type { OptimizerConfig, CustomParameters } from "@/types";

interface OptimizerSelectorProps {
  selectedOptimizer?: string;
  onOptimizerChange: (optimizer: string, config: OptimizerConfig, customParams?: any) => void;
  modelCount?: number;
  useCase?: string;
}

const OPTIMIZER_CONFIGS: OptimizerConfig[] = [
  {
    id: "basic",
    name: "Standard Optimization",
    description: "Smart prompt refinement with format improvements and example-based learning",
    icon: <Zap className="w-6 h-6" />,
    category: "basic",
    complexity: "low",
    execution_time: "fast",
    optimization_quality: "good",
    features: [
      "Format and style refinement",
      "Example-based learning",
      "Instruction optimization",
      "Works with any model"
    ],
    use_cases: [
      "General prompt improvement",
      "Q&A and classification tasks",
      "RAG applications",
      "Any LLM workflow"
    ],
    pros: [
      "Fast execution (5-10 minutes)",
      "Works with all models",
      "Reliable improvements",
      "Simple to configure"
    ],
    cons: [
      "May need multiple runs for complex prompts"
    ],
    technical_details: [
      "Uses DSPy MIPROv2 optimizer",
      "Auto mode: 'basic' (light optimization)",
      "Limited prompt restructuring",
      "Focus on format improvements"
    ],
    parameters: {
      auto_mode: "basic",
      max_bootstrapped_demos: 4,
      max_labeled_demos: 5,
      num_candidates: 10,
      num_threads: 18,
      max_errors: 10,
      seed: 9,
      init_temperature: 0.5,
      track_stats: true,
      log_dir: undefined,
      metric_threshold: undefined,
      num_trials: undefined,
      minibatch: true,
      minibatch_size: 25,
      minibatch_full_eval_steps: 10,
      program_aware_proposer: true,
      data_aware_proposer: true,
      view_data_batch_size: 10,
      tip_aware_proposer: true,
      fewshot_aware_proposer: true,
      use_llama_tips: true
    }
  },
];

export const OptimizerSelector: React.FC<OptimizerSelectorProps> = ({
  selectedOptimizer,
  onOptimizerChange,
  modelCount = 0,
  useCase
}) => {
  const [expandedOptimizer, setExpandedOptimizer] = useState<string | null>(null);
  const [showTechnicalConfig, setShowTechnicalConfig] = useState<string | null>(null);
  const [customParameters, setCustomParameters] = useState<Record<string, CustomParameters>>({});

  // Auto-select the basic optimizer on mount if none selected
  useEffect(() => {
    if (!selectedOptimizer) {
      const basicConfig = OPTIMIZER_CONFIGS.find(c => c.id === "basic");
      if (basicConfig) {
        onOptimizerChange("basic", basicConfig, basicConfig.parameters);
      }
    }
  }, []);

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case "basic":
        return <Zap className="w-4 h-4" />;
      case "experimental":
        return <Sparkles className="w-4 h-4" />;
      default:
        return <Settings className="w-4 h-4" />;
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case "basic":
        return "bg-green-500/20 text-green-300 border-green-400/30";
      case "experimental":
        return "bg-purple-500/20 text-purple-300 border-purple-400/30";
      default:
        return "bg-white/[0.05] text-white/70 border-white/[0.1]";
    }
  };

  const getRecommendedOptimizer = () => {
    return "basic";
  };

  const getEffectiveParameters = (optimizerId: string): CustomParameters => {
    const baseConfig = OPTIMIZER_CONFIGS.find(c => c.id === optimizerId);
    const customParams = customParameters[optimizerId];

    if (!baseConfig) {
      return {
        auto_mode: "basic",
        max_bootstrapped_demos: 4,
        max_labeled_demos: 5,
        num_candidates: 10,
        num_threads: 18,
        max_errors: 10,
        seed: 9,
        init_temperature: 0.5,
        track_stats: true,
        log_dir: undefined,
        metric_threshold: undefined,
        num_trials: undefined,
        minibatch: true,
        minibatch_size: 25,
        minibatch_full_eval_steps: 10,
        program_aware_proposer: true,
        data_aware_proposer: true,
        view_data_batch_size: 10,
        tip_aware_proposer: true,
        fewshot_aware_proposer: true,
        use_llama_tips: true
      };
    }

    return customParams || baseConfig.parameters;
  };

  const updateParameter = (optimizerId: string, paramName: keyof CustomParameters, value: any) => {
    const baseConfig = OPTIMIZER_CONFIGS.find(c => c.id === optimizerId);
    if (!baseConfig) return;

    const currentParams = customParameters[optimizerId] || baseConfig.parameters;
    const updatedParams = { ...currentParams, [paramName]: value };

    setCustomParameters(prev => ({
      ...prev,
      [optimizerId]: updatedParams
    }));

    // Notify parent with updated configuration
    const effectiveConfig = { ...baseConfig, parameters: updatedParams };
    onOptimizerChange(optimizerId, effectiveConfig, updatedParams);
  };

  const handleOptimizerSelect = (optimizerId: string) => {
    const config = OPTIMIZER_CONFIGS.find(c => c.id === optimizerId);
    if (!config) return;

    const effectiveParams = getEffectiveParameters(optimizerId);
    const effectiveConfig = { ...config, parameters: effectiveParams };

    onOptimizerChange(optimizerId, effectiveConfig, effectiveParams);
  };

  return (
    <div className="space-y-6">
      <SectionTitle
        title="Optimization Settings"
        subtitle="Review the optimizer configuration or expand to customize advanced parameters"
      />


      <div className="grid grid-cols-1 gap-6">
        {OPTIMIZER_CONFIGS.map((optimizer) => {
          const isSelected = selectedOptimizer === optimizer.id;
          const isExpanded = expandedOptimizer === optimizer.id;
          const isRecommended = optimizer.id === getRecommendedOptimizer();

          return (
            <div
              key={optimizer.id}
              className={cn(
                "relative rounded-2xl border-2 transition-all duration-300",
                "bg-white/[0.02]",
                isSelected
                  ? "border-[#4da3ff] bg-[#4da3ff]/10 shadow-[#4da3ff]/20"
                  : "border-white/[0.1] hover:border-[#4da3ff]/30"
              )}
            >
              {/* Recommended Badge */}
              {isRecommended && (
                <div className="absolute -top-3 left-6 z-10">
                  <Badge variant="accent" className="px-3 py-1">
                    <Target className="w-3 h-3 mr-1" />
                    Recommended
                  </Badge>
                </div>
              )}

              {/* Selection indicator */}
              {isSelected && (
                <div className="absolute top-4 right-4 w-8 h-8 bg-[#4da3ff] rounded-full flex items-center justify-center">
                  <Check className="w-5 h-5 text-white" />
                </div>
              )}

              <div className="p-6">
                {/* Header */}
                <div
                  className="flex items-start gap-4 cursor-pointer"
                  onClick={() => handleOptimizerSelect(optimizer.id)}
                >
                  {/* Icon */}
                  <div className={cn(
                    "w-14 h-14 rounded-xl flex items-center justify-center flex-shrink-0",
                    isSelected
                      ? "bg-[#4da3ff] text-white"
                      : "bg-white/[0.08] text-white/70"
                  )}>
                    {optimizer.icon}
                  </div>

                  {/* Main content */}
                  <div className="flex-1 min-w-0">
                    {/* Title and badges */}
                    <div className="flex items-center gap-2 mb-2 flex-wrap">
                      <h3 className="text-xl font-bold text-white">
                        {optimizer.name}
                      </h3>
                      <Badge className={cn("text-xs font-medium border", getCategoryColor(optimizer.category))}>
                        {getCategoryIcon(optimizer.category)}
                        <span className="ml-1 capitalize">{optimizer.category}</span>
                      </Badge>
                    </div>

                    {/* Description */}
                    <p className="text-white/60 mb-4 leading-relaxed">
                      {optimizer.description}
                    </p>

                    {/* Quick stats */}
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
                      <div className="flex items-center gap-2">
                        <BarChart3 className="w-4 h-4 text-white/30" />
                        <div>
                          <p className="text-xs text-white/50 uppercase tracking-wide font-medium">
                            Complexity
                          </p>
                          <p className={cn("font-semibold capitalize", getStatusColor(optimizer.complexity))}>
                            {optimizer.complexity}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4 text-white/30" />
                        <div>
                          <p className="text-xs text-white/50 uppercase tracking-wide font-medium">
                            Speed
                          </p>
                          <p className={cn("font-semibold capitalize", getSpeedColor(optimizer.execution_time))}>
                            {optimizer.execution_time}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <Target className="w-4 h-4 text-white/30" />
                        <div>
                          <p className="text-xs text-white/50 uppercase tracking-wide font-medium">
                            Quality
                          </p>
                          <p className={cn("font-semibold capitalize", getQualityColor(optimizer.optimization_quality))}>
                            {optimizer.optimization_quality}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Key features */}
                    <div className="flex flex-wrap gap-2">
                      {optimizer.features.slice(0, 3).map((feature, index) => (
                        <Badge
                          key={index}
                          variant="outline"
                          className="text-xs bg-white/[0.05] border-white/[0.1] text-white/60"
                        >
                          {feature}
                        </Badge>
                      ))}
                      {optimizer.features.length > 3 && (
                        <Badge variant="default">
                          +{optimizer.features.length - 3} more
                        </Badge>
                      )}
                    </div>

                    {/* Subtle technical attribution */}
                    <p className="text-[11px] text-white/30 mt-3">
                      Built on DSPy MIPROv2
                    </p>
                  </div>
                </div>

                {/* Expandable details */}
                <Collapsible
                  open={isExpanded}
                  onOpenChange={(open) => setExpandedOptimizer(open ? optimizer.id : null)}
                >
                  <CollapsibleTrigger asChild>
                    <Button
                      variant="ghost"
                      className="w-full mt-4 flex items-center justify-center gap-2 text-white/60 hover:text-white hover:bg-white/[0.05]"
                    >
                      {isExpanded ? (
                        <>
                          <ChevronUp className="w-4 h-4" />
                          Hide Details
                        </>
                      ) : (
                        <>
                          <ChevronDown className="w-4 h-4" />
                          View Details
                        </>
                      )}
                    </Button>
                  </CollapsibleTrigger>

                  <CollapsibleContent className="mt-4 pt-4 border-t border-white/[0.1]">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* Use Cases */}
                      <div>
                        <h4 className="font-semibold text-white mb-2 flex items-center gap-2">
                          <Target className="w-4 h-4" />
                          Best For
                        </h4>
                        <ul className="space-y-1">
                          {optimizer.use_cases.map((useCase, index) => (
                            <li key={index} className="text-sm text-white/60 flex items-start gap-2">
                              <Check className="w-3 h-3 mt-0.5 text-green-400 flex-shrink-0" />
                              {useCase}
                            </li>
                          ))}
                        </ul>
                      </div>

                      {/* Pros & Cons */}
                      <div>
                        <h4 className="font-semibold text-white mb-2 flex items-center gap-2">
                          <BarChart3 className="w-4 h-4" />
                          Trade-offs
                        </h4>
                        <div className="space-y-3">
                          <div>
                            <p className="text-xs font-medium text-green-400 uppercase tracking-wide mb-1">Advantages</p>
                            <ul className="space-y-1">
                              {optimizer.pros.slice(0, 2).map((pro, index) => (
                                <li key={index} className="text-sm text-white/60 flex items-start gap-2">
                                  <Check className="w-3 h-3 mt-0.5 text-green-400 flex-shrink-0" />
                                  {pro}
                                </li>
                              ))}
                            </ul>
                          </div>
                          <div>
                            <p className="text-xs font-medium text-orange-400 uppercase tracking-wide mb-1">Considerations</p>
                            <ul className="space-y-1">
                              {optimizer.cons.slice(0, 2).map((con, index) => (
                                <li key={index} className="text-sm text-white/60 flex items-start gap-2">
                                  <AlertCircle className="w-3 h-3 mt-0.5 text-orange-400 flex-shrink-0" />
                                  {con}
                                </li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Technical Details */}
                    <div className="mt-6 p-4 bg-white/[0.03] rounded-xl">
                      <h4 className="font-semibold text-white mb-2 flex items-center gap-2">
                        <Cpu className="w-4 h-4" />
                        Technical Configuration
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                        <div>
                          <p className="text-white/60"><strong className="text-white">Auto Mode:</strong> {optimizer.parameters.auto_mode}</p>
                          <p className="text-white/60"><strong className="text-white">Max Demos:</strong> {optimizer.parameters.max_labeled_demos}</p>
                        </div>
                        <div>
                          <p className="text-white/60"><strong className="text-white">Candidates:</strong> {optimizer.parameters.num_candidates}</p>
                          <p className="text-white/60"><strong className="text-white">Threads:</strong> {optimizer.parameters.num_threads}</p>
                        </div>
                      </div>
                    </div>
                  </CollapsibleContent>
                </Collapsible>

                {/* Technical Configuration */}
                {isSelected && (
                  <div className="mt-4 pt-4 border-t border-white/[0.1]">
                    <Collapsible
                      open={showTechnicalConfig === optimizer.id}
                      onOpenChange={(open) => setShowTechnicalConfig(open ? optimizer.id : null)}
                    >
                      <CollapsibleTrigger asChild>
                        <Button
                          variant="outlinedGray"
                          size="medium"
                          className="w-full"
                        >
                          <Settings className="w-4 h-4" />
                          {showTechnicalConfig === optimizer.id ? (
                            <>
                              <ChevronUp className="w-4 h-4" />
                              Hide Technical Configuration
                            </>
                          ) : (
                            <>
                              <ChevronDown className="w-4 h-4" />
                              Configure Advanced Parameters
                            </>
                          )}
                        </Button>
                      </CollapsibleTrigger>

                      <CollapsibleContent className="mt-4">
                        <div className="bg-white/[0.03] rounded-xl p-4">
                          <h5 className="font-semibold text-white mb-3 flex items-center gap-2">
                            <Cpu className="w-4 h-4" />
                            Technical Parameters
                          </h5>
                          <p className="text-sm text-white/60 mb-4">
                            Customize the optimization parameters. Leave defaults if unsure.
                          </p>

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {/* Max Candidates */}
                            <div className="space-y-2">
                              <Label className="text-sm font-medium text-white">
                                Number of Candidates
                              </Label>
                              <Input
                                type="number"
                                min="1"
                                max="50"
                                value={getEffectiveParameters(optimizer.id).num_candidates}
                                onChange={(e) => updateParameter(optimizer.id, 'num_candidates', parseInt(e.target.value))}
                                className="border-white/[0.1] bg-white/[0.05] text-white focus:border-[#4da3ff]/50 focus:ring-[#4da3ff]/30"
                              />
                              <p className="text-xs text-white/50">How many candidate instructions to generate</p>
                            </div>

                            {/* Max Bootstrapped Demos */}
                            <div className="space-y-2">
                              <Label className="text-sm font-medium text-white">
                                Max Bootstrapped Demos
                              </Label>
                              <Input
                                type="number"
                                min="1"
                                max="20"
                                value={getEffectiveParameters(optimizer.id).max_bootstrapped_demos}
                                onChange={(e) => updateParameter(optimizer.id, 'max_bootstrapped_demos', parseInt(e.target.value))}
                                className="border-white/[0.1] bg-white/[0.05] text-white focus:border-[#4da3ff]/50 focus:ring-[#4da3ff]/30"
                              />
                              <p className="text-xs text-white/50">Examples generated from your data</p>
                            </div>

                            {/* Max Labeled Demos */}
                            <div className="space-y-2">
                              <Label className="text-sm font-medium text-white">
                                Max Labeled Demos
                              </Label>
                              <Input
                                type="number"
                                min="1"
                                max="20"
                                value={getEffectiveParameters(optimizer.id).max_labeled_demos}
                                onChange={(e) => updateParameter(optimizer.id, 'max_labeled_demos', parseInt(e.target.value))}
                                className="border-white/[0.1] bg-white/[0.05] text-white focus:border-[#4da3ff]/50 focus:ring-[#4da3ff]/30"
                              />
                              <p className="text-xs text-white/50">Labeled examples to include</p>
                            </div>

                            {/* Num Threads */}
                            <div className="space-y-2">
                              <Label className="text-sm font-medium text-white">
                                Number of Threads
                              </Label>
                              <Input
                                type="number"
                                min="1"
                                max="64"
                                value={getEffectiveParameters(optimizer.id).num_threads}
                                onChange={(e) => updateParameter(optimizer.id, 'num_threads', parseInt(e.target.value))}
                                className="border-white/[0.1] bg-white/[0.05] text-white focus:border-[#4da3ff]/50 focus:ring-[#4da3ff]/30"
                              />
                              <p className="text-xs text-white/50">Parallel processing for faster optimization</p>
                            </div>

                            {/* Max Errors */}
                            <div className="space-y-2">
                              <Label className="text-sm font-medium text-white">
                                Max Errors
                              </Label>
                              <Input
                                type="number"
                                min="1"
                                max="50"
                                value={getEffectiveParameters(optimizer.id).max_errors}
                                onChange={(e) => updateParameter(optimizer.id, 'max_errors', parseInt(e.target.value))}
                                className="border-white/[0.1] bg-white/[0.05] text-white focus:border-[#4da3ff]/50 focus:ring-[#4da3ff]/30"
                              />
                              <p className="text-xs text-white/50">How many errors to tolerate during optimization</p>
                            </div>

                            {/* Seed */}
                            <div className="space-y-2">
                              <Label className="text-sm font-medium text-white">
                                Random Seed
                              </Label>
                              <Input
                                type="number"
                                min="0"
                                value={getEffectiveParameters(optimizer.id).seed}
                                onChange={(e) => updateParameter(optimizer.id, 'seed', parseInt(e.target.value))}
                                className="border-white/[0.1] bg-white/[0.05] text-white focus:border-[#4da3ff]/50 focus:ring-[#4da3ff]/30"
                              />
                              <p className="text-xs text-white/50">For reproducible results</p>
                            </div>


                          </div>

                          <div className="mt-4 p-3 bg-blue-500/10 border border-blue-400/30 rounded-lg">
                            <p className="text-sm text-blue-300">
                              <strong>Note:</strong> These parameters control the core optimization behavior. The defaults work well for most cases.
                              Higher values for candidates and demos generally improve quality but increase execution time.
                            </p>
                          </div>
                        </div>
                      </CollapsibleContent>
                    </Collapsible>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Help section */}
      <div className="mt-8 p-4 bg-[#4da3ff]/10 border border-[#4da3ff]/20 rounded-2xl">
        <div className="flex items-start gap-3">
          <HelpCircle className="w-5 h-5 text-[#4da3ff] mt-0.5 flex-shrink-0" />
          <div>
            <h4 className="font-semibold text-white mb-1">How It Works</h4>
            <p className="text-sm text-white/60 leading-relaxed">
              The optimizer will test variations of your prompt against your dataset and find the version that performs best.
              Click <strong className="text-white">"Configure Advanced Parameters"</strong> to fine-tune technical settings.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
