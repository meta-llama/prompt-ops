import React, { useState, useRef, useMemo } from "react";
import {
  ArrowRight,
  CheckCircle,
  FileText,
  Lightbulb,
  Database,
  Target,
  Zap,
  Brain,
  Settings,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
  Columns,
  LayoutList,
} from "lucide-react";
import { diffWords } from "diff";
import { Button } from "@/components/ui/button";
import { apiUrl, wsUrl } from "@/lib/config";
import { WizardSection } from "@/components/ui/wizard-section";
import { InfoBox } from "@/components/ui/info-box";
import { getProviderIcon, getProviderName } from "@/lib/providers";
import { UseCaseSelector } from "./UseCaseSelector";
import { FieldMappingInterface } from "./FieldMappingInterface";
import { MetricsSelector } from "./MetricsSelector";
import { ModelProviderSelector } from "./ModelProviderSelector";
import { OptimizerSelector } from "./OptimizerSelector";
import { DatasetUploader } from "./DatasetUploader";

// Diff view component for comparing original and optimized prompts
const DiffView: React.FC<{
  original: string;
  optimized: string;
  showOriginal: boolean;
}> = ({ original, optimized, showOriginal }) => {
  const diffResult = useMemo(() => diffWords(original, optimized), [original, optimized]);

  return (
    <div className="whitespace-pre-wrap text-white/80 text-sm leading-relaxed">
      {diffResult.map((part, index) => {
        if (showOriginal) {
          if (part.added) return null;
          if (part.removed) {
            return (
              <span
                key={index}
                className="bg-red-500/20 text-red-300 px-0.5 rounded line-through decoration-red-400"
              >
                {part.value}
              </span>
            );
          }
          return <span key={index}>{part.value}</span>;
        }

        if (part.removed) return null;
        if (part.added) {
          return (
            <span
              key={index}
              className="bg-emerald-500/20 text-emerald-300 px-0.5 rounded"
            >
              {part.value}
            </span>
          );
        }
        return <span key={index}>{part.value}</span>;
      })}
    </div>
  );
};

// Unified diff view showing all changes inline
const UnifiedDiffView: React.FC<{ original: string; optimized: string }> = ({
  original,
  optimized
}) => {
  const diffResult = useMemo(() => diffWords(original, optimized), [original, optimized]);

  return (
    <div className="whitespace-pre-wrap text-foreground text-base leading-relaxed">
      {diffResult.map((part, index) => {
        if (part.removed) {
          return (
            <span
              key={index}
              className="bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300 px-0.5 rounded line-through decoration-red-400"
            >
              {part.value}
            </span>
          );
        }
        if (part.added) {
          return (
            <span
              key={index}
              className="bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300 px-0.5 rounded"
            >
              {part.value}
            </span>
          );
        }
        return <span key={index}>{part.value}</span>;
      })}
    </div>
  );
};

interface OnboardingWizardProps {
  activeMode: "enhance" | "migrate";
  onComplete: (config: any) => void;
}

// Step definitions
const WIZARD_STEPS = [
  { id: "prompt", title: "Your Prompt", icon: FileText },
  { id: "usecase", title: "Use Case", icon: Lightbulb },
  { id: "dataset", title: "Dataset", icon: Database },
  { id: "fieldmapping", title: "Field Mapping", icon: ArrowRight },
  { id: "metrics", title: "Success Metrics", icon: Target },
  { id: "models", title: "AI Models", icon: Brain },
  { id: "optimizer", title: "Optimizer", icon: Zap },
];

export const OnboardingWizard: React.FC<OnboardingWizardProps> = ({
  activeMode,
  onComplete,
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [formData, setFormData] = useState({
    prompt: "",
    useCase: "",
    datasetPath: "",
    uploadedFile: null as File | null,
    datasetRecordCount: 0,
    datasetFieldCount: 0,
    fieldMappings: {} as Record<string, string>,
    datasetType: "standard_json",
    metrics: [] as string[],
    metricConfigurations: {} as Record<string, any>,
    modelConfigurations: [] as any[],
    modelProvider: "Llama 3.1 8B",
    selectedOptimizer: "",
    optimizerConfig: null as any,
    customOptimizerParams: null as any,
  });

  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [creatingProject, setCreatingProject] = useState(false);
  const [projectCreationResult, setProjectCreationResult] = useState<any>(null);

  // Optimization streaming state
  const [optimizing, setOptimizing] = useState(false);
  const [optimizationLogs, setOptimizationLogs] = useState<any[]>([]);
  const [optimizationProgress, setOptimizationProgress] = useState({ phase: "", progress: 0, message: "" });
  const [optimizationResult, setOptimizationResult] = useState<any>(null);
  const [websocket, setWebsocket] = useState<WebSocket | null>(null);
  const [viewMode, setViewMode] = useState<'split' | 'unified'>('split');

  // Generate dynamic project name
  const generateProjectName = () => {
    const now = new Date();
    const pad = (n: number) => n.toString().padStart(2, '0');
    const date = `${pad(now.getDate())}${pad(now.getMonth() + 1)}${now.getFullYear().toString().slice(-2)}`;
    const time = `${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`;
    const useCase = formData.useCase || 'custom';
    return `${useCase}-project-${date}-${time}`;
  };

  const handleCreateProject = async () => {
    setCreatingProject(true);
    setProjectCreationResult(null);

    try {
      const wizardData = {
        prompt: { text: formData.prompt, inputs: ["question"], outputs: ["answer"] },
        useCase: formData.useCase,
        dataset: {
          path: formData.datasetPath,
          fieldMappings: formData.fieldMappings,
          trainSize: 50,
          validationSize: 20
        },
        models: { selected: formData.modelConfigurations },
        metrics: formData.metrics,
        metricConfigurations: formData.metricConfigurations,
        optimizer: {
          selectedOptimizer: formData.selectedOptimizer,
          customParams: formData.customOptimizerParams
        }
      };

      const projectName = generateProjectName();
      const response = await fetch(apiUrl("/create-project"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          wizardData,
          projectName
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      if (result.success) {
        setProjectCreationResult(result);
      } else {
        throw new Error(result.error || "Failed to create project");
      }

    } catch (error) {
      console.error("Error creating project:", error);
      setProjectCreationResult({
        success: false,
        error: error.message || "Failed to create project"
      });
    } finally {
      setCreatingProject(false);
    }
  };

  const handleComplete = () => {
    startOptimization();
  };

  const startOptimization = () => {
    if (!projectCreationResult || !projectCreationResult.actualProjectName) {
      console.error("No project created to optimize");
      return;
    }

    setOptimizing(true);
    setOptimizationLogs([]);
    setOptimizationProgress({ phase: "", progress: 0, message: "" });
    setOptimizationResult(null);

    const ws = new WebSocket(wsUrl(`/ws/optimize/${projectCreationResult.actualProjectName}`));
    setWebsocket(ws);

    ws.onopen = () => {
      console.log("WebSocket connected for optimization");
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case "status":
          setOptimizationProgress(prev => ({
            ...prev,
            phase: data.phase,
            message: data.message
          }));
          break;

        case "progress":
          setOptimizationProgress({
            phase: data.phase,
            progress: data.progress,
            message: data.message
          });
          break;

        case "log":
          setOptimizationLogs(prev => [...prev, {
            id: Date.now() + Math.random(),
            level: data.level,
            logger: data.logger,
            message: data.message,
            timestamp: data.timestamp
          }]);
          break;

        case "complete":
          setOptimizationResult(data);
          setOptimizing(false);
          ws.close();
          break;

        case "error":
          setOptimizationResult({
            success: false,
            error: data.message
          });
          setOptimizing(false);
          ws.close();
          break;
      }
    };

    ws.onclose = () => {
      console.log("WebSocket connection closed");
      setWebsocket(null);
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      setOptimizationResult({
        success: false,
        error: "WebSocket connection failed"
      });
      setOptimizing(false);
      setWebsocket(null);
    };
  };

  React.useEffect(() => {
    return () => {
      if (websocket) {
        websocket.close();
      }
    };
  }, [websocket]);


  const updateFormData = (field: string, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const goToNextStep = () => {
    if (currentStep < WIZARD_STEPS.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const goToPreviousStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const goToStep = (stepIndex: number) => {
    setCurrentStep(stepIndex);
  };

  const isCurrentStepValid = () => {
    const stepId = WIZARD_STEPS[currentStep].id;
    const status = getSectionStatus(stepId);
    return status === 'complete';
  };

  const isFormValid = () => {
    if (formData.prompt.trim() === "") return false;
    if (formData.useCase === "") return false;
    if (formData.datasetPath === "") return false;

    if (formData.useCase !== "custom") {
      const requirements =
        formData.useCase === "qa"
          ? ["question", "answer"]
          : ["context", "query", "answer"];
      if (!requirements.every((field) => formData.fieldMappings[field])) return false;
    }

    if (formData.metrics.length === 0) return false;

    if (formData.modelConfigurations.length === 0) return false;
    const modelsValid = formData.modelConfigurations.every((config) => {
      const hasModel = config.model_name && config.model_name.trim() !== "";
      const provider = config.provider_id;
      const needsApiKey = ["openrouter", "together"].includes(provider);
      const hasApiKey = !needsApiKey || (config.api_key && config.api_key.trim() !== "");
      const hasValidRole =
        formData.modelConfigurations.length === 1 ||
        config.role === "both" ||
        (formData.modelConfigurations.some((c) => c.role === "target" || c.role === "both") &&
          formData.modelConfigurations.some((c) => c.role === "optimizer" || c.role === "both"));
      return hasModel && hasApiKey && hasValidRole;
    });
    if (!modelsValid) return false;

    if (formData.selectedOptimizer === "") return false;

    return true;
  };

  const getSectionStatus = (sectionId: string): 'complete' | 'incomplete' | 'empty' => {
    switch (sectionId) {
      case 'prompt':
        return formData.prompt.trim() !== "" ? 'complete' : 'empty';
      case 'usecase':
        return formData.useCase !== "" ? 'complete' : 'empty';
      case 'dataset':
        return formData.datasetPath !== "" ? 'complete' : 'empty';
      case 'fieldmapping':
        if (formData.useCase === "custom") return 'complete';
        if (formData.datasetPath === "") return 'empty';
        const requirements = formData.useCase === "qa" ? ["question", "answer"] : ["context", "query", "answer"];
        return requirements.every((field) => formData.fieldMappings[field]) ? 'complete' : 'incomplete';
      case 'metrics':
        return formData.metrics.length > 0 ? 'complete' : 'empty';
      case 'models':
        if (formData.modelConfigurations.length === 0) return 'empty';
        const modelsValid = formData.modelConfigurations.every((config) => {
          const hasModel = config.model_name && config.model_name.trim() !== "";
          const provider = config.provider_id;
          const needsApiKey = ["openrouter", "together"].includes(provider);
          const hasApiKey = !needsApiKey || (config.api_key && config.api_key.trim() !== "");
          return hasModel && hasApiKey;
        });
        return modelsValid ? 'complete' : 'incomplete';
      case 'optimizer':
        return formData.selectedOptimizer !== "" ? 'complete' : 'empty';
      default:
        return 'empty';
    }
  };

  const handleFileUpload = async (file: File) => {
    setUploadLoading(true);
    setUploadError(null);

    try {
      const formDataObj = new FormData();
      formDataObj.append("file", file);

      const response = await fetch(
        apiUrl("/api/datasets/upload"),
        {
          method: "POST",
          body: formDataObj,
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to upload dataset");
      }

      const data = await response.json();

      updateFormData("datasetPath", data.filename);
      updateFormData("uploadedFile", file);
      updateFormData("datasetRecordCount", data.total_records || 0);
      // Count unique fields from preview data
      const fieldCount = data.preview && data.preview.length > 0
        ? Object.keys(data.preview[0]).length
        : 0;
      updateFormData("datasetFieldCount", fieldCount);

      console.log("Dataset uploaded successfully:", data);
    } catch (error) {
      console.error("Error uploading dataset:", error);
      setUploadError(
        error instanceof Error ? error.message : "Failed to upload dataset"
      );
    } finally {
      setUploadLoading(false);
    }
  };

  const handleFieldMappingUpdate = (mappings: Record<string, string>) => {
    updateFormData("fieldMappings", mappings);
  };

  // Render progress stepper
  const renderStepper = () => (
    <div className="mb-8">
      <div className="flex items-start justify-between">
        {WIZARD_STEPS.map((step, index) => {
          const Icon = step.icon;
          const isActive = index === currentStep;
          const isComplete = getSectionStatus(step.id) === 'complete';
          const isAccessible = index <= currentStep || isComplete;

          return (
            <React.Fragment key={step.id}>
              <div className="flex flex-col items-center flex-1">
                <button
                  onClick={() => isAccessible && goToStep(index)}
                  disabled={!isAccessible}
                  className={`w-12 h-12 rounded-full flex items-center justify-center border-2 transition-all ${
                    isComplete
                      ? "bg-emerald-500 border-emerald-500 text-white"
                      : isActive
                      ? "bg-[#0064E0] border-[#0064E0] text-white"
                      : isAccessible
                      ? "border-white/[0.2] bg-white/[0.05] text-white/60 hover:border-[#0064E0]/50"
                      : "border-white/[0.1] bg-white/[0.02] text-white/30 cursor-not-allowed"
                  }`}
                >
                  {isComplete ? (
                    <CheckCircle className="w-6 h-6" />
                  ) : (
                    <Icon className="w-5 h-5" />
                  )}
                </button>
                <span
                  className={`mt-2 text-xs text-center ${
                    isActive
                      ? "text-white font-medium"
                      : isComplete
                      ? "text-emerald-400"
                      : "text-white/50"
                  }`}
                >
                  {step.title}
                </span>
              </div>

              {index < WIZARD_STEPS.length - 1 && (
                <div className="flex items-center pt-[24px]">
                  <div
                    className={`h-0.5 flex-1 mx-2 transition-colors ${
                      getSectionStatus(WIZARD_STEPS[index + 1].id) === 'complete'
                        ? "bg-emerald-500"
                        : "bg-white/[0.1]"
                    }`}
                  />
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );

  const getStepSubtext = () => {
    const stepId = WIZARD_STEPS[currentStep].id;
    switch (stepId) {
      case "prompt":
        return "Automatically test variations and measure what performs best";
      case "usecase":
        return "Tell us what your prompt does so we can suggest the right setup";
      case "dataset":
        return "Upload test cases with inputs and expected outputs";
      case "fieldmapping":
        return "Map your data columns to what the optimizer needs";
      case "metrics":
        return "Choose how we should measure success";
      case "models":
        return "Pick which AI models to use for testing";
      case "optimizer":
        return "Configure how your prompt will be optimized";
      default:
        return "";
    }
  };

  const renderRequirementsHeader = () => (
    <div className="text-center mb-8 pt-4">
      <h1 className="text-2xl md:text-3xl font-normal text-white mb-4 tracking-tight">
        Find the best version of your prompt
      </h1>
      <p className="text-white/60 text-lg max-w-2xl mx-auto">
        {getStepSubtext()}
      </p>
    </div>
  );

  const renderPromptSection = () => (
    <div>
      <WizardSection
        id="prompt"
        title="Your Prompt"
        icon={<FileText className="w-5 h-5" />}
        status={getSectionStatus('prompt')}
        collapsed={false}
        onToggle={() => {}}
      >
        <p className="text-white/60 text-sm">
          Enter the prompt you want to optimize. This is the instruction or system prompt that guides AI behavior.
        </p>

        <div className="space-y-3">
          <label className="block text-sm font-medium text-white">
            Current Prompt
          </label>
          <textarea
            value={formData.prompt}
            onChange={(e) => updateFormData("prompt", e.target.value)}
            placeholder="Enter your prompt here..."
            className="w-full h-32 p-4 border border-white/[0.1] rounded-xl focus:ring-2 focus:ring-[#0064E0]/50 focus:border-[#0064E0]/50 resize-none bg-white/[0.05] text-white placeholder:text-white/40 transition-colors"
          />
        </div>

        <div className="space-y-2">
          <p className="text-sm font-medium text-white/60">
            Quick Examples:
          </p>
          <div className="flex flex-wrap gap-2">
            {[
              "Analyze the sentiment of this text:",
              "Summarize this document in 3 bullet points:",
              "Answer this question based on the context:",
              "Classify this text into categories:",
            ].map((example) => (
              <button
                key={example}
                onClick={() => updateFormData("prompt", example)}
                className="text-xs bg-[#0064E0]/20 hover:bg-[#0064E0]/30 text-[#4da3ff] px-3 py-1.5 rounded-full border border-[#0064E0]/30 transition-colors"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      </WizardSection>
    </div>
  );

  const renderUseCaseSection = () => (
    <div>
      <WizardSection
        id="usecase"
        title="Use Case"
        icon={<Lightbulb className="w-5 h-5" />}
        status={getSectionStatus('usecase')}
        collapsed={false}
        onToggle={() => {}}
      >
        <p className="text-white/60 text-sm">
          Choose the type that best matches your project to get relevant options for field mapping and metrics.
        </p>

        <UseCaseSelector
          selectedUseCase={formData.useCase}
          onSelectUseCase={(useCaseId) => updateFormData("useCase", useCaseId)}
        />
      </WizardSection>
    </div>
  );

  const renderDatasetSection = () => (
    <div>
      <WizardSection
        id="dataset"
        title="Dataset"
        icon={<Database className="w-5 h-5" />}
        status={getSectionStatus('dataset')}
        collapsed={false}
        onToggle={() => {}}
      >
        <DatasetUploader
          datasetPath={formData.datasetPath}
          uploadedFile={formData.uploadedFile}
          datasetRecordCount={formData.datasetRecordCount}
          datasetFieldCount={formData.datasetFieldCount}
          useCase={formData.useCase}
          onUpload={handleFileUpload}
          onRemove={() => {
            updateFormData("datasetPath", "");
            updateFormData("uploadedFile", null);
            updateFormData("datasetRecordCount", 0);
            updateFormData("datasetFieldCount", 0);
            setUploadError(null);
          }}
          loading={uploadLoading}
          error={uploadError}
        />
      </WizardSection>
    </div>
  );

  const renderFieldMappingSection = () => (
    <div>
      <WizardSection
        id="fieldmapping"
        title="Field Mapping"
        icon={<ArrowRight className="w-5 h-5" />}
        status={getSectionStatus('fieldmapping')}
        collapsed={false}
        onToggle={() => {}}
      >
        {formData.datasetPath ? (
          <FieldMappingInterface
            filename={formData.datasetPath}
            useCase={formData.useCase}
            onMappingUpdate={handleFieldMappingUpdate}
            existingMappings={formData.fieldMappings}
          />
        ) : (
          <div className="text-center py-8 text-white/50">
            <ArrowRight className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>Upload a dataset first to configure field mappings</p>
          </div>
        )}
      </WizardSection>
    </div>
  );

  const handleMetricsChange = (
    selectedMetrics: string[],
    configurations: Record<string, any>
  ) => {
    updateFormData("metrics", selectedMetrics);
    updateFormData("metricConfigurations", configurations);
  };

  const renderMetricsSection = () => (
    <div>
      <WizardSection
        id="metrics"
        title="Success Metrics"
        icon={<Target className="w-5 h-5" />}
        status={getSectionStatus('metrics')}
        collapsed={false}
        onToggle={() => {}}
      >
        <MetricsSelector
          useCase={formData.useCase}
          fieldMappings={formData.fieldMappings}
          selectedMetrics={formData.metrics}
          onMetricsChange={handleMetricsChange}
        />
      </WizardSection>
    </div>
  );

  const renderModelsSection = () => (
    <div>
      <WizardSection
        id="models"
        title="AI Models"
        icon={<Brain className="w-5 h-5" />}
        status={getSectionStatus('models')}
        collapsed={false}
        onToggle={() => {}}
      >
        <ModelProviderSelector
          useCase={formData.useCase}
          fieldMappings={formData.fieldMappings}
          onConfigurationChange={(configs) =>
            setFormData((prev) => ({ ...prev, modelConfigurations: configs }))
          }
        />
      </WizardSection>
    </div>
  );

  const handleOptimizerChange = (optimizer: string, config: any, customParams?: any) => {
    updateFormData("selectedOptimizer", optimizer);
    updateFormData("optimizerConfig", config);
    if (customParams) {
      updateFormData("customOptimizerParams", customParams);
    }
  };

  const getOptimizerParameters = () => {
    if (formData.optimizerConfig?.parameters) {
      return formData.optimizerConfig.parameters;
    }

    return {
      num_candidates: 10,
      num_threads: 18,
      max_labeled_demos: 5,
      auto_mode: "basic"
    };
  };

  const renderOptimizerSection = () => (
    <div>
      <WizardSection
        id="optimizer"
        title="Optimizer"
        icon={<Zap className="w-5 h-5" />}
        status={getSectionStatus('optimizer')}
        collapsed={false}
        onToggle={() => {}}
      >
        <OptimizerSelector
          selectedOptimizer={formData.selectedOptimizer}
          onOptimizerChange={handleOptimizerChange}
          modelCount={formData.modelConfigurations.length}
          useCase={formData.useCase}
        />
      </WizardSection>
    </div>
  );

  const renderCurrentStep = () => {
    const stepId = WIZARD_STEPS[currentStep].id;
    switch (stepId) {
      case "prompt":
        return renderPromptSection();
      case "usecase":
        return renderUseCaseSection();
      case "dataset":
        return renderDatasetSection();
      case "fieldmapping":
        return renderFieldMappingSection();
      case "metrics":
        return renderMetricsSection();
      case "models":
        return renderModelsSection();
      case "optimizer":
        return renderOptimizerSection();
      default:
        return null;
    }
  };

  return (
    <div className="w-full">
      {/* Main Form Container */}
      <div className="glass-panel p-6 md:p-8">
        {/* Header */}
        {renderRequirementsHeader()}

        {/* Progress Stepper */}
        {renderStepper()}

        {/* Current Step Content */}
        <div className="mb-8">
          {renderCurrentStep()}
        </div>

        {/* Step Navigation */}
        <div className="flex justify-between items-center mb-8 pt-6 border-t border-white/[0.08]">
          {currentStep > 0 ? (
            <Button
              onClick={goToPreviousStep}
              variant="outlined"
              size="medium"
              className="border-white/[0.15] text-white hover:bg-white/[0.05]"
            >
              <ChevronLeft className="w-5 h-5" />
              Previous
            </Button>
          ) : (
            <div />
          )}

          <div className="text-sm text-white/50">
            Step {currentStep + 1} of {WIZARD_STEPS.length}
          </div>

          {currentStep < WIZARD_STEPS.length - 1 ? (
            <Button
              onClick={goToNextStep}
              disabled={!isCurrentStepValid()}
              variant="filled"
              size="medium"
            >
              Next
              <ChevronRight className="w-5 h-5" />
            </Button>
          ) : (
            <Button
              onClick={handleCreateProject}
              disabled={!isFormValid() || creatingProject || projectCreationResult?.success}
              variant="filledTeal"
              size="medium"
            >
              {creatingProject ? (
                <>
                  Creating Project...
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                </>
              ) : projectCreationResult?.success ? (
                <>
                  Project Created
                  <CheckCircle />
                </>
              ) : (
                <>
                  Create Project
                  <CheckCircle />
                </>
              )}
            </Button>
          )}
        </div>

        {/* Final Action Section - Show results when available */}
        {currentStep === WIZARD_STEPS.length - 1 && (
          <div className="mt-6">

          {/* Project Creation Results */}
          {projectCreationResult && (
            <div className={`mb-6 p-4 rounded-xl border ${
              projectCreationResult.success
                ? 'bg-emerald-500/10 border-emerald-500/30'
                : 'bg-red-500/10 border-red-500/30'
            }`}>
              <div className="flex items-center space-x-3 mb-3">
                {projectCreationResult.success ? (
                  <CheckCircle className="w-6 h-6 text-emerald-400" />
                ) : (
                  <AlertCircle className="w-6 h-6 text-red-400" />
                )}
                <h3 className="font-bold text-lg text-white">
                  {projectCreationResult.success ? 'Project Created Successfully!' : 'Project Creation Failed'}
                </h3>
              </div>

              {projectCreationResult.success ? (
                <div className="space-y-3">
                  <p className="text-emerald-300">{projectCreationResult.message}</p>

                  {projectCreationResult.actualProjectName !== projectCreationResult.requestedProjectName && (
                    <div className="bg-[#0064E0]/10 p-3 rounded border border-[#0064E0]/30">
                      <p className="text-sm font-medium text-[#4da3ff] mb-1">Project Name Updated:</p>
                      <p className="text-sm text-[#4da3ff]/80">
                        A project with the name "{projectCreationResult.requestedProjectName}" already existed,
                        so your project was created as "{projectCreationResult.actualProjectName}" instead.
                      </p>
                    </div>
                  )}

                  <div className="bg-white/[0.05] p-3 rounded border border-white/[0.1]">
                    <p className="text-sm font-medium text-white mb-1">Project Location:</p>
                    <p className="text-sm font-mono text-white/60 bg-black/30 p-2 rounded">
                      {projectCreationResult.projectPath}
                    </p>
                  </div>
                </div>
              ) : (
                <p className="text-red-400">{projectCreationResult.error}</p>
              )}
            </div>
          )}

          {/* Start Optimization Button */}
          {projectCreationResult?.success && !optimizing && !optimizationResult && (
            <div className="flex justify-center mb-6">
              <Button
                onClick={handleComplete}
                variant="filledTeal"
                size="large"
              >
                Start Optimization
                <Zap />
              </Button>
            </div>
          )}

          {/* Optimization Progress */}
          {optimizing && (
            <div className="mb-6 space-y-4">
              <div className="text-center">
                <h3 className="text-xl font-bold text-white mb-2">
                  Optimizing Your Prompt...
                </h3>
                <p className="text-white/60">
                  This may take a few minutes. Real-time progress is shown below.
                </p>
              </div>

              {/* Progress Bar */}
              <div className="bg-white/[0.05] p-4 rounded-xl border border-white/[0.1]">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-white">
                    {optimizationProgress.phase || "Initializing..."}
                  </span>
                  <span className="text-sm text-white/60">
                    {Math.round(optimizationProgress.progress)}%
                  </span>
                </div>
                <div className="w-full bg-white/[0.1] rounded-full h-2">
                  <div
                    className="bg-[#0064E0] h-2 rounded-full transition-all duration-300"
                    style={{ width: `${optimizationProgress.progress}%` }}
                  ></div>
                </div>
                <p className="text-sm text-white/50 mt-2">
                  {optimizationProgress.message}
                </p>
              </div>

              {/* Live Logs */}
              <div className="bg-black/40 rounded-xl p-4 max-h-64 overflow-y-auto border border-white/[0.1]">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-white font-medium">Live Optimization Logs</h4>
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
                    <span className="text-emerald-400 text-sm">Live</span>
                  </div>
                </div>
                <div className="space-y-1 font-mono text-sm">
                  {optimizationLogs.map((log) => (
                    <div
                      key={log.id}
                      className={`${
                        log.level === "ERROR"
                          ? "text-red-400"
                          : log.level === "WARNING"
                          ? "text-yellow-400"
                          : log.level === "INFO"
                          ? "text-blue-400"
                          : "text-white/60"
                      }`}
                    >
                      {log.message}
                    </div>
                  ))}
                  {optimizationLogs.length === 0 && (
                    <div className="text-white/40 italic">Waiting for logs...</div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Optimization Results */}
          {optimizationResult && optimizationResult.success && (() => {
            // Calculate diff stats
            const diff = diffWords(optimizationResult.originalPrompt || "", optimizationResult.optimizedPrompt || "");
            let added = 0;
            let removed = 0;
            diff.forEach(part => {
              if (part.added) added += part.value.split(/\s+/).filter(Boolean).length;
              if (part.removed) removed += part.value.split(/\s+/).filter(Boolean).length;
            });

            return (
              <div className="bg-white/[0.02] rounded-xl p-6 border border-white/[0.1] mb-6">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-2xl font-normal text-foreground">Results</h2>

                  {/* View mode toggle and stats */}
                  <div className="flex items-center gap-4">
                    {/* Diff stats */}
                    <div className="flex items-center gap-3 text-sm">
                      <span className="flex items-center gap-1.5 text-emerald-700 bg-emerald-50 dark:bg-emerald-900/30 dark:text-emerald-300 px-2.5 py-1 rounded-md border border-emerald-200 dark:border-emerald-800">
                        <span className="font-semibold">+{added}</span>
                        <span className="text-emerald-600 dark:text-emerald-400">words</span>
                      </span>
                      <span className="flex items-center gap-1.5 text-red-700 bg-red-50 dark:bg-red-900/30 dark:text-red-300 px-2.5 py-1 rounded-md border border-red-200 dark:border-red-800">
                        <span className="font-semibold">-{removed}</span>
                        <span className="text-red-600 dark:text-red-400">words</span>
                      </span>
                    </div>

                    {/* View toggle */}
                    <div className="bg-muted p-1 rounded-full inline-flex border border-border">
                      <button
                        onClick={() => setViewMode('split')}
                        className={`flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-full transition-colors ${
                          viewMode === 'split'
                            ? 'bg-panel text-foreground shadow-sm'
                            : 'text-muted-foreground hover:text-foreground'
                        }`}
                        title="Side by side"
                      >
                        <Columns size={16} />
                        Split
                      </button>
                      <button
                        onClick={() => setViewMode('unified')}
                        className={`flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-full transition-colors ${
                          viewMode === 'unified'
                            ? 'bg-panel text-foreground shadow-sm'
                            : 'text-muted-foreground hover:text-foreground'
                        }`}
                        title="Unified view"
                      >
                        <LayoutList size={16} />
                        Unified
                      </button>
                    </div>
                  </div>
                </div>

                {/* Content */}
                {viewMode === 'split' ? (
                  /* Side-by-side view */
                  <div className="grid grid-cols-2 gap-4 mb-8">
                    {/* Before panel */}
                    <div className="flex flex-col">
                      <div className="flex items-center gap-2 mb-3">
                        <div className="w-3 h-3 rounded-full bg-red-400"></div>
                        <span className="text-sm font-semibold text-white/60 uppercase tracking-wide">
                          Original
                        </span>
                      </div>
                      <div className="flex-1 border border-white/[0.1] bg-white/[0.03] rounded-xl p-4 max-h-64 overflow-y-auto">
                        <DiffView
                          original={optimizationResult.originalPrompt || ""}
                          optimized={optimizationResult.optimizedPrompt || ""}
                          showOriginal={true}
                        />
                      </div>
                    </div>

                    {/* After panel */}
                    <div className="flex flex-col">
                      <div className="flex items-center gap-2 mb-3">
                        <div className="w-3 h-3 rounded-full bg-emerald-400"></div>
                        <span className="text-sm font-semibold text-white/60 uppercase tracking-wide">
                          Optimized
                        </span>
                      </div>
                      <div className="flex-1 border border-white/[0.1] bg-white/[0.03] rounded-xl p-4 max-h-64 overflow-y-auto">
                        <DiffView
                          original={optimizationResult.originalPrompt || ""}
                          optimized={optimizationResult.optimizedPrompt || ""}
                          showOriginal={false}
                        />
                      </div>
                    </div>
                  </div>
                ) : (
                  /* Unified view */
                  <div className="mb-8">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
                        All Changes
                      </span>
                      <span className="text-xs text-muted-foreground/70">
                        (strikethrough = removed, highlighted = added)
                      </span>
                    </div>
                    <div className="border border-border bg-panel rounded-2xl p-5 h-[60vh] overflow-y-auto">
                      <UnifiedDiffView
                        original={optimizationResult.originalPrompt || ""}
                        optimized={optimizationResult.optimizedPrompt || ""}
                      />
                    </div>
                  </div>
                )}

                {/* Legend */}
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <div className="flex items-center gap-2">
                    <span className="inline-block w-4 h-4 bg-red-100 dark:bg-red-900/40 border border-red-200 dark:border-red-800 rounded"></span>
                    <span>Removed</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="inline-block w-4 h-4 bg-emerald-100 dark:bg-emerald-900/40 border border-emerald-200 dark:border-emerald-800 rounded"></span>
                    <span>Added</span>
                  </div>
                </div>
              </div>
            );
          })()}

          {optimizationResult && !optimizationResult.success && (
            <div className="mb-6">
              <InfoBox variant="error" title="Optimization Failed">
                {optimizationResult.error}
              </InfoBox>
            </div>
          )}

            {/* Reset button after completion */}
            {optimizationResult && (
              <div className="flex justify-center mt-4">
                <Button
                  onClick={() => {
                    setProjectCreationResult(null);
                    setOptimizationResult(null);
                    setOptimizationLogs([]);
                    setCurrentStep(0);
                  }}
                  variant="outlined"
                  size="medium"
                  className="border-white/[0.15] text-white hover:bg-white/[0.05]"
                >
                  Start New Optimization
                </Button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
