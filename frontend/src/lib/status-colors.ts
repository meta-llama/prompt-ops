/**
 * Utility functions for consistent status-based coloring across the app.
 */

export type StatusLevel = "low" | "medium" | "high";
export type SpeedLevel = "fast" | "medium" | "slow";
export type QualityLevel = "good" | "better" | "best";

/**
 * Get text color class for a three-level status (low/medium/high).
 * Low = green, Medium = yellow, High = red
 */
export const getStatusColor = (status: StatusLevel): string => {
  switch (status) {
    case "low":
      return "text-green-600 dark:text-green-400";
    case "medium":
      return "text-yellow-600 dark:text-yellow-400";
    case "high":
      return "text-red-600 dark:text-red-400";
    default:
      return "text-gray-600 dark:text-gray-400";
  }
};

/**
 * Get text color class for speed levels (fast/medium/slow).
 * Fast = green, Medium = yellow, Slow = red
 */
export const getSpeedColor = (speed: SpeedLevel): string => {
  switch (speed) {
    case "fast":
      return "text-green-600 dark:text-green-400";
    case "medium":
      return "text-yellow-600 dark:text-yellow-400";
    case "slow":
      return "text-red-600 dark:text-red-400";
    default:
      return "text-gray-600 dark:text-gray-400";
  }
};

/**
 * Get text color class for quality levels (good/better/best).
 * Good = green, Better = blue, Best = purple
 */
export const getQualityColor = (quality: QualityLevel): string => {
  switch (quality) {
    case "good":
      return "text-green-600 dark:text-green-400";
    case "better":
      return "text-blue-600 dark:text-blue-400";
    case "best":
      return "text-purple-600 dark:text-purple-400";
    default:
      return "text-gray-600 dark:text-gray-400";
  }
};
