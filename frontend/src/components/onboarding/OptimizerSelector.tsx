import React, { useState } from "react";
import { cn } from "@/lib/utils";
import {
  Check,
  Settings,
  Zap,
  Brain,
  Target,
  ChevronDown,
  ChevronUp,
  HelpCircle,
  AlertCircle,
  Cpu,
  Clock,
  BarChart3,
  GitBranch,
  Layers,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface OptimizerConfig {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  category: "basic" | "advanced" | "experimental";
  complexity: "low" | "medium" | "high";
  execution_time: "fast" | "medium" | "slow";
  optimization_quality: "good" | "better" | "best";
  features: string[];
  use_cases: string[];
  pros: string[];
  cons: string[];
  technical_details: string[];
  parameters: CustomParameters;
}

interface OptimizerSelectorProps {
  selectedOptimizer?: string;
  onOptimizerChange: (optimizer: string, config: OptimizerConfig, customParams?: any) => void;
  modelCount?: number;
  useCase?: string;
}

interface CustomParameters {
  auto_mode: "basic" | "intermediate" | "advanced";
  max_bootstrapped_demos: number;
  max_labeled_demos: number;
  num_candidates: number;
  num_threads: number;
  max_errors: number;
  seed: number;
  init_temperature: number;
  track_stats: boolean;
  log_dir?: string;
  metric_threshold?: number;
  num_trials?: number;
  minibatch: boolean;
  minibatch_size: number;
  minibatch_full_eval_steps: number;
  program_aware_proposer: boolean;
  data_aware_proposer: boolean;
  view_data_batch_size: number;
  tip_aware_proposer: boolean;
  fewshot_aware_proposer: boolean;
  use_llama_tips: boolean;
}

const OPTIMIZER_CONFIGS: OptimizerConfig[] = [
  {
    id: "basic",
    name: "Basic Optimization",
    description: "Fast optimization using DSPy's MIPROv2 with basic auto mode for quick improvements",
    icon: <Zap className="w-6 h-6" />,
    category: "basic",
    complexity: "low",
    execution_time: "fast",
    optimization_quality: "good",
    features: [
      "Format and style adjustments",
      "Quick optimization rounds",
      "Lightweight processing",
      "Good for most use cases"
    ],
    use_cases: [
      "Quick prompt improvements",
      "Initial optimization experiments",
      "Resource-constrained environments",
      "Simple classification tasks"
    ],
    pros: [
      "Fast execution (5-10 minutes)",
      "Low resource usage",
      "Good baseline improvements",
      "Simple to configure"
    ],
    cons: [
      "Limited restructuring",
      "May miss complex optimizations",
      "Basic instruction generation"
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
  {
    id: "llama",
    name: "Llama-Optimized Strategy",
    description: "Advanced Llama-specific optimization with preprocessing and model-aware improvements",
    icon: <Brain className="w-6 h-6" />,
    category: "advanced",
    complexity: "medium",
    execution_time: "medium",
    optimization_quality: "better",
    features: [
      "Llama-specific formatting",
      "Model-aware optimization",
      "Chain of responsibility processing",
      "Advanced instruction generation"
    ],
    use_cases: [
      "Llama model optimization",
      "Complex reasoning tasks",
      "Production deployments",
      "Quality-focused optimization"
    ],
    pros: [
      "Llama-specific improvements",
      "Better quality results",
      "Model-aware processing",
      "Advanced preprocessing"
    ],
    cons: [
      "Longer execution time",
      "More complex configuration",
      "Requires Llama models"
    ],
    technical_details: [
      "Wraps BasicOptimizationStrategy",
      "Applies Llama-specific preprocessing",
      "Uses prompt processing chains",
      "Includes model-specific tips"
    ],
    parameters: {
      auto_mode: "intermediate",
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

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case "basic":
        return <Zap className="w-4 h-4" />;
      case "advanced":
        return <Brain className="w-4 h-4" />;
      case "experimental":
        return <Sparkles className="w-4 h-4" />;
      default:
        return <Settings className="w-4 h-4" />;
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case "basic":
        return "bg-green-100 text-green-800 border-green-200";
      case "advanced":
        return "bg-blue-100 text-blue-800 border-blue-200";
      case "experimental":
        return "bg-purple-100 text-purple-800 border-purple-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case "low":
        return "text-green-600";
      case "medium":
        return "text-yellow-600";
      case "high":
        return "text-red-600";
      default:
        return "text-gray-600";
    }
  };

  const getExecutionTimeColor = (time: string) => {
    switch (time) {
      case "fast":
        return "text-green-600";
      case "medium":
        return "text-yellow-600";
      case "slow":
        return "text-red-600";
      default:
        return "text-gray-600";
    }
  };

  const getQualityColor = (quality: string) => {
    switch (quality) {
      case "good":
        return "text-green-600";
      case "better":
        return "text-blue-600";
      case "best":
        return "text-purple-600";
      default:
        return "text-gray-600";
    }
  };

  const getRecommendedOptimizer = () => {
    if (useCase === "qa" || useCase === "rag") {
      return "llama"; // Recommended for Q&A and RAG tasks
    }
    return "basic"; // Default recommendation
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
      <div className="text-center mb-6">
        <h2 className="text-4xl md:text-5xl font-black text-facebook-text mb-4 tracking-tight">
          Choose Your
          <br />
          <span className="bg-gradient-to-r from-facebook-blue via-facebook-blue-light to-facebook-blue-dark bg-clip-text text-transparent">
            Optimizer
          </span>
        </h2>
        <p className="text-facebook-text/70 text-lg">
          Select the optimization strategy that best fits your use case and quality requirements
        </p>
      </div>

      {/* Recommendation Alert */}
      {useCase && (
        <Alert className="border-facebook-blue/20 bg-facebook-blue/5">
          <AlertCircle className="h-4 w-4 text-facebook-blue" />
          <AlertDescription className="text-facebook-text">
            <strong>Recommendation:</strong> For your <strong>{useCase.toUpperCase()}</strong> use case,
            we recommend the <strong>{OPTIMIZER_CONFIGS.find(o => o.id === getRecommendedOptimizer())?.name}</strong> optimizer
            for optimal results.
          </AlertDescription>
        </Alert>
      )}

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
                "bg-white/90 backdrop-blur-xl shadow-lg",
                isSelected
                  ? "border-facebook-blue bg-facebook-blue/5 shadow-facebook-blue/20"
                  : "border-facebook-border hover:border-facebook-blue/50 hover:shadow-xl"
              )}
            >
              {/* Recommended Badge */}
              {isRecommended && (
                <div className="absolute -top-3 left-6 z-10">
                  <Badge className="bg-gradient-to-r from-facebook-blue to-facebook-blue-light text-white px-3 py-1 font-semibold">
                    <Target className="w-3 h-3 mr-1" />
                    Recommended
                  </Badge>
                </div>
              )}

              {/* Selection indicator */}
              {isSelected && (
                <div className="absolute top-4 right-4 w-8 h-8 bg-facebook-blue rounded-full flex items-center justify-center shadow-lg">
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
                      ? "bg-facebook-blue text-white"
                      : "bg-facebook-gray text-facebook-text"
                  )}>
                    {optimizer.icon}
                  </div>

                  {/* Main content */}
                  <div className="flex-1 min-w-0">
                    {/* Title and badges */}
                    <div className="flex items-center gap-2 mb-2 flex-wrap">
                      <h3 className="text-xl font-bold text-facebook-text">
                        {optimizer.name}
                      </h3>
                      <Badge className={cn("text-xs font-medium border", getCategoryColor(optimizer.category))}>
                        {getCategoryIcon(optimizer.category)}
                        <span className="ml-1 capitalize">{optimizer.category}</span>
                      </Badge>
                    </div>

                    {/* Description */}
                    <p className="text-facebook-text/70 mb-4 leading-relaxed">
                      {optimizer.description}
                    </p>

                    {/* Quick stats */}
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
                      <div className="flex items-center gap-2">
                        <BarChart3 className="w-4 h-4 text-facebook-text/50" />
                        <div>
                          <p className="text-xs text-facebook-text/50 uppercase tracking-wide font-medium">
                            Complexity
                          </p>
                          <p className={cn("font-semibold capitalize", getComplexityColor(optimizer.complexity))}>
                            {optimizer.complexity}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4 text-facebook-text/50" />
                        <div>
                          <p className="text-xs text-facebook-text/50 uppercase tracking-wide font-medium">
                            Speed
                          </p>
                          <p className={cn("font-semibold capitalize", getExecutionTimeColor(optimizer.execution_time))}>
                            {optimizer.execution_time}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <Target className="w-4 h-4 text-facebook-text/50" />
                        <div>
                          <p className="text-xs text-facebook-text/50 uppercase tracking-wide font-medium">
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
                          className="text-xs bg-facebook-gray/50 border-facebook-border text-facebook-text"
                        >
                          {feature}
                        </Badge>
                      ))}
                      {optimizer.features.length > 3 && (
                        <Badge variant="outline" className="text-xs bg-facebook-gray/50 border-facebook-border text-facebook-text">
                          +{optimizer.features.length - 3} more
                        </Badge>
                      )}
                    </div>
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
                      className="w-full mt-4 flex items-center justify-center gap-2 text-facebook-text/70 hover:text-facebook-text hover:bg-facebook-gray/50"
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

                  <CollapsibleContent className="mt-4 pt-4 border-t border-facebook-border">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* Use Cases */}
                      <div>
                        <h4 className="font-semibold text-facebook-text mb-2 flex items-center gap-2">
                          <Target className="w-4 h-4" />
                          Best For
                        </h4>
                        <ul className="space-y-1">
                          {optimizer.use_cases.map((useCase, index) => (
                            <li key={index} className="text-sm text-facebook-text/70 flex items-start gap-2">
                              <Check className="w-3 h-3 mt-0.5 text-green-500 flex-shrink-0" />
                              {useCase}
                            </li>
                          ))}
                        </ul>
                      </div>

                      {/* Pros & Cons */}
                      <div>
                        <h4 className="font-semibold text-facebook-text mb-2 flex items-center gap-2">
                          <BarChart3 className="w-4 h-4" />
                          Trade-offs
                        </h4>
                        <div className="space-y-3">
                          <div>
                            <p className="text-xs font-medium text-green-600 uppercase tracking-wide mb-1">Advantages</p>
                            <ul className="space-y-1">
                              {optimizer.pros.slice(0, 2).map((pro, index) => (
                                <li key={index} className="text-sm text-facebook-text/70 flex items-start gap-2">
                                  <Check className="w-3 h-3 mt-0.5 text-green-500 flex-shrink-0" />
                                  {pro}
                                </li>
                              ))}
                            </ul>
                          </div>
                          <div>
                            <p className="text-xs font-medium text-orange-600 uppercase tracking-wide mb-1">Considerations</p>
                            <ul className="space-y-1">
                              {optimizer.cons.slice(0, 2).map((con, index) => (
                                <li key={index} className="text-sm text-facebook-text/70 flex items-start gap-2">
                                  <AlertCircle className="w-3 h-3 mt-0.5 text-orange-500 flex-shrink-0" />
                                  {con}
                                </li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Technical Details */}
                    <div className="mt-6 p-4 bg-facebook-gray/30 rounded-xl">
                      <h4 className="font-semibold text-facebook-text mb-2 flex items-center gap-2">
                        <Cpu className="w-4 h-4" />
                        Technical Configuration
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                        <div>
                          <p className="text-facebook-text/60"><strong>Auto Mode:</strong> {optimizer.parameters.auto_mode}</p>
                          <p className="text-facebook-text/60"><strong>Max Demos:</strong> {optimizer.parameters.max_labeled_demos}</p>
                        </div>
                        <div>
                          <p className="text-facebook-text/60"><strong>Candidates:</strong> {optimizer.parameters.num_candidates}</p>
                          <p className="text-facebook-text/60"><strong>Threads:</strong> {optimizer.parameters.num_threads}</p>
                        </div>
                      </div>
                    </div>
                  </CollapsibleContent>
                </Collapsible>

                {/* Technical Configuration */}
                {isSelected && (
                  <div className="mt-4 pt-4 border-t border-facebook-border">
                    <Collapsible
                      open={showTechnicalConfig === optimizer.id}
                      onOpenChange={(open) => setShowTechnicalConfig(open ? optimizer.id : null)}
                    >
                      <CollapsibleTrigger asChild>
                        <Button
                          variant="outline"
                          className="w-full flex items-center justify-center gap-2 text-facebook-text hover:bg-facebook-blue/5 border-facebook-blue/20"
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
                        <div className="bg-facebook-gray/20 rounded-xl p-4">
                          <h5 className="font-semibold text-facebook-text mb-3 flex items-center gap-2">
                            <Cpu className="w-4 h-4" />
                            Technical Parameters
                          </h5>
                          <p className="text-sm text-facebook-text/60 mb-4">
                            Customize the optimization parameters. Leave defaults if unsure.
                          </p>

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {/* Max Candidates */}
                            <div className="space-y-2">
                              <Label className="text-sm font-medium text-facebook-text">
                                Number of Candidates
                              </Label>
                              <Input
                                type="number"
                                min="1"
                                max="50"
                                value={getEffectiveParameters(optimizer.id).num_candidates}
                                onChange={(e) => updateParameter(optimizer.id, 'num_candidates', parseInt(e.target.value))}
                                className="border-facebook-border"
                              />
                              <p className="text-xs text-facebook-text/50">How many candidate instructions to generate</p>
                            </div>

                            {/* Max Bootstrapped Demos */}
                            <div className="space-y-2">
                              <Label className="text-sm font-medium text-facebook-text">
                                Max Bootstrapped Demos
                              </Label>
                              <Input
                                type="number"
                                min="1"
                                max="20"
                                value={getEffectiveParameters(optimizer.id).max_bootstrapped_demos}
                                onChange={(e) => updateParameter(optimizer.id, 'max_bootstrapped_demos', parseInt(e.target.value))}
                                className="border-facebook-border"
                              />
                              <p className="text-xs text-facebook-text/50">Examples generated from your data</p>
                            </div>

                            {/* Max Labeled Demos */}
                            <div className="space-y-2">
                              <Label className="text-sm font-medium text-facebook-text">
                                Max Labeled Demos
                              </Label>
                              <Input
                                type="number"
                                min="1"
                                max="20"
                                value={getEffectiveParameters(optimizer.id).max_labeled_demos}
                                onChange={(e) => updateParameter(optimizer.id, 'max_labeled_demos', parseInt(e.target.value))}
                                className="border-facebook-border"
                              />
                              <p className="text-xs text-facebook-text/50">Labeled examples to include</p>
                            </div>

                            {/* Num Threads */}
                            <div className="space-y-2">
                              <Label className="text-sm font-medium text-facebook-text">
                                Number of Threads
                              </Label>
                              <Input
                                type="number"
                                min="1"
                                max="64"
                                value={getEffectiveParameters(optimizer.id).num_threads}
                                onChange={(e) => updateParameter(optimizer.id, 'num_threads', parseInt(e.target.value))}
                                className="border-facebook-border"
                              />
                              <p className="text-xs text-facebook-text/50">Parallel processing for faster optimization</p>
                            </div>

                            {/* Max Errors */}
                            <div className="space-y-2">
                              <Label className="text-sm font-medium text-facebook-text">
                                Max Errors
                              </Label>
                              <Input
                                type="number"
                                min="1"
                                max="50"
                                value={getEffectiveParameters(optimizer.id).max_errors}
                                onChange={(e) => updateParameter(optimizer.id, 'max_errors', parseInt(e.target.value))}
                                className="border-facebook-border"
                              />
                              <p className="text-xs text-facebook-text/50">How many errors to tolerate during optimization</p>
                            </div>

                            {/* Seed */}
                            <div className="space-y-2">
                              <Label className="text-sm font-medium text-facebook-text">
                                Random Seed
                              </Label>
                              <Input
                                type="number"
                                min="0"
                                value={getEffectiveParameters(optimizer.id).seed}
                                onChange={(e) => updateParameter(optimizer.id, 'seed', parseInt(e.target.value))}
                                className="border-facebook-border"
                              />
                              <p className="text-xs text-facebook-text/50">For reproducible results</p>
                            </div>


                          </div>

                          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                            <p className="text-sm text-blue-700">
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
      <div className="mt-8 p-4 bg-facebook-blue/5 border border-facebook-blue/20 rounded-2xl">
        <div className="flex items-start gap-3">
          <HelpCircle className="w-5 h-5 text-facebook-blue mt-0.5 flex-shrink-0" />
          <div>
            <h4 className="font-semibold text-facebook-text mb-1">Need Help Choosing?</h4>
            <p className="text-sm text-facebook-text/70 leading-relaxed">
              <strong>Start with Basic</strong> for quick improvements and experimentation.
              <strong> Use Llama-Optimized</strong> for production Llama deployments and better quality results.
              Click "Configure Advanced Parameters" on any selected optimizer to customize technical settings.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
