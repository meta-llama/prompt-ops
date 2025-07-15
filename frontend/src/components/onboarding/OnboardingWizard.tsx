import React, { useState } from 'react';
import { ArrowLeft, ArrowRight, CheckCircle, FileText, Lightbulb, Database, Target, Eye } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { StepIndicator } from './StepIndicator';
import { UseCaseSelector } from './UseCaseSelector';
import { FieldMappingInterface } from './FieldMappingInterface';

interface OnboardingWizardProps {
  activeMode: 'enhance' | 'migrate';
  onComplete: (config: any) => void;
}

export const OnboardingWizard: React.FC<OnboardingWizardProps> = ({ activeMode, onComplete }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [formData, setFormData] = useState({
    prompt: '',
    useCase: '',
    datasetPath: '',
    uploadedFile: null as File | null,
    fieldMappings: {} as Record<string, string>,
    datasetType: 'standard_json',
    metrics: ['Exact Match'],
    modelProvider: 'Llama 3.1 8B',
  });

  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const steps = [
    { id: 'requirements', title: 'What you need', description: 'Before you begin' },
    { id: 'prompt', title: 'Your Prompt', description: 'What to optimize' },
    { id: 'usecase', title: 'Use Case', description: 'Type of application' },
    { id: 'dataset', title: 'Dataset', description: 'Upload your data' },
    { id: 'fieldmapping', title: 'Field Mapping', description: 'Map your fields' },
    { id: 'metrics', title: 'Success Metrics', description: 'How to measure success' },
    { id: 'review', title: 'Review & Optimize', description: 'Final review' },
  ];

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleComplete = () => {
    const config = {
      prompt: formData.prompt,
      useCase: formData.useCase,
      datasetPath: formData.datasetPath,
      fieldMappings: formData.fieldMappings,
      datasetType: formData.datasetType,
      metrics: formData.metrics,
      modelProvider: formData.modelProvider,
    };
    onComplete(config);
  };

  const updateFormData = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const isStepValid = () => {
    switch (currentStep) {
      case 0: return true; // Requirements step
      case 1: return formData.prompt.trim() !== ''; // Prompt step
      case 2: return formData.useCase !== ''; // Use case step
      case 3: return formData.datasetPath !== ''; // Dataset upload step
      case 4: // Field mapping step
        if (formData.useCase === 'custom') return true;
        const requirements = formData.useCase === 'qa'
          ? ['question', 'answer']
          : ['question', 'documents', 'answer'];
        return requirements.every(field => formData.fieldMappings[field]);
      case 5: return true; // Metrics step
      case 6: return true; // Review step
      default: return false;
    }
  };

  const handleFileUpload = async (file: File) => {
    setUploadLoading(true);
    setUploadError(null);

    try {
      const formDataObj = new FormData();
      formDataObj.append('file', file);

      const response = await fetch('http://localhost:8000/api/datasets/upload', {
        method: 'POST',
        body: formDataObj,
      });

      if (!response.ok) {
        throw new Error('Failed to upload dataset');
      }

      const data = await response.json();

      updateFormData('datasetPath', data.filename);
      updateFormData('uploadedFile', file);

      console.log('Dataset uploaded successfully:', data);
    } catch (error) {
      console.error('Error uploading dataset:', error);
      setUploadError(error instanceof Error ? error.message : 'Failed to upload dataset');
    } finally {
      setUploadLoading(false);
    }
  };

  const handleFieldMappingComplete = (mappings: Record<string, string>) => {
    updateFormData('fieldMappings', mappings);
    handleNext();
  };

  const renderRequirementsStep = () => (
    <div className="space-y-6">
      <div className="text-center mb-6">
        <h2 className="text-4xl md:text-5xl font-black text-facebook-text mb-4 tracking-tight">
          What You
          <br />
          <span className="bg-gradient-to-r from-facebook-blue via-facebook-blue-light to-facebook-blue-dark bg-clip-text text-transparent">
            Need
          </span>
        </h2>
        <p className="text-facebook-text/70 text-lg">
          Before we begin, make sure you have these ready:
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white/90 backdrop-blur-xl p-6 rounded-2xl border border-facebook-border shadow-xl">
          <div className="flex items-center mb-4">
            <div className="w-12 h-12 bg-gradient-to-r from-facebook-blue to-facebook-blue-light rounded-full flex items-center justify-center mr-4">
              <FileText className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="font-bold text-facebook-text">A Prompt</h3>
              <p className="text-sm text-facebook-text/70">Your current prompt or instruction</p>
            </div>
          </div>
          <p className="text-sm text-facebook-text/60">
            The text you want to optimize for better performance.
          </p>
        </div>

        <div className="bg-white/90 backdrop-blur-xl p-6 rounded-2xl border border-facebook-border shadow-xl">
          <div className="flex items-center mb-4">
            <div className="w-12 h-12 bg-gradient-to-r from-facebook-blue to-facebook-blue-light rounded-full flex items-center justify-center mr-4">
              <Database className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="font-bold text-facebook-text">A Dataset</h3>
              <p className="text-sm text-facebook-text/70">JSON file with examples</p>
            </div>
          </div>
          <p className="text-sm text-facebook-text/60">
            Training examples to optimize your prompt against.
          </p>
        </div>

        <div className="bg-white/90 backdrop-blur-xl p-6 rounded-2xl border border-facebook-border shadow-xl">
          <div className="flex items-center mb-4">
            <div className="w-12 h-12 bg-gradient-to-r from-facebook-blue to-facebook-blue-light rounded-full flex items-center justify-center mr-4">
              <Target className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="font-bold text-facebook-text">Success Metrics</h3>
              <p className="text-sm text-facebook-text/70">How to measure improvement</p>
            </div>
          </div>
          <p className="text-sm text-facebook-text/60">
            Define what makes a good output for your use case.
          </p>
        </div>

        <div className="bg-white/90 backdrop-blur-xl p-6 rounded-2xl border border-facebook-border shadow-xl">
          <div className="flex items-center mb-4">
            <div className="w-12 h-12 bg-gradient-to-r from-facebook-blue to-facebook-blue-light rounded-full flex items-center justify-center mr-4">
              <Lightbulb className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="font-bold text-facebook-text">A Clear Goal</h3>
              <p className="text-sm text-facebook-text/70">What you want to achieve</p>
            </div>
          </div>
          <p className="text-sm text-facebook-text/60">
            Understanding of what improved performance looks like.
          </p>
        </div>
      </div>

      <div className="bg-facebook-blue/10 border border-facebook-blue/20 rounded-2xl p-6 shadow-lg backdrop-blur-xl">
        <div className="flex items-center mb-3">
          <Lightbulb className="w-5 h-5 text-facebook-blue mr-2" />
          <h3 className="font-bold text-facebook-text">Pro Tip</h3>
        </div>
        <p className="text-facebook-text/70 text-sm">
          The more specific your examples and success criteria, the better your optimized prompt will be.
          Quality over quantity - 20 good examples often work better than 200 poor ones.
        </p>
      </div>
    </div>
  );

  const renderPromptStep = () => (
    <div className="space-y-6">
      <div className="text-center mb-6">
        <h2 className="text-4xl md:text-5xl font-black text-facebook-text mb-4 tracking-tight">
          Your
          <br />
          <span className="bg-gradient-to-r from-facebook-blue via-facebook-blue-light to-facebook-blue-dark bg-clip-text text-transparent">
            Prompt
          </span>
        </h2>
        <p className="text-facebook-text/70 text-lg">
          Enter the prompt you want to optimize:
        </p>
      </div>

      <div className="bg-white/90 backdrop-blur-xl p-6 rounded-2xl border border-facebook-border shadow-xl">
        <div className="mb-4">
          <label className="block text-sm font-medium text-facebook-text mb-2">
            Current Prompt
          </label>
          <textarea
            value={formData.prompt}
            onChange={(e) => updateFormData('prompt', e.target.value)}
            placeholder="Enter your prompt here..."
            className="w-full h-32 p-4 border border-facebook-border rounded-xl focus:ring-2 focus:ring-facebook-blue focus:border-transparent resize-none bg-facebook-gray/50 text-facebook-text placeholder-facebook-text/50"
          />
        </div>

        <div className="space-y-2">
          <p className="text-sm font-medium text-facebook-text">Quick Examples:</p>
          <div className="flex flex-wrap gap-2">
            {[
              "Analyze the sentiment of this text:",
              "Summarize this document in 3 bullet points:",
              "Answer this question based on the context:",
              "Classify this text into categories:",
            ].map((example) => (
              <button
                key={example}
                onClick={() => updateFormData('prompt', example)}
                className="text-xs bg-facebook-blue/10 hover:bg-facebook-blue/20 text-facebook-blue px-3 py-1 rounded-full border border-facebook-blue/30 transition-colors duration-200 transform hover:scale-105"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  const renderUseCaseStep = () => (
    <div className="space-y-6">
      <div className="text-center mb-6">
        <h2 className="text-4xl md:text-5xl font-black text-facebook-text mb-4 tracking-tight">
          Use
          <br />
          <span className="bg-gradient-to-r from-facebook-blue via-facebook-blue-light to-facebook-blue-dark bg-clip-text text-transparent">
            Case
          </span>
        </h2>
        <p className="text-facebook-text/70 text-lg">
          Choose the type that best matches your project to get relevant options in the next steps.
        </p>
      </div>

      <UseCaseSelector
        selectedUseCase={formData.useCase}
        onSelectUseCase={(useCaseId) => updateFormData('useCase', useCaseId)}
      />
    </div>
  );

  const renderDatasetStep = () => (
    <div className="space-y-6">
      <div className="text-center mb-6">
        <h2 className="text-4xl md:text-5xl font-black text-facebook-text mb-4 tracking-tight">
          Upload Your
          <br />
          <span className="bg-gradient-to-r from-facebook-blue via-facebook-blue-light to-facebook-blue-dark bg-clip-text text-transparent">
            Dataset
          </span>
        </h2>
        <p className="text-facebook-text/70 text-lg">
          Upload a JSON file containing your training examples.
        </p>
      </div>

      <div
        className={`border-2 border-dashed rounded-2xl p-12 text-center shadow-lg transition-all duration-300 ${
          formData.datasetPath ? 'border-green-400 bg-green-50/80 backdrop-blur-xl' :
          uploadError ? 'border-red-400 bg-red-50/80 backdrop-blur-xl' :
          'border-facebook-border bg-white/90 backdrop-blur-xl hover:border-facebook-blue hover:shadow-xl'
        }`}
      >
        {uploadLoading ? (
          <div className="space-y-4">
            <div className="w-16 h-16 bg-facebook-blue/10 rounded-full flex items-center justify-center mx-auto">
              <div className="w-8 h-8 border-2 border-facebook-blue border-t-transparent rounded-full animate-spin"></div>
            </div>
            <p className="text-facebook-text">Uploading dataset...</p>
          </div>
        ) : formData.datasetPath ? (
          <div className="space-y-4">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto">
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
            <div>
              <p className="font-semibold text-facebook-text">{formData.datasetPath}</p>
              <p className="text-sm text-facebook-text/70">
                {formData.uploadedFile ? (formData.uploadedFile.size / 1024).toFixed(2) : '0'} KB
              </p>
            </div>
            <button
              onClick={() => {
                updateFormData('datasetPath', '');
                updateFormData('uploadedFile', null);
                setUploadError(null);
              }}
              className="text-sm text-red-600 hover:underline"
            >
              Remove file
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <FileText className="w-12 h-12 text-facebook-text/40 mx-auto" />
            <div>
              <label htmlFor="file-upload" className="cursor-pointer">
                <span className="text-facebook-blue hover:underline font-semibold">Click to upload</span>
                <span className="text-facebook-text/70"> or drag and drop</span>
              </label>
              <input
                id="file-upload"
                type="file"
                accept=".json"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) {
                    handleFileUpload(file);
                  }
                }}
              />
            </div>
            <p className="text-sm text-facebook-text/60">JSON files only, max 10MB</p>
            {uploadError && (
              <p className="text-sm text-red-600 bg-red-50 p-2 rounded">
                {uploadError}
              </p>
            )}
          </div>
        )}
      </div>

      {/* Dataset format helper */}
      {formData.useCase && formData.useCase !== 'custom' && (
        <div className="bg-facebook-blue/10 border border-facebook-blue/20 rounded-2xl p-6 shadow-lg backdrop-blur-xl">
          <p className="text-sm font-semibold text-facebook-text mb-3">
            Expected format for {formData.useCase.toUpperCase()}:
          </p>
          <pre className="text-xs bg-white/90 p-4 rounded-xl border border-facebook-border overflow-x-auto text-facebook-text/80">
            {formData.useCase === 'qa'
              ? JSON.stringify([{ question: "What is the capital of France?", answer: "Paris" }], null, 2)
              : JSON.stringify([{ query: "What are the key terms in this contract?", documents: ["Document 1 content text...", "Document 2 content text..."], answer: "The key terms include..." }], null, 2)
            }
          </pre>
        </div>
      )}
    </div>
  );

  const renderFieldMappingStep = () => {
    if (formData.useCase === 'custom') {
      return (
        <div className="space-y-6">
          <div className="text-center mb-6">
            <h2 className="text-4xl md:text-5xl font-black text-facebook-text mb-4 tracking-tight">
              Field
              <br />
              <span className="bg-gradient-to-r from-facebook-blue via-facebook-blue-light to-facebook-blue-dark bg-clip-text text-transparent">
                Mapping
              </span>
            </h2>
            <p className="text-facebook-text/70 text-lg">
              Custom configurations will be handled in the main interface.
            </p>
          </div>

          <div className="bg-white/90 backdrop-blur-xl p-6 rounded-2xl border border-facebook-border shadow-xl text-center">
            <Eye className="w-16 h-16 text-facebook-text/40 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-facebook-text mb-2">
              Custom Configuration
            </h3>
            <p className="text-facebook-text/70">
              You'll be able to configure field mappings and other settings in the main optimization interface.
            </p>
          </div>
        </div>
      );
    }

    return (
      <FieldMappingInterface
        filename={formData.datasetPath}
        useCase={formData.useCase}
        onMappingComplete={handleFieldMappingComplete}
        onCancel={handleBack}
      />
    );
  };

  const renderMetricsStep = () => (
    <div className="space-y-6">
      <div className="text-center mb-6">
        <h2 className="text-4xl md:text-5xl font-black text-facebook-text mb-4 tracking-tight">
          Define Success
          <br />
          <span className="bg-gradient-to-r from-facebook-blue via-facebook-blue-light to-facebook-blue-dark bg-clip-text text-transparent">
            Metrics
          </span>
        </h2>
        <p className="text-facebook-text/70 text-lg">
          {formData.useCase === 'custom'
            ? "Configure all settings for your optimization."
            : "Review and adjust the pre-configured settings if needed."
          }
        </p>
      </div>

      <div className="space-y-4">
        {/* Show current configuration */}
        <div className="bg-white/90 backdrop-blur-xl p-6 rounded-2xl border border-facebook-border shadow-xl">
          <h3 className="font-bold text-facebook-text mb-4 text-xl">Current Configuration</h3>
          <div className="space-y-3">
            <div className="flex justify-between py-2 border-b border-facebook-border/30">
              <span className="text-facebook-text/70">Use Case:</span>
              <span className="font-medium text-facebook-text">{formData.useCase}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-facebook-border/30">
              <span className="text-facebook-text/70">Dataset:</span>
              <span className="font-medium text-facebook-text">{formData.datasetPath}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-facebook-border/30">
              <span className="text-facebook-text/70">Metrics:</span>
              <span className="font-medium text-facebook-text">{formData.metrics.join(', ')}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-facebook-border/30">
              <span className="text-facebook-text/70">Model:</span>
              <span className="font-medium text-facebook-text">{formData.modelProvider}</span>
            </div>
          </div>
        </div>

        {formData.useCase !== 'custom' && (
          <p className="text-sm text-facebook-text/70 text-center">
            These settings have been optimized for {formData.useCase.toUpperCase()} use cases.
            You can proceed with these defaults or customize them in the main interface.
          </p>
        )}
      </div>
    </div>
  );

  const renderReviewStep = () => (
    <div className="space-y-6">
      <div className="text-center mb-6">
        <h2 className="text-4xl md:text-5xl font-black text-facebook-text mb-4 tracking-tight">
          Review &
          <br />
          <span className="bg-gradient-to-r from-facebook-blue via-facebook-blue-light to-facebook-blue-dark bg-clip-text text-transparent">
            Optimize
          </span>
        </h2>
        <p className="text-facebook-text/70 text-lg">
          Everything looks good! Review your configuration and start the optimization.
        </p>
      </div>

      <div className="bg-white/90 backdrop-blur-xl p-6 rounded-2xl border border-facebook-border shadow-xl space-y-4">
        <div>
          <h3 className="font-bold text-facebook-text mb-3 text-lg">Prompt:</h3>
          <p className="text-facebook-text bg-facebook-gray p-4 rounded-xl border border-facebook-border font-medium">
            {formData.prompt}
          </p>
        </div>

        {activeMode === 'migrate' && (
          <>
            <div>
              <h3 className="font-bold text-facebook-text mb-3 text-lg">Configuration:</h3>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="bg-facebook-gray p-3 rounded-xl border border-facebook-border">
                  <span className="text-facebook-text/70">Use Case:</span> <span className="font-medium text-facebook-text">{formData.useCase}</span>
                </div>
                <div className="bg-facebook-gray p-3 rounded-xl border border-facebook-border">
                  <span className="text-facebook-text/70">Dataset:</span> <span className="font-medium text-facebook-text">{formData.datasetPath}</span>
                </div>
              </div>
            </div>

            {Object.keys(formData.fieldMappings).length > 0 && (
              <div>
                <h3 className="font-bold text-facebook-text mb-3 text-lg">Field Mappings:</h3>
                <div className="bg-facebook-gray p-3 rounded-xl border border-facebook-border">
                  <pre className="text-xs text-facebook-text/80">
                    {JSON.stringify(formData.fieldMappings, null, 2)}
                  </pre>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      <div className="text-center">
        <Button
          onClick={handleComplete}
          className="bg-gradient-to-r from-facebook-blue via-facebook-blue-light to-facebook-blue-dark hover:opacity-90 text-white px-8 py-4 rounded-2xl text-lg font-bold shadow-lg shadow-facebook-blue/25 transform hover:scale-105 transition-all duration-300"
        >
          Start Optimization
        </Button>
      </div>
    </div>
  );

  const renderStepContent = () => {
    switch (currentStep) {
      case 0: // Requirements
        return renderRequirementsStep();
      case 1: // Prompt
        return renderPromptStep();
      case 2: // Use case
        return renderUseCaseStep();
      case 3: // Dataset
        return renderDatasetStep();
      case 4: // Field Mapping
        return renderFieldMappingStep();
      case 5: // Metrics
        return renderMetricsStep();
      case 6: // Review
        return renderReviewStep();
      default:
        return null;
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      {/* Progress Indicator */}
      <div className="mb-8">
        <StepIndicator
          steps={steps}
          currentStep={currentStep}
          className="justify-center"
        />
      </div>

      {/* Step Content */}
      <div className="bg-white/90 backdrop-blur-xl rounded-2xl shadow-xl border border-facebook-border p-8">
        {renderStepContent()}
      </div>

      {/* Navigation Buttons */}
      <div className="flex justify-between mt-6">
        <Button
          onClick={handleBack}
          disabled={currentStep === 0}
          variant="outline"
          className="flex items-center gap-2 border-facebook-border text-facebook-text hover:bg-facebook-gray rounded-xl px-6 py-3 font-semibold shadow-md transition-all duration-300"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </Button>

        <Button
          onClick={handleNext}
          disabled={!isStepValid()}
          className={`flex items-center gap-2 rounded-xl px-6 py-3 font-bold shadow-lg transition-all duration-300 transform hover:scale-105 ${
            currentStep === steps.length - 1
              ? 'bg-gradient-to-r from-facebook-blue via-facebook-blue-light to-facebook-blue-dark hover:opacity-90 text-white shadow-facebook-blue/25'
              : 'bg-facebook-blue hover:bg-facebook-blue-dark text-white shadow-facebook-blue/25'
          }`}
        >
          {currentStep === steps.length - 1 ? 'Complete Setup' : 'Next'}
          <ArrowRight className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
};
