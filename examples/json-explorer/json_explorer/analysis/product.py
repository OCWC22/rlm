"""
Product Analyzer: Product management insights.

Analyzes data for:
- Feature usage and requests
- Bug reports and issues
- User journey pain points
- Product-market fit signals
"""

from .base import BaseAnalyzer, AnalysisQuestion, AnalysisCategory


class ProductAnalyzer(BaseAnalyzer):
    """
    Product-focused analysis for PMs and product teams.
    
    Use cases:
    - Feature prioritization
    - Bug triage
    - User journey analysis
    - Product roadmap input
    """
    
    name = "product"
    description = "Product Management Analysis"
    
    questions = [
        AnalysisQuestion(
            id="feature_usage",
            question="Which features do people mention using the most? What parts of the product get discussed?",
            description="Feature Usage",
            category=AnalysisCategory.QUANTITATIVE,
            priority=1,
        ),
        AnalysisQuestion(
            id="feature_requests",
            question="What new features or improvements are people requesting? Prioritize by frequency and urgency.",
            description="Feature Requests",
            category=AnalysisCategory.DISCOVERY,
            priority=2,
        ),
        AnalysisQuestion(
            id="bugs_issues",
            question="What bugs, errors, crashes, or technical issues are people reporting? Include reproduction steps if mentioned.",
            description="Bugs & Issues",
            category=AnalysisCategory.DISCOVERY,
            priority=3,
        ),
        AnalysisQuestion(
            id="user_journey",
            question="What are the key steps in user journeys? Where do people get stuck or frustrated?",
            description="User Journey Pain Points",
            category=AnalysisCategory.QUALITATIVE,
            priority=4,
        ),
        AnalysisQuestion(
            id="onboarding",
            question="What do people say about getting started, onboarding, or the learning curve?",
            description="Onboarding Experience",
            category=AnalysisCategory.QUALITATIVE,
            priority=5,
        ),
        AnalysisQuestion(
            id="integration_requests",
            question="What integrations, APIs, or third-party connections do people want?",
            description="Integration Requests",
            category=AnalysisCategory.DISCOVERY,
            priority=6,
        ),
        AnalysisQuestion(
            id="power_user_features",
            question="What advanced or power-user features do experienced users want?",
            description="Power User Needs",
            category=AnalysisCategory.DISCOVERY,
            priority=7,
        ),
        AnalysisQuestion(
            id="aha_moments",
            question="What 'aha moments' or breakthrough experiences do users describe?",
            description="Aha Moments",
            category=AnalysisCategory.QUALITATIVE,
            priority=8,
        ),
    ]


class ReleaseAnalyzer(BaseAnalyzer):
    """
    Analyze feedback on a specific release or version.
    """
    
    name = "release"
    description = "Release Feedback Analysis"
    
    def __init__(
        self,
        version: str = "the latest release",
        enabled_questions: list[str] = None,
    ):
        """
        Initialize with version to analyze.
        
        Args:
            version: Version or release name (e.g., "v2.0", "the January update")
        """
        super().__init__(enabled_questions)
        self.version = version
        
        self.questions = [
            AnalysisQuestion(
                id="whats_new",
                question=f"What do people say about the new features in {version}?",
                description="New Feature Reactions",
                category=AnalysisCategory.SENTIMENT,
                priority=1,
            ),
            AnalysisQuestion(
                id="regressions",
                question=f"What regressions, broken features, or 'it used to work' complaints are there about {version}?",
                description="Regressions",
                category=AnalysisCategory.DISCOVERY,
                priority=2,
            ),
            AnalysisQuestion(
                id="upgrade_issues",
                question=f"What upgrade, migration, or installation issues did people have with {version}?",
                description="Upgrade Issues",
                category=AnalysisCategory.DISCOVERY,
                priority=3,
            ),
            AnalysisQuestion(
                id="performance",
                question=f"What do people say about performance, speed, or reliability of {version}?",
                description="Performance Feedback",
                category=AnalysisCategory.SENTIMENT,
                priority=4,
            ),
        ]

