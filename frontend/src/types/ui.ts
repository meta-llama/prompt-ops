/**
 * UI types - Status indicators, variants, and visual states
 */

/**
 * Generic status level for indicators (cost, complexity, etc.)
 */
export type StatusLevel = "low" | "medium" | "high";

/**
 * Speed level for performance indicators
 */
export type SpeedLevel = "fast" | "medium" | "slow";

/**
 * Quality level for output quality indicators
 */
export type QualityLevel = "good" | "better" | "best";

/**
 * Status for step cards in the optimization grid
 */
export type StepStatus = "empty" | "active" | "completed" | "error";

/**
 * Status for wizard sections
 */
export type WizardSectionStatus = "complete" | "incomplete" | "empty";

/**
 * Role type for model configuration
 */
export type RoleType = "target" | "optimizer" | "both";

/**
 * Variant for info box styling
 */
export type InfoBoxVariant = "info" | "warning" | "success" | "error";

