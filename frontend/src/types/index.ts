/**
 * Centralized type exports
 *
 * Import types from here for convenience:
 *   import type { Project, OptimizationStep } from '@/types';
 */

// Domain types
export type { Project, OptimizationStep, DocItem } from "./domain";

// UI types
export type {
  StatusLevel,
  SpeedLevel,
  QualityLevel,
  StepStatus,
  WizardSectionStatus,
  RoleType,
  InfoBoxVariant,
} from "./ui";

// API types
export type { FieldInfo, DatasetAnalysis, PreviewData } from "./api";

// Onboarding types
export type {
  UseCase,
  Step,
  CustomParameters,
  OptimizerConfig,
  ProviderConfig,
  ModelConfig,
  MetricConfig,
} from "./onboarding";

