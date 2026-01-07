"""
Analysis Framework: Modular analysis pipelines for JSON data.

This package provides:
- BaseAnalyzer: Abstract base for all analyzers
- AnalysisPipeline: Run multiple analyzers and generate reports
- Built-in analyzers: Marketing, Research, Product, Support

Usage:
    from json_explorer.analysis import AnalysisPipeline, MarketingAnalyzer
    
    pipeline = AnalysisPipeline(explorer)
    pipeline.add_analyzer(MarketingAnalyzer())
    results = pipeline.run()
    pipeline.save_reports("./reports")

Custom analyzer:
    from json_explorer.analysis import BaseAnalyzer, AnalysisQuestion
    
    class MyAnalyzer(BaseAnalyzer):
        name = "my_analyzer"
        description = "My custom analysis"
        
        questions = [
            AnalysisQuestion(
                id="my_question",
                question="What patterns exist?",
                description="Pattern analysis",
            ),
        ]
"""

from .base import (
    BaseAnalyzer,
    AnalysisQuestion,
    AnalysisResult,
    AnalysisPipeline,
    AnalysisReport,
    AnalysisCategory,
)

from .marketing import MarketingAnalyzer, CampaignAnalyzer
from .research import ResearchAnalyzer, TopicAnalyzer
from .product import ProductAnalyzer, ReleaseAnalyzer
from .support import SupportAnalyzer, OnboardingAnalyzer
from .sentiment import SentimentAnalyzer
from .custom import CustomAnalyzer, QuickAnalyzer, create_analyzer_template
from .specialized import (
    CompetitorAnalyzer,
    TrendAnalyzer,
    InfluencerAnalyzer,
    PricingAnalyzer,
    BugAnalyzer,
    OnboardingDeepDive,
)

__all__ = [
    # Base classes
    "BaseAnalyzer",
    "AnalysisQuestion",
    "AnalysisResult",
    "AnalysisPipeline",
    "AnalysisReport",
    "AnalysisCategory",
    
    # Core analyzers
    "MarketingAnalyzer",
    "ResearchAnalyzer",
    "ProductAnalyzer",
    "SupportAnalyzer",
    "SentimentAnalyzer",
    
    # Parametric analyzers
    "CampaignAnalyzer",  # Analyze specific campaign/launch
    "TopicAnalyzer",     # Deep dive on specific topic
    "ReleaseAnalyzer",   # Analyze specific release
    "OnboardingAnalyzer",
    
    # Specialized analyzers
    "CompetitorAnalyzer",
    "TrendAnalyzer",
    "InfluencerAnalyzer",
    "PricingAnalyzer",
    "BugAnalyzer",
    "OnboardingDeepDive",
    
    # Custom/quick analysis
    "CustomAnalyzer",
    "QuickAnalyzer",
    "create_analyzer_template",
]

