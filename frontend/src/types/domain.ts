/**
 * Domain types - Core business entities used across the application
 */

import type React from "react";

/**
 * Represents a project in the workspace
 */
export interface Project {
  name: string;
  path: string;
  hasConfig: boolean;
  hasPrompt: boolean;
  hasDataset: boolean;
  createdAt: number;
  modifiedAt: number;
}

/**
 * Represents a step in the optimization process
 */
export interface OptimizationStep {
  id: string;
  label: string;
  completed: boolean;
  inProgress: boolean;
}

/**
 * Represents a documentation item
 */
export interface DocItem {
  id: string;
  title: string;
  path: string;
  category: string;
  description?: string;
  lastModified?: string;
  icon?: React.ElementType;
}

