import os
import tempfile
import unittest

from src.hub_spoke.driver_agent import StockPlannerDriver
from src.hub_spoke.models import AgentTask
from src.hub_spoke.worker_graph import resolve_execution_order, resolve_parallel_stages
from src.hub_spoke.workers.base_agent import BaseWorkerAgent
from src.hub_spoke.workers.fundamental_agent import FundamentalAgent
from src.hub_spoke.workers.market_news_agent import MarketNewsCollectorAgent
from src.hub_spoke.workers.chart_analyzer import ChartAnalyzerAgent
from src.hub_spoke.workers.market_sentiment_agent import MarketSentimentAnalyzerAgent
from src.hub_spoke.workers.company_performance_agent import CompanyPerformanceAgent


class ExecutionGraphTests(unittest.TestCase):
    def test_driver_respects_dependency_order(self):
        driver = StockPlannerDriver()
        task = AgentTask(
            task_id="T-100",
            title="Risk and paper-trading plan",
            description="Assess volatility and prepare a paper-trading rollout with execution and risk reviews.",
            priority="high",
            tags=["risk", "paper", "execution"],
            context={"market": "us_equities"},
        )
        ordered = driver.classify_task(task)
        self.assertTrue(ordered.index("history") < ordered.index("risk"))
        self.assertTrue(ordered.index("risk") < ordered.index("execution"))
        self.assertTrue(ordered.index("execution") < ordered.index("paper"))

    def test_dependency_graph_topological_sort(self):
        order = resolve_execution_order(["execution", "paper", "risk"])
        self.assertLess(order.index("history"), order.index("risk"))
        self.assertLess(order.index("risk"), order.index("execution"))
        self.assertLess(order.index("execution"), order.index("paper"))

    def test_state_based_routing_follows_market_analysis_to_broker_flow(self):
        task = AgentTask(
            task_id="S-1",
            title="Broker execution review",
            description="Confirm the signal, risk controls, and order routing before execution.",
            priority="critical",
            state="broker_execution",
            tags=["broker", "execution", "risk"],
            context={"workflow_state": "broker_execution"},
        )
        ordered = StockPlannerDriver().classify_task(task)
        self.assertIn("history", ordered)
        self.assertIn("risk", ordered)
        self.assertIn("execution", ordered)
        self.assertLess(ordered.index("history"), ordered.index("risk"))
        self.assertLess(ordered.index("risk"), ordered.index("execution"))

    def test_worker_has_queue_and_memory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            worker = FundamentalAgent(state_dir=tmpdir)
            task = AgentTask(
                task_id="Q-1",
                title="Fundamental review",
                description="Evaluate the earnings quality and valuation thesis.",
                priority="normal",
                tags=["fundamental"],
                context={"symbol": "MSFT"},
            )
            worker.enqueue(task)
            worker.write_memory("symbol", "MSFT")
            result = worker.execute(task)
            self.assertEqual(len(worker.task_queue), 1)
            self.assertEqual(worker.read_memory("symbol"), "MSFT")
            self.assertEqual(result.task_id, task.task_id)
            self.assertIn("MSFT", str(worker.memory))

    def test_market_news_agent_collects_news_and_52_week_context(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = MarketNewsCollectorAgent(state_dir=tmpdir)
            task = AgentTask(
                task_id="NEWS-1",
                title="Market pulse for NVDA",
                description="Check circulating news and macro drivers for NVIDIA and the surrounding market environment.",
                priority="high",
                tags=["news", "market", "nvda"],
                context={"symbol": "NVDA", "market": "us_equities"},
            )
            result = agent.execute(task)
            self.assertEqual(result.task_id, task.task_id)
            details = result.details
            self.assertIn("NVDA", details.get("symbol", ""))
            self.assertIn("screener", str(details.get("screener_52_week_url", "")).lower())
            self.assertTrue(details.get("news_items") or details.get("news_summary"))
            self.assertTrue(details.get("market_factors"))

    def test_company_performance_agent_creates_5_year_report_and_routes_review(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = CompanyPerformanceAgent(state_dir=tmpdir)
            task = AgentTask(
                task_id="COMP-1",
                title="NVDA company performance review",
                description="Check NVDA performance over the last 5 years, current news, and future strategic plans that could affect the stock.",
                priority="high",
                tags=["company", "performance", "news", "guidance"],
                context={"symbol": "NVDA", "market": "us_equities"},
            )
            result = agent.execute(task)
            details = result.details
            self.assertEqual(result.task_id, task.task_id)
            self.assertIn("NVDA", details.get("symbol", ""))
            self.assertEqual(details.get("performance_window"), "5Y")
            self.assertTrue(details.get("news_items") or details.get("news_summary"))
            self.assertTrue(details.get("future_plan_summary") or details.get("strategy_outlook"))
            self.assertIn("fundamental", details.get("agents_to_review", []))
            self.assertIn("history", details.get("agents_to_review", []))
            self.assertIn("risk", details.get("agents_to_review", []))

    def test_parallel_market_analysis_runs_before_broker_gate(self):
        stages = resolve_parallel_stages(["news", "chart", "sentiment", "company", "history", "risk", "execution"])
        self.assertIn(["news", "chart", "sentiment", "company"], stages)
        self.assertIn(["history"], stages)
        self.assertIn(["risk"], stages)
        self.assertIn(["execution"], stages)
        self.assertLess(stages.index(["news", "chart", "sentiment", "company"]), stages.index(["history"]))
        self.assertLess(stages.index(["history"]), stages.index(["risk"]))
        self.assertLess(stages.index(["risk"]), stages.index(["execution"]))

    def test_worker_priority_defaults_follow_industry_standard(self):
        self.assertEqual(BaseWorkerAgent.priority, "normal")
        self.assertEqual(FundamentalAgent.priority, "high")
        self.assertEqual(FundamentalAgent().priority, "high")
        self.assertEqual(FundamentalAgent().priority, "high")
        self.assertEqual(FundamentalAgent.priority, "high")
        self.assertEqual(FundamentalAgent().read_memory("missing", "fallback"), "fallback")

    def test_worker_state_persists_across_restart(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            worker = FundamentalAgent(state_dir=tmpdir)
            task = AgentTask(
                task_id="persist-1",
                title="Persisted fundamental review",
                description="Store the review for later restart and replay.",
                priority="high",
                tags=["fundamental"],
                context={"symbol": "AAPL"},
            )
            worker.enqueue(task)
            worker.write_memory("symbol", "AAPL")
            worker.persist_state()

            restored = FundamentalAgent(state_dir=tmpdir)
            restored.load_state()
            self.assertEqual(restored.read_memory("symbol"), "AAPL")
            self.assertEqual(len(restored.task_queue), 1)
            self.assertEqual(restored.peek_queue().task_id, "persist-1")
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "fundamental-agent-state.json")))


if __name__ == "__main__":
    unittest.main()
