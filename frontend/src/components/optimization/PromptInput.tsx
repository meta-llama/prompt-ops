import React, { useState, useRef, useEffect, useContext } from 'react';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { ArrowUp, FileJson, Loader2, Trash2, Upload, X, Settings, ChevronDown, ChevronUp, Eye, EyeOff } from 'lucide-react';
import { useToast } from '../../hooks/use-toast';
import { AppContext } from '../../context/AppContext';
import { apiUrl } from '@/lib/config';
import { Badge } from '@/components/ui/badge';
import { OptimizationProgress, OptimizationStep } from './OptimizationProgress';
import { OptimizationResults } from './OptimizationResults';
import { OnboardingWizard } from '../onboarding/OnboardingWizard';

export const PromptInput = () => {
  const { toast } = useToast();
  const [prompt, setPrompt] = useState('');
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [optimizedPrompt, setOptimizedPrompt] = useState('');
  const [originalPrompt, setOriginalPrompt] = useState('');
  const [showResults, setShowResults] = useState(false);
  const [copySuccess, setCopySuccess] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const { activeMode, setIsModeLocked } = useContext(AppContext);

  // Dataset upload state
  const [showDatasetDialog, setShowDatasetDialog] = useState(false);
  const [isUploadingDataset, setIsUploadingDataset] = useState(false);
  const [uploadedDatasets, setUploadedDatasets] = useState<any[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Configuration state from OnboardingWizard
  const [config, setConfig] = useState({
    model: 'Llama 3.3 70B',
    proposer: 'Llama 3.3 70B',
    strategy: 'MiPro',
    datasetAdapter: '',
    metrics: 'Exact Match',
    useLlamaTips: true,
    openrouterApiKey: undefined
  });

  // Enhance mode settings state
  const [showEnhanceSettings, setShowEnhanceSettings] = useState(false);
  const [enhanceSettings, setEnhanceSettings] = useState({
    apiBaseUrl: '',
    apiFormat: 'openai',
    apiKey: '',
    model: '',
  });
  const [showApiKey, setShowApiKey] = useState(false);

  // Load enhance settings from localStorage on mount
  useEffect(() => {
    const savedSettings = localStorage.getItem('enhanceSettings');
    if (savedSettings) {
      try {
        setEnhanceSettings(JSON.parse(savedSettings));
      } catch (e) {
        console.error('Failed to load saved enhance settings:', e);
      }
    }
  }, []);

  // Save enhance settings to localStorage when changed
  useEffect(() => {
    if (enhanceSettings.apiBaseUrl || enhanceSettings.apiKey || enhanceSettings.model) {
      localStorage.setItem('enhanceSettings', JSON.stringify(enhanceSettings));
    }
  }, [enhanceSettings]);
  const [showWizard, setShowWizard] = useState(true);
  const [wizardCompleted, setWizardCompleted] = useState(false);

  // Fetch uploaded datasets on component mount
  useEffect(() => {
    fetchUploadedDatasets();
  }, []);

  const fetchUploadedDatasets = async () => {
    try {
      const response = await fetch(apiUrl('/api/datasets'));
      if (response.ok) {
        const data = await response.json();
        setUploadedDatasets(data.datasets || []);
      }
    } catch (error) {
      console.error('Error fetching datasets:', error);
    }
  };

  const handleWizardComplete = (wizardConfig: any) => {
    console.log('Wizard completed with config:', wizardConfig);

    setConfig({
      model: wizardConfig.models?.selected?.[0]?.taskModel || 'Llama 3.3 70B',
      proposer: wizardConfig.models?.selected?.[0]?.proposerModel || 'Llama 3.3 70B',
      strategy: wizardConfig.optimizer || 'MiPro',
      datasetAdapter: wizardConfig.datasetType || '',
      metrics: Array.isArray(wizardConfig.metrics) ? wizardConfig.metrics.join(', ') : wizardConfig.metrics || 'Exact Match',
      useLlamaTips: wizardConfig.useLlamaTips !== false,
      openrouterApiKey: wizardConfig.apiKey
    });

    setWizardCompleted(true);
    setShowWizard(false);

    toast({
      title: "Configuration Complete",
      description: "Your optimization settings have been configured successfully.",
    });
  };

  const handleDatasetUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (uploadedDatasets.length > 0) {
      if (!window.confirm('You already have an uploaded dataset. Replace it with the new one?')) {
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
        return;
      }
      await handleDatasetDelete(uploadedDatasets[0].filename);
    }

    setIsUploadingDataset(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(apiUrl('/api/datasets/upload'), {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to upload dataset');
      }

      const data = await response.json();
      await fetchUploadedDatasets();

      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }

      console.log('Dataset uploaded successfully:', data);
    } catch (error) {
      console.error('Error uploading dataset:', error);
    } finally {
      setIsUploadingDataset(false);
    }
  };

  const handleDatasetDelete = async (filename: string) => {
    try {
      const response = await fetch(apiUrl(`/api/datasets/${filename}`), {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete dataset');
      }

      await fetchUploadedDatasets();
    } catch (error) {
      console.error('Error deleting dataset:', error);
    }
  };

  const optimizationSteps: OptimizationStep[] = [
    {
      id: 'analyze',
      label: 'Analyzing original prompt',
      completed: currentStep > 0,
      inProgress: currentStep === 0 && isOptimizing
    },
    {
      id: 'process',
      label: 'Processing dataset',
      completed: currentStep > 1,
      inProgress: currentStep === 1 && isOptimizing
    },
    {
      id: 'generate',
      label: 'Generating optimized versions...',
      completed: currentStep > 2,
      inProgress: currentStep === 2 && isOptimizing
    },
    {
      id: 'evaluate',
      label: 'Evaluating performance',
      completed: currentStep > 3,
      inProgress: currentStep === 3 && isOptimizing
    }
  ];

  const handleCopyToClipboard = () => {
    navigator.clipboard.writeText(optimizedPrompt);
    setCopySuccess(true);
    setTimeout(() => setCopySuccess(false), 2000);
  };

  const resetOptimization = () => {
    setIsOptimizing(false);
    setShowResults(false);
    setCurrentStep(0);
  };

  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    const handleBeforeUnload = () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const handleOptimizePrompt = async () => {
    if (!prompt.trim() || isOptimizing) return;

    if (activeMode === 'migrate') {
      if (uploadedDatasets.length === 0) {
        alert('Please upload a dataset before optimizing.');
        return;
      }
      if (!config.datasetAdapter) {
        alert('Please select a dataset adapter type before optimizing.');
        return;
      }
    }

    abortControllerRef.current = new AbortController();

    setIsModeLocked(true);
    setIsOptimizing(true);
    setShowResults(false);
    setOriginalPrompt(prompt);
    setCurrentStep(0);

    try {
      const endpoint = activeMode === 'enhance' ? 'enhance-prompt' : 'migrate-prompt';

      const requestBody = activeMode === 'enhance'
        ? {
            prompt,
            config: {
              ...(enhanceSettings.apiBaseUrl && { apiBaseUrl: enhanceSettings.apiBaseUrl }),
              ...(enhanceSettings.apiFormat && { apiFormat: enhanceSettings.apiFormat }),
              ...(enhanceSettings.apiKey && { apiKey: enhanceSettings.apiKey }),
              ...(enhanceSettings.model && { model: enhanceSettings.model }),
            }
          }
        : {
            prompt,
            config: {
              provider: "openrouter",
              ...config
            }
          };

      const response = await fetch(apiUrl(`/api/${endpoint}`), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error('Failed to optimize prompt');
      }

      const data = await response.json();
      setOptimizedPrompt(data.optimizedPrompt);
      setShowResults(true);
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        console.log('Optimization cancelled by user');
        toast({
          title: "Optimization Cancelled",
          description: "The optimization was cancelled.",
        });
      } else {
        console.error('Error optimizing prompt:', error);
        toast({
          title: "Optimization Failed",
          description: error instanceof Error ? error.message : "An unexpected error occurred during optimization. Please check your configuration and try again.",
          variant: "destructive",
        });
      }
    } finally {
      setIsOptimizing(false);
      setCurrentStep(0);
      setIsModeLocked(false);
      abortControllerRef.current = null;
    }
  };

  const handleCancelOptimization = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  };

  return (
    <div className="relative max-w-6xl mx-auto">
      {showResults ? (
        <div className="mt-8">
          <OptimizationResults
            originalPrompt={originalPrompt}
            optimizedPrompt={optimizedPrompt}
            onCopy={handleCopyToClipboard}
          />
          <div className="flex justify-center mt-8 gap-4">
            <button
              onClick={() => {
                setPrompt('');
                setOptimizedPrompt('');
                setShowResults(false);
                setIsModeLocked(false);
              }}
              className="bg-white/[0.05] hover:bg-white/[0.1] text-white border border-white/[0.15] px-8 py-3 rounded-full font-medium transition-colors"
            >
              Start New
            </button>
          </div>
        </div>
      ) : isOptimizing ? (
        <div className="glass-panel p-8 text-center">
          <h2 className="text-3xl font-bold mb-2 text-white">Run Optimization</h2>
          <p className="text-white/70 mb-8">Ready to optimize your prompt for Llama models. This process typically takes 5-10 minutes.</p>

          <div className="flex justify-center mb-8">
            <div className="w-20 h-20">
              <div className="w-full h-full rounded-full animate-spin"
                style={{
                  background: 'conic-gradient(from 0deg, transparent, rgba(0, 100, 224, 0) 10%, rgba(0, 100, 224, 0.2) 20%, rgba(0, 100, 224, 0.4) 30%, rgba(0, 100, 224, 0.8) 40%, rgba(0, 100, 224, 1) 50%, rgba(0, 100, 224, 0) 60%)',
                  borderRadius: '50%',
                  boxShadow: '0 0 20px rgba(0, 100, 224, 0.3)'
                }}>
              </div>
            </div>
          </div>

          <h3 className="text-2xl font-semibold mb-2 text-white">Optimizing Prompt...</h3>
          <p className="text-white/70 mb-8">This may take several minutes.</p>

          <OptimizationProgress steps={optimizationSteps} />

          <div className="flex justify-center mt-6">
            <button
              onClick={handleCancelOptimization}
              className="bg-white/[0.05] hover:bg-white/[0.1] text-white border border-white/[0.15] px-6 py-2 rounded-full font-medium transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <>
          {/* Prompt input - only show in enhance mode */}
          {activeMode === 'enhance' && (
            <div className="relative glass-panel p-6 md:p-8 mb-8">
              {/* Header */}
              <div className="text-center mb-8 pt-4">
                <h1 className="text-2xl md:text-3xl font-normal text-white mb-4 tracking-tight">
                  Prompt Enhancement
                </h1>
                <p className="text-white/70 text-lg max-w-2xl mx-auto">
                  Get an AI-refined version of your prompt in seconds — no dataset required
                </p>
              </div>

              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Your prompt..."
                disabled={isOptimizing}
                aria-label="Enter your prompt to enhance"
                className={`w-full h-28 p-4 text-xl text-white bg-white/[0.05] placeholder:text-white/50 border border-white/[0.1] rounded-xl focus:ring-2 focus:ring-[#0064E0] focus:border-[#0064E0] focus:outline-none resize-none leading-relaxed transition-colors ${isOptimizing ? 'opacity-75' : ''}`}
              />

              {/* API Settings panel */}
              <div className="mt-4 border-t border-white/[0.08] pt-4">
                <div className="flex items-center gap-2 text-sm text-white/70 mb-4">
                  <Settings size={16} aria-hidden="true" />
                  <span className="font-medium">Model Configuration</span>
                </div>

                <div className="space-y-4 p-4 bg-white/[0.03] rounded-xl border border-white/[0.08]">
                  {/* Model name input - REQUIRED */}
                  <div>
                    <Label className="text-sm text-white/80 mb-1.5">
                      Model Name <span className="text-red-400">*</span>
                    </Label>
                    <input
                      type="text"
                      value={enhanceSettings.model}
                      onChange={(e) => setEnhanceSettings({ ...enhanceSettings, model: e.target.value })}
                      placeholder="e.g., openrouter/meta-llama/llama-4-maverick"
                      className="w-full px-3 py-2 text-sm border border-white/[0.1] bg-white/[0.05] text-white placeholder:text-white/50 rounded-lg focus:ring-2 focus:ring-[#0064E0] focus:border-[#0064E0] focus:outline-none transition-colors"
                      disabled={isOptimizing}
                      required
                    />
                    <div className="text-xs text-white/70 mt-1">
                      Use LiteLLM format: <code className="bg-white/[0.1] px-1 rounded text-white/80">provider/model-name</code> (e.g., <code className="bg-white/[0.1] px-1 rounded text-white/80">openrouter/meta-llama/llama-3.3-70b-instruct</code>)
                    </div>
                  </div>

                  {/* Optional settings divider */}
                  <div className="border-t border-white/[0.08] pt-4 mt-4">
                    <button
                      onClick={() => setShowEnhanceSettings(!showEnhanceSettings)}
                      className="flex items-center gap-2 text-sm text-white/70 hover:text-white transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[#0064E0] focus-visible:ring-offset-2 focus-visible:ring-offset-[#0a0c10] rounded"
                    >
                      {showEnhanceSettings ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      <span>Advanced Settings (optional)</span>
                      {(enhanceSettings.apiBaseUrl || enhanceSettings.apiKey) && (
                        <Badge className="ml-2 bg-emerald-500/20 text-emerald-300 border-emerald-500/30">Configured</Badge>
                      )}
                    </button>
                    <p className="text-xs text-white/70 mt-1">
                      Only needed for custom providers that LiteLLM doesn't auto-detect
                    </p>
                  </div>

                  {showEnhanceSettings && (
                    <div className="space-y-4 pt-2">
                      {/* API Base URL */}
                      <div>
                        <Label className="text-sm text-white/80 mb-1.5">API Base URL</Label>
                        <input
                          type="text"
                          value={enhanceSettings.apiBaseUrl}
                          onChange={(e) => setEnhanceSettings({ ...enhanceSettings, apiBaseUrl: e.target.value })}
                          placeholder="e.g., https://api.llama.com/compat/v1"
                          className="w-full px-3 py-2 text-sm border border-white/[0.1] bg-white/[0.05] text-white placeholder:text-white/50 rounded-lg focus:ring-2 focus:ring-[#0064E0] focus:border-[#0064E0] focus:outline-none transition-colors"
                          disabled={isOptimizing}
                        />
                        <div className="text-xs text-white/70 mt-1">
                          Override the API endpoint for self-hosted or custom providers
                        </div>
                      </div>

                      {/* API Key input */}
                      <div>
                        <Label className="text-sm text-white/80 mb-1.5">API Key</Label>
                        <div className="relative">
                          <input
                            type={showApiKey ? "text" : "password"}
                            value={enhanceSettings.apiKey}
                            onChange={(e) => setEnhanceSettings({ ...enhanceSettings, apiKey: e.target.value })}
                            placeholder="Your API key (if not set in environment)"
                            className="w-full px-3 py-2 pr-10 text-sm border border-white/[0.1] bg-white/[0.05] text-white placeholder:text-white/50 rounded-lg focus:ring-2 focus:ring-[#0064E0] focus:border-[#0064E0] focus:outline-none transition-colors"
                            disabled={isOptimizing}
                          />
                          <button
                            type="button"
                            onClick={() => setShowApiKey(!showApiKey)}
                            className="absolute right-2 top-1/2 -translate-y-1/2 text-white/70 hover:text-white transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[#0064E0] rounded"
                            aria-label={showApiKey ? "Hide API key" : "Show API key"}
                          >
                            {showApiKey ? <EyeOff size={16} aria-hidden="true" /> : <Eye size={16} aria-hidden="true" />}
                          </button>
                        </div>
                        <div className="text-xs text-white/70 mt-1">
                          Override the API key (usually set via environment variable)
                        </div>
                      </div>

                      {/* Clear settings button */}
                      {(enhanceSettings.apiBaseUrl || enhanceSettings.apiKey) && (
                        <button
                          onClick={() => {
                            setEnhanceSettings({ ...enhanceSettings, apiBaseUrl: '', apiKey: '' });
                            localStorage.setItem('enhanceSettings', JSON.stringify({ ...enhanceSettings, apiBaseUrl: '', apiKey: '' }));
                          }}
                          className="text-xs text-red-400 hover:text-red-300 flex items-center gap-1 transition-colors"
                        >
                          <X size={14} />
                          Clear advanced settings
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </div>

              <div className="flex items-center justify-center mt-6">
                <Button
                  onClick={handleOptimizePrompt}
                  disabled={isOptimizing || !prompt.trim() || !enhanceSettings.model.trim()}
                  variant="filled"
                  size="large"
                >
                  {isOptimizing ? (
                    <>
                      Enhancing...
                      <Loader2 className="animate-spin" />
                    </>
                  ) : (
                    <>
                      Enhance Prompt
                      <ArrowUp />
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}

          {/* Onboarding wizard - always rendered but hidden when not in migrate mode or when completed */}
          <div className={activeMode === 'migrate' && showWizard ? 'block' : 'hidden'}>
            <OnboardingWizard
              activeMode={activeMode as "migrate" | "enhance"}
              onComplete={handleWizardComplete}
            />
          </div>

          {/* Configuration summary - shown after wizard completion */}
          {activeMode === 'migrate' && wizardCompleted && !showWizard && (
            <div className="glass-panel p-6 max-w-4xl mx-auto">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-2xl font-bold text-white">Configuration Summary</h3>
                <Button
                  onClick={() => setShowWizard(true)}
                  variant="outlined"
                  size="medium"
                  className="border-white/[0.15] text-white hover:bg-white/[0.05]"
                >
                  Reconfigure
                </Button>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="font-medium text-white/70">Dataset Adapter:</span>
                  <p className="text-white">{config.datasetAdapter || 'Not selected'}</p>
                </div>
                <div>
                  <span className="font-medium text-white/70">Metrics:</span>
                  <p className="text-white">{config.metrics}</p>
                </div>
                <div>
                  <span className="font-medium text-white/70">Optimizer:</span>
                  <p className="text-white">{config.strategy}</p>
                </div>
                <div>
                  <span className="font-medium text-white/70">Model:</span>
                  <p className="text-white">{config.model}</p>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* Dataset Upload Dialog */}
      <Dialog open={showDatasetDialog} onOpenChange={setShowDatasetDialog}>
        <DialogContent className="max-w-2xl bg-[#0a0c10] border-white/[0.1]">
          <DialogHeader>
            <DialogTitle className="text-white">Manage Dataset</DialogTitle>
            <DialogDescription className="text-white/70">
              {uploadedDatasets.length > 0
                ? "View or replace your current dataset."
                : "Upload a JSON dataset file for optimization."}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6">
            {/* Current Dataset Section */}
            {uploadedDatasets.length > 0 && (
              <div className="border border-emerald-500/30 bg-emerald-500/10 rounded-xl p-4">
                <h3 className="text-lg font-semibold text-emerald-300 mb-2">Current Dataset</h3>
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <FileJson className="w-5 h-5 mr-2 text-emerald-400" />
                    <div>
                      <span className="font-medium text-white">{uploadedDatasets[0].filename}</span>
                      <span className="text-sm text-white/70 ml-2">
                        ({uploadedDatasets[0].total_records} records)
                      </span>
                    </div>
                  </div>
                  <Button
                    size="medium"
                    variant="outlinedDestructive"
                    onClick={() => handleDatasetDelete(uploadedDatasets[0].filename)}
                    className="border-red-500/30 text-red-400 hover:bg-red-500/10"
                  >
                    <Trash2 className="w-4 h-4 mr-1" />
                    Remove
                  </Button>
                </div>

                {/* Dataset Preview */}
                {uploadedDatasets[0].preview && uploadedDatasets[0].preview.length > 0 && (
                  <div className="mt-4">
                    <h4 className="text-sm font-semibold text-white/70 mb-2">Preview:</h4>
                    <div className="bg-black/40 border border-white/[0.1] rounded-lg p-3 max-h-40 overflow-y-auto">
                      <pre className="text-xs text-white/70 whitespace-pre-wrap font-mono">
                        {JSON.stringify(uploadedDatasets[0].preview[0], null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Upload Section */}
            <div>
              <h3 className="text-lg font-semibold text-white mb-3">
                {uploadedDatasets.length > 0 ? "Replace Dataset" : "Upload Dataset"}
              </h3>
              <div className="flex gap-3">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".json"
                  onChange={handleDatasetUpload}
                  className="hidden"
                  disabled={isUploadingDataset}
                />
                <Button
                  onClick={() => fileInputRef.current?.click()}
                  className={`w-full ${
                    uploadedDatasets.length > 0
                      ? "bg-white/[0.05] hover:bg-white/[0.1] text-white border border-white/[0.15]"
                      : "bg-white/[0.03] hover:bg-white/[0.08] text-white/80 border-2 border-dashed border-white/[0.2]"
                  }`}
                  disabled={isUploadingDataset}
                >
                  {isUploadingDataset ? (
                    <>
                      Uploading...
                      <Loader2 className="w-4 h-4 ml-2 animate-spin" />
                    </>
                  ) : (
                    <>
                      {uploadedDatasets.length > 0 ? "Choose New Dataset" : "Choose JSON File"}
                      <Upload className="w-4 h-4 ml-2" />
                    </>
                  )}
                </Button>
              </div>
              <p className="text-sm text-white/70 mt-2">
                {uploadedDatasets.length > 0
                  ? "Uploading a new dataset will replace the current one."
                  : "Upload a JSON dataset file for evaluation examples."}
              </p>
            </div>

            {/* No Dataset Message */}
            {uploadedDatasets.length === 0 && (
              <div className="text-center py-8 text-white/70 bg-white/[0.03] rounded-xl border border-white/[0.08]">
                <FileJson className="w-12 h-12 mx-auto mb-3 text-white/30" aria-hidden="true" />
                <p>No dataset uploaded yet</p>
                <p className="text-sm mt-1 text-white/70">You need a dataset to optimize prompts</p>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};
