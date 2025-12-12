import React, { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import { apiUrl } from "@/lib/config";
import {
  ArrowRight,
  CheckCircle,
  AlertCircle,
  Eye,
  RefreshCw,
  FileText,
  Database,
  Hash,
  List,
  Settings,
} from "lucide-react";

interface FieldInfo {
  name: string;
  type: string;
  samples: any[];
  coverage: number;
  populated_count: number;
  total_count: number;
}

interface FieldMappingInterfaceProps {
  filename: string;
  useCase: string;
  onMappingUpdate: (mappings: Record<string, string>) => void;
  className?: string;
  existingMappings?: Record<string, string>;
}

interface DatasetAnalysis {
  total_records: number;
  sample_size: number;
  fields: FieldInfo[];
  suggestions: Record<string, any>;
  sample_data: any[];
  error?: string;
}

interface PreviewData {
  original_data: any[];
  transformed_data: any[];
  adapter_config: any;
  error?: string;
}

const USE_CASE_REQUIREMENTS = {
  qa: {
    required: ["question", "answer"],
    optional: ["id", "metadata"],
    description: "Question-Answer format",
  },
  rag: {
    required: ["context", "query", "answer"],
    optional: ["id", "metadata"],
    description: "RAG (Retrieval-Augmented Generation) format",
  },
  custom: {
    required: [],
    optional: [],
    description: "Custom configuration",
  },
};

const getFieldIcon = (fieldType: string) => {
  switch (fieldType) {
    case "string":
      return <FileText className="w-4 h-4" />;
    case "array":
      return <List className="w-4 h-4" />;
    case "object":
      return <Database className="w-4 h-4" />;
    case "number":
      return <Hash className="w-4 h-4" />;
    default:
      return <Settings className="w-4 h-4" />;
  }
};



// Individual custom field mapping component to prevent input focus loss
const CustomFieldMapping: React.FC<{
  targetField: string;
  sourceField: string;
  availableFields: FieldInfo[];
  onTargetFieldChange: (oldField: string, newField: string) => void;
  onSourceFieldChange: (field: string, value: string) => void;
  onRemove: () => void;
}> = ({
  targetField,
  sourceField,
  availableFields,
  onTargetFieldChange,
  onSourceFieldChange,
  onRemove,
}) => {
  const [localTargetField, setLocalTargetField] = useState(targetField);

  // Update local state when prop changes
  useEffect(() => {
    setLocalTargetField(targetField);
  }, [targetField]);

  const handleTargetFieldBlur = () => {
    if (localTargetField !== targetField) {
      onTargetFieldChange(targetField, localTargetField);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleTargetFieldBlur();
    }
  };

  return (
    <div className="p-4 border border-border rounded-lg">
      <div className="flex items-center space-x-3 mb-2">
        <input
          type="text"
          placeholder="Target field name (e.g., 'question', 'answer')"
          value={localTargetField}
          onChange={(e) => setLocalTargetField(e.target.value)}
          onBlur={handleTargetFieldBlur}
          onKeyPress={handleKeyPress}
          className="flex-1 p-2 border border-border rounded-md focus:ring-2 focus:ring-ring focus:border-transparent bg-input text-foreground"
        />
        <button
          onClick={onRemove}
          className="px-3 py-2 text-red-600 hover:bg-red-50 rounded-md border border-red-300"
        >
          Remove
        </button>
      </div>

      <select
        value={sourceField || ""}
        onChange={(e) => onSourceFieldChange(targetField, e.target.value)}
        className="w-full p-2 border border-border rounded-md focus:ring-2 focus:ring-ring focus:border-transparent bg-input text-foreground"
      >
        <option value="">Select source field...</option>
        {availableFields.map((field) => (
          <option key={field.name} value={field.name}>
            {field.name} ({field.type})
          </option>
        ))}
      </select>
    </div>
  );
};

export const FieldMappingInterface: React.FC<FieldMappingInterfaceProps> = ({
  filename,
  useCase,
  onMappingUpdate,
  className,
  existingMappings = {},
}) => {
  const [analysis, setAnalysis] = useState<DatasetAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mappings, setMappings] =
    useState<Record<string, string>>(existingMappings);
  const [showPreview, setShowPreview] = useState(false);
  const [previewData, setPreviewData] = useState<PreviewData | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  const requirements =
    USE_CASE_REQUIREMENTS[useCase as keyof typeof USE_CASE_REQUIREMENTS];

  useEffect(() => {
    analyzeDataset();
  }, [filename]);

  useEffect(() => {
    setMappings(existingMappings);
  }, [existingMappings]);

  const analyzeDataset = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(
        apiUrl(`/api/datasets/analyze/${filename}`),
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      if (!response.ok) {
        throw new Error("Failed to analyze dataset");
      }

      const data: DatasetAnalysis = await response.json();

      if (data.error) {
        setError(data.error);
        return;
      }

      setAnalysis(data);

      // No automatic mappings since we removed suggested mappings
      // Just use existing mappings
      setMappings(existingMappings);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to analyze dataset"
      );
    } finally {
      setLoading(false);
    }
  };

  const handleMappingChange = (targetField: string, sourceField: string) => {
    const newMappings = {
      ...mappings,
      [targetField]: sourceField,
    };
    setMappings(newMappings);
    onMappingUpdate(newMappings);
  };

  const handlePreview = async () => {
    if (!canPreview()) return;

    try {
      setPreviewLoading(true);

      const response = await fetch(
        apiUrl("/api/datasets/preview-transformation"),
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            filename,
            mappings,
            use_case: useCase,
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to preview transformation");
      }

      const data: PreviewData = await response.json();
      setPreviewData(data);
      setShowPreview(true);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to preview transformation"
      );
    } finally {
      setPreviewLoading(false);
    }
  };

  const canPreview = () => {
    if (useCase === "custom") {
      // For custom use cases, allow preview if at least one mapping is defined
      return (
        Object.keys(mappings).length > 0 &&
        Object.values(mappings).some((value) => value !== "")
      );
    }
    return requirements.required.every((field) => mappings[field]);
  };


  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2" />
          <p className="text-muted-foreground">Analyzing dataset...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
        <div className="flex items-center mb-2">
          <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
          <h3 className="text-lg font-semibold text-red-800">Analysis Error</h3>
        </div>
        <p className="text-red-700">{error}</p>
        <button
          onClick={analyzeDataset}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Try Again
        </button>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="p-6 text-center">
        <p className="text-muted-foreground">No analysis data available</p>
      </div>
    );
  }

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <div className="bg-card rounded-2xl p-6 border border-border">
        <h2 className="text-2xl md:text-3xl font-normal text-foreground mb-4 tracking-tight">Field Mapping</h2>
        <p className="text-muted-foreground text-lg mb-4">
          To evaluate your dataset correctly, map your dataset's fields to the required fields below.
          Check the <span className="font-medium text-foreground">Completeness</span> percentages to ensure your selected fields have sufficient data coverage.
        </p>

        <div className="flex items-center space-x-4 text-sm text-muted-foreground">
          <span>Dataset: {filename}</span>
          <span>•</span>
          <span>{analysis.total_records} records</span>
          <span>•</span>
          <span>{analysis.fields.length} fields detected</span>
        </div>
      </div>

      {/* Field Mapping */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
        {/* Required/Custom Fields */}
        <div className="bg-card rounded-2xl p-6 border border-border max-h-[600px] overflow-y-auto">
          <h3 className="text-lg font-semibold text-foreground mb-4">
            {useCase === "custom" ? "Custom Field Mappings" : "Required Fields"}
          </h3>

          {useCase === "custom" ? (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground mb-4">
                Create custom field mappings for your dataset. Add as many
                mappings as needed for your use case.
              </p>

              {/* Custom field mapping inputs */}
              <div className="space-y-3">
                {Object.entries(mappings).map(
                  ([targetField, sourceField], index) => (
                    <CustomFieldMapping
                      key={`mapping-${index}`}
                      targetField={targetField}
                      sourceField={sourceField}
                      availableFields={analysis.fields}
                      onTargetFieldChange={(oldField, newField) => {
                        const newMappings = { ...mappings };
                        delete newMappings[oldField];
                        if (newField) {
                          newMappings[newField] = sourceField;
                        }
                        setMappings(newMappings);
                        onMappingUpdate(newMappings);
                      }}
                      onSourceFieldChange={(field, value) => {
                        handleMappingChange(field, value);
                      }}
                      onRemove={() => {
                        const newMappings = { ...mappings };
                        delete newMappings[targetField];
                        setMappings(newMappings);
                        onMappingUpdate(newMappings);
                      }}
                    />
                  )
                )}

                {/* Add new mapping button */}
                <button
                  onClick={() => {
                    const newTargetField = `field_${
                      Object.keys(mappings).length + 1
                    }`;
                    const newMappings = { ...mappings, [newTargetField]: "" };
                    setMappings(newMappings);
                    onMappingUpdate(newMappings);
                  }}
                  className="w-full p-3 border-2 border-dashed border-border rounded-lg text-muted-foreground hover:border-meta-blue dark:hover:border-meta-blue-light hover:text-meta-blue dark:hover:text-meta-blue-light transition-colors"
                >
                  + Add Field Mapping
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {requirements.required.map((requiredField) => (
                <div
                  key={requiredField}
                  className={cn(
                    "p-4 border-2 border-dashed rounded-lg",
                    mappings[requiredField] && mappings[requiredField] !== ""
                      ? "border-meta-teal bg-meta-teal/10"
                      : "border-red-500 bg-red-50/30"
                  )}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-foreground">
                      {requiredField}
                    </span>
                    <span className="text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/30 px-2 py-1 rounded">
                      Required
                    </span>
                  </div>

                  <select
                    value={mappings[requiredField] || ""}
                    onChange={(e) =>
                      handleMappingChange(requiredField, e.target.value)
                    }
                    className="w-full p-2 border border-border rounded-md focus:ring-2 focus:ring-ring focus:border-transparent bg-input text-foreground"
                  >
                    <option value="">Select field...</option>
                    {analysis.fields.map((field) => (
                      <option key={field.name} value={field.name}>
                        {field.name} ({field.type})
                      </option>
                    ))}
                  </select>

                  {mappings[requiredField] && (
                    <div className="mt-2 flex items-center text-sm text-meta-teal">
                      <CheckCircle className="w-4 h-4 mr-1" />
                      Mapped to: {mappings[requiredField]}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-card rounded-2xl p-6 border border-border max-h-[600px] flex flex-col">
          <h3 className="text-lg font-semibold text-foreground mb-4">
            Detected Fields
          </h3>
          <div className="space-y-3 overflow-y-auto flex-1">
            {analysis.fields.map((field, index) => (
              <div
                key={index}
                className="p-3 border border-border rounded-lg hover:bg-muted"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    {getFieldIcon(field.type)}
                    <span className="font-medium text-foreground">
                      {field.name}
                    </span>
                    <span className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded">
                      {field.type}
                    </span>
                  </div>
                  {/* Field Completeness Information */}
                  <div className="flex items-center justify-end">
                    <div
                      className="flex items-center space-x-1"
                      title={`${field.populated_count} out of ${field.total_count} records have this field populated with data`}
                    >
                      <span className="text-xs text-muted-foreground">Completeness:</span>
                      <span
                        className={cn(
                          "text-xs font-medium",
                          field.coverage >= 0.9 ? "text-meta-teal" :
                          field.coverage >= 0.7 ? "text-yellow-600" : "text-red-600"
                        )}
                      >
                        {Math.round(field.coverage * 100)}%
                      </span>
                    </div>
                  </div>
                </div>

                {field.samples.length > 0 && (
                  <div className="text-xs text-muted-foreground space-y-1">
                    <div>Sample values:</div>
                    {field.samples.slice(0, 2).map((sample, i) => (
                      <div
                        key={i}
                        className="bg-muted p-1 rounded text-xs font-mono text-foreground"
                      >
                        {typeof sample === "string"
                          ? `"${sample}"`
                          : JSON.stringify(sample)}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Preview Section */}
      {showPreview && previewData && (
        <div className="bg-card rounded-2xl p-6 border border-border">
          <h3 className="text-lg font-semibold text-foreground mb-4">
            Preview Transformation
          </h3>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <h4 className="text-sm font-medium text-muted-foreground mb-2">
                Original Data
              </h4>
              <div className="bg-muted p-3 rounded-lg max-h-64 overflow-y-auto">
                <pre className="text-xs text-muted-foreground">
                  {JSON.stringify(previewData.original_data[0], null, 2)}
                </pre>
              </div>
            </div>

            <div>
              <h4 className="text-sm font-medium text-muted-foreground mb-2">
                Transformed Data
              </h4>
              <div className="bg-muted p-3 rounded-lg max-h-64 overflow-y-auto">
                <pre className="text-xs text-muted-foreground">
                  {JSON.stringify(previewData.transformed_data[0], null, 2)}
                </pre>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Preview Section - Keep preview functionality but remove navigation buttons */}
      {canPreview() && (
        <div className="flex justify-end">
          <button
            onClick={handlePreview}
            disabled={previewLoading}
            className={cn(
              "flex items-center space-x-2 px-6 py-2 border border-meta-blue text-meta-blue rounded-full",
              "hover:bg-meta-blue hover:text-white transition-colors",
              "disabled:opacity-50 disabled:cursor-not-allowed"
            )}
          >
            {previewLoading ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Eye className="w-4 h-4" />
            )}
            <span>Preview Mapping</span>
          </button>
        </div>
      )}
    </div>
  );
};
