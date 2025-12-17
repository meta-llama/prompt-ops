import React, { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import {
  Check,
  Settings,
  Zap,
  Shield,
  Globe,
  Server,
  Eye,
  EyeOff,
  AlertCircle,
  CheckCircle,
  Loader2,
  Plus,
  Trash2,
  ExternalLink,
  Cloud,
  DollarSign,
  Clock,
  Brain,
  Target,
  Split,
  Merge,
} from "lucide-react";
import { RoleBadge, RoleType } from "@/components/ui/role-badge";
import { InfoBox } from "@/components/ui/info-box";
import { SectionTitle } from "@/components/ui/section-title";

interface ProviderConfig {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  category: "cloud" | "local" | "enterprise";
  pricing: "free" | "paid" | "usage";
  setup_difficulty: "easy" | "medium" | "hard";
  api_base: string;
  model_prefix: string;
  popular_models: string[];
  pros: string[];
  cons: string[];
  docs_url: string;
  requires_signup: boolean;
}

interface ModelConfig {
  id: string; // Unique identifier for this configuration
  provider_id: string;
  model_name: string;
  role: "target" | "optimizer" | "both";
  api_key?: string;
  api_base?: string;
  temperature: number;
  max_tokens: number;
  // Custom provider fields
  custom_provider_name?: string;
  model_prefix?: string;
  auth_method?: "api_key" | "bearer_token" | "custom_headers";
  custom_headers?: Record<string, string>;
}

interface ModelProviderSelectorProps {
  useCase: string;
  fieldMappings: Record<string, string>;
  onConfigurationChange: (configs: ModelConfig[]) => void;
}

const PROVIDER_CONFIGS: ProviderConfig[] = [
  {
    id: "openrouter",
    name: "OpenRouter",
    description: "Access 200+ models from multiple providers through one API",
    icon: <Globe className="w-6 h-6" />,
    category: "cloud",
    pricing: "usage",
    setup_difficulty: "easy",
    api_base: "https://openrouter.ai/api/v1",
    model_prefix: "openrouter/",
    popular_models: [
      "meta-llama/llama-3.1-8b-instruct",
      "meta-llama/llama-3.3-70b-instruct",
      "anthropic/claude-3.5-sonnet",
      "openai/gpt-4o",
    ],
    pros: ["Huge model selection", "Competitive pricing", "Easy setup"],
    cons: ["Usage-based pricing"],
    docs_url: "https://openrouter.ai/docs",
    requires_signup: true,
  },

  {
    id: "vllm",
    name: "vLLM (Local)",
    description: "Run models locally with fast inference engine",
    icon: <Server className="w-6 h-6" />,
    category: "local",
    pricing: "free",
    setup_difficulty: "medium",
    api_base: "http://localhost:8000/v1",
    model_prefix: "hosted_vllm/",
    popular_models: [
      "meta-llama/Llama-3.1-8B-Instruct",
      "microsoft/DialoGPT-medium",
      "google/flan-t5-large",
    ],
    pros: ["Local Inference", "Data privacy", "Full control"],
    cons: ["Requires setup", "Hardware dependent", "Local only"],
    docs_url: "https://docs.vllm.ai/",
    requires_signup: false,
  },
  {
    id: "nvidia_nim",
    name: "NVIDIA NIM",
    description: "Optimized containers for NVIDIA GPUs",
    icon: <Shield className="w-6 h-6" />,
    category: "enterprise",
    pricing: "free",
    setup_difficulty: "hard",
    api_base: "http://localhost:8000/v1",
    model_prefix: "openai/",
    popular_models: [
      "meta/llama-3.1-8b-instruct",
      "microsoft/phi-3-mini-4k-instruct",
      "mistralai/mixtral-8x7b-instruct-v0.1",
    ],
    pros: ["GPU optimized", "Enterprise grade", "High performance"],
    cons: ["Requires NVIDIA NIMS", "Complex setup", "Enterprise focused"],
    docs_url: "https://docs.nvidia.com/nim/",
    requires_signup: true,
  },
  {
    id: "custom",
    name: "Custom Provider",
    description:
      "Configure your own API endpoint (LiteLLM, Azure AI Studio, etc.)",
    icon: <Settings className="w-6 h-6" />,
    category: "enterprise",
    pricing: "usage",
    setup_difficulty: "medium",
    api_base: "",
    model_prefix: "",
    popular_models: [
      "your-model-name",
      "azure_ai/command-r-plus",
      "azure_ai/mistral-large-latest",
      "custom/your-model",
    ],
    pros: ["Full control", "Any provider", "Custom endpoints"],
    cons: ["Requires configuration", "Manual setup", "Provider dependent"],
    docs_url: "https://docs.litellm.ai/docs/providers",
    requires_signup: false,
  },
];

const ROLE_DESCRIPTIONS = {
  target:
    "🎯 Target Model - The model you're optimizing FOR (where your prompt will be deployed in production)",
  optimizer:
    "🧠 Optimizer Model - The AI that generates improved prompt variations during optimization",
  both: "🔄 Dual Role - Single model handles both optimization and deployment",
};

export const ModelProviderSelector: React.FC<ModelProviderSelectorProps> = ({
  useCase,
  fieldMappings,
  onConfigurationChange,
}) => {
  const [selectedProviders, setSelectedProviders] = useState<string[]>([]);
  const [configurations, setConfigurations] = useState<ModelConfig[]>([]);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [testingConnections, setTestingConnections] = useState<
    Record<string, boolean>
  >({});
  const [connectionStatus, setConnectionStatus] = useState<
    Record<string, "success" | "error" | "untested">
  >({});
  const [showApiKeys, setShowApiKeys] = useState<Record<string, boolean>>({});

  // Smart defaults based on use case
  useEffect(() => {
    if (useCase && selectedProviders.length === 0) {
      // Auto-select OpenRouter for all use cases
      setSelectedProviders(["openrouter"]);
      // Still show advanced options for custom use case
      if (useCase === "custom") {
        setShowAdvanced(true);
      }
    }
  }, [useCase, selectedProviders.length]);

  // Initialize configurations when providers change
  useEffect(() => {
    setConfigurations((prevConfigs) => {
      // Keep existing configurations for selected providers
      const existingConfigs = prevConfigs.filter((config) =>
        selectedProviders.includes(config.provider_id)
      );

      // Add default configurations for newly selected providers
      const newConfigs: ModelConfig[] = [...existingConfigs];

      selectedProviders.forEach((providerId) => {
        const provider = PROVIDER_CONFIGS.find((p) => p.id === providerId);
        if (!provider) return;

        // Check if we already have any configuration for this provider
        const hasExistingConfig = existingConfigs.some(
          (config) => config.provider_id === providerId
        );

        // Only add default configuration if none exists for this provider
        if (!hasExistingConfig) {
          // Determine the best default role for this provider
          const globalTarget = newConfigs.find(
            (c) => c.role === "target" || c.role === "both"
          );
          const globalOptimizer = newConfigs.find(
            (c) => c.role === "optimizer" || c.role === "both"
          );
          const globalBoth = newConfigs.find((c) => c.role === "both");

          let defaultRole: "target" | "optimizer" | "both" = "both";

          // If this is the first provider and no other configs exist, use "both"
          if (newConfigs.length === 0) {
            defaultRole = "both";
          }
          // If someone already has "both", don't add anything (let user manually add if needed)
          else if (globalBoth) {
            return; // Skip adding default config
          }
          // If we need a target and this provider is suitable
          else if (
            !globalTarget &&
            (provider.category === "local" ||
              provider.category === "enterprise")
          ) {
            defaultRole = "target";
          }
          // If we need an optimizer and this provider is suitable
          else if (!globalOptimizer && provider.category === "cloud") {
            defaultRole = "optimizer";
          }
          // Otherwise, let user choose manually
          else {
            return; // Skip adding default config
          }

          newConfigs.push({
            id: `${providerId}-${Date.now()}`,
            provider_id: providerId,
            model_name: provider.popular_models[0],
            role: defaultRole,
            api_base: provider.api_base,
            api_key: "",
            temperature: 0.0,
            max_tokens: 4096,
            // Custom provider fields
            custom_provider_name: providerId === "custom" ? "" : undefined,
            model_prefix: providerId === "custom" ? "" : provider.model_prefix,
            auth_method: providerId === "custom" ? "api_key" : undefined,
            custom_headers: providerId === "custom" ? {} : undefined,
          });
        }
      });

      return newConfigs;
    });
  }, [selectedProviders]);

  // Notify parent of configuration changes
  useEffect(() => {
    onConfigurationChange(configurations);
  }, [configurations]); // Remove onConfigurationChange from dependencies to prevent infinite loop

  const handleProviderToggle = (providerId: string) => {
    setSelectedProviders((prev) => {
      if (prev.includes(providerId)) {
        // Remove provider
        return prev.filter((id) => id !== providerId);
      } else {
        // Add provider, but limit to 2 providers max
        if (prev.length >= 2) {
          alert(
            "Maximum 2 providers allowed. You only need one for both roles, or two for separate target/optimizer models."
          );
          return prev;
        }
        return [...prev, providerId];
      }
    });
  };

  const handleConfigChange = (
    configId: string,
    field: keyof ModelConfig,
    value: any
  ) => {
    setConfigurations((prevConfigs) => {
      const newConfigs = prevConfigs.map((config) =>
        config.id === configId ? { ...config, [field]: value } : config
      );
      return newConfigs;
    });
  };

  const addConfiguration = (
    providerId: string,
    role: "target" | "optimizer"
  ) => {
    const provider = PROVIDER_CONFIGS.find((p) => p.id === providerId);
    if (!provider) return;

    // Check if this role is already filled globally
    const existingTargetConfig = configurations.find(
      (c) => c.role === "target" || c.role === "both"
    );
    const existingOptimizerConfig = configurations.find(
      (c) => c.role === "optimizer" || c.role === "both"
    );

    if (role === "target" && existingTargetConfig) {
      alert(
        "Target model is already configured. Remove the existing target configuration first."
      );
      return;
    }

    if (role === "optimizer" && existingOptimizerConfig) {
      alert(
        "Optimizer model is already configured. Remove the existing optimizer configuration first."
      );
      return;
    }

    const newConfig: ModelConfig = {
      id: `${providerId}-${role}-${Date.now()}`,
      provider_id: providerId,
      model_name: provider.popular_models[0],
      role: role,
      api_base: provider.api_base,
      api_key: "",
      temperature: 0.0,
      max_tokens: 4096,
      // Custom provider fields
      custom_provider_name: providerId === "custom" ? "" : undefined,
      model_prefix: providerId === "custom" ? "" : provider.model_prefix,
      auth_method: providerId === "custom" ? "api_key" : undefined,
      custom_headers: providerId === "custom" ? {} : undefined,
    };

    setConfigurations((prevConfigs) => [...prevConfigs, newConfig]);
  };

  const removeConfiguration = (configId: string) => {
    setConfigurations((prevConfigs) =>
      prevConfigs.filter((config) => config.id !== configId)
    );
  };

  // Split a "both" configuration into separate target and optimizer configs
  const splitConfiguration = (configId: string) => {
    const config = configurations.find((c) => c.id === configId);
    if (!config || config.role !== "both") return;

    const provider = PROVIDER_CONFIGS.find((p) => p.id === config.provider_id);
    if (!provider) return;

    // Create target config
    const targetConfig: ModelConfig = {
      ...config,
      id: `${config.provider_id}-target-${Date.now()}`,
      role: "target",
    };

    // Create optimizer config with potentially different model
    const optimizerConfig: ModelConfig = {
      ...config,
      id: `${config.provider_id}-optimizer-${Date.now() + 1}`,
      role: "optimizer",
      // Default to a more powerful model for optimizer if available
      model_name:
        provider.popular_models.find(
          (model) =>
            model.includes("claude-3.5") ||
            model.includes("gpt-4") ||
            model.includes("70b")
        ) || config.model_name,
    };

    setConfigurations((prevConfigs) =>
      prevConfigs
        .map((c) => (c.id === configId ? targetConfig : c))
        .concat([optimizerConfig])
    );
  };

  // Merge separate target and optimizer configs from same provider into "both"
  const mergeConfigurations = (providerId: string) => {
    const providerConfigs = configurations.filter(
      (c) => c.provider_id === providerId
    );
    const targetConfig = providerConfigs.find((c) => c.role === "target");
    const optimizerConfig = providerConfigs.find((c) => c.role === "optimizer");

    if (!targetConfig || !optimizerConfig) return;

    // Create merged config based on target config
    const mergedConfig: ModelConfig = {
      ...targetConfig,
      role: "both",
    };

    setConfigurations((prevConfigs) =>
      prevConfigs
        .filter((c) => c.id !== targetConfig.id && c.id !== optimizerConfig.id)
        .concat([mergedConfig])
    );
  };

  // Change role of a configuration
  const changeConfigRole = (
    configId: string,
    newRole: "target" | "optimizer" | "both"
  ) => {
    // Check if the new role is already taken
    const { hasTarget, hasOptimizer } = getRoleStatus();

    if (newRole === "target" && hasTarget) {
      const existingTarget = configurations.find(
        (c) => (c.role === "target" || c.role === "both") && c.id !== configId
      );
      if (existingTarget) {
        alert(
          "Target role is already assigned. Remove the existing target configuration first."
        );
        return;
      }
    }

    if (newRole === "optimizer" && hasOptimizer) {
      const existingOptimizer = configurations.find(
        (c) =>
          (c.role === "optimizer" || c.role === "both") && c.id !== configId
      );
      if (existingOptimizer) {
        alert(
          "Optimizer role is already assigned. Remove the existing optimizer configuration first."
        );
        return;
      }
    }

    if (newRole === "both" && (hasTarget || hasOptimizer)) {
      const existing = configurations.find(
        (c) =>
          (c.role === "target" ||
            c.role === "optimizer" ||
            c.role === "both") &&
          c.id !== configId
      );
      if (existing) {
        alert(
          "Cannot set to 'both' when other roles are already assigned. Remove other configurations first."
        );
        return;
      }
    }

    setConfigurations((prevConfigs) =>
      prevConfigs.map((config) =>
        config.id === configId ? { ...config, role: newRole } : config
      )
    );
  };

  // Helper to compute available roles for a config
  const getAvailableRolesForConfig = (currentRole: RoleType, configId: string): RoleType[] => {
    const { hasTarget, hasOptimizer } = getRoleStatus();

    return (["target", "optimizer", "both"] as RoleType[]).filter((r) => {
      if (r === currentRole) return false;

      // Check if this role is taken by another config (not the current one)
      const currentConfig = configurations.find(c => c.id === configId);
      const otherConfigs = configurations.filter(c => c.id !== configId);

      const otherHasTarget = otherConfigs.some(c => c.role === "target" || c.role === "both");
      const otherHasOptimizer = otherConfigs.some(c => c.role === "optimizer" || c.role === "both");

      if (r === "target" && otherHasTarget) return false;
      if (r === "optimizer" && otherHasOptimizer) return false;
      if (r === "both" && (otherHasTarget || otherHasOptimizer)) return false;

      return true;
    });
  };

  // Interactive role badge wrapper that handles role changes
  const InteractiveRoleBadge = ({
    role,
    configId,
    className = "",
  }: {
    role: RoleType;
    configId: string;
    className?: string;
  }) => {
    const availableRoles = getAvailableRolesForConfig(role, configId);

    return (
      <RoleBadge
        role={role}
        interactive
        availableRoles={availableRoles}
        onRoleChange={(newRole) => changeConfigRole(configId, newRole)}
        className={className}
      />
    );
  };

  // Helper functions for role management
  const getRoleStatus = () => {
    const hasTarget = configurations.some(
      (c) => c.role === "target" || c.role === "both"
    );
    const hasOptimizer = configurations.some(
      (c) => c.role === "optimizer" || c.role === "both"
    );
    const hasBoth = configurations.some((c) => c.role === "both");

    return { hasTarget, hasOptimizer, hasBoth };
  };

  const canAddRole = (providerId: string, role: "target" | "optimizer") => {
    const { hasTarget, hasOptimizer, hasBoth } = getRoleStatus();
    const providerConfigs = configurations.filter(
      (c) => c.provider_id === providerId
    );
    const providerHasRole = providerConfigs.some(
      (c) => c.role === role || c.role === "both"
    );

    // If any config has "both" role, can't add anything else
    if (hasBoth) return false;

    // If this provider already has this role, can't add another
    if (providerHasRole) return false;

    // If role is globally filled, can't add another
    if (role === "target" && hasTarget) return false;
    if (role === "optimizer" && hasOptimizer) return false;

    return true;
  };

  const getAvailableRoles = (providerId: string) => {
    const canAddTarget = canAddRole(providerId, "target");
    const canAddOptimizer = canAddRole(providerId, "optimizer");
    const { hasTarget, hasOptimizer, hasBoth } = getRoleStatus();
    const providerConfigs = configurations.filter(
      (c) => c.provider_id === providerId
    );

    // If this provider has no configs and no global "both" exists, can suggest "both"
    const canAddBoth =
      providerConfigs.length === 0 && !hasBoth && !hasTarget && !hasOptimizer;

    return { canAddTarget, canAddOptimizer, canAddBoth };
  };

  const testConnection = async (config: ModelConfig) => {
    const configKey = `${config.provider_id}-${config.role}-${config.id}`;
    setTestingConnections((prev) => ({ ...prev, [configKey]: true }));

    try {
      // Basic validation first
      const hasApiKey = config.api_key && config.api_key.length > 0;
      const provider = PROVIDER_CONFIGS.find(
        (p) => p.id === config.provider_id
      );

      // Check if authentication is required
      const requiresAuth =
        provider?.requires_signup || config.provider_id === "custom";

      if (
        requiresAuth &&
        !hasApiKey &&
        config.auth_method !== "custom_headers"
      ) {
        throw new Error("Authentication required - please provide an API key");
      }

      // For custom headers, check if headers are provided
      if (
        config.auth_method === "custom_headers" &&
        (!config.custom_headers ||
          Object.keys(config.custom_headers).length === 0)
      ) {
        throw new Error("Custom headers required");
      }

      // For custom providers, check if required fields are filled
      if (config.provider_id === "custom") {
        if (
          !config.api_base ||
          !config.model_name ||
          !config.custom_provider_name
        ) {
          throw new Error(
            "Please fill in all required fields for custom provider"
          );
        }
      }

      // Perform actual API test
      await performActualAPITest(config);

      setConnectionStatus((prev) => ({ ...prev, [configKey]: "success" }));
    } catch (error) {
      console.error("Connection test failed:", error);
      setConnectionStatus((prev) => ({
        ...prev,
        [configKey]: "error",
      }));

      // Show user-friendly error message
      const errorMessage =
        error instanceof Error ? error.message : "Connection test failed";
      // Don't duplicate "Connection test failed" if the error message is already user-friendly
      const isUserFriendlyError =
        error instanceof Error &&
        (error.message.includes("API key") ||
          error.message.includes("Access denied") ||
          error.message.includes("Invalid request") ||
          error.message.includes("Provider server error") ||
          error.message.includes("Connection failed") ||
          error.message.includes("Network error") ||
          error.message.includes("timeout"));

      const displayMessage = isUserFriendlyError
        ? errorMessage
        : `Connection test failed: ${errorMessage}`;
      alert(displayMessage);
    } finally {
      setTestingConnections((prev) => ({ ...prev, [configKey]: false }));
    }
  };

  const performActualAPITest = async (config: ModelConfig) => {
    const provider = PROVIDER_CONFIGS.find((p) => p.id === config.provider_id);
    let apiUrl = config.api_base || provider?.api_base || "";

    // Ensure URL ends with proper path
    if (!apiUrl.endsWith("/")) {
      apiUrl += "/";
    }

    // For better API key validation, we'll make a small completion request instead of just checking models
    // This actually validates the API key works for the intended purpose
    const testUrl = `${apiUrl}chat/completions`;

    // Prepare headers
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };

    // Add authentication
    if (config.auth_method === "custom_headers" && config.custom_headers) {
      Object.assign(headers, config.custom_headers);
    } else if (config.auth_method === "bearer_token" && config.api_key) {
      headers["Authorization"] = `Bearer ${config.api_key}`;
    } else if (config.api_key) {
      // Default to Authorization header for most providers
      headers["Authorization"] = `Bearer ${config.api_key}`;
    }

    // Add provider-specific headers
    if (config.provider_id === "openrouter") {
      headers["HTTP-Referer"] = window.location.origin;
      headers["X-Title"] = "Prompt Ops";
    }

    // Prepare test request body - minimal completion request
    const testBody = {
      model: config.model_name,
      messages: [
        {
          role: "user",
          content: "test",
        },
      ],
      max_tokens: 1,
      temperature: 0,
      stream: false,
    };

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 second timeout

    try {
      console.log(
        `Testing connection to ${config.provider_id} with URL: ${testUrl}`
      );
      console.log("Headers:", headers);
      console.log("Body:", testBody);

      const response = await fetch(testUrl, {
        method: "POST",
        headers,
        body: JSON.stringify(testBody),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      console.log(`Response status: ${response.status}`);
      console.log(
        "Response headers:",
        Object.fromEntries(response.headers.entries())
      );

      if (!response.ok) {
        // Get the response text for better error messages
        let errorText = "";
        try {
          const errorData = await response.json();
          errorText =
            errorData.error?.message ||
            errorData.message ||
            JSON.stringify(errorData);
        } catch {
          errorText = await response.text();
        }

        console.log("Error response:", errorText);

        if (response.status === 401) {
          // Make 401 errors more user-friendly
          let friendlyMessage = "Incorrect or invalid API key";
          if (errorText.toLowerCase().includes("no auth")) {
            friendlyMessage =
              "API key is missing or invalid - please check your key";
          } else if (errorText.toLowerCase().includes("unauthorized")) {
            friendlyMessage = "API key is incorrect or doesn't have access";
          } else if (errorText.toLowerCase().includes("expired")) {
            friendlyMessage = "API key has expired - please generate a new one";
          } else if (
            errorText.toLowerCase().includes("quota") ||
            errorText.toLowerCase().includes("limit")
          ) {
            friendlyMessage = "API quota exceeded or rate limit reached";
          }
          throw new Error(friendlyMessage);
        } else if (response.status === 403) {
          let friendlyMessage = "Access denied";
          if (
            errorText.toLowerCase().includes("quota") ||
            errorText.toLowerCase().includes("limit")
          ) {
            friendlyMessage = "API quota exceeded or rate limit reached";
          } else if (errorText.toLowerCase().includes("permission")) {
            friendlyMessage = "API key doesn't have required permissions";
          }
          throw new Error(friendlyMessage);
        } else if (response.status === 404) {
          throw new Error("API endpoint not found - check your base URL");
        } else if (response.status === 422) {
          let friendlyMessage = "Invalid request";
          if (errorText.toLowerCase().includes("model")) {
            friendlyMessage = "Model name is invalid or not available";
          } else if (errorText.toLowerCase().includes("parameter")) {
            friendlyMessage = "Invalid request parameters";
          }
          throw new Error(friendlyMessage);
        } else if (response.status >= 500) {
          throw new Error("Provider server error - please try again later");
        } else {
          throw new Error(
            `Connection failed (${response.status}) - please check your configuration`
          );
        }
      }

      // Try to parse response to ensure it's valid
      const data = await response.json();
      console.log("Successful response:", data);

      // Verify it looks like a completion response
      if (!data || (!data.choices && !data.id && !data.object)) {
        console.warn("Unexpected API response format:", data);
        // Still consider it successful if we got a 200 response
      }

      return data;
    } catch (error) {
      clearTimeout(timeoutId);
      console.error("API test error:", error);

      if (error instanceof Error) {
        if (error.name === "AbortError") {
          throw new Error(
            "Connection timeout - check your internet connection and API endpoint"
          );
        } else if (
          error.message.includes("Failed to fetch") ||
          error.message.includes("NetworkError") ||
          error.message.includes("fetch")
        ) {
          throw new Error(
            "Network error - check your internet connection and API endpoint URL"
          );
        } else if (
          error.message.includes("CORS") ||
          error.message.includes("cors")
        ) {
          throw new Error(
            "CORS error - this API may not support browser requests"
          );
        }
      }

      throw error;
    }
  };

  // Smart recommendations based on use case
  const getRecommendedSetup = () => {
    switch (useCase) {
      case "rag":
        return "For RAG: Use a larger model like Llama 3.3 70B as Optimizer (better prompt generation) and Llama 3.1 8B as Target (cost-effective deployment).";
      case "qa":
        return "For Q&A: Use Claude or GPT-4 as Optimizer (advanced reasoning) and your target Llama model for deployment. Custom providers like Azure AI Studio work great for production.";
      case "custom":
        return "For custom workflows: Consider cloud models for optimization (more capable) and local models for target deployment (cost + privacy). Use Custom Provider for Azure AI Studio, LiteLLM, or other specialized endpoints.";
      default:
        return "Start with OpenRouter for both roles, then consider separating for cost optimization. Add Custom Provider if you have existing Azure/enterprise endpoints.";
    }
  };

  return (
    <div className="space-y-6">
      <SectionTitle
        title="Choose Your AI Models"
        subtitle="Select inference providers and configure models for your optimization"
      />

      {/* Dual Model Explanation */}
      <div className="bg-muted border border-border rounded-xl p-6 mb-4">
        <div className="flex items-start space-x-4">
          <div className="flex-shrink-0">
            <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center">
              <Brain className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            </div>
          </div>
          <div className="flex-1">
            <h3 className="font-bold text-foreground mb-2 text-lg">
              🎯 Dual Model Optimization
            </h3>
            <p className="text-muted-foreground mb-3">
              Prompt Ops uses two AI models working together to optimize
              your prompts:
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div className="bg-card/60 p-3 rounded-lg border border-green-200 dark:border-green-800">
                <div className="flex items-center space-x-2 mb-1">
                  <Target className="w-4 h-4 text-green-600 dark:text-green-400" />
                  <span className="font-semibold text-green-800 dark:text-green-300">
                    Target Model
                  </span>
                </div>
                <p className="text-muted-foreground">
                  The model you're optimizing FOR - where your prompt will be
                  deployed in production
                </p>
              </div>
              <div className="bg-card/60 p-3 rounded-lg border border-purple-200 dark:border-purple-800">
                <div className="flex items-center space-x-2 mb-1">
                  <Zap className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                  <span className="font-semibold text-purple-800 dark:text-purple-300">
                    Optimizer Model
                  </span>
                </div>
                <p className="text-muted-foreground">
                  The AI that generates improved prompt variations during
                  optimization
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Smart Recommendation */}
      <InfoBox variant="info" title="Smart Recommendation">
        {getRecommendedSetup()}
      </InfoBox>

      {/* Provider Selection */}
      <div className="space-y-4">
        <h3 className="text-xl font-bold text-foreground">
          1. Select Inference Providers
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {PROVIDER_CONFIGS.map((provider) => (
            <div
              key={provider.id}
              className={cn(
                "border-2 rounded-2xl p-4 cursor-pointer transition-colors",
                selectedProviders.includes(provider.id)
                  ? "border-meta-blue bg-meta-blue/5 dark:bg-meta-blue/10"
                  : "border-border hover:border-muted-foreground/30"
              )}
              onClick={() => handleProviderToggle(provider.id)}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center space-x-3">
                  <div
                    className={cn(
                      "p-2 rounded-lg",
                      provider.category === "cloud"
                        ? "bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400"
                        : provider.category === "local"
                        ? "bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400"
                        : "bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400"
                    )}
                  >
                    {provider.icon}
                  </div>
                  <div>
                    <h4 className="font-semibold text-foreground">
                      {provider.name}
                    </h4>
                    <p className="text-sm text-muted-foreground">
                      {provider.description}
                    </p>
                  </div>
                </div>

                {selectedProviders.includes(provider.id) && (
                  <Check className="w-5 h-5 text-meta-blue dark:text-meta-blue-light" />
                )}
              </div>

              {/* Quick stats */}
              <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                <div className="flex items-center space-x-1">
                  {provider.category === "cloud" ? (
                    <Cloud className="w-3 h-3" />
                  ) : provider.category === "local" ? (
                    <Server className="w-3 h-3" />
                  ) : (
                    <Shield className="w-3 h-3" />
                  )}
                  <span className="capitalize">{provider.category}</span>
                </div>
                <div className="flex items-center space-x-1">
                  <DollarSign className="w-3 h-3" />
                  <span className="capitalize">{provider.pricing}</span>
                </div>
                <div className="flex items-center space-x-1">
                  <Clock className="w-3 h-3" />
                  <span className="capitalize">
                    {provider.setup_difficulty} setup
                  </span>
                </div>
              </div>

              {/* Pros/Cons */}
              <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-green-600 dark:text-green-400 font-medium">Pros:</span>
                  <ul className="text-muted-foreground mt-1">
                    {provider.pros.slice(0, 2).map((pro, idx) => (
                      <li key={idx}>• {pro}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <span className="text-orange-600 dark:text-orange-400 font-medium">
                    Considerations:
                  </span>
                  <ul className="text-muted-foreground mt-1">
                    {provider.cons.slice(0, 2).map((con, idx) => (
                      <li key={idx}>• {con}</li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Documentation link */}
              <div className="mt-3 pt-3 border-t border-border/50">
                <a
                  href={provider.docs_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-meta-blue dark:text-meta-blue-light text-xs hover:underline flex items-center space-x-1"
                  onClick={(e) => e.stopPropagation()}
                >
                  <span>Documentation</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Configuration */}
      {selectedProviders.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-bold text-foreground">
              2. Configure Models
            </h3>
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="text-meta-blue text-sm hover:underline flex items-center space-x-1"
            >
              <Settings className="w-4 h-4" />
              <span>{showAdvanced ? "Hide" : "Show"} Advanced Options</span>
            </button>
          </div>

          {/* Interactive Role Status Overview */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4 mb-6">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-semibold text-blue-900 dark:text-blue-300">
                Model Role Assignment
              </h4>
              <div className="text-xs text-blue-600 dark:text-blue-400">
                Click role badges below to change assignments
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {(() => {
                const { hasTarget, hasOptimizer, hasBoth } = getRoleStatus();
                const targetConfig = configurations.find(
                  (c) => c.role === "target" || c.role === "both"
                );
                const optimizerConfig = configurations.find(
                  (c) => c.role === "optimizer" || c.role === "both"
                );

                return (
                  <>
                    {/* Target Status */}
                    <div
                      className={`p-3 rounded-lg border transition-all ${
                        hasTarget
                          ? "bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800 shadow-sm"
                          : "bg-muted border-border hover:bg-muted/80"
                      }`}
                    >
                      <div className="flex items-center space-x-2 mb-2">
                        <Target
                          className={`w-4 h-4 ${
                            hasTarget ? "text-green-600 dark:text-green-400" : "text-muted-foreground"
                          }`}
                        />
                        <span
                          className={`font-medium ${
                            hasTarget ? "text-green-800 dark:text-green-300" : "text-muted-foreground"
                          }`}
                        >
                          Target Model
                        </span>
                        {hasTarget && (
                          <CheckCircle className="w-4 h-4 text-green-600 dark:text-green-400" />
                        )}
                      </div>
                      {targetConfig ? (
                        <div className="space-y-1">
                          <div className="flex items-center space-x-2">
                            <InteractiveRoleBadge
                              role={targetConfig.role}
                              configId={targetConfig.id}
                              className="z-20"
                            />
                            {targetConfig.role === "both" && (
                              <span className="text-xs text-blue-600 dark:text-blue-400 font-medium">
                                Also optimizer
                              </span>
                            )}
                          </div>
                          <div className="text-sm text-muted-foreground">
                            <div className="font-medium text-foreground">
                              {targetConfig.provider_id === "custom"
                                ? targetConfig.custom_provider_name
                                : PROVIDER_CONFIGS.find(
                                    (p) => p.id === targetConfig.provider_id
                                  )?.name}
                            </div>
                            <div className="truncate">
                              {targetConfig.model_name}
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="text-center py-2">
                          <p className="text-sm text-muted-foreground mb-2">
                            Not configured
                          </p>
                          <button
                            onClick={() => {
                              if (selectedProviders.length > 0) {
                                addConfiguration(
                                  selectedProviders[0],
                                  "target"
                                );
                              }
                            }}
                            className="text-xs bg-green-600 text-white px-2 py-1 rounded hover:bg-green-700 transition-colors"
                          >
                            Add Target
                          </button>
                        </div>
                      )}
                    </div>

                    {/* Optimizer Status */}
                    <div
                      className={`p-3 rounded-lg border transition-all ${
                        hasOptimizer
                          ? "bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-800 shadow-sm"
                          : "bg-muted border-border hover:bg-muted/80"
                      }`}
                    >
                      <div className="flex items-center space-x-2 mb-2">
                        <Brain
                          className={`w-4 h-4 ${
                            hasOptimizer ? "text-purple-600 dark:text-purple-400" : "text-muted-foreground"
                          }`}
                        />
                        <span
                          className={`font-medium ${
                            hasOptimizer ? "text-purple-800 dark:text-purple-300" : "text-muted-foreground"
                          }`}
                        >
                          Optimizer Model
                        </span>
                        {hasOptimizer && (
                          <CheckCircle className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                        )}
                      </div>
                      {optimizerConfig ? (
                        <div className="space-y-1">
                          <div className="flex items-center space-x-2">
                            <InteractiveRoleBadge
                              role={optimizerConfig.role}
                              configId={optimizerConfig.id}
                              className="z-20"
                            />
                            {optimizerConfig.role === "both" && (
                              <span className="text-xs text-green-600 dark:text-green-400 font-medium">
                                Also target
                              </span>
                            )}
                          </div>
                          <div className="text-sm text-muted-foreground">
                            <div className="font-medium text-foreground">
                              {optimizerConfig.provider_id === "custom"
                                ? optimizerConfig.custom_provider_name
                                : PROVIDER_CONFIGS.find(
                                    (p) => p.id === optimizerConfig.provider_id
                                  )?.name}
                            </div>
                            <div className="truncate">
                              {optimizerConfig.model_name}
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="text-center py-2">
                          <p className="text-sm text-muted-foreground mb-2">
                            Not configured
                          </p>
                          <button
                            onClick={() => {
                              if (selectedProviders.length > 0) {
                                addConfiguration(
                                  selectedProviders[0],
                                  "optimizer"
                                );
                              }
                            }}
                            className="text-xs bg-purple-600 text-white px-2 py-1 rounded hover:bg-purple-700 transition-colors"
                          >
                            Add Optimizer
                          </button>
                        </div>
                      )}
                    </div>

                    {/* Overall Status */}
                    <div
                      className={`p-3 rounded-lg border ${
                        hasTarget && hasOptimizer
                          ? "bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800"
                          : hasBoth
                          ? "bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800"
                          : "bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800"
                      }`}
                    >
                      <div className="flex items-center space-x-2 mb-1">
                        <Settings
                          className={`w-4 h-4 ${
                            (hasTarget && hasOptimizer) || hasBoth
                              ? "text-blue-600 dark:text-blue-400"
                              : "text-yellow-600 dark:text-yellow-400"
                          }`}
                        />
                        <span
                          className={`font-medium ${
                            (hasTarget && hasOptimizer) || hasBoth
                              ? "text-blue-800 dark:text-blue-300"
                              : "text-yellow-800 dark:text-yellow-300"
                          }`}
                        >
                          Setup Status
                        </span>
                      </div>
                      {hasTarget && hasOptimizer ? (
                        <div className="space-y-1">
                          <p className="text-sm text-blue-600 dark:text-blue-400 font-medium">
                            ✅ Ready for optimization
                          </p>
                          <p className="text-xs text-blue-500 dark:text-blue-400/70">
                            Using separate models for each role
                          </p>
                        </div>
                      ) : hasBoth ? (
                        <div className="space-y-1">
                          <p className="text-sm text-blue-600 dark:text-blue-400 font-medium">
                            ✅ Ready for optimization
                          </p>
                          <p className="text-xs text-blue-500 dark:text-blue-400/70">
                            Using single model for both roles
                          </p>
                        </div>
                      ) : (
                        <div className="space-y-1">
                          <p className="text-sm text-yellow-700 dark:text-yellow-300">
                            ⚠️ Configure {!hasTarget ? "target" : ""}{" "}
                            {!hasTarget && !hasOptimizer ? " & " : ""}{" "}
                            {!hasOptimizer ? "optimizer" : ""} model
                            {!hasTarget && !hasOptimizer ? "s" : ""}
                          </p>
                          <p className="text-xs text-yellow-600 dark:text-yellow-400/70">
                            Select a provider above to get started
                          </p>
                        </div>
                      )}
                    </div>
                  </>
                );
              })()}
            </div>
          </div>

          <div className="space-y-6">
            {selectedProviders.map((providerId) => {
              const provider = PROVIDER_CONFIGS.find(
                (p) => p.id === providerId
              );
              const providerConfigs = configurations.filter(
                (config) => config.provider_id === providerId
              );

              if (!provider) return null;

                return (
                  <div
                    key={providerId}
                    className="bg-card rounded-2xl p-6 border border-border"
                  >
                  {/* Provider Header */}
                  <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center space-x-3">
                      {provider.icon}
                      <div>
                        <h4 className="font-semibold text-foreground text-lg">
                          {provider.name}
                        </h4>
                        <p className="text-sm text-muted-foreground">
                          {providerConfigs.length} configuration
                          {providerConfigs.length !== 1 ? "s" : ""}
                        </p>
                      </div>
                    </div>

                    {/* Add Configuration Buttons */}
                    <div className="flex items-center space-x-2">
                      {(() => {
                        const { canAddTarget, canAddOptimizer, canAddBoth } =
                          getAvailableRoles(providerId);
                        const { hasTarget, hasOptimizer, hasBoth } =
                          getRoleStatus();

                        return (
                          <>
                            {/* Add Both button (only if no configs exist anywhere) */}
                            {canAddBoth && (
                              <button
                                onClick={() => {
                                  const newConfig: ModelConfig = {
                                    id: `${providerId}-both-${Date.now()}`,
                                    provider_id: providerId,
                                    model_name: provider.popular_models[0],
                                    role: "both",
                                    api_base: provider.api_base,
                                    api_key: "",
                                    temperature: 0.0,
                                    max_tokens: 4096,
                                    custom_provider_name:
                                      providerId === "custom" ? "" : undefined,
                                    model_prefix:
                                      providerId === "custom"
                                        ? ""
                                        : provider.model_prefix,
                                    auth_method:
                                      providerId === "custom"
                                        ? "api_key"
                                        : undefined,
                                    custom_headers:
                                      providerId === "custom" ? {} : undefined,
                                  };
                                  setConfigurations((prev) => [
                                    ...prev,
                                    newConfig,
                                  ]);
                                }}
                                className="text-sm bg-blue-500 text-white px-3 py-1 rounded-full hover:bg-blue-600 transition-colors flex items-center space-x-1"
                              >
                                <Plus className="w-3 h-3" />
                                <div className="flex items-center space-x-1">
                                  <Target className="w-3 h-3" />
                                  <Brain className="w-3 h-3" />
                                </div>
                                <span>Both</span>
                              </button>
                            )}

                            {/* Add Target button */}
                            {canAddTarget && (
                              <button
                                onClick={() =>
                                  addConfiguration(providerId, "target")
                                }
                                className="text-sm bg-green-500 text-white px-3 py-1 rounded-full hover:bg-green-600 transition-colors flex items-center space-x-1"
                              >
                                <Plus className="w-3 h-3" />
                                <Target className="w-3 h-3" />
                                <span>Target</span>
                              </button>
                            )}

                            {/* Add Optimizer button */}
                            {canAddOptimizer && (
                              <button
                                onClick={() =>
                                  addConfiguration(providerId, "optimizer")
                                }
                                className="text-sm bg-purple-500 text-white px-3 py-1 rounded-full hover:bg-purple-600 transition-colors flex items-center space-x-1"
                              >
                                <Plus className="w-3 h-3" />
                                <Brain className="w-3 h-3" />
                                <span>Optimizer</span>
                              </button>
                            )}

                            {/* Status indicator when no buttons available */}
                            {!canAddTarget &&
                              !canAddOptimizer &&
                              !canAddBoth && (
                                <div className="text-sm text-gray-500 flex items-center space-x-1">
                                  <CheckCircle className="w-4 h-4 text-green-500" />
                                  <span>Roles complete</span>
                                </div>
                              )}
                          </>
                        );
                      })()}
                    </div>
                  </div>

                  {/* Split/Merge Controls */}
                  {(() => {
                    const hasBothConfig = providerConfigs.some(
                      (c) => c.role === "both"
                    );
                    const hasTargetAndOptimizer =
                      providerConfigs.some((c) => c.role === "target") &&
                      providerConfigs.some((c) => c.role === "optimizer");

                    if (hasBothConfig) {
                      return (
                        <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-2">
                              <Split className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                              <span className="text-sm font-medium text-blue-800 dark:text-blue-300">
                                Using one model for both roles
                              </span>
                            </div>
                            <button
                              onClick={() => {
                                const bothConfig = providerConfigs.find(
                                  (c) => c.role === "both"
                                );
                                if (bothConfig)
                                  splitConfiguration(bothConfig.id);
                              }}
                              className="text-sm bg-blue-600 text-white px-3 py-1 rounded-full hover:bg-blue-700 transition-colors flex items-center space-x-1"
                            >
                              <Split className="w-3 h-3" />
                              <span>Use Different Models</span>
                            </button>
                          </div>
                        </div>
                      );
                    } else if (hasTargetAndOptimizer) {
                      return (
                        <div className="mb-4 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-2">
                              <Merge className="w-4 h-4 text-green-600 dark:text-green-400" />
                              <span className="text-sm font-medium text-green-800 dark:text-green-300">
                                Using separate models for each role
                              </span>
                            </div>
                            <button
                              onClick={() => mergeConfigurations(providerId)}
                              className="text-sm bg-green-600 text-white px-3 py-1 rounded-full hover:bg-green-700 transition-colors flex items-center space-x-1"
                            >
                              <Merge className="w-3 h-3" />
                              <span>Use Same Model</span>
                            </button>
                          </div>
                        </div>
                      );
                    }
                    return null;
                  })()}

                  {/* Configurations */}
                  <div className="space-y-4">
                    {providerConfigs.map((config) => {
                      const configKey = `${config.provider_id}-${config.role}-${config.id}`;

                      return (
                        <div
                          key={config.id}
                          className="bg-muted rounded-lg p-4 border border-border"
                        >
                          <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center space-x-3">
                              <InteractiveRoleBadge
                                role={config.role}
                                configId={config.id}
                              />
                              <h5 className="font-medium text-foreground">
                                Model Configuration
                              </h5>
                            </div>

                            <div className="flex items-center space-x-2">
                              {/* Connection status */}
                              {testingConnections[configKey] ? (
                                <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
                              ) : connectionStatus[configKey] === "success" ? (
                                <CheckCircle className="w-4 h-4 text-green-500" />
                              ) : connectionStatus[configKey] === "error" ? (
                                <AlertCircle className="w-4 h-4 text-red-500" />
                              ) : null}

                              <button
                                onClick={() => testConnection(config)}
                                disabled={testingConnections[configKey]}
                                className="text-sm bg-meta-blue text-white px-3 py-1 rounded-full hover:bg-meta-blue-800 transition-colors disabled:opacity-50"
                              >
                                {testingConnections[configKey]
                                  ? "Testing..."
                                  : "Test Connection"}
                              </button>

                              {providerConfigs.length > 1 && (
                                <button
                                  onClick={() => removeConfiguration(config.id)}
                                  className="text-xs bg-red-500 text-white px-2 py-1 rounded hover:bg-red-600 transition-colors"
                                >
                                  <Trash2 className="w-3 h-3" />
                                </button>
                              )}
                            </div>
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {/* Custom Provider Name (for custom providers) */}
                            {config.provider_id === "custom" && (
                              <div className="md:col-span-2">
                                <label className="block text-sm font-medium text-foreground mb-2">
                                  Provider Name
                                  <span className="text-red-500 ml-1">*</span>
                                </label>
                                <input
                                  type="text"
                                  value={config.custom_provider_name || ""}
                                  onChange={(e) =>
                                    handleConfigChange(
                                      config.id,
                                      "custom_provider_name",
                                      e.target.value
                                    )
                                  }
                                  placeholder="e.g., Azure AI Studio, My Custom API"
                                  className="w-full p-3 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring bg-input text-foreground"
                                />
                              </div>
                            )}

                            {/* API Base URL (for custom providers and vLLM) */}
                            {(config.provider_id === "custom" ||
                              config.provider_id === "vllm") && (
                              <div className="md:col-span-2">
                                <label className="block text-sm font-medium text-foreground mb-2">
                                  API Base URL
                                  <span className="text-red-500 ml-1">*</span>
                                </label>
                                <input
                                  type="url"
                                  value={config.api_base || ""}
                                  onChange={(e) =>
                                    handleConfigChange(
                                      config.id,
                                      "api_base",
                                      e.target.value
                                    )
                                  }
                                  placeholder={
                                    config.provider_id === "vllm"
                                      ? "e.g., http://localhost:8000"
                                      : "e.g., https://your-endpoint.eastus2.inference.ai.azure.com/"
                                  }
                                  className="w-full p-3 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring bg-input text-foreground"
                                />
                              </div>
                            )}

                            {/* Model Prefix (for custom providers) */}
                            {config.provider_id === "custom" && (
                              <div>
                                <label className="block text-sm font-medium text-foreground mb-2">
                                  Model Prefix (LiteLLM format)
                                </label>
                                <input
                                  type="text"
                                  value={config.model_prefix || ""}
                                  onChange={(e) =>
                                    handleConfigChange(
                                      config.id,
                                      "model_prefix",
                                      e.target.value
                                    )
                                  }
                                  placeholder="e.g., azure_ai/, custom/"
                                  className="w-full p-3 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring bg-input text-foreground"
                                />
                                <p className="text-xs text-muted-foreground mt-1">
                                  Leave empty for direct model names
                                </p>
                              </div>
                            )}

                            {/* Authentication Method (for custom providers) */}
                            {config.provider_id === "custom" && (
                              <div>
                                <label className="block text-sm font-medium text-foreground mb-2">
                                  Authentication Method
                                </label>
                                <select
                                  value={config.auth_method || "api_key"}
                                  onChange={(e) =>
                                    handleConfigChange(
                                      config.id,
                                      "auth_method",
                                      e.target.value as
                                        | "api_key"
                                        | "bearer_token"
                                        | "custom_headers"
                                    )
                                  }
                                  className="w-full p-3 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring bg-input text-foreground"
                                >
                                  <option value="api_key">API Key</option>
                                  <option value="bearer_token">
                                    Bearer Token
                                  </option>
                                  <option value="custom_headers">
                                    Custom Headers
                                  </option>
                                </select>
                              </div>
                            )}

                            {/* Model Selection */}
                            <div>
                              <label className="block text-sm font-medium text-foreground mb-2">
                                Model
                                {config.provider_id === "custom" && (
                                  <span className="text-red-500 ml-1">*</span>
                                )}
                              </label>
                              {config.provider_id === "custom" ? (
                                <input
                                  type="text"
                                  value={config.model_name}
                                  onChange={(e) =>
                                    handleConfigChange(
                                      config.id,
                                      "model_name",
                                      e.target.value
                                    )
                                  }
                                  placeholder="e.g., command-r-plus, mistral-large-latest"
                                  className="w-full p-3 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring bg-input text-foreground"
                                />
                              ) : (
                                <select
                                  value={config.model_name}
                                  onChange={(e) =>
                                    handleConfigChange(
                                      config.id,
                                      "model_name",
                                      e.target.value
                                    )
                                  }
                                  className="w-full p-3 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring bg-input text-foreground"
                                >
                                  {provider?.popular_models.map((model) => (
                                    <option key={model} value={model}>
                                      {model.split("/").pop() || model}
                                    </option>
                                  ))}
                                </select>
                              )}
                              {config.provider_id === "custom" && (
                                <p className="text-xs text-muted-foreground mt-1">
                                  Final model will be:{" "}
                                  {config.model_prefix || ""}
                                  {config.model_name}
                                </p>
                              )}
                            </div>

                            {/* Authentication */}
                            {(provider?.requires_signup ||
                              config.provider_id === "custom") && (
                              <div>
                                <label className="block text-sm font-medium text-foreground mb-2">
                                  {config.provider_id === "custom"
                                    ? config.auth_method === "bearer_token"
                                      ? "Bearer Token"
                                      : config.auth_method === "custom_headers"
                                      ? "Authentication"
                                      : "API Key"
                                    : "API Key"}
                                  <span className="text-red-500 ml-1">*</span>
                                </label>
                                {config.provider_id === "custom" &&
                                config.auth_method === "custom_headers" ? (
                                  <div className="space-y-2">
                                    <p className="text-xs text-muted-foreground">
                                      Configure custom headers for
                                      authentication
                                    </p>
                                    <textarea
                                      value={JSON.stringify(
                                        config.custom_headers || {},
                                        null,
                                        2
                                      )}
                                      onChange={(e) => {
                                        try {
                                          const headers = JSON.parse(
                                            e.target.value
                                          );
                                          handleConfigChange(
                                            config.id,
                                            "custom_headers",
                                            headers
                                          );
                                        } catch (error) {
                                          // Invalid JSON, keep as is for now
                                        }
                                      }}
                                      placeholder={`{
  "Authorization": "Bearer your-token",
  "X-API-Key": "your-api-key"
}`}
                                      rows={4}
                                      className="w-full p-3 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring bg-input text-foreground font-mono text-sm"
                                    />
                                  </div>
                                ) : (
                                  <div className="relative">
                                    <input
                                      type={
                                        showApiKeys[configKey]
                                          ? "text"
                                          : "password"
                                      }
                                      value={config.api_key || ""}
                                      onChange={(e) => {
                                        handleConfigChange(
                                          config.id,
                                          "api_key",
                                          e.target.value
                                        );
                                      }}
                                      placeholder={
                                        config.provider_id === "custom"
                                          ? config.auth_method ===
                                            "bearer_token"
                                            ? "Enter your bearer token"
                                            : "Enter your API key"
                                          : "Enter your API key"
                                      }
                                      className="w-full p-3 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring bg-input text-foreground pr-10"
                                    />
                                    <button
                                      type="button"
                                      onClick={() =>
                                        setShowApiKeys((prev) => ({
                                          ...prev,
                                          [configKey]: !prev[configKey],
                                        }))
                                      }
                                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground hover:text-foreground"
                                    >
                                      {showApiKeys[configKey] ? (
                                        <EyeOff className="w-4 h-4" />
                                      ) : (
                                        <Eye className="w-4 h-4" />
                                      )}
                                    </button>
                                  </div>
                                )}
                              </div>
                            )}

                            {/* Advanced Options */}
                            {showAdvanced && (
                              <>
                                <div>
                                  <label className="block text-sm font-medium text-foreground mb-2">
                                    Temperature
                                  </label>
                                  <input
                                    type="number"
                                    min="0"
                                    max="2"
                                    step="0.1"
                                    value={config.temperature}
                                    onChange={(e) =>
                                      handleConfigChange(
                                        config.id,
                                        "temperature",
                                        parseFloat(e.target.value)
                                      )
                                    }
                                    className="w-full p-3 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring bg-input text-foreground"
                                  />
                                </div>

                                <div>
                                  <label className="block text-sm font-medium text-foreground mb-2">
                                    Max Tokens
                                  </label>
                                  <input
                                    type="number"
                                    min="1"
                                    max="100000"
                                    value={config.max_tokens}
                                    onChange={(e) =>
                                      handleConfigChange(
                                        config.id,
                                        "max_tokens",
                                        parseInt(e.target.value)
                                      )
                                    }
                                    className="w-full p-3 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring bg-input text-foreground"
                                  />
                                </div>

                                {selectedProviders.length > 1 && (
                                  <div>
                                    <label className="block text-sm font-medium text-foreground mb-2">
                                      Role Assignment
                                    </label>
                                    <select
                                      value={config.role}
                                      onChange={(e) =>
                                        handleConfigChange(
                                          config.id,
                                          "role",
                                          e.target.value as
                                            | "target"
                                            | "optimizer"
                                            | "both"
                                        )
                                      }
                                      className="w-full p-3 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring bg-input text-foreground"
                                    >
                                      <option value="both">
                                        🔄 Both (Target + Optimizer)
                                      </option>
                                      <option value="target">
                                        🎯 Target Model (Production Deployment)
                                      </option>
                                      <option value="optimizer">
                                        🧠 Optimizer Model (Prompt Generation)
                                      </option>
                                    </select>
                                  </div>
                                )}

                                <div>
                                  <label className="block text-sm font-medium text-foreground mb-2">
                                    API Base URL
                                  </label>
                                  <input
                                    type="url"
                                    value={config.api_base || ""}
                                    onChange={(e) =>
                                      handleConfigChange(
                                        config.id,
                                        "api_base",
                                        e.target.value
                                      )
                                    }
                                    className="w-full p-3 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring bg-input text-foreground"
                                  />
                                </div>
                              </>
                            )}
                          </div>

                          {/* Connection error message */}
                          {connectionStatus[configKey] === "error" && (
                            <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                              <div className="flex items-center space-x-2">
                                <AlertCircle className="w-4 h-4 text-red-600 dark:text-red-400" />
                                <span className="text-red-800 dark:text-red-300 text-sm">
                                  Connection failed. Please check your API key
                                  and configuration.
                                </span>
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Setup Instructions */}
      {selectedProviders.some((id) => {
        const provider = PROVIDER_CONFIGS.find((p) => p.id === id);
        return provider?.setup_difficulty !== "easy";
      }) && (
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-xl p-4">
          <h4 className="font-semibold text-yellow-900 dark:text-yellow-300 mb-2">
            Setup Instructions
          </h4>
          <div className="space-y-2 text-sm text-yellow-800 dark:text-yellow-200">
            {selectedProviders.map((id) => {
              const provider = PROVIDER_CONFIGS.find((p) => p.id === id);
              if (provider?.setup_difficulty === "easy") return null;

              return (
                <div key={id}>
                  <strong>{provider?.name}:</strong>
                  {provider?.id === "vllm" && (
                    <div className="ml-4 mt-1">
                      <p>
                        1. Install vLLM:{" "}
                        <code className="bg-yellow-100 dark:bg-yellow-900/40 px-1 rounded">
                          pip install vllm
                        </code>
                      </p>
                      <p>
                        2. Start server:{" "}
                        <code className="bg-yellow-100 dark:bg-yellow-900/40 px-1 rounded">
                          vllm serve{" "}
                          {configurations
                            .find((c) => c.provider_id === "vllm")
                            ?.model_name?.replace("hosted_vllm/", "") ||
                            "meta-llama/Llama-3.1-8B-Instruct"}
                        </code>
                      </p>
                    </div>
                  )}
                  {provider?.id === "nvidia_nim" && (
                    <div className="ml-4 mt-1">
                      <p>1. Install Docker and NVIDIA Container Toolkit</p>
                      <p>
                        2. Pull and run NIM container (see documentation for
                        details)
                      </p>
                    </div>
                  )}
                  {provider?.id === "custom" && (
                    <div className="ml-4 mt-1">
                      <p className="font-medium mb-2">
                        Azure AI Studio via LiteLLM:
                      </p>
                      <p>1. Set up your Azure AI Studio endpoint</p>
                      <p>
                        2. Use format:{" "}
                        <code className="bg-yellow-100 dark:bg-yellow-900/40 text-yellow-900 dark:text-yellow-200 px-1 rounded text-xs">
                          azure_ai/
                        </code>{" "}
                        as model prefix
                      </p>
                      <p>
                        3. Model example:{" "}
                        <code className="bg-yellow-100 dark:bg-yellow-900/40 text-yellow-900 dark:text-yellow-200 px-1 rounded text-xs">
                          command-r-plus
                        </code>{" "}
                        → Final:{" "}
                        <code className="bg-yellow-100 dark:bg-yellow-900/40 text-yellow-900 dark:text-yellow-200 px-1 rounded text-xs">
                          azure_ai/command-r-plus
                        </code>
                      </p>
                      <p className="mt-2 font-medium">
                        Other LiteLLM Providers:
                      </p>
                      <p>
                        4. See{" "}
                        <a
                          href="https://docs.litellm.ai/docs/providers"
                          target="_blank"
                          className="text-blue-600 dark:text-blue-400 hover:underline"
                        >
                          LiteLLM docs
                        </a>{" "}
                        for 100+ supported providers
                      </p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
