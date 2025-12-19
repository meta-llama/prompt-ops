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
      <p className="text-white/60 text-sm">
        Upload a JSON file containing your evaluation examples.
      </p>

      {/* Upload Zone */}
      <div
        onClick={handleUploadAreaClick}
        className={cn(
          "border-2 border-dashed rounded-xl p-8 text-center transition-colors",
          datasetPath
            ? "border-meta-teal bg-meta-teal/10"
            : error
            ? "border-red-400 bg-red-400/10"
            : "border-white/[0.15] bg-white/[0.03] hover:border-[#4da3ff] cursor-pointer"
        )}
      >
        {loading ? (
          <div className="space-y-3">
            <div className="w-12 h-12 bg-[#4da3ff]/20 rounded-full flex items-center justify-center mx-auto">
              <div className="w-6 h-6 border-2 border-[#4da3ff] border-t-transparent rounded-full animate-spin" />
            </div>
            <p className="text-white">Uploading dataset...</p>
          </div>
        ) : datasetPath ? (
          <div className="space-y-3">
            <div className="w-12 h-12 bg-meta-teal/20 rounded-full flex items-center justify-center mx-auto">
              <CheckCircle className="w-6 h-6 text-meta-teal" />
            </div>
            <div>
              <p className="font-semibold text-white">{datasetPath}</p>
              <p className="text-sm text-white/60">
                {uploadedFile ? (uploadedFile.size / 1024).toFixed(2) : "0"} KB
              </p>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onRemove();
              }}
              className="text-sm text-white/60 hover:text-white transition-colors flex items-center gap-2 mx-auto"
            >
              <Trash2 className="w-4 h-4" />
              Remove file
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            <Database className="w-10 h-10 text-white/30 mx-auto" />
            <div>
              <span className="text-[#4da3ff] font-semibold">
                Click to upload
              </span>
              <span className="text-white/60"> or drag and drop</span>
              <input
                ref={fileInputRef}
                id="dataset-upload"
                type="file"
                accept=".json"
                className="hidden"
                onChange={handleFileChange}
              />
            </div>
            <p className="text-xs text-white/50">
              JSON files only, max 10MB
            </p>
            {error && (
              <p className="text-sm text-red-400 bg-red-400/10 p-2 rounded">
                {error}
              </p>
            )}
          </div>
        )}
      </div>

      {/* Dataset format helper */}
      {useCase && useCase !== "custom" && (
        <div className="bg-[#4da3ff]/10 border border-[#4da3ff]/20 rounded-xl p-4">
          <p className="text-xs font-semibold text-white mb-2">
            Expected format for {useCase.toUpperCase()}:
          </p>
          <pre className="text-xs bg-white/[0.03] p-3 rounded-lg border border-white/[0.08] overflow-x-auto text-white/70">
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
