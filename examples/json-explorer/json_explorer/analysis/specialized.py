"""
Specialized Analyzers: Domain-specific analysis modules.

These are more focused analyzers for specific use cases.
"""

from typing import Optional

from .base import BaseAnalyzer, AnalysisQuestion, AnalysisCategory


class CompetitorAnalyzer(BaseAnalyzer):
    """
    Analyze competitor mentions and comparisons.
    
    Use when you want to understand how competitors are perceived.
    """
    
    name = "competitors"
    description = "Competitive Intelligence Analysis"
    
    def __init__(
        self,
        competitors: Optional[list[str]] = None,
        enabled_questions: Optional[list[str]] = None,
    ):
        """
        Initialize competitor analyzer.
        
        Args:
            competitors: List of competitor names to track specifically
        """
        super().__init__(enabled_questions)
        self.competitors = competitors or []
        
        # Base questions
        self.questions = [
            AnalysisQuestion(
                id="competitor_mentions",
                question="Which competitors, alternatives, or similar products are mentioned? In what context?",
                description="All Competitor Mentions",
                category=AnalysisCategory.DISCOVERY,
                priority=1,
            ),
            AnalysisQuestion(
                id="comparisons",
                question="How do people compare our product to competitors? What are the pros and cons?",
                description="Product Comparisons",
                category=AnalysisCategory.COMPARISON,
                priority=2,
            ),
            AnalysisQuestion(
                id="switching_reasons",
                question="Why do people switch to or from competitors? What triggers switching?",
                description="Switching Reasons",
                category=AnalysisCategory.QUALITATIVE,
                priority=3,
            ),
            AnalysisQuestion(
                id="competitor_advantages",
                question="What advantages do people say competitors have over us?",
                description="Competitor Advantages",
                category=AnalysisCategory.COMPARISON,
                priority=4,
            ),
            AnalysisQuestion(
                id="our_advantages",
                question="What advantages do people say we have over competitors?",
                description="Our Advantages",
                category=AnalysisCategory.COMPARISON,
                priority=5,
            ),
        ]
        
        # Add specific competitor questions
        for competitor in self.competitors:
            self.questions.append(AnalysisQuestion(
                id=f"competitor_{competitor.lower().replace(' ', '_')}",
                question=f"What are people saying about {competitor}? How does it compare to us?",
                description=f"{competitor} Analysis",
                category=AnalysisCategory.COMPARISON,
                priority=10,
            ))


class TrendAnalyzer(BaseAnalyzer):
    """
    Analyze trends, changes, and emerging topics.
    """
    
    name = "trends"
    description = "Trend & Change Analysis"
    
    questions = [
        AnalysisQuestion(
            id="emerging_topics",
            question="What new or emerging topics are people starting to discuss?",
            description="Emerging Topics",
            category=AnalysisCategory.DISCOVERY,
            priority=1,
        ),
        AnalysisQuestion(
            id="growing_concerns",
            question="What concerns or issues are becoming more frequent or urgent?",
            description="Growing Concerns",
            category=AnalysisCategory.TEMPORAL,
            priority=2,
        ),
        AnalysisQuestion(
            id="changing_sentiment",
            question="How has sentiment or opinion changed over time? What shifted?",
            description="Sentiment Shifts",
            category=AnalysisCategory.TEMPORAL,
            priority=3,
        ),
        AnalysisQuestion(
            id="fading_topics",
            question="What topics or issues seem to be fading or resolved?",
            description="Fading Topics",
            category=AnalysisCategory.TEMPORAL,
            priority=4,
        ),
        AnalysisQuestion(
            id="predictions",
            question="What predictions or expectations do people have for the future?",
            description="Future Predictions",
            category=AnalysisCategory.QUALITATIVE,
            priority=5,
        ),
    ]


class InfluencerAnalyzer(BaseAnalyzer):
    """
    Identify influential voices and key community members.
    """
    
    name = "influencers"
    description = "Influencer & Community Analysis"
    
    questions = [
        AnalysisQuestion(
            id="top_contributors",
            question="Who are the most active or influential contributors in the community?",
            description="Top Contributors",
            category=AnalysisCategory.DISCOVERY,
            priority=1,
        ),
        AnalysisQuestion(
            id="thought_leaders",
            question="Who provides the most insightful, helpful, or authoritative information?",
            description="Thought Leaders",
            category=AnalysisCategory.QUALITATIVE,
            priority=2,
        ),
        AnalysisQuestion(
            id="advocates",
            question="Who actively advocates or recommends the product to others?",
            description="Product Advocates",
            category=AnalysisCategory.DISCOVERY,
            priority=3,
        ),
        AnalysisQuestion(
            id="critics",
            question="Who are the most vocal critics? What are their main complaints?",
            description="Vocal Critics",
            category=AnalysisCategory.SENTIMENT,
            priority=4,
        ),
        AnalysisQuestion(
            id="community_dynamics",
            question="What are the dynamics between community members? Any notable interactions?",
            description="Community Dynamics",
            category=AnalysisCategory.QUALITATIVE,
            priority=5,
        ),
    ]


class PricingAnalyzer(BaseAnalyzer):
    """
    Deep dive into pricing perception and value.
    """
    
    name = "pricing"
    description = "Pricing & Value Analysis"
    
    questions = [
        AnalysisQuestion(
            id="price_sentiment",
            question="What is the overall sentiment about pricing? Is it seen as fair, expensive, or cheap?",
            description="Price Sentiment",
            category=AnalysisCategory.SENTIMENT,
            priority=1,
        ),
        AnalysisQuestion(
            id="value_perception",
            question="Do people feel they get good value for money? What drives value perception?",
            description="Value Perception",
            category=AnalysisCategory.SENTIMENT,
            priority=2,
        ),
        AnalysisQuestion(
            id="pricing_model",
            question="What do people say about the pricing model (subscription, one-time, tiers)?",
            description="Pricing Model Feedback",
            category=AnalysisCategory.QUALITATIVE,
            priority=3,
        ),
        AnalysisQuestion(
            id="price_comparisons",
            question="How do people compare our pricing to alternatives?",
            description="Price Comparisons",
            category=AnalysisCategory.COMPARISON,
            priority=4,
        ),
        AnalysisQuestion(
            id="willingness_to_pay",
            question="What would people be willing to pay? What price points are mentioned?",
            description="Willingness to Pay",
            category=AnalysisCategory.QUANTITATIVE,
            priority=5,
        ),
        AnalysisQuestion(
            id="deal_breakers",
            question="What pricing aspects are deal-breakers or cause people to leave?",
            description="Pricing Deal-Breakers",
            category=AnalysisCategory.DISCOVERY,
            priority=6,
        ),
    ]


class BugAnalyzer(BaseAnalyzer):
    """
    Focus on bugs, issues, and technical problems.
    """
    
    name = "bugs"
    description = "Bug & Issue Analysis"
    
    questions = [
        AnalysisQuestion(
            id="reported_bugs",
            question="What bugs, errors, or technical issues are people reporting? Include error messages.",
            description="Reported Bugs",
            category=AnalysisCategory.DISCOVERY,
            priority=1,
        ),
        AnalysisQuestion(
            id="reproduction_steps",
            question="What steps or conditions lead to bugs? How do people reproduce issues?",
            description="Reproduction Steps",
            category=AnalysisCategory.QUALITATIVE,
            priority=2,
        ),
        AnalysisQuestion(
            id="affected_areas",
            question="Which features or areas of the product have the most reported issues?",
            description="Affected Areas",
            category=AnalysisCategory.QUANTITATIVE,
            priority=3,
        ),
        AnalysisQuestion(
            id="workarounds",
            question="What workarounds have people found for bugs or issues?",
            description="User Workarounds",
            category=AnalysisCategory.DISCOVERY,
            priority=4,
        ),
        AnalysisQuestion(
            id="severity",
            question="Which bugs seem most severe or urgent based on user frustration?",
            description="Bug Severity",
            category=AnalysisCategory.SENTIMENT,
            priority=5,
        ),
    ]


class OnboardingDeepDive(BaseAnalyzer):
    """
    Deep analysis of onboarding and new user experience.
    """
    
    name = "onboarding_deep"
    description = "Onboarding Deep Dive Analysis"
    
    questions = [
        AnalysisQuestion(
            id="first_impressions",
            question="What are people's first impressions when they start using the product?",
            description="First Impressions",
            category=AnalysisCategory.SENTIMENT,
            priority=1,
        ),
        AnalysisQuestion(
            id="setup_friction",
            question="What friction or difficulty do people experience during setup?",
            description="Setup Friction",
            category=AnalysisCategory.DISCOVERY,
            priority=2,
        ),
        AnalysisQuestion(
            id="time_to_value",
            question="How long does it take people to get value? What helps or delays this?",
            description="Time to Value",
            category=AnalysisCategory.QUALITATIVE,
            priority=3,
        ),
        AnalysisQuestion(
            id="tutorial_feedback",
            question="What do people say about tutorials, docs, or onboarding materials?",
            description="Tutorial Feedback",
            category=AnalysisCategory.SENTIMENT,
            priority=4,
        ),
        AnalysisQuestion(
            id="early_drops",
            question="What causes people to give up or abandon during onboarding?",
            description="Abandonment Reasons",
            category=AnalysisCategory.DISCOVERY,
            priority=5,
        ),
        AnalysisQuestion(
            id="successful_starts",
            question="What do successful new users do differently? What's the happy path?",
            description="Success Patterns",
            category=AnalysisCategory.QUALITATIVE,
            priority=6,
        ),
    ]

