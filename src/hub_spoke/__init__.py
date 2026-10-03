"""Hub-and-spoke agent orchestration package for the trading system."""

from .models import AgentTask, AgentResult
from .driver_agent import StockPlannerDriver
from .queue import QueueTask, TaskQueue
from .roadmap import STOCK_TRADING_ROADMAP, build_stock_trading_queue
from .workflow import WorkflowEngine, WorkflowResult
from .workers import (
    HistoryAnalyzerAgent,
    StageBuildSequenceAgent,
    EnvironmentChecksAgent,
    PaperTradingAgent,
    ShadowModeAgent,
    LiveModeAgent,
    ObservabilityAgent,
    ModelDiversityAgent,
    FundamentalAgent,
    TechnicalAgent,
    RiskSentimentAgent,
    DebateControllerAgent,
    MasterAgent,
    ExecutionAgent,
    MarketNewsCollectorAgent,
    CompanyPerformanceAgent,
    ChartAnalyzerAgent,
    MarketSentimentAnalyzerAgent,
)

__all__ = [
    "AgentTask",
    "AgentResult",
    "QueueTask",
    "TaskQueue",
    "StockPlannerDriver",
    "WorkflowEngine",
    "WorkflowResult",
    "STOCK_TRADING_ROADMAP",
    "build_stock_trading_queue",
    "HistoryAnalyzerAgent",
    "StageBuildSequenceAgent",
    "EnvironmentChecksAgent",
    "PaperTradingAgent",
    "ShadowModeAgent",
    "LiveModeAgent",
    "ObservabilityAgent",
    "ModelDiversityAgent",
    "FundamentalAgent",
    "TechnicalAgent",
    "RiskSentimentAgent",
    "DebateControllerAgent",
    "MasterAgent",
    "ExecutionAgent",
    "MarketNewsCollectorAgent",
    "CompanyPerformanceAgent",
    "ChartAnalyzerAgent",
    "MarketSentimentAnalyzerAgent",
]
