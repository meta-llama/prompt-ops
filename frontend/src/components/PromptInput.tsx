import React, { useState, useContext, useRef } from 'react';
import { Badge } from '@/components/ui/badge';
import { ArrowUp, Plus, Loader2, Copy, Check } from 'lucide-react';
import { AppContext } from '../context/AppContext';
import { OptimizationProgress, OptimizationStep } from './OptimizationProgress';
import { OptimizationResults } from './OptimizationResults';

export const PromptInput = () => {
  const [prompt, setPrompt] = useState('');
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [optimizedPrompt, setOptimizedPrompt] = useState('');
  const [originalPrompt, setOriginalPrompt] = useState('');
  const [showResults, setShowResults] = useState(false);
  const [copySuccess, setCopySuccess] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const { activeMode, setIsModeLocked } = useContext(AppContext)!;

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

  const handleOptimizePrompt = async () => {
    if (!prompt.trim() || isOptimizing) return;

    // Lock the mode selection when optimization starts
    setIsModeLocked(true);
    setIsOptimizing(true);
    setShowResults(false);
    setOriginalPrompt(prompt);
    setCurrentStep(0);

    // Simulate the optimization steps with delays
    const simulateSteps = async () => {
      // Step 1: Analyzing original prompt
      await new Promise(resolve => setTimeout(resolve, 1500));
      setCurrentStep(1);

      // Step 2: Processing dataset
      await new Promise(resolve => setTimeout(resolve, 1500));
      setCurrentStep(2);

      // Step 3: Generating optimized versions
      await new Promise(resolve => setTimeout(resolve, 2000));
      setCurrentStep(3);

      // Step 4: Evaluating performance
      await new Promise(resolve => setTimeout(resolve, 1500));
    };

    try {
      // Start the simulation
      await simulateSteps();

      // Connect to FastAPI backend with the appropriate endpoint based on mode
      const endpoint = activeMode === 'enhance' ? 'enhance-prompt' : 'migrate-prompt';

      // Only include configuration for migrate-prompt endpoint
      const requestBody = activeMode === 'enhance'
        ? { prompt }
        : {
            prompt,
            config: {
              // These would ideally come from UI form inputs
              provider: "openrouter",
              taskModel: "meta-llama/llama-3-70b-instruct",
              proposerModel: "meta-llama/llama-3-70b-instruct",
              optimizer: "MiPro", // One of: MiPro, GEPA, Infer
              optimizationLevel: "basic", // One of: basic, intermediate, advanced
              dataset: "Q&A", // One of: Q&A, RAG, Custom
              metrics: "Exact Match", // One of: Exact Match, Standard JSON, Custom
              useLlamaTips: true,
              // Add openrouter API key if provided in UI
              // openrouterApiKey: "your-api-key-here"
            }
          };

      const response = await fetch(`http://localhost:8000/api/${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error('Failed to optimize prompt');
      }

      const data = await response.json();
      setOptimizedPrompt(data.optimizedPrompt);

      // Show results instead of updating the prompt directly
      setShowResults(true);
    } catch (error) {
      console.error('Error optimizing prompt:', error);
      // You could add error handling UI here
    } finally {
      setIsOptimizing(false);
    }
  };

  return (
    <div className="relative max-w-4xl mx-auto">
      {showResults ? (
        <div className="mt-8">
          <OptimizationResults
            originalPrompt={originalPrompt}
            optimizedPrompt={optimizedPrompt}
            onCopy={handleCopyToClipboard}
          />
          <div className="flex justify-center mt-8 gap-4">
            {/* <button
              onClick={() => {
                setShowResults(false);
                setPrompt(optimizedPrompt); // Update the prompt with the optimized version
              }}
              className="bg-facebook-blue hover:bg-facebook-blue-dark text-white px-8 py-3 rounded-xl font-medium transition-all duration-300 shadow-lg hover:shadow-facebook-blue/25 transform hover:scale-105"
            >
              Continue Editing
            </button> */}
            <button
              onClick={() => {
                setPrompt('');
                setOptimizedPrompt('');
                setShowResults(false);
                setIsModeLocked(false); // Unlock mode selection when starting new
              }}
              className="bg-facebook-gray hover:bg-facebook-border text-facebook-text border border-facebook-border px-8 py-3 rounded-xl font-medium transition-all duration-300 shadow-lg transform hover:scale-105"
            >
              Start New
            </button>
          </div>
        </div>
      ) : isOptimizing ? (
        <div className="bg-white/90 backdrop-blur-xl rounded-2xl p-8 shadow-xl border border-facebook-border text-center">
          <h2 className="text-3xl font-bold mb-2 text-facebook-text">Run Optimization</h2>
          <p className="text-facebook-text/70 mb-8">Ready to optimize your prompt for Llama models. This process typically takes 5-10 minutes.</p>

          <div className="flex justify-center mb-8">
            <div className="w-20 h-20">
              <div className="w-full h-full rounded-full animate-spin"
                style={{
                  background: 'conic-gradient(from 0deg, transparent, hsl(var(--facebook-blue) / 0) 10%, hsl(var(--facebook-blue) / 0.2) 20%, hsl(var(--facebook-blue) / 0.4) 30%, hsl(var(--facebook-blue) / 0.8) 40%, hsl(var(--facebook-blue)) 50%, hsl(var(--facebook-blue) / 0) 60%)',
                  borderRadius: '50%',
                  boxShadow: '0 0 20px hsl(var(--facebook-blue) / 0.3)'
                }}>
              </div>
            </div>
          </div>

          <h3 className="text-2xl font-semibold mb-2 text-facebook-text">Optimizing Prompt...</h3>
          <p className="text-facebook-text/70 mb-8">This may take several minutes. Please don't close this window.</p>

          <OptimizationProgress steps={optimizationSteps} />
        </div>
      ) : (
        <div className="relative bg-white/90 backdrop-blur-xl rounded-2xl p-6 shadow-xl border border-facebook-border">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Your prompt..."
            disabled={isOptimizing}
            className={`w-full h-28 p-0 text-xl text-facebook-text bg-transparent placeholder:text-facebook-text/50 border-none outline-none resize-none leading-relaxed ${isOptimizing ? 'opacity-75' : ''}`}
          />

          <div className="flex items-center justify-between mt-6">
            <div className="flex items-center gap-3">
              <Badge
                className="bg-facebook-gray/50 text-facebook-text hover:bg-facebook-gray px-4 py-2 rounded-xl text-sm font-medium backdrop-blur-sm border border-facebook-border"
              >
                Add Dataset
              </Badge>
            </div>

            <button
              onClick={handleOptimizePrompt}
              disabled={isOptimizing || !prompt.trim()}
              className={`bg-facebook-blue hover:bg-facebook-blue-dark text-white p-3 rounded-xl shadow-lg hover:shadow-facebook-blue/25 transition-all duration-300 transform ${!isOptimizing && prompt.trim() ? 'hover:scale-110 hover:-translate-y-1' : 'opacity-75 cursor-not-allowed'}`}
            >
              {isOptimizing ? <Loader2 size={20} className="animate-spin" /> : <ArrowUp size={20} />}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
