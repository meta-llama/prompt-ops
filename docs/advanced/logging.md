# Logging and Telemetry

The `llama-prompt-ops` library includes a flexible logging framework to provide insights into the optimization process. You can control the verbosity of the output and export detailed telemetry for analysis.

## Configuring Log Levels

You can configure the logging level in two ways:

1.  **Via the command-line interface:**

    Use the `--log-level` option when running the `migrate` command:

    ```bash
    llama-prompt-ops migrate --config your_config.yaml --log-level DEBUG
    ```

    Available log levels are `DEBUG`, `INFO`, `WARNING`, `ERROR`, and `CRITICAL`.

2.  **Via the YAML configuration file:**

    Add a `logging` section to your `config.yaml` file:

    ```yaml
    logging:
      level: DEBUG
    ```

    The command-line option will override the setting in the configuration file.

## Exporting Telemetry

The logging framework can capture detailed timings and metrics during the optimization process and export them to a JSON file. To enable this, add an `export_path` to the `logging` section of your configuration file:

```yaml
logging:
  level: INFO
  export_path: "results/telemetry_${TIMESTAMP}.json"
```

The `${TIMESTAMP}` placeholder will be replaced with a timestamp of the format `YYYYMMDD_HHMMSS`.

The exported JSON file will contain two main sections:

-   `timings`: The duration of each major phase of the optimization process.
-   `metrics`: A list of metrics logged during the process, including the metric key, value, and step.

## Pre-Optimization Summary

Before starting the optimization process, `llama-prompt-ops` displays a comprehensive summary of the optimization configuration. This summary provides transparency into what will happen during optimization and helps with debugging and reproducibility.

### Summary Contents

The pre-optimization summary includes:

- **Task Model**: The model used for executing the task
- **Proposer Model**: The model used for generating instruction proposals (MIPROv2)
- **Metric**: The evaluation metric being used
- **Train / Val size**: Number of training and validation examples
- **MIPRO Params**: Key MIPROv2 optimization parameters
- **Guidance**: Any custom instruction tips provided to the proposer
- **Baseline score**: Performance of the original prompt before optimization

### Example Output

```
=== Pre-Optimization Summary ===
    Task Model       : openai/gpt-4o-mini
    Proposer Model   : openai/gpt-4o
    Metric           : facility_metric
    Train / Val size : 100 / 25
    MIPRO Params     : {"auto_user":"basic","auto_dspy":"light","max_labeled_demos":5,"max_bootstrapped_demos":4,"num_candidates":10,"num_threads":18,"init_temperature":0.5,"seed":9}
    Guidance         : Use chain-of-thought reasoning and show your work step by step...
    Baseline score   : 0.4200
```

### Controlling Visibility

The pre-optimization summary is logged at `INFO` level. To see it, ensure your log level is set to `INFO` or lower:

```bash
# Via command line
llama-prompt-ops migrate --config config.yaml --log-level INFO

# Via environment variable
export PROMPT_OPS_LOG_LEVEL=INFO
llama-prompt-ops migrate --config config.yaml
```

The summary provides valuable context for understanding optimization results and can help identify configuration issues before the optimization process begins.
