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
