"""
Base Analysis Framework: Domain-agnostic analysis infrastructure.

Design Philosophy:
- Analyzers are pluggable modules with predefined questions
- Pipeline orchestrates multiple analyzers
- Reports are standardized but customizable
- Easy to extend for any domain (marketing, research, support, etc.)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, Any
from enum import Enum
import json


class AnalysisCategory(Enum):
    """Categories of analysis for organization."""
    SENTIMENT = "sentiment"
    DISCOVERY = "discovery"
    QUANTITATIVE = "quantitative"
    QUALITATIVE = "qualitative"
    COMPARISON = "comparison"
    TEMPORAL = "temporal"
    CUSTOM = "custom"


@dataclass
class AnalysisQuestion:
    """
    A single analysis question to run.
    
    Attributes:
        id: Unique identifier (used for filenames)
        question: The natural language question to ask
        description: Human-readable description
        category: Type of analysis
        exhaustive: Whether to find EVERY mention (slower but complete)
        priority: Order of importance (lower = more important)
        enabled: Whether to run this question
        post_processor: Optional function to process the result
    """
    id: str
    question: str
    description: str
    category: AnalysisCategory = AnalysisCategory.DISCOVERY
    exhaustive: bool = True  # Find every mention by default
    priority: int = 10
    enabled: bool = True
    post_processor: Optional[Callable[[str], str]] = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "question": self.question,
            "description": self.description,
            "category": self.category.value,
            "exhaustive": self.exhaustive,
            "priority": self.priority,
        }


@dataclass
class AnalysisResult:
    """
    Result from running a single analysis question.
    """
    question: AnalysisQuestion
    answer: str
    success: bool
    
    # Stats
    citations_found: int = 0
    unique_authors: int = 0
    positive_mentions: int = 0
    negative_mentions: int = 0
    neutral_mentions: int = 0
    tokens_used: int = 0
    duration_ms: float = 0
    
    # References for verification
    reference_ids: list[str] = field(default_factory=list)
    
    # Error info
    error: Optional[str] = None
    
    # Raw result object (for full access)
    raw_result: Optional[Any] = None
    
    @property
    def sentiment_label(self) -> str:
        """Get overall sentiment label."""
        if self.positive_mentions > self.negative_mentions:
            return "positive"
        elif self.negative_mentions > self.positive_mentions:
            return "negative"
        return "neutral"
    
    @property
    def sentiment_emoji(self) -> str:
        """Get sentiment emoji."""
        if self.positive_mentions > self.negative_mentions:
            return "🟢"
        elif self.negative_mentions > self.positive_mentions:
            return "🔴"
        return "🟡"
    
    def to_dict(self) -> dict:
        return {
            "question": self.question.to_dict(),
            "answer": self.answer,
            "success": self.success,
            "citations_found": self.citations_found,
            "unique_authors": self.unique_authors,
            "positive_mentions": self.positive_mentions,
            "negative_mentions": self.negative_mentions,
            "neutral_mentions": self.neutral_mentions,
            "tokens_used": self.tokens_used,
            "duration_ms": self.duration_ms,
            "reference_ids": self.reference_ids[:20],
            "error": self.error,
        }


@dataclass
class AnalysisReport:
    """
    Complete report from an analyzer.
    """
    analyzer_name: str
    analyzer_description: str
    source_file: Optional[str]
    generated_at: str
    
    results: list[AnalysisResult] = field(default_factory=list)
    
    # Aggregated stats
    total_questions: int = 0
    successful_questions: int = 0
    total_citations: int = 0
    total_tokens: int = 0
    
    def add_result(self, result: AnalysisResult):
        """Add a result and update stats."""
        self.results.append(result)
        self.total_questions += 1
        if result.success:
            self.successful_questions += 1
        self.total_citations += result.citations_found
        self.total_tokens += result.tokens_used
    
    def to_markdown(self) -> str:
        """Generate markdown report."""
        lines = [
            f"# {self.analyzer_description}",
            "",
            f"**Source:** `{self.source_file or 'N/A'}`",
            f"**Generated:** {self.generated_at}",
            "",
            "---",
            "",
            "## 📊 Overview",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Questions Run | {self.total_questions} |",
            f"| Successful | {self.successful_questions} |",
            f"| Total Citations | {self.total_citations:,} |",
            f"| Total Tokens | {self.total_tokens:,} |",
            "",
            "---",
            "",
            "## 📋 Results by Question",
            "",
        ]
        
        for result in sorted(self.results, key=lambda r: r.question.priority):
            lines.extend([
                f"### {result.question.description}",
                "",
                f"**Question:** {result.question.question}",
                "",
            ])
            
            if result.success:
                lines.append(f"| Stat | Value |")
                lines.append(f"|------|-------|")
                lines.append(f"| Citations | {result.citations_found} |")
                lines.append(f"| Sentiment | {result.sentiment_emoji} {result.sentiment_label} |")
                lines.append(f"| Authors | {result.unique_authors} |")
                lines.append("")
                lines.append(result.answer)
            else:
                lines.append(f"❌ Error: {result.error}")
            
            lines.extend(["", "---", ""])
        
        lines.append(f"*Generated by {self.analyzer_name}*")
        return "\n".join(lines)
    
    def to_dict(self) -> dict:
        return {
            "analyzer_name": self.analyzer_name,
            "analyzer_description": self.analyzer_description,
            "source_file": self.source_file,
            "generated_at": self.generated_at,
            "total_questions": self.total_questions,
            "successful_questions": self.successful_questions,
            "total_citations": self.total_citations,
            "total_tokens": self.total_tokens,
            "results": [r.to_dict() for r in self.results],
        }


class BaseAnalyzer(ABC):
    """
    Abstract base class for domain-specific analyzers.
    
    Subclass this to create analyzers for different domains
    (marketing, research, product, support, etc.).
    
    Example:
        class MyAnalyzer(BaseAnalyzer):
            name = "my_analyzer"
            description = "My Custom Analysis"
            
            questions = [
                AnalysisQuestion(
                    id="patterns",
                    question="What patterns exist in this data?",
                    description="Pattern Discovery",
                ),
            ]
    """
    
    # Override in subclass
    name: str = "base"
    description: str = "Base Analyzer"
    
    # List of questions to run
    questions: list[AnalysisQuestion] = []
    
    def __init__(self, enabled_questions: Optional[list[str]] = None):
        """
        Initialize analyzer.
        
        Args:
            enabled_questions: If provided, only run these question IDs.
                              If None, run all questions where enabled=True.
        """
        self.enabled_questions = enabled_questions
    
    def get_questions(self) -> list[AnalysisQuestion]:
        """Get list of questions to run."""
        questions = [q for q in self.questions if q.enabled]
        
        if self.enabled_questions:
            questions = [q for q in questions if q.id in self.enabled_questions]
        
        return sorted(questions, key=lambda q: q.priority)
    
    def add_question(self, question: AnalysisQuestion):
        """Add a custom question at runtime."""
        self.questions.append(question)
    
    def run(
        self,
        explorer,
        save_traces: bool = True,
        trace_dir: Optional[str] = None,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> AnalysisReport:
        """
        Run all questions in this analyzer.
        
        Args:
            explorer: JsonExplorer instance with loaded data
            save_traces: Whether to save execution traces
            trace_dir: Directory for traces
            progress_callback: Called with (question_id, current, total)
            
        Returns:
            AnalysisReport with all results
        """
        report = AnalysisReport(
            analyzer_name=self.name,
            analyzer_description=self.description,
            source_file=explorer.file_path,
            generated_at=datetime.now().isoformat(),
        )
        
        questions = self.get_questions()
        
        for i, question in enumerate(questions):
            if progress_callback:
                progress_callback(question.id, i + 1, len(questions))
            
            result = self._run_question(
                explorer,
                question,
                save_traces,
                trace_dir,
            )
            
            report.add_result(result)
        
        return report
    
    def _run_question(
        self,
        explorer,
        question: AnalysisQuestion,
        save_traces: bool,
        trace_dir: Optional[str],
    ) -> AnalysisResult:
        """Run a single question."""
        try:
            # Run query
            query_result = explorer.query(
                question.question,
                save_trace=save_traces,
                trace_dir=trace_dir,
            )
            
            # Extract verification data
            verification = query_result.verification
            
            # Apply post-processor if defined
            answer = query_result.answer
            if question.post_processor:
                answer = question.post_processor(answer)
            
            return AnalysisResult(
                question=question,
                answer=answer,
                success=query_result.success,
                citations_found=verification.citations_found if verification else 0,
                unique_authors=verification.unique_authors if verification else 0,
                positive_mentions=verification.positive_mentions if verification else 0,
                negative_mentions=verification.negative_mentions if verification else 0,
                neutral_mentions=verification.neutral_mentions if verification else 0,
                tokens_used=query_result.total_tokens,
                duration_ms=query_result.duration_ms,
                reference_ids=verification.reference_ids if verification else [],
                raw_result=query_result,
            )
            
        except Exception as e:
            return AnalysisResult(
                question=question,
                answer="",
                success=False,
                error=str(e),
            )


class AnalysisPipeline:
    """
    Run multiple analyzers and generate combined reports.
    
    Example:
        pipeline = AnalysisPipeline(explorer)
        pipeline.add_analyzer(MarketingAnalyzer())
        pipeline.add_analyzer(ProductAnalyzer())
        results = pipeline.run()
        pipeline.save_reports("./reports")
    """
    
    def __init__(self, explorer):
        """
        Initialize pipeline.
        
        Args:
            explorer: JsonExplorer instance with loaded data
        """
        self.explorer = explorer
        self.analyzers: list[BaseAnalyzer] = []
        self.reports: list[AnalysisReport] = []
    
    def add_analyzer(self, analyzer: BaseAnalyzer):
        """Add an analyzer to the pipeline."""
        self.analyzers.append(analyzer)
    
    def run(
        self,
        save_traces: bool = True,
        trace_dir: Optional[str] = None,
        progress_callback: Optional[Callable[[str, str, int, int], None]] = None,
    ) -> list[AnalysisReport]:
        """
        Run all analyzers.
        
        Args:
            save_traces: Whether to save execution traces
            trace_dir: Directory for traces
            progress_callback: Called with (analyzer_name, question_id, current, total)
            
        Returns:
            List of AnalysisReport objects
        """
        self.reports = []
        
        for analyzer in self.analyzers:
            def wrapped_callback(q_id, current, total):
                if progress_callback:
                    progress_callback(analyzer.name, q_id, current, total)
            
            report = analyzer.run(
                self.explorer,
                save_traces=save_traces,
                trace_dir=trace_dir,
                progress_callback=wrapped_callback,
            )
            
            self.reports.append(report)
        
        return self.reports
    
    def save_reports(self, output_dir: str):
        """
        Save all reports to directory.
        
        Creates:
        - SUMMARY.md (executive summary)
        - {analyzer_name}.md (individual reports)
        - {analyzer_name}.json (machine-readable)
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save individual reports
        for report in self.reports:
            # Markdown
            md_path = output_path / f"{report.analyzer_name}.md"
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(report.to_markdown())
            
            # JSON
            json_path = output_path / f"{report.analyzer_name}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
        
        # Generate summary
        self._save_summary(output_path)
    
    def _save_summary(self, output_path: Path):
        """Generate executive summary."""
        summary_path = output_path / "SUMMARY.md"
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("# 📊 Analysis Summary\n\n")
            f.write(f"**Source:** `{self.explorer.file_path}`\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
            f.write("---\n\n")
            
            # Overview table
            f.write("## 📈 Analyzers Run\n\n")
            f.write("| Analyzer | Questions | Citations | Tokens | Report |\n")
            f.write("|----------|-----------|-----------|--------|--------|\n")
            
            total_questions = 0
            total_citations = 0
            total_tokens = 0
            
            for report in self.reports:
                total_questions += report.total_questions
                total_citations += report.total_citations
                total_tokens += report.total_tokens
                
                f.write(f"| {report.analyzer_description} | {report.total_questions} | ")
                f.write(f"{report.total_citations:,} | {report.total_tokens:,} | ")
                f.write(f"[View](./{report.analyzer_name}.md) |\n")
            
            f.write(f"| **Total** | **{total_questions}** | ")
            f.write(f"**{total_citations:,}** | **{total_tokens:,}** | |\n")
            
            f.write("\n---\n\n")
            
            # Key findings from each
            f.write("## 🔑 Key Findings\n\n")
            
            for report in self.reports:
                f.write(f"### {report.analyzer_description}\n\n")
                
                # Top 3 results by citation count
                top_results = sorted(
                    [r for r in report.results if r.success],
                    key=lambda r: r.citations_found,
                    reverse=True,
                )[:3]
                
                for result in top_results:
                    f.write(f"**{result.question.description}** ")
                    f.write(f"({result.citations_found} citations, {result.sentiment_emoji})\n\n")
                    
                    # First 300 chars of answer
                    preview = result.answer[:300]
                    if len(result.answer) > 300:
                        cutoff = preview.rfind('.')
                        if cutoff > 150:
                            preview = preview[:cutoff+1]
                        else:
                            preview += "..."
                    
                    f.write(f"> {preview}\n\n")
                
                f.write(f"[📄 Full Report](./{report.analyzer_name}.md)\n\n")
            
            f.write("---\n\n")
            f.write("*Generated by JSON Explorer Analysis Pipeline*\n")
    
    def get_all_results(self) -> list[AnalysisResult]:
        """Get flattened list of all results."""
        return [r for report in self.reports for r in report.results]
    
    def get_results_by_category(self, category: AnalysisCategory) -> list[AnalysisResult]:
        """Get results filtered by category."""
        return [
            r for r in self.get_all_results()
            if r.question.category == category
        ]

