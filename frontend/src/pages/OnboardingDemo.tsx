import React, { useState } from 'react';
import { OnboardingWizard } from '../components/onboarding/OnboardingWizard';
import { SimplePromptInput } from '../components/optimization/SimplePromptInput';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AppContext } from '../context/AppContext';

const OnboardingDemo = () => {
  const [activeMode, setActiveMode] = useState<'enhance' | 'migrate'>('migrate');
  const [showWizard, setShowWizard] = useState(true);
  const [completedConfig, setCompletedConfig] = useState<any>(null);

  const handleWizardComplete = (config: any) => {
    console.log('Wizard completed with config:', config);
    setCompletedConfig(config);
    setShowWizard(false);
  };

  const handleSimpleOptimize = (prompt: string) => {
    console.log('Optimizing prompt:', prompt);
    alert(`Optimizing: "${prompt}"\n\nThis is a demo - check console for details.`);
  };

  const resetDemo = () => {
    setShowWizard(true);
    setCompletedConfig(null);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4">
        {/* Demo Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Onboarding Improvements Demo
          </h1>
          <p className="text-lg text-gray-600 mb-4">
            Test the new simplified interface and onboarding flow
          </p>
          <div className="flex justify-center gap-4">
            <Button
              onClick={resetDemo}
              variant="outline"
              className="text-sm"
            >
              Reset Demo
            </Button>
            <Button
              onClick={() => window.location.href = '/'}
              variant="outline"
              className="text-sm"
            >
              Back to Main App
            </Button>
          </div>
        </div>

        {/* Demo Content */}
        <Tabs defaultValue="wizard" className="w-full">
          <TabsList className="grid w-full max-w-md mx-auto grid-cols-2 mb-8">
            <TabsTrigger value="wizard">Onboarding Wizard</TabsTrigger>
            <TabsTrigger value="simple">Simple Interface</TabsTrigger>
          </TabsList>

          {/* Wizard Demo */}
          <TabsContent value="wizard" className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-2xl font-semibold mb-4">Step-by-Step Wizard</h2>
              <p className="text-gray-600 mb-6">
                This wizard guides new users through the setup process with clear steps and validation.
              </p>

              {/* Mode Selection */}
              <div className="mb-6">
                {/* <label className="text-sm font-medium text-gray-700 mb-2 block">
                  Select Mode:
                </label> */}
                <div className="flex gap-2">
                  {/* <Button
                    onClick={() => setActiveMode('enhance')}
                    variant={activeMode === 'enhance' ? 'default' : 'outline'}
                    className="flex-1"
                  >
                    Enhance
                  </Button> */}
                  <Button
                    onClick={() => setActiveMode('migrate')}
                    variant={activeMode === 'migrate' ? 'default' : 'outline'}
                    className="flex-1"
                  >
                    Migrate
                  </Button>
                </div>
              </div>

              {/* Wizard or Completion Message */}
              {showWizard ? (
                <OnboardingWizard
                  activeMode={activeMode}
                  onComplete={handleWizardComplete}
                />
              ) : (
                <div className="text-center py-12 bg-green-50 rounded-lg border border-green-200">
                  <h3 className="text-xl font-semibold text-green-800 mb-2">
                    Wizard Completed! 🎉
                  </h3>
                  <p className="text-green-700 mb-4">
                    Configuration saved successfully.
                  </p>
                  <div className="bg-white p-4 rounded border border-green-300 max-w-md mx-auto text-left">
                    <pre className="text-sm text-gray-700 overflow-auto">
                      {JSON.stringify(completedConfig, null, 2)}
                    </pre>
                  </div>
                  <Button
                    onClick={resetDemo}
                    className="mt-4 bg-green-600 hover:bg-green-700"
                  >
                    Try Again
                  </Button>
                </div>
              )}
            </div>
          </TabsContent>

          {/* Simple Interface Demo */}
          <TabsContent value="simple" className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-2xl font-semibold mb-4">Simplified Interface</h2>
              <p className="text-gray-600 mb-6">
                This is the clean, minimal interface based on your mockup with collapsible configuration.
              </p>

              {/* Mode Toggle for Simple Interface */}
              <div className="max-w-4xl mx-auto mb-8">
                <div className="flex justify-center mb-6">
                  <div className="bg-white p-1 rounded-xl shadow-md border-2 border-gray-300">
                    <div className="flex gap-1">
                      <Button
                        onClick={() => setActiveMode('enhance')}
                        variant="ghost"
                        className={`px-6 py-2 ${
                          activeMode === 'enhance'
                            ? 'bg-orange-400 text-white hover:bg-orange-400'
                            : 'text-gray-700'
                        }`}
                      >
                        Enhance
                      </Button>
                      <Button
                        onClick={() => setActiveMode('migrate')}
                        variant="ghost"
                        className={`px-6 py-2 ${
                          activeMode === 'migrate'
                            ? 'bg-orange-400 text-white hover:bg-orange-400'
                            : 'text-gray-700'
                        }`}
                      >
                        Migrate
                      </Button>
                    </div>
                  </div>
                </div>

                <AppContext.Provider value={{
                  activeMode,
                  setActiveMode: (mode: string) => setActiveMode(mode as 'enhance' | 'migrate'),
                  isModeLocked: false,
                  setIsModeLocked: () => {}
                }}>
                  <SimplePromptInput
                    onOptimize={handleSimpleOptimize}
                    isOptimizing={false}
                  />
                </AppContext.Provider>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default OnboardingDemo;
