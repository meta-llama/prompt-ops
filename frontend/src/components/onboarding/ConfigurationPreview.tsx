import React, { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import {
  Download,
  Eye,
  FileText,
  Copy,
  CheckCircle,
  Folder,
  Code,
  Settings
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface ConfigurationPreviewProps {
  wizardData: any;
  onComplete?: (configData: any) => void;
}

interface GeneratedConfig {
  success: boolean;
  config?: any;
  yaml?: string;
  error?: string;
}

export const ConfigurationPreview: React.FC<ConfigurationPreviewProps> = ({
  wizardData,
  onComplete
}) => {
  const [generatedConfig, setGeneratedConfig] = useState<GeneratedConfig | null>(null);
  const [loading, setLoading] = useState(false);
  const [projectName, setProjectName] = useState("my-prompt-project");
  const [copied, setCopied] = useState(false);
  const [showFullConfig, setShowFullConfig] = useState(false);
  const [creatingProject, setCreatingProject] = useState(false);
  const [projectCreated, setProjectCreated] = useState(false);

  useEffect(() => {
    generateConfig();
  }, [wizardData]);

  const generateConfig = async () => {
    setLoading(true);
    try {
      const response = await fetch("http://localhost:8000/generate-config", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          wizardData,
          projectName
        }),
      });

      const result = await response.json();
      setGeneratedConfig(result);
    } catch (error) {
      setGeneratedConfig({
        success: false,
        error: error instanceof Error ? error.message : "Failed to generate configuration"
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async () => {
    if (generatedConfig?.yaml) {
      await navigator.clipboard.writeText(generatedConfig.yaml);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownload = () => {
    if (generatedConfig?.yaml) {
      const blob = new Blob([generatedConfig.yaml], { type: "application/x-yaml" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${projectName}-config.yaml`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
  };

  const handleCreateProject = async () => {
    setCreatingProject(true);
    try {
      const response = await fetch("http://localhost:8000/create-project", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          wizardData,
          projectName
        }),
      });

      const result = await response.json();
      if (result.success) {
        setProjectCreated(true);
        onComplete?.(result);
      }
    } catch (error) {
      console.error("Failed to create project:", error);
    } finally {
      setCreatingProject(false);
    }
  };

  const getConfigSummary = () => {
    if (!generatedConfig?.config) return null;

    const config = generatedConfig.config;
    return {
      strategy: config.optimization?.strategy || "basic",
      model: config.model?.task_model || "Not specified",
      metric: config.metric?.class?.split('.').pop() || "Not specified",
      dataset: config.dataset?.path || "data/dataset.json"
    };
  };

  const summary = getConfigSummary();

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="text-center">
          <div className="inline-flex items-center space-x-2">
            <div className="animate-spin h-4 w-4 border-2 border-facebook-blue border-t-transparent rounded-full"></div>
            <span className="text-facebook-text">Generating configuration...</span>
          </div>
        </div>
      </div>
    );
  }

  if (generatedConfig?.error) {
    return (
      <Alert className="border-red-200 bg-red-50">
        <AlertDescription className="text-red-700">
          Error generating configuration: {generatedConfig.error}
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <h2 className="text-2xl font-bold text-facebook-text">Configuration Ready!</h2>
        <p className="text-facebook-text/70">
          Your llama-prompt-ops configuration has been generated based on your selections.
        </p>
      </div>

      {/* Project Name Input */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Folder className="w-5 h-5" />
            <span>Project Settings</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <Label htmlFor="projectName">Project Name</Label>
            <Input
              id="projectName"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              placeholder="my-prompt-project"
              className="border-facebook-border"
            />
            <p className="text-xs text-facebook-text/50">
              This will be used for the project folder and file names.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Configuration Summary */}
      {summary && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Settings className="w-5 h-5" />
              <span>Configuration Summary</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-facebook-text/70">Strategy</label>
                <div className="mt-1">
                  <Badge variant="outline" className="capitalize">
                    {summary.strategy}
                  </Badge>
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-facebook-text/70">Model</label>
                <div className="mt-1 text-sm text-facebook-text">
                  {summary.model.split('/').pop()}
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-facebook-text/70">Metric</label>
                <div className="mt-1 text-sm text-facebook-text">
                  {summary.metric}
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-facebook-text/70">Dataset</label>
                <div className="mt-1 text-sm text-facebook-text">
                  {summary.dataset}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Configuration Preview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Code className="w-5 h-5" />
              <span>Generated Configuration</span>
            </div>
            <div className="flex space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowFullConfig(!showFullConfig)}
                className="text-facebook-text border-facebook-border"
              >
                <Eye className="w-4 h-4 mr-2" />
                {showFullConfig ? "Hide" : "Preview"}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleCopy}
                className="text-facebook-text border-facebook-border"
              >
                {copied ? (
                  <CheckCircle className="w-4 h-4 mr-2" />
                ) : (
                  <Copy className="w-4 h-4 mr-2" />
                )}
                {copied ? "Copied!" : "Copy"}
              </Button>
            </div>
          </CardTitle>
          <CardDescription>
            config.yaml file for your llama-prompt-ops project
          </CardDescription>
        </CardHeader>
        <CardContent>
          {showFullConfig && generatedConfig?.yaml && (
            <div className="space-y-3">
              <Textarea
                value={generatedConfig.yaml}
                readOnly
                className="font-mono text-sm h-64 resize-none border-facebook-border"
              />
            </div>
          )}
          {!showFullConfig && (
            <div className="text-center py-8 text-facebook-text/50">
              <FileText className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>Click "Preview" to view the generated configuration</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row gap-3">
        <Button
          onClick={handleDownload}
          className="flex-1 bg-facebook-blue hover:bg-facebook-blue/90 text-white"
          disabled={!generatedConfig?.yaml}
        >
          <Download className="w-4 h-4 mr-2" />
          Download Config
        </Button>

        <Button
          onClick={handleCreateProject}
          className="flex-1 bg-green-600 hover:bg-green-700 text-white"
          disabled={!generatedConfig?.yaml || creatingProject}
        >
          {creatingProject ? (
            <>
              <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full mr-2"></div>
              Creating Project...
            </>
          ) : (
            <>
              <Folder className="w-4 h-4 mr-2" />
              Create Full Project
            </>
          )}
        </Button>
      </div>

      {/* Success Message */}
      {projectCreated && (
        <Alert className="border-green-200 bg-green-50">
          <CheckCircle className="w-4 h-4 text-green-600" />
          <AlertDescription className="text-green-700">
            Project created successfully! You can now download the files or use them with llama-prompt-ops.
          </AlertDescription>
        </Alert>
      )}

      {/* Next Steps */}
      <Card className="bg-blue-50 border-blue-200">
        <CardHeader>
          <CardTitle className="text-blue-900">Next Steps</CardTitle>
        </CardHeader>
        <CardContent className="text-blue-800 space-y-2">
          <ol className="list-decimal list-inside space-y-1 text-sm">
            <li>Download the configuration file or create a full project</li>
            <li>Install llama-prompt-ops: <code className="bg-blue-100 px-1 rounded">pip install llama-prompt-ops</code></li>
            <li>Add your API key to the .env file</li>
            <li>Customize your prompt in prompts/prompt.txt</li>
            <li>Add your dataset to data/dataset.json</li>
            <li>Run optimization: <code className="bg-blue-100 px-1 rounded">prompt-ops migrate --config config.yaml</code></li>
          </ol>
        </CardContent>
      </Card>
    </div>
  );
};
