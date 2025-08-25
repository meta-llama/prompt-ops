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

## Instruction Proposal Tracking

During the optimization process, `llama-prompt-ops` provides real-time progress tracking for the instruction proposal phase. This feature gives you visibility into how many candidate instructions have been generated and the time taken for each proposal.

### Real-Time Progress Display

When DSPy's MIPROv2 optimizer generates candidate instructions, you'll see progress updates like:

```
⏳ Proposing instructions: |██████░░░░░░░░░░░░░░░░░░░░░░░░| 1/5 (20.0%) | avg: 1.24s
⏳ Proposing instructions: |████████████░░░░░░░░░░░░░░░░░░| 2/5 (40.0%) | avg: 1.18s
⏳ Proposing instructions: |██████████████████░░░░░░░░░░░░| 3/5 (60.0%) | avg: 1.15s
⏳ Proposing instructions: |████████████████████████░░░░░░| 4/5 (80.0%) | avg: 1.12s
⏳ Proposing instructions: |██████████████████████████████| 5/5 (100.0%) | avg: 1.10s
```

### Progress Information

Each progress line includes:

- **Visual Progress Bar**: Shows completion percentage with filled (█) and unfilled (░) characters
- **Completion Count**: Current number of completed proposals vs. total (e.g., "3/5")
- **Percentage**: Numerical completion percentage
- **Average Time**: Running average time per proposal in seconds

### Technical Details

The instruction proposal tracker is implemented using the `InstructionProposalTracker` class in the telemetry module. It:

- Tracks timing for each individual instruction candidate
- Displays progress only after each candidate is completed (avoiding duplicate lines)
- Calculates running averages to help estimate remaining time
- Integrates seamlessly with the existing logging framework

### Controlling Visibility

The instruction proposal progress is logged at `INFO` level. To see these updates:

```bash
# Ensure log level is INFO or lower
llama-prompt-ops migrate --config config.yaml --log-level INFO
```

This feature improves the user experience by providing transparency into what can be a time-consuming phase of the optimization process, especially when generating many instruction candidates or using slower models.
