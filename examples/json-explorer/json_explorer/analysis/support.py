"""
Support Analyzer: Customer support and success insights.

Analyzes data for:
- Common support issues
- FAQ candidates
- Documentation gaps
- Self-service opportunities
"""

from .base import BaseAnalyzer, AnalysisQuestion, AnalysisCategory


class SupportAnalyzer(BaseAnalyzer):
    """
    Support-focused analysis for CS and success teams.
    
    Use cases:
    - FAQ generation
    - Knowledge base improvement
    - Support ticket reduction
    - Self-service optimization
    """
    
    name = "support"
    description = "Customer Support Analysis"
    
    questions = [
        AnalysisQuestion(
            id="common_questions",
            question="What questions do people ask most frequently? What are the common support topics?",
            description="Common Questions (FAQ)",
            category=AnalysisCategory.QUANTITATIVE,
            priority=1,
        ),
        AnalysisQuestion(
            id="how_to_questions",
            question="What 'how do I...' or tutorial-type questions do people ask?",
            description="How-To Questions",
            category=AnalysisCategory.DISCOVERY,
            priority=2,
        ),
        AnalysisQuestion(
            id="troubleshooting",
            question="What error messages, troubleshooting steps, or fixes do people discuss?",
            description="Troubleshooting Patterns",
            category=AnalysisCategory.DISCOVERY,
            priority=3,
        ),
        AnalysisQuestion(
            id="documentation_gaps",
            question="What documentation, guides, or help content do people say is missing or unclear?",
            description="Documentation Gaps",
            category=AnalysisCategory.DISCOVERY,
            priority=4,
        ),
        AnalysisQuestion(
            id="community_solutions",
            question="What solutions do community members provide to each other? What works?",
            description="Community Solutions",
            category=AnalysisCategory.QUALITATIVE,
            priority=5,
        ),
        AnalysisQuestion(
            id="escalation_patterns",
            question="What issues cause frustration or require escalation? What makes people angry?",
            description="Escalation Triggers",
            category=AnalysisCategory.SENTIMENT,
            priority=6,
        ),
        AnalysisQuestion(
            id="response_time",
            question="What do people say about response times, support quality, or help availability?",
            description="Support Experience",
            category=AnalysisCategory.SENTIMENT,
            priority=7,
        ),
        AnalysisQuestion(
            id="self_service",
            question="What could people do themselves if they had better tools or docs?",
            description="Self-Service Opportunities",
            category=AnalysisCategory.DISCOVERY,
            priority=8,
        ),
    ]


class OnboardingAnalyzer(BaseAnalyzer):
    """
    Analyze onboarding and new user experience.
    """
    
    name = "onboarding"
    description = "Onboarding Experience Analysis"
    
    questions = [
        AnalysisQuestion(
            id="first_steps",
            question="What do new users say about their first experience? What's their initial reaction?",
            description="First Impressions",
            category=AnalysisCategory.SENTIMENT,
            priority=1,
        ),
        AnalysisQuestion(
            id="confusion_points",
            question="Where do new users get confused, stuck, or ask for help?",
            description="Confusion Points",
            category=AnalysisCategory.DISCOVERY,
            priority=2,
        ),
        AnalysisQuestion(
            id="setup_issues",
            question="What setup, installation, or configuration issues do new users face?",
            description="Setup Issues",
            category=AnalysisCategory.DISCOVERY,
            priority=3,
        ),
        AnalysisQuestion(
            id="missing_guidance",
            question="What guidance, tutorials, or onboarding content do users say is missing?",
            description="Missing Guidance",
            category=AnalysisCategory.DISCOVERY,
            priority=4,
        ),
        AnalysisQuestion(
            id="success_path",
            question="What did successful new users do? What's the happy path?",
            description="Success Path",
            category=AnalysisCategory.QUALITATIVE,
            priority=5,
        ),
    ]

