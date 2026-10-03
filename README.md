# Hub-and-Spoke AI Agent Setup

This repository contains the first-pass basic implementation of a hub-and-spoke multi-agent architecture for a stock trading system.

## Architecture

- Driver agent: Stock planner
- Worker agents:
  - history-analyzer
  - stage-build-sequence
  - environment-checks
  - paper-trading
  - shadow-mode
  - live-mode
  - observability-and-logs
  - model-diversity-checks

## Run the demo

```bash
python main.py
```

## LLM planner setup

The driver uses an OpenAI-compatible planner that attempts to call an LLM when the environment is configured. If no API key is available, it gracefully falls back to the built-in heuristic planner.

Create a `.env` file with values like:

```bash
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_BASE_URL=https://api.openai.com/v1
```

You can also set `AZURE_OPENAI_API_KEY` and `AZURE_OPENAI_ENDPOINT` if using Azure OpenAI.

## Notes

This scaffold is intentionally modular so each worker can be upgraded with richer prompts, memory, tools, and LLM logic over time.
