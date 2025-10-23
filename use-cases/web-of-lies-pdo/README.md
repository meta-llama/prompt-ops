# Web of Lies - PDO Optimization Use Case

This use case demonstrates using the **PDO (Prompt Duel Optimizer)** strategy to optimize prompts for the "Web of Lies" logical reasoning task.

## Task Description

The Web of Lies task tests logical reasoning abilities. Each example presents a chain of statements about people who either always tell the truth or always lie. The model must determine whether the final person in the chain tells the truth or lies.

### Example

```
Question: Sherrie tells the truth. Vernell says Sherrie tells the truth.
Alexis says Vernell lies. Michaela says Alexis tells the truth.
Elanor says Michaela tells the truth. Does Elanor tell the truth?

Answer: No
```

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
   ```

2. **Run the optimization**:
   ```bash
   cd use-cases/web-of-lies-pdo
   prompt-ops optimize --config config.yaml
   ```

## Configuration Highlights

- **Dataset**: 1000 Web of Lies logical reasoning problems
- **Answer Format**: Binary ("Yes" or "No")
- **Optimization Strategy**: PDO with dueling bandits
- **Models**: Using Llama 3.3 70B via OpenRouter for both task execution and prompt generation
- **Rounds**: 30 optimization rounds
- **Duels per Round**: 25 (comparing prompt performance)

## Key PDO Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `total_rounds` | 30 | Number of optimization iterations |
| `gen_new_prompt_round_frequency` | 10 | Generate new prompts every 10 rounds |
| `num_duels_per_round` | 25 | Prompt comparisons per round |
| `num_initial_instructions` | 20 | Starting prompt pool size |
| `thompson_alpha` | 1.2 | Confidence bound parameter |
| `ranking_method` | copeland | Method for ranking prompt performance |

## Project Structure

```
web-of-lies-pdo/
├── config.yaml              # PDO optimization configuration
├── prompts/
│   └── prompt.txt          # Initial prompt template
├── data/
│   └── web_of_lies.json    # 1000 logical reasoning examples
├── results/                # Optimization results (generated)
└── logs/                   # Execution logs (generated)
```

## Expected Outcomes

The PDO optimization will:
1. Start with a simple baseline prompt
2. Generate variations through LLM-driven mutation
3. Test prompts against each other in duels
4. Identify which reasoning strategies work best
5. Produce an optimized prompt that improves logical reasoning accuracy

## Tips

- **Reduce rounds for testing**: Set `total_rounds: 5` for quick experiments
- **Adjust concurrency**: Increase `max_concurrent_threads` if you have higher rate limits
- **Monitor progress**: Check the logs directory for detailed execution information
- **Compare strategies**: Try this same task with other optimization strategies (e.g., QPDO, MIPRO)
