"""
Research Analyzer: Academic and user research analysis.

Analyzes data for:
- Themes and patterns
- User behavior insights
- Trends over time
- Key opinions and debates
"""

from .base import BaseAnalyzer, AnalysisQuestion, AnalysisCategory


class ResearchAnalyzer(BaseAnalyzer):
    """
    Research-focused analysis for academics and UX researchers.
    
    Use cases:
    - User research synthesis
    - Theme extraction
    - Pattern identification
    - Trend analysis
    """
    
    name = "research"
    description = "Research & Discovery Analysis"
    
    questions = [
        AnalysisQuestion(
            id="main_themes",
            question="What are the main themes, topics, and subjects discussed? Group related discussions together.",
            description="Main Themes",
            category=AnalysisCategory.DISCOVERY,
            priority=1,
        ),
        AnalysisQuestion(
            id="user_behaviors",
            question="What user behaviors, habits, or workflows are mentioned? How do people use the product or service?",
            description="User Behaviors",
            category=AnalysisCategory.QUALITATIVE,
            priority=2,
        ),
        AnalysisQuestion(
            id="mental_models",
            question="What mental models or assumptions do users have? How do they think about the product or domain?",
            description="Mental Models",
            category=AnalysisCategory.QUALITATIVE,
            priority=3,
        ),
        AnalysisQuestion(
            id="unmet_needs",
            question="What unmet needs, gaps, or missing capabilities are users expressing? What are they trying but failing to do?",
            description="Unmet Needs",
            category=AnalysisCategory.DISCOVERY,
            priority=4,
        ),
        AnalysisQuestion(
            id="terminology",
            question="What terminology, jargon, or language do users use to describe things? What are their own words?",
            description="User Language",
            category=AnalysisCategory.QUALITATIVE,
            priority=5,
        ),
        AnalysisQuestion(
            id="debates",
            question="What debates, disagreements, or differing opinions exist in the community? Where do people disagree?",
            description="Debates & Disagreements",
            category=AnalysisCategory.COMPARISON,
            priority=6,
        ),
        AnalysisQuestion(
            id="expertise_levels",
            question="What different expertise levels or personas are visible? Who are the experts vs beginners?",
            description="User Personas",
            category=AnalysisCategory.DISCOVERY,
            priority=7,
        ),
        AnalysisQuestion(
            id="workarounds",
            question="What workarounds, hacks, or creative solutions have users developed?",
            description="User Workarounds",
            category=AnalysisCategory.DISCOVERY,
            priority=8,
        ),
    ]


class TopicAnalyzer(BaseAnalyzer):
    """
    Analyze a specific topic in depth.
    
    Use when you want exhaustive information about one subject.
    """
    
    name = "topic"
    description = "Deep Topic Analysis"
    
    def __init__(
        self,
        topic: str,
        enabled_questions: list[str] = None,
    ):
        """
        Initialize with topic to analyze.
        
        Args:
            topic: The topic to analyze (e.g., "Kling 2.6", "video generation")
        """
        super().__init__(enabled_questions)
        self.topic = topic
        
        # Create questions about this topic
        self.questions = [
            AnalysisQuestion(
                id="all_mentions",
                question=f"What are people saying about {topic}? Find every single mention with full context.",
                description=f"All Mentions of {topic}",
                category=AnalysisCategory.DISCOVERY,
                exhaustive=True,
                priority=1,
            ),
            AnalysisQuestion(
                id="opinions",
                question=f"What opinions do people have about {topic}? Include positive, negative, and neutral views.",
                description=f"Opinions on {topic}",
                category=AnalysisCategory.SENTIMENT,
                priority=2,
            ),
            AnalysisQuestion(
                id="comparisons",
                question=f"How do people compare {topic} to alternatives or competitors?",
                description=f"Comparisons of {topic}",
                category=AnalysisCategory.COMPARISON,
                priority=3,
            ),
            AnalysisQuestion(
                id="use_cases",
                question=f"What use cases, applications, or examples of {topic} do people discuss?",
                description=f"Use Cases for {topic}",
                category=AnalysisCategory.QUALITATIVE,
                priority=4,
            ),
            AnalysisQuestion(
                id="questions",
                question=f"What questions do people ask about {topic}? What are they trying to understand?",
                description=f"Questions about {topic}",
                category=AnalysisCategory.DISCOVERY,
                priority=5,
            ),
        ]

