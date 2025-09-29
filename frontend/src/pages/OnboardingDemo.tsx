import React, { useState } from "react";
import { OnboardingWizard } from "../components/onboarding/OnboardingWizard";
import { Button } from "@/components/ui/button";

const OnboardingDemo = () => {
  const [activeMode, setActiveMode] = useState<"enhance" | "migrate">(
    "migrate"
  );
  const [showWizard, setShowWizard] = useState(true);
  const [completedConfig, setCompletedConfig] = useState<any>(null);

  const handleWizardComplete = (config: any) => {
    console.log("Wizard completed with config:", config);
    setCompletedConfig(config);
    setShowWizard(false);
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
          <div className="flex justify-center gap-4">
            <Button
              onClick={() => (window.location.href = "/")}
              variant="outline"
              className="text-sm"
            >
              Back to Main App
            </Button>
          </div>
        </div>

        {/* Demo Content */}
        <div className="w-full">
          {/* Wizard Demo */}
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-2xl font-semibold mb-4">
                Step-by-Step Wizard
              </h2>
              <p className="text-gray-600 mb-6">
                This wizard guides new users through the setup process with
                clear steps and validation.
              </p>


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
          </div>
        </div>
      </div>
    </div>
  );
};

export default OnboardingDemo;
