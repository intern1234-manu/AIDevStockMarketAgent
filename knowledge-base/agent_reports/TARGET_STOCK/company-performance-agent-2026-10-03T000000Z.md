# company-performance-agent — 2026-10-03T000000Z

## Role
Company-performance intelligence worker.

## Objective
Review the target company’s 5-year performance, strategic direction, and forward-looking drivers without binding the model to a particular stock.

## Findings
- The analysis is now generic and reads the symbol from task context.
- The output stays at a business-quality and strategy level instead of using static stock-specific examples.
- It supports downstream fundamental, history, and risk review.

## Duplicate check
No duplicate task: this worker supplements the market-news and fundamental views rather than repeating them.

## Reminder for future runs
Avoid hardcoded examples for any one company. The agent should use the task symbol and generic business-driver logic only.
