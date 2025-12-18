import React from "react";
import { Database, CheckCircle, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";

export interface DatasetUploaderProps {
  datasetPath: string;
  uploadedFile: File | null;
  useCase: string;
  onUpload: (file: File) => void;
  onRemove: () => void;
  loading: boolean;
  error: string | null;
  className?: string;
}

/**
 * A file upload component for datasets.
 * Displays upload state, file info, and format hints based on use case.
 */
export const DatasetUploader: React.FC<DatasetUploaderProps> = ({
  datasetPath,
  uploadedFile,
  useCase,
  onUpload,
  onRemove,
  loading,
  error,
  className,
}) => {
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onUpload(file);
    }
  };

  const handleUploadAreaClick = () => {
    if (!loading && !datasetPath) {
      fileInputRef.current?.click();
    }
  };

  return (
    <div className={cn("space-y-4", className)}>
      <p className="text-muted-foreground text-sm">
        Upload a JSON file containing your evaluation examples.
      </p>

      {/* Upload Zone */}
      <div
        onClick={handleUploadAreaClick}
        className={cn(
          "border-2 border-dashed rounded-xl p-8 text-center transition-colors",
          datasetPath
            ? "border-meta-teal bg-meta-teal/5"
            : error
            ? "border-red-500 bg-red-500/5 dark:border-red-400 dark:bg-red-400/5"
            : "border-border bg-panel hover:border-meta-blue cursor-pointer"
        )}
      >
        {loading ? (
          <div className="space-y-3">
            <div className="w-12 h-12 bg-meta-blue/10 rounded-full flex items-center justify-center mx-auto">
              <div className="w-6 h-6 border-2 border-meta-blue border-t-transparent rounded-full animate-spin" />
            </div>
            <p className="text-foreground">Uploading dataset...</p>
          </div>
        ) : datasetPath ? (
          <div className="space-y-3">
            <div className="w-12 h-12 bg-meta-teal/10 rounded-full flex items-center justify-center mx-auto">
              <CheckCircle className="w-6 h-6 text-meta-teal" />
            </div>
            <div>
              <p className="font-semibold text-foreground">{datasetPath}</p>
              <p className="text-sm text-muted-foreground">
                {uploadedFile ? (uploadedFile.size / 1024).toFixed(2) : "0"} KB
              </p>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onRemove();
              }}
              className="text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center gap-2 mx-auto"
            >
              <Trash2 className="w-4 h-4" />
              Remove file
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            <Database className="w-10 h-10 text-muted-foreground/50 mx-auto" />
            <div>
              <span className="text-meta-blue font-semibold">
                Click to upload
              </span>
              <span className="text-muted-foreground"> or drag and drop</span>
              <input
                ref={fileInputRef}
                id="dataset-upload"
                type="file"
                accept=".json"
                className="hidden"
                onChange={handleFileChange}
              />
            </div>
            <p className="text-xs text-muted-foreground">
              JSON files only, max 10MB
            </p>
            {error && (
              <p className="text-sm text-red-600 bg-red-50 dark:bg-red-900/30 dark:text-red-400 p-2 rounded">
                {error}
              </p>
            )}
          </div>
        )}
      </div>

      {/* Dataset format helper */}
      {useCase && useCase !== "custom" && (
        <div className="bg-meta-blue/5 border border-meta-blue/20 rounded-xl p-4">
          <p className="text-xs font-semibold text-foreground mb-2">
            Expected format for {useCase.toUpperCase()}:
          </p>
          <pre className="text-xs bg-panel p-3 rounded-lg border border-border overflow-x-auto text-muted-foreground">
            {useCase === "qa"
              ? JSON.stringify(
                  [
                    {
                      question: "What is the capital of France?",
                      answer: "Paris",
                    },
                  ],
                  null,
                  2
                )
              : JSON.stringify(
                  [
                    {
                      query: "What are the key terms in this contract?",
                      context: [
                        "Document 1 content text...",
                        "Document 2 content text...",
                      ],
                      answer: "The key terms include...",
                    },
                  ],
                  null,
                  2
                )}
          </pre>
        </div>
      )}
    </div>
  );
};
