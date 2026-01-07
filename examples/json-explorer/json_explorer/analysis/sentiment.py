"""
Sentiment Analyzer: General sentiment and opinion analysis.

Analyzes data for:
- Overall sentiment
- Emotional tone
- Opinion distribution
- Influence patterns
"""

from .base import BaseAnalyzer, AnalysisQuestion, AnalysisCategory


class SentimentAnalyzer(BaseAnalyzer):
    """
    Sentiment and opinion analysis.
    
    Use cases:
    - Brand sentiment monitoring
    - Community health check
    - Opinion tracking
    - Influencer identification
    """
    
    name = "sentiment"
    description = "Sentiment & Opinion Analysis"
    
    questions = [
        AnalysisQuestion(
            id="overall_sentiment",
            question="What is the overall sentiment of the community? Is it positive, negative, or neutral? Give examples.",
            description="Overall Sentiment",
            category=AnalysisCategory.SENTIMENT,
            priority=1,
        ),
        AnalysisQuestion(
            id="positive_highlights",
            question="What are people most positive about? What generates enthusiasm and praise?",
            description="Positive Highlights",
            category=AnalysisCategory.SENTIMENT,
            priority=2,
        ),
        AnalysisQuestion(
            id="negative_concerns",
            question="What are people most negative about? What generates complaints and frustration?",
            description="Negative Concerns",
            category=AnalysisCategory.SENTIMENT,
            priority=3,
        ),
        AnalysisQuestion(
            id="emotional_peaks",
            question="What topics or events generated the strongest emotional reactions?",
            description="Emotional Peaks",
            category=AnalysisCategory.SENTIMENT,
            priority=4,
        ),
        AnalysisQuestion(
            id="influencers",
            question="Who are the most influential voices in the community? Who shapes opinions?",
            description="Key Influencers",
            category=AnalysisCategory.DISCOVERY,
            priority=5,
        ),
        AnalysisQuestion(
            id="trust_signals",
            question="What builds or breaks trust? What do people say about reliability and trustworthiness?",
            description="Trust Signals",
            category=AnalysisCategory.SENTIMENT,
            priority=6,
        ),
        AnalysisQuestion(
            id="recommendations",
            question="What do people recommend to others? What advice do they give?",
            description="Recommendations",
            category=AnalysisCategory.QUALITATIVE,
            priority=7,
        ),
        AnalysisQuestion(
            id="nps_signals",
            question="Would people recommend this product? What signals loyalty or churn risk?",
            description="NPS Signals",
            category=AnalysisCategory.SENTIMENT,
            priority=8,
        ),
    ]

