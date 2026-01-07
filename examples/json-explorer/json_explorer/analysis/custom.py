"""
Custom Analyzer: Build your own analysis.

Use this to create ad-hoc analyses with custom questions.
"""

from typing import Optional
import yaml
import json
from pathlib import Path

from .base import BaseAnalyzer, AnalysisQuestion, AnalysisCategory


class CustomAnalyzer(BaseAnalyzer):
    """
    Custom analyzer with user-defined questions.
    
    Use cases:
    - One-off analyses
    - Domain-specific research
    - Experimental queries
    
    Example:
        analyzer = CustomAnalyzer(
            name="my_analysis",
            description="My Custom Analysis",
            questions=[
                AnalysisQuestion(
                    id="custom_q1",
                    question="What patterns exist?",
                    description="Pattern Discovery",
                ),
            ],
        )
    """
    
    def __init__(
        self,
        name: str = "custom",
        description: str = "Custom Analysis",
        questions: Optional[list[AnalysisQuestion]] = None,
        enabled_questions: Optional[list[str]] = None,
    ):
        """
        Initialize custom analyzer.
        
        Args:
            name: Unique name for this analyzer
            description: Human-readable description
            questions: List of AnalysisQuestion objects
            enabled_questions: If provided, only run these question IDs
        """
        super().__init__(enabled_questions)
        self.name = name
        self.description = description
        self.questions = questions or []
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> "CustomAnalyzer":
        """
        Load analyzer from YAML file.
        
        YAML format:
            name: my_analyzer
            description: My Custom Analysis
            questions:
              - id: q1
                question: What patterns exist?
                description: Pattern Discovery
                category: discovery
              - id: q2
                question: What sentiment is present?
                description: Sentiment Analysis
                category: sentiment
        """
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        
        return cls._from_dict(data)
    
    @classmethod
    def from_json(cls, json_path: str) -> "CustomAnalyzer":
        """
        Load analyzer from JSON file.
        """
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        return cls._from_dict(data)
    
    @classmethod
    def _from_dict(cls, data: dict) -> "CustomAnalyzer":
        """Create analyzer from dictionary."""
        category_map = {
            "sentiment": AnalysisCategory.SENTIMENT,
            "discovery": AnalysisCategory.DISCOVERY,
            "quantitative": AnalysisCategory.QUANTITATIVE,
            "qualitative": AnalysisCategory.QUALITATIVE,
            "comparison": AnalysisCategory.COMPARISON,
            "temporal": AnalysisCategory.TEMPORAL,
            "custom": AnalysisCategory.CUSTOM,
        }
        
        questions = []
        for q in data.get("questions", []):
            questions.append(AnalysisQuestion(
                id=q["id"],
                question=q["question"],
                description=q.get("description", q["id"]),
                category=category_map.get(q.get("category", "custom"), AnalysisCategory.CUSTOM),
                exhaustive=q.get("exhaustive", True),
                priority=q.get("priority", 10),
                enabled=q.get("enabled", True),
            ))
        
        return cls(
            name=data.get("name", "custom"),
            description=data.get("description", "Custom Analysis"),
            questions=questions,
        )
    
    def to_yaml(self, output_path: str):
        """Save analyzer definition to YAML."""
        data = {
            "name": self.name,
            "description": self.description,
            "questions": [
                {
                    "id": q.id,
                    "question": q.question,
                    "description": q.description,
                    "category": q.category.value,
                    "exhaustive": q.exhaustive,
                    "priority": q.priority,
                }
                for q in self.questions
            ]
        }
        
        with open(output_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
    
    def to_json(self, output_path: str):
        """Save analyzer definition to JSON."""
        data = {
            "name": self.name,
            "description": self.description,
            "questions": [
                {
                    "id": q.id,
                    "question": q.question,
                    "description": q.description,
                    "category": q.category.value,
                    "exhaustive": q.exhaustive,
                    "priority": q.priority,
                }
                for q in self.questions
            ]
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


class QuickAnalyzer(BaseAnalyzer):
    """
    Quick single-question analyzer.
    
    Use for one-off queries without creating a full analyzer.
    
    Example:
        analyzer = QuickAnalyzer(
            question="What are people saying about pricing?"
        )
        result = analyzer.run(explorer)
    """
    
    def __init__(
        self,
        question: str,
        question_id: str = "quick_query",
        description: str = None,
        exhaustive: bool = True,
    ):
        """
        Initialize quick analyzer.
        
        Args:
            question: The question to ask
            question_id: ID for the question (used in reports)
            description: Optional description
            exhaustive: Whether to find every mention
        """
        super().__init__()
        
        self.name = "quick"
        self.description = description or question[:50] + "..."
        
        self.questions = [
            AnalysisQuestion(
                id=question_id,
                question=question,
                description=description or question[:50],
                category=AnalysisCategory.CUSTOM,
                exhaustive=exhaustive,
                priority=1,
            )
        ]


def create_analyzer_template(output_path: str):
    """
    Create a template analyzer YAML file for users to customize.
    """
    template = """# Custom Analyzer Template
# Edit this file to create your own analysis

name: my_custom_analysis
description: My Custom Analysis

# Add your questions below
questions:
  # Question 1: Discovery
  - id: main_themes
    question: What are the main themes or topics discussed?
    description: Theme Discovery
    category: discovery
    exhaustive: true
    priority: 1

  # Question 2: Sentiment
  - id: sentiment
    question: What is the overall sentiment? Is it positive, negative, or mixed?
    description: Sentiment Analysis
    category: sentiment
    priority: 2

  # Question 3: Custom
  - id: custom_query
    question: Replace this with your own question
    description: My Custom Question
    category: custom
    priority: 3

# Category options:
#   - sentiment: Opinion and emotion analysis
#   - discovery: Finding patterns and themes
#   - quantitative: Counting and measuring
#   - qualitative: Deep understanding
#   - comparison: Comparing things
#   - temporal: Time-based analysis
#   - custom: Everything else
"""
    
    with open(output_path, 'w') as f:
        f.write(template)
    
    return output_path

