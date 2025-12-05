# MS MARCO - PDO Optimization Use Case

This use case demonstrates using the **PDO (Prompt Duel Optimizer)** strategy to optimize prompts for concise, accurate answers on MS MARCO-style open-ended questions.

## What is PDO?

PDO (Prompt Duel Optimizer) is a dueling bandit optimization strategy that:
- Maintains a pool of prompt variations
- Runs "duels" between prompts to compare performance
- Uses Thompson sampling to intelligently select which prompts to test
- Evolves the prompt pool by generating new variations from top performers
- Uses the Copeland ranking method to determine the best prompts

## Getting Started

1. **Set your API key** in a `.env` file in the project root:
   ```bash
   OPENROUTER_API_KEY=your_api_key_here
   # LiteLLM auto-detects the provider from your model name (openrouter/model)
   ```

2. **Run the optimization**:
   ```bash
   cd use-cases/ms-marco-pdo
   prompt-ops optimize --config config.yaml
   ```

## Configuration Highlights

- **Dataset**: MS MARCO-style QA (`dataset/ms_marco_description.json`)
- **I/O Fields**: Input = `question`, Output = `answer`
- **Task Type**: Open-ended, concise answer generation
- **Optimization Strategy**: PDO with dueling bandits
- **Models**: Llama 3.3 70B via OpenRouter for task + prompt generation
- **Rounds**: 20 optimization rounds
- **Duels per Round**: 25

## Key PDO Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `total_rounds` | 20 | Number of optimization iterations |
| `gen_new_prompt_round_frequency` | 20 | Generate new prompts every 20 rounds |
| `num_duels_per_round` | 25 | Prompt comparisons per round |
| `num_eval_examples_per_duel` | 1 | Examples per duel |
| `num_initial_instructions` | 20 | Starting prompt pool size |
| `thompson_alpha` | 1.2 | Confidence bound parameter |
| `ranking_method` | copeland | Method for ranking prompt performance |

## Project Structure

```
ms-marco-pdo/
├── config.yaml                 # PDO optimization configuration
├── prompts/
│   └── prompt.txt             # Initial prompt template
├── dataset/
│   └── ms_marco_description.json  # MS MARCO-style QA samples
├── results/                   # Optimization results (generated)
└── MSMARCO_PDO_eval.ipynb     # Optional: evaluation/analysis notebook
```

## Expected Outcomes

The PDO optimization will:
1. Start with a concise baseline answering prompt
2. Generate variations through LLM-driven mutation
3. Test prompts against each other in duels
4. Identify which prompting strategies improve answer quality
5. Produce an optimized prompt that increases accuracy and clarity

## Tips

- **Quick tests**: Set `total_rounds: 5` for faster iterations
- **Adjust concurrency**: Tune `max_concurrent_threads` based on your rate limits
- **Monitor**: Inspect `results/` for intermediate rankings and best prompts
- **Compare**: Try other strategies (e.g., QPDO, MIPRO) on the same dataset
