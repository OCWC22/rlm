"""
Marketing Analyzer: Community intelligence for marketers.

Analyzes Discord/community exports for:
- Product sentiment
- Feature requests
- Competitive intelligence
- Pricing perception
- Success stories
- Campaign feedback
"""

from .base import BaseAnalyzer, AnalysisQuestion, AnalysisCategory


class MarketingAnalyzer(BaseAnalyzer):
    """
    Marketing-focused analysis of community data.
    
    Use cases:
    - Product marketing research
    - Competitive intelligence
    - Customer voice analysis
    - Campaign effectiveness
    """
    
    name = "marketing"
    description = "Marketing Intelligence Analysis"
    
    questions = [
        AnalysisQuestion(
            id="product_sentiment",
            question="What are people saying about our product? Include all positive and negative feedback with exact quotes and who said them.",
            description="Product Sentiment",
            category=AnalysisCategory.SENTIMENT,
            priority=1,
        ),
        AnalysisQuestion(
            id="feature_requests",
            question="What features, improvements, or capabilities are users requesting? List every request mentioned.",
            description="Feature Requests",
            category=AnalysisCategory.DISCOVERY,
            priority=2,
        ),
        AnalysisQuestion(
            id="pain_points",
            question="What problems, bugs, frustrations, or complaints are users mentioning? Include all issues with context.",
            description="Customer Pain Points",
            category=AnalysisCategory.DISCOVERY,
            priority=3,
        ),
        AnalysisQuestion(
            id="competitor_mentions",
            question="What are people saying about competitors or alternative products? How do they compare our product to others?",
            description="Competitive Intelligence",
            category=AnalysisCategory.COMPARISON,
            priority=4,
        ),
        AnalysisQuestion(
            id="success_stories",
            question="What success stories, wins, or positive outcomes are users sharing? What worked well for them?",
            description="Success Stories",
            category=AnalysisCategory.QUALITATIVE,
            priority=5,
        ),
        AnalysisQuestion(
            id="pricing_feedback",
            question="What are people saying about pricing, cost, value, or affordability? Include all opinions on price.",
            description="Pricing Perception",
            category=AnalysisCategory.SENTIMENT,
            priority=6,
        ),
        AnalysisQuestion(
            id="brand_perception",
            question="How do people describe our brand, company, or team? What reputation do we have?",
            description="Brand Perception",
            category=AnalysisCategory.SENTIMENT,
            priority=7,
        ),
        AnalysisQuestion(
            id="champions",
            question="Who are the most helpful and engaged community members? Who advocates for us?",
            description="Community Champions",
            category=AnalysisCategory.DISCOVERY,
            priority=8,
        ),
    ]


class CampaignAnalyzer(BaseAnalyzer):
    """
    Analyze specific campaign or launch reactions.
    
    Use this when you want to understand response to a specific event.
    """
    
    name = "campaign"
    description = "Campaign & Launch Analysis"
    
    def __init__(
        self,
        campaign_name: str = "the launch",
        enabled_questions: list[str] = None,
    ):
        """
        Initialize with campaign context.
        
        Args:
            campaign_name: Name of campaign to analyze (e.g., "the v2.0 launch")
        """
        super().__init__(enabled_questions)
        self.campaign_name = campaign_name
        
        # Dynamically create questions with campaign name
        self.questions = [
            AnalysisQuestion(
                id="initial_reaction",
                question=f"What was the initial reaction to {campaign_name}? Include all first impressions.",
                description="Initial Reactions",
                category=AnalysisCategory.SENTIMENT,
                priority=1,
            ),
            AnalysisQuestion(
                id="positive_feedback",
                question=f"What positive feedback did {campaign_name} receive? What did people like?",
                description="Positive Feedback",
                category=AnalysisCategory.SENTIMENT,
                priority=2,
            ),
            AnalysisQuestion(
                id="concerns",
                question=f"What concerns, criticisms, or negative feedback did {campaign_name} receive?",
                description="Concerns & Criticism",
                category=AnalysisCategory.SENTIMENT,
                priority=3,
            ),
            AnalysisQuestion(
                id="questions_asked",
                question=f"What questions did people ask about {campaign_name}? What was unclear?",
                description="Questions Raised",
                category=AnalysisCategory.DISCOVERY,
                priority=4,
            ),
            AnalysisQuestion(
                id="suggestions",
                question=f"What suggestions or improvements did people offer for {campaign_name}?",
                description="Suggestions",
                category=AnalysisCategory.DISCOVERY,
                priority=5,
            ),
        ]

