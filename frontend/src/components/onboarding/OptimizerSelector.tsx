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
  Clock,
  BarChart3,
  Sparkles,
  Cpu,
  GitBranch,
  Layers,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { SectionTitle } from "@/components/ui/section-title";
import { InfoBox } from "@/components/ui/info-box";
import { getStatusColor, getSpeedColor, getQualityColor } from "@/lib/status-colors";

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
        return "bg-green-100 text-green-800 border-green-200 dark:bg-green-900/30 dark:text-green-300 dark:border-green-800";
      case "advanced":
        return "bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-800";
      case "experimental":
        return "bg-purple-100 text-purple-800 border-purple-200 dark:bg-purple-900/30 dark:text-purple-300 dark:border-purple-800";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-700";
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
      <SectionTitle
        title="Choose Your Optimizer"
        subtitle="Select the optimization strategy that best fits your use case and quality requirements"
      />

      {/* Recommendation */}
      {useCase && (
        <InfoBox variant="info" title="Recommendation">
          For your <strong>{useCase.toUpperCase()}</strong> use case,
          we recommend the <strong>{OPTIMIZER_CONFIGS.find(o => o.id === getRecommendedOptimizer())?.name}</strong> optimizer
          for optimal results.
        </InfoBox>
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
                "bg-card",
                isSelected
                  ? "border-meta-blue dark:border-meta-blue-light bg-meta-blue/5 dark:bg-meta-blue/10 shadow-meta-blue/20"
                  : "border-border hover:border-meta-blue/30 dark:hover:border-meta-blue-light/30"
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
                <div className="absolute top-4 right-4 w-8 h-8 bg-meta-blue dark:bg-meta-blue-light rounded-full flex items-center justify-center">
                  <Check className="w-5 h-5 text-white dark:text-meta-gray-900" />
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
                      ? "bg-meta-blue dark:bg-meta-blue-light text-white dark:text-meta-gray-900"
                      : "bg-muted text-foreground"
                  )}>
                    {optimizer.icon}
                  </div>

                  {/* Main content */}
                  <div className="flex-1 min-w-0">
                    {/* Title and badges */}
                    <div className="flex items-center gap-2 mb-2 flex-wrap">
                      <h3 className="text-xl font-bold text-foreground">
                        {optimizer.name}
                      </h3>
                      <Badge className={cn("text-xs font-medium border", getCategoryColor(optimizer.category))}>
                        {getCategoryIcon(optimizer.category)}
                        <span className="ml-1 capitalize">{optimizer.category}</span>
                      </Badge>
                    </div>

                    {/* Description */}
                    <p className="text-muted-foreground mb-4 leading-relaxed">
                      {optimizer.description}
                    </p>

                    {/* Quick stats */}
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
                      <div className="flex items-center gap-2">
                        <BarChart3 className="w-4 h-4 text-muted-foreground/50" />
                        <div>
                          <p className="text-xs text-muted-foreground/70 uppercase tracking-wide font-medium">
                            Complexity
                          </p>
                          <p className={cn("font-semibold capitalize", getStatusColor(optimizer.complexity))}>
                            {optimizer.complexity}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4 text-muted-foreground/50" />
                        <div>
                          <p className="text-xs text-muted-foreground/70 uppercase tracking-wide font-medium">
                            Speed
                          </p>
                          <p className={cn("font-semibold capitalize", getSpeedColor(optimizer.execution_time))}>
                            {optimizer.execution_time}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <Target className="w-4 h-4 text-muted-foreground/50" />
                        <div>
                          <p className="text-xs text-muted-foreground/70 uppercase tracking-wide font-medium">
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
                          className="text-xs bg-muted/50 border-border text-muted-foreground"
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
                      className="w-full mt-4 flex items-center justify-center gap-2 text-muted-foreground hover:text-foreground hover:bg-muted/50"
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

                  <CollapsibleContent className="mt-4 pt-4 border-t border-border">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* Use Cases */}
                      <div>
                        <h4 className="font-semibold text-foreground mb-2 flex items-center gap-2">
                          <Target className="w-4 h-4" />
                          Best For
                        </h4>
                        <ul className="space-y-1">
                          {optimizer.use_cases.map((useCase, index) => (
                            <li key={index} className="text-sm text-muted-foreground flex items-start gap-2">
                              <Check className="w-3 h-3 mt-0.5 text-green-500 dark:text-green-400 flex-shrink-0" />
                              {useCase}
                            </li>
                          ))}
                        </ul>
                      </div>

                      {/* Pros & Cons */}
                      <div>
                        <h4 className="font-semibold text-foreground mb-2 flex items-center gap-2">
                          <BarChart3 className="w-4 h-4" />
                          Trade-offs
                        </h4>
                        <div className="space-y-3">
                          <div>
                            <p className="text-xs font-medium text-green-600 dark:text-green-400 uppercase tracking-wide mb-1">Advantages</p>
                            <ul className="space-y-1">
                              {optimizer.pros.slice(0, 2).map((pro, index) => (
                                <li key={index} className="text-sm text-muted-foreground flex items-start gap-2">
                                  <Check className="w-3 h-3 mt-0.5 text-green-500 dark:text-green-400 flex-shrink-0" />
                                  {pro}
                                </li>
                              ))}
                            </ul>
                          </div>
                          <div>
                            <p className="text-xs font-medium text-orange-600 dark:text-orange-400 uppercase tracking-wide mb-1">Considerations</p>
                            <ul className="space-y-1">
                              {optimizer.cons.slice(0, 2).map((con, index) => (
                                <li key={index} className="text-sm text-muted-foreground flex items-start gap-2">
                                  <AlertCircle className="w-3 h-3 mt-0.5 text-orange-500 dark:text-orange-400 flex-shrink-0" />
                                  {con}
                                </li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Technical Details */}
                    <div className="mt-6 p-4 bg-muted/30 rounded-xl">
                      <h4 className="font-semibold text-foreground mb-2 flex items-center gap-2">
                        <Cpu className="w-4 h-4" />
                        Technical Configuration
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                        <div>
                          <p className="text-muted-foreground"><strong className="text-foreground">Auto Mode:</strong> {optimizer.parameters.auto_mode}</p>
                          <p className="text-muted-foreground"><strong className="text-foreground">Max Demos:</strong> {optimizer.parameters.max_labeled_demos}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground"><strong className="text-foreground">Candidates:</strong> {optimizer.parameters.num_candidates}</p>
                          <p className="text-muted-foreground"><strong className="text-foreground">Threads:</strong> {optimizer.parameters.num_threads}</p>
                        </div>
                      </div>
                    </div>
                  </CollapsibleContent>
                </Collapsible>

                {/* Technical Configuration */}
                {isSelected && (
                  <div className="mt-4 pt-4 border-t border-border">
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
                        <div className="bg-muted/20 rounded-xl p-4">
                          <h5 className="font-semibold text-foreground mb-3 flex items-center gap-2">
                            <Cpu className="w-4 h-4" />
                            Technical Parameters
                          </h5>
                          <p className="text-sm text-muted-foreground mb-4">
                            Customize the optimization parameters. Leave defaults if unsure.
                          </p>

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {/* Max Candidates */}
                            <div className="space-y-2">
                              <Label className="text-sm font-medium text-foreground">
                                Number of Candidates
                              </Label>
                              <Input
                                type="number"
                                min="1"
                                max="50"
                                value={getEffectiveParameters(optimizer.id).num_candidates}
                                onChange={(e) => updateParameter(optimizer.id, 'num_candidates', parseInt(e.target.value))}
                                className="border-border bg-input text-foreground"
                              />
                              <p className="text-xs text-muted-foreground">How many candidate instructions to generate</p>
                            </div>

                            {/* Max Bootstrapped Demos */}
                            <div className="space-y-2">
                              <Label className="text-sm font-medium text-foreground">
                                Max Bootstrapped Demos
                              </Label>
                              <Input
                                type="number"
                                min="1"
                                max="20"
                                value={getEffectiveParameters(optimizer.id).max_bootstrapped_demos}
                                onChange={(e) => updateParameter(optimizer.id, 'max_bootstrapped_demos', parseInt(e.target.value))}
                                className="border-border bg-input text-foreground"
                              />
                              <p className="text-xs text-muted-foreground">Examples generated from your data</p>
                            </div>

                            {/* Max Labeled Demos */}
                            <div className="space-y-2">
                              <Label className="text-sm font-medium text-foreground">
                                Max Labeled Demos
                              </Label>
                              <Input
                                type="number"
                                min="1"
                                max="20"
                                value={getEffectiveParameters(optimizer.id).max_labeled_demos}
                                onChange={(e) => updateParameter(optimizer.id, 'max_labeled_demos', parseInt(e.target.value))}
                                className="border-border bg-input text-foreground"
                              />
                              <p className="text-xs text-muted-foreground">Labeled examples to include</p>
                            </div>

                            {/* Num Threads */}
                            <div className="space-y-2">
                              <Label className="text-sm font-medium text-foreground">
                                Number of Threads
                              </Label>
                              <Input
                                type="number"
                                min="1"
                                max="64"
                                value={getEffectiveParameters(optimizer.id).num_threads}
                                onChange={(e) => updateParameter(optimizer.id, 'num_threads', parseInt(e.target.value))}
                                className="border-border bg-input text-foreground"
                              />
                              <p className="text-xs text-muted-foreground">Parallel processing for faster optimization</p>
                            </div>

                            {/* Max Errors */}
                            <div className="space-y-2">
                              <Label className="text-sm font-medium text-foreground">
                                Max Errors
                              </Label>
                              <Input
                                type="number"
                                min="1"
                                max="50"
                                value={getEffectiveParameters(optimizer.id).max_errors}
                                onChange={(e) => updateParameter(optimizer.id, 'max_errors', parseInt(e.target.value))}
                                className="border-border bg-input text-foreground"
                              />
                              <p className="text-xs text-muted-foreground">How many errors to tolerate during optimization</p>
                            </div>

                            {/* Seed */}
                            <div className="space-y-2">
                              <Label className="text-sm font-medium text-foreground">
                                Random Seed
                              </Label>
                              <Input
                                type="number"
                                min="0"
                                value={getEffectiveParameters(optimizer.id).seed}
                                onChange={(e) => updateParameter(optimizer.id, 'seed', parseInt(e.target.value))}
                                className="border-border bg-input text-foreground"
                              />
                              <p className="text-xs text-muted-foreground">For reproducible results</p>
                            </div>


                          </div>

                          <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                            <p className="text-sm text-blue-700 dark:text-blue-300">
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
      <div className="mt-8 p-4 bg-meta-blue/5 dark:bg-meta-blue/10 border border-meta-blue/20 dark:border-meta-blue-light/20 rounded-2xl">
        <div className="flex items-start gap-3">
          <HelpCircle className="w-5 h-5 text-meta-blue dark:text-meta-blue-light mt-0.5 flex-shrink-0" />
          <div>
            <h4 className="font-semibold text-foreground mb-1">Need Help Choosing?</h4>
            <p className="text-sm text-muted-foreground leading-relaxed">
              <strong className="text-foreground">Start with Basic</strong> for quick improvements and experimentation.
              <strong className="text-foreground"> Use Llama-Optimized</strong> for production Llama deployments and better quality results.
              Click "Configure Advanced Parameters" on any selected optimizer to customize technical settings.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
