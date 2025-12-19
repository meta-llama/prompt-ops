/**
 * Onboarding types - Types for the onboarding wizard flow
 */

import type React from "react";

/**
 * A use case option in the use case selector
 */
export interface UseCase {
  id: string;
  title: string;
  description: string;
  examples: string[];
  expectedFormat?: {
    title: string;
    structure: string;
  };
  icon: React.ReactNode;
  config: {
    datasetAdapter?: string;
    metrics?: string;
    optimizer?: string;
    model?: string;
  };
}

/**
 * A step in the step indicator
 */
export interface Step {
  id: string;
  title: string;
  description?: string;
}

/**
 * Custom parameters for optimizer configuration
 */
export interface CustomParameters {
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

/**
 * Configuration for an optimizer option
 */
export interface OptimizerConfig {
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

/**
 * Configuration for a model provider option
 */
export interface ProviderConfig {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  category: "cloud" | "local" | "enterprise";
  pricing: "free" | "paid" | "usage";
  setup_difficulty: "easy" | "medium" | "hard";
  api_base: string;
  model_prefix: string;
  popular_models: string[];
  pros: string[];
  cons: string[];
  docs_url: string;
  requires_signup: boolean;
}

/**
 * Configuration for a selected model
 */
export interface ModelConfig {
  id: string;
  provider_id: string;
  model_name: string;
  role: "target" | "optimizer" | "both";
  api_key?: string;
  api_base?: string;
  temperature: number;
  max_tokens: number;
  custom_provider_name?: string;
  model_prefix?: string;
  auth_method?: "api_key" | "bearer_token" | "custom_headers";
  custom_headers?: Record<string, string>;
  useDefaultKey?: boolean;  // Whether this config uses the default API key from .env
}

/**
 * Configuration for a metric option
 */
export interface MetricConfig {
  id: string;
  name: string;
  description: string;
  type: "exact" | "semantic" | "structured" | "custom";
  icon: React.ReactNode;
  useCases: string[];
  dataRequirements: string[];
  parameters?: {
    [key: string]: {
      type:
        | "boolean"
        | "number"
        | "string"
        | "select"
        | "array"
        | "object"
        | "fieldMapping";
      default: any;
      description: string;
      options?: string[];
      arrayType?: "string" | "number";
      objectSchema?: {
        [key: string]: {
          type: "string" | "number" | "boolean";
          required?: boolean;
        };
      };
    };
  };
  examples: {
    input: string;
    output: string;
    score: string;
  }[];
  pros: string[];
  cons: string[];
  recommendedFor: string[];
}
