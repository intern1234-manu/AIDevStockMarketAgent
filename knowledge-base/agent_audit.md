# Agent audit and duplicate review

## Objective
This audit checks the worker set, the driver model, and the assignment logic for duplicate responsibilities and stock-specific hardcoding.

## Summary
- The driver remains the central coordinator and is not duplicated.
- Worker roles are unique and complementary rather than overlapping.
- No agent is bound to a specific company in the current implementation.
- Company analysis is symbol-driven and generic; the worker reads the target symbol from task context and performs a reusable evaluation pattern.

## Duplicate-task review
| Worker | Role | Duplicate risk | Assessment |
| --- | --- | --- | --- |
| market-news-collector | live or fallback news and macro sentiment | low | It is distinct from company-performance because it gathers external market news and broader catalysts. |
| company-performance-agent | 5-year performance and strategic review | low | It complements rather than duplicates the news worker; it focuses on structural company quality and plan assessment. |
| chart-analyzer | technical structure | low | Unique to price behavior and trend analysis. |
| market-sentiment-analyzer | broad sentiment and volatility | low | Unique to market mood and broader regime context. |
| history-analyzer | historical pattern review | low | Distinct from technical and fundamental research. |
| fundamental-agent | business quality and valuation | low | Distinct from company-performance because it is a deeper underwriting view. |
| technical-agent | timing and signal review | low | Distinct from chart analysis due to decision-support emphasis. |
| risk-sentiment-agent | risk gate | low | Distinct from sentiment and execution because it validates safety before approval. |
| debate-controller | opposing view synthesis | low | Distinct from decision approval. |
| master-agent | final decision | low | Distinct from debate and execution. |
| execution-agent | broker-safe route | low | Distinct from planning and approval. |

## Stock binding check
The previous version had stock-specific examples embedded in the company report logic. Those examples were removed so the worker now behaves generically for any ticker or symbol passed in context. The agent does not hardcode NVDA, AAPL, or MSFT behavior.

## Recommended guardrails
- Keep every worker symbol-agnostic unless the task explicitly passes a ticker.
- Do not store per-company static logic in the prompt or worker logic.
- Store prompt updates and mistake logs in the knowledge base so each new instruction is reviewed before being promoted.
