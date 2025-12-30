/**
 * API types - Request/response types for backend communication
 */

/**
 * Information about a field in an uploaded dataset
 */
export interface FieldInfo {
  name: string;
  type: string;
  samples: any[];
  coverage: number;
  populated_count: number;
  total_count: number;
}

/**
 * Analysis result from the dataset analysis endpoint
 */
export interface DatasetAnalysis {
  total_records: number;
  sample_size: number;
  fields: FieldInfo[];
  suggestions: Record<string, any>;
  sample_data: any[];
  error?: string;
}

/**
 * Preview data for dataset transformation
 */
export interface PreviewData {
  original_data: any[];
  transformed_data: any[];
  adapter_config: any;
  error?: string;
}

