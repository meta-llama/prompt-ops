# my_lpo_test_project

A prompt optimization project created with llama-prompt-ops.

## Getting Started

1. Set your API key in the `.env` file:
   ```
   OPENROUTER_API_KEY=your_api_key_here
   ```

2. Run the optimization:
   ```bash
   cd my_lpo_test_project
   llama-prompt-ops migrate
   ```

## Project Structure

- `config.yaml`: Configuration file for the project
- `prompts/prompt.txt`: The prompt template to optimize
- `data/dataset.json`: Sample dataset for training and evaluation
- `.env`: Environment variables including API keys
