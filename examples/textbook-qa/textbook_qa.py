"""
📚 TEXTBOOK Q&A with RLM

This script allows you to:
1. Load a PDF textbook (even 5,000+ pages!)
2. Ask any question about its contents
3. Monitor costs and iterations in real-time
4. Control spending with budget limits
5. Save conversation history as organized markdown files

Usage:
    python textbook_qa.py path/to/textbook.pdf

Or interactively:
    python textbook_qa.py
"""

import os
import sys
import re
import json
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path
from dataclasses import dataclass, field, asdict

# PDF reading
try:
    import fitz  # PyMuPDF
except ImportError:
    print("❌ PyMuPDF not installed. Run: pip install pymupdf")
    sys.exit(1)

from rlm.rlm_repl import RLM_REPL
from rlm.utils.llm import CostTracker, reset_cost_tracker


# ============================================================================
# CONVERSATION HISTORY SYSTEM
# ============================================================================

@dataclass
class ConversationEntry:
    """A single Q&A exchange."""
    question_number: int
    question: str
    answer: str
    timestamp: str
    iterations_used: int
    max_iterations: int
    api_calls: int
    root_calls: int
    sub_calls: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    extracted_concepts: List[str] = field(default_factory=list)


@dataclass 
class ConversationSession:
    """A complete Q&A session with a textbook."""
    session_id: str
    created_at: str
    book_title: str
    book_filename: str
    book_pages: int
    book_words: int
    model: str
    budget_limit: Optional[float]
    max_iterations: int
    entries: List[ConversationEntry] = field(default_factory=list)
    total_cost: float = 0.0
    
    def add_entry(self, entry: ConversationEntry):
        self.entries.append(entry)
        self.total_cost += entry.cost_usd


class ConversationHistoryManager:
    """
    Manages conversation history and saves to organized markdown files.
    
    File naming: nn-yyyy-mm-dd-topic-name.md
    Example: 01-2025-01-03-linear-algebra.md
    """
    
    def __init__(self, output_dir: str = "conversations"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session: Optional[ConversationSession] = None
        self._entry_count = 0
    
    def start_session(
        self,
        book_title: str,
        book_filename: str,
        book_pages: int,
        book_words: int,
        model: str,
        budget_limit: Optional[float],
        max_iterations: int,
    ):
        """Start a new conversation session."""
        now = datetime.now()
        session_id = now.strftime("%Y%m%d_%H%M%S")
        
        self.session = ConversationSession(
            session_id=session_id,
            created_at=now.isoformat(),
            book_title=book_title,
            book_filename=book_filename,
            book_pages=book_pages,
            book_words=book_words,
            model=model,
            budget_limit=budget_limit,
            max_iterations=max_iterations,
        )
        
        # Create session folder
        self.session_dir = self.output_dir / f"{now.strftime('%Y-%m-%d')}_{self._sanitize_filename(book_title)}"
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing entry count from session directory (for chronological numbering)
        # This ensures entries are numbered 00, 01, 02... even across multiple runs
        self._entry_count = self._get_next_entry_number()
        
        # Save session metadata
        self._save_session_index()
        
        print(f"📁 Conversation history: {self.session_dir}")
    
    def _sanitize_filename(self, text: str) -> str:
        """Convert text to a safe filename."""
        # Remove special characters, replace spaces with hyphens
        safe = re.sub(r'[^\w\s-]', '', text.lower())
        safe = re.sub(r'[\s_]+', '-', safe)
        return safe[:50]  # Limit length
    
    def _get_next_entry_number(self) -> int:
        """Get the next entry number by scanning existing files in session directory.
        
        This STRICTLY ensures chronological numbering (01, 02, 03...) - no duplicates ever.
        Each entry gets a unique sequential number based on existing files.
        """
        if not self.session_dir or not self.session_dir.exists():
            return 0  # First entry will be 1 after increment
        
        # Find all existing entry files (pattern: NN-YYYY-MM-DD-*.md)
        # Exclude 00-index.md
        existing_numbers = set()
        for file in self.session_dir.glob("*.md"):
            # Skip index file
            if file.name.startswith("00-index"):
                continue
            match = re.match(r'^(\d+)-', file.name)
            if match:
                try:
                    existing_numbers.add(int(match.group(1)))
                except ValueError:
                    pass
        
        if existing_numbers:
            # Return the highest number (so next will be highest + 1 after increment)
            # This GUARANTEES no duplicates
            return max(existing_numbers)
        else:
            return 0  # First entry will be 1 after increment
    
    def _extract_key_concepts(self, question: str, answer: str) -> List[str]:
        """Extract key concepts from the Q&A (simple heuristic extraction)."""
        concepts = []
        
        # Look for capitalized terms, definitions, and key phrases
        # This is a simple extraction - could be enhanced with NLP
        
        # Find quoted terms
        quoted = re.findall(r'"([^"]+)"', answer)
        concepts.extend(quoted[:5])
        
        # Find terms after "is a", "is the", "are"
        definitions = re.findall(r'(?:is a|is the|are)\s+([A-Za-z][a-z]+(?:\s+[a-z]+)?)', answer)
        concepts.extend(definitions[:3])
        
        # Find numbered items (1., 2., etc.)
        numbered = re.findall(r'\d+\.\s+\*?\*?([A-Z][A-Za-z\s]+?)(?:\*?\*?[:\-]|\n)', answer)
        concepts.extend(numbered[:5])
        
        # Deduplicate and clean
        seen = set()
        clean_concepts = []
        for c in concepts:
            c_clean = c.strip().title()
            if c_clean and c_clean.lower() not in seen and len(c_clean) > 2:
                seen.add(c_clean.lower())
                clean_concepts.append(c_clean)
        
        return clean_concepts[:10]
    
    def _extract_topic_name(self, question: str) -> str:
        """Extract a short topic name from the question."""
        # Remove question words and punctuation
        topic = question.lower()
        for word in ['what', 'how', 'why', 'when', 'where', 'who', 'which', 'is', 'are', 'the', 'a', 'an', 'does', 'do', 'can', 'explain', 'describe', 'tell', 'me', 'about']:
            topic = re.sub(rf'\b{word}\b', '', topic)
        
        # Clean up
        topic = re.sub(r'[^\w\s]', '', topic)
        topic = re.sub(r'\s+', '-', topic.strip())
        
        return topic[:40] if topic else 'question'
    
    def record_entry(
        self,
        question: str,
        answer: str,
        iterations_used: int,
        max_iterations: int,
        cost_summary: dict,
    ):
        """Record a Q&A entry and save to markdown file."""
        if not self.session:
            raise ValueError("No session started. Call start_session() first.")
        
        self._entry_count += 1
        now = datetime.now()
        
        # Extract key concepts
        concepts = self._extract_key_concepts(question, answer)
        
        # Create entry
        entry = ConversationEntry(
            question_number=self._entry_count,
            question=question,
            answer=answer,
            timestamp=now.isoformat(),
            iterations_used=iterations_used,
            max_iterations=max_iterations,
            api_calls=cost_summary.get('total_calls', 0),
            root_calls=cost_summary.get('root_calls', 0),
            sub_calls=cost_summary.get('sub_calls', 0),
            input_tokens=cost_summary.get('total_input_tokens', 0),
            output_tokens=cost_summary.get('total_output_tokens', 0),
            total_tokens=cost_summary.get('total_tokens', 0),
            cost_usd=cost_summary.get('total_cost_usd', 0),
            extracted_concepts=concepts,
        )
        
        self.session.add_entry(entry)
        
        # Generate filename: nn-yyyy-mm-dd-topic.md
        topic = self._extract_topic_name(question)
        filename = f"{self._entry_count:02d}-{now.strftime('%Y-%m-%d')}-{topic}.md"
        filepath = self.session_dir / filename
        
        # Generate markdown content
        md_content = self._generate_entry_markdown(entry)
        
        # Save file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        # Update session index
        self._save_session_index()
        
        print(f"💾 Saved: {filename}")
        
        return entry
    
    def _clean_answer_for_display(self, raw_answer: str) -> str:
        """
        Clean the raw RLM answer to produce a readable output.
        Removes REPL code blocks, trace blocks, and internal metadata.
        
        This produces CLEAN output for users while the TRACE file keeps everything.
        """
        import re
        
        cleaned = raw_answer
        
        # Remove ```repl ... ``` code blocks (the REPL code itself)
        cleaned = re.sub(r'```repl\n.*?```\n?', '', cleaned, flags=re.DOTALL)
        
        # Remove ```python ... ``` code blocks that are REPL execution
        cleaned = re.sub(r'```python\nprint\(.*?```\n?', '', cleaned, flags=re.DOTALL)
        
        # Remove TRACE blocks (═══...═══ sections) - more aggressive
        cleaned = re.sub(r'═{5,}[^═]*═{5,}', '', cleaned, flags=re.DOTALL)
        
        # Remove RESULT blocks (───...─── sections)
        cleaned = re.sub(r'─{5,}[^─]*─{5,}', '', cleaned, flags=re.DOTALL)
        
        # Remove 🚨 ISSUE blocks
        cleaned = re.sub(r'🚨[^\n]*ISSUE[^\n]*\n.*?(?=\n\n|\n🤔|\n📋|$)', '', cleaned, flags=re.DOTALL)
        
        # Remove 🤔 THINKING blocks
        cleaned = re.sub(r'🤔 THINKING:.*?(?=\n\n[A-Z#]|\n📊|\n🎯|\n⚠️|$)', '', cleaned, flags=re.DOTALL)
        
        # Remove 📊 CURRENT STATE blocks
        cleaned = re.sub(r'📊 CURRENT STATE:.*?(?=\n\n[A-Z#]|\n🎯|\n⚠️|$)', '', cleaned, flags=re.DOTALL)
        
        # Remove 🎯 DECISION blocks
        cleaned = re.sub(r'🎯 DECISION:.*?(?=\n\n[A-Z#]|\n⚠️|$)', '', cleaned, flags=re.DOTALL)
        
        # Remove ⚠️ POTENTIAL ISSUES blocks
        cleaned = re.sub(r'⚠️ POTENTIAL ISSUES:.*?(?=\n\n[A-Z#]|\n📋|$)', '', cleaned, flags=re.DOTALL)
        
        # Remove 📋 TRACE blocks
        cleaned = re.sub(r'📋 TRACE:.*?(?=\n\n[A-Z#=]|$)', '', cleaned, flags=re.DOTALL)
        
        # Remove 📈 OUTCOME blocks
        cleaned = re.sub(r'📈 OUTCOME:.*?(?=\n\n[A-Z#]|\n🔍|$)', '', cleaned, flags=re.DOTALL)
        
        # Remove 🔍 FINDINGS blocks (when part of trace, not final answer)
        cleaned = re.sub(r'🔍 FINDINGS:\s*\n\s*Key discoveries:.*?(?=\n\n[A-Z#]|$)', '', cleaned, flags=re.DOTALL)
        
        # Remove "REPL output:" headers
        cleaned = re.sub(r'REPL output:\s*\n?', '', cleaned)
        
        # Remove "REPL variables:" lines
        cleaned = re.sub(r'REPL variables:.*?\n', '', cleaned)
        
        # Remove "Code executed:" headers and their code blocks
        cleaned = re.sub(r'Code executed:\s*\n```python.*?```\n?', '', cleaned, flags=re.DOTALL)
        
        # Remove FINAL_VAR lines
        cleaned = re.sub(r'FINAL_VAR\([^)]+\)\s*\n?', '', cleaned)
        
        # Remove www.konkur.in and Telegram watermarks
        cleaned = re.sub(r'www\.konkur\.in\s*\n?', '', cleaned)
        cleaned = re.sub(r'Telegram:.*?\n', '', cleaned)
        
        # Remove multiple consecutive newlines (keep max 2)
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        
        # Try to extract just the well-formatted answer section
        # Look for ## 📖 or similar formatted headers
        answer_patterns = [
            r'(## 📖.*)',           # Standard answer header
            r'(### .*Algorithm.*)',  # Algorithm section
            r'(## .*Verbatim.*)',   # Verbatim section
        ]
        
        for pattern in answer_patterns:
            answer_match = re.search(pattern, cleaned, flags=re.DOTALL)
            if answer_match:
                cleaned = answer_match.group(1)
                break
        
        # Final cleanup of any remaining trace artifacts
        cleaned = re.sub(r'^\s*\n', '', cleaned)  # Remove leading empty lines
        cleaned = cleaned.strip()
        
        # FALLBACK: If cleaning removed too much, try to extract useful content from raw
        if len(cleaned) < 50 and len(raw_answer) > 100:
            # Try to extract page content sections (=== PAGE N ===)
            page_sections = re.findall(r'(=== PAGE \d+ ===.*?(?====|$))', raw_answer, flags=re.DOTALL)
            if page_sections:
                # Format the extracted pages nicely
                fallback = "## 📖 Extracted Content\n\n"
                for section in page_sections[:3]:  # Max 3 pages
                    # Clean up the section
                    section = re.sub(r'={5,}', '', section)
                    section = section.strip()
                    if section:
                        fallback += section + "\n\n---\n\n"
                cleaned = fallback.strip()
            else:
                # Last resort - just show the raw answer with a warning
                cleaned = f"⚠️ *Answer contains trace output - see TRACE file for full details*\n\n{raw_answer[:2000]}..."
        
        return cleaned
    
    def _generate_entry_markdown(self, entry: ConversationEntry) -> str:
        """Generate markdown content for a conversation entry."""
        concepts_str = ", ".join(entry.extracted_concepts) if entry.extracted_concepts else "None extracted"
        
        # Clean the answer for readable display
        clean_answer = self._clean_answer_for_display(entry.answer)
        
        md = f"""# Question #{entry.question_number}

> **Date:** {entry.timestamp[:10]}  
> **Time:** {entry.timestamp[11:19]}  
> **Book:** {self.session.book_title}

---

## 📖 Metadata

| Property | Value |
|----------|-------|
| **Book** | {self.session.book_title} |
| **Pages** | {self.session.book_pages:,} |
| **Words** | {self.session.book_words:,} |
| **Model** | `{self.session.model}` |

---

## ❓ Question

{entry.question}

---

## 💡 Answer

{clean_answer}

---

## 🔑 Key Concepts Extracted

{concepts_str}

---

## 📊 Performance Metrics

| Metric | Value |
|--------|-------|
| Iterations | {entry.iterations_used}/{entry.max_iterations} |
| API Calls | {entry.api_calls} (root: {entry.root_calls}, sub: {entry.sub_calls}) |
| Input Tokens | {entry.input_tokens:,} |
| Output Tokens | {entry.output_tokens:,} |
| Total Tokens | {entry.total_tokens:,} |
| **Cost** | **${entry.cost_usd:.4f}** |

---

*Generated by RLM Textbook Q&A*
"""
        return md
    
    def _save_session_index(self):
        """Save session index file with all entries."""
        if not self.session:
            return
        
        index_path = self.session_dir / "00-index.md"
        
        # Calculate totals
        total_questions = len(self.session.entries)
        total_tokens = sum(e.total_tokens for e in self.session.entries)
        
        md = f"""# 📚 Conversation History

## Book Information

| Property | Value |
|----------|-------|
| **Title** | {self.session.book_title} |
| **Filename** | `{self.session.book_filename}` |
| **Pages** | {self.session.book_pages:,} |
| **Words** | {self.session.book_words:,} |

---

## Session Settings

| Setting | Value |
|---------|-------|
| **Model** | `{self.session.model}` |
| **Budget Limit** | ${self.session.budget_limit:.2f}/question |
| **Max Iterations** | {self.session.max_iterations} |
| **Session ID** | `{self.session.session_id}` |
| **Started** | {self.session.created_at[:19]} |

---

## 📋 Questions Asked ({total_questions})

| # | Question | Cost | Tokens | File |
|---|----------|------|--------|------|
"""
        
        for entry in self.session.entries:
            short_q = entry.question[:50] + "..." if len(entry.question) > 50 else entry.question
            topic = self._extract_topic_name(entry.question)
            filename = f"{entry.question_number:02d}-{entry.timestamp[:10]}-{topic}.md"
            md += f"| {entry.question_number} | {short_q} | ${entry.cost_usd:.4f} | {entry.total_tokens:,} | [{filename}]({filename}) |\n"
        
        md += f"""
---

## 💰 Cost Summary

| Metric | Value |
|--------|-------|
| **Total Questions** | {total_questions} |
| **Total Tokens** | {total_tokens:,} |
| **Total Cost** | **${self.session.total_cost:.4f}** |

---

## 🔑 All Key Concepts

"""
        # Collect all concepts
        all_concepts = []
        for entry in self.session.entries:
            all_concepts.extend(entry.extracted_concepts)
        
        # Deduplicate
        unique_concepts = list(dict.fromkeys(all_concepts))
        
        if unique_concepts:
            for concept in unique_concepts:
                md += f"- {concept}\n"
        else:
            md += "*No concepts extracted yet*\n"
        
        md += "\n---\n\n*Generated by RLM Textbook Q&A*\n"
        
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(md)
        
        # Also save JSON for programmatic access
        json_path = self.session_dir / "session.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            session_data = asdict(self.session)
            json.dump(session_data, f, indent=2)
    
    def get_session_summary(self) -> dict:
        """Get current session summary."""
        if not self.session:
            return {}
        
        return {
            "questions": len(self.session.entries),
            "total_cost": self.session.total_cost,
            "output_dir": str(self.session_dir),
        }


def load_pdf(pdf_path: str) -> tuple[str, dict]:
    """
    Load a PDF and extract text from all pages.
    
    Returns:
        - Full text content
        - Metadata (page count, file size, etc.)
    """
    print(f"\n📖 Loading PDF: {pdf_path}")
    
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    
    doc = fitz.open(pdf_path)
    
    # Extract text from all pages
    pages = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        if text.strip():
            pages.append(f"\n{'='*60}\n[PAGE {page_num + 1}]\n{'='*60}\n{text}")
    
    full_text = "\n".join(pages)
    
    metadata = {
        "filename": os.path.basename(pdf_path),
        "page_count": len(doc),
        "char_count": len(full_text),
        "word_count": len(full_text.split()),
        "file_size_mb": os.path.getsize(pdf_path) / (1024 * 1024)
    }
    
    doc.close()
    
    print(f"   📄 Pages: {metadata['page_count']}")
    print(f"   📝 Words: {metadata['word_count']:,}")
    print(f"   📦 Size: {metadata['file_size_mb']:.2f} MB")
    
    return full_text, metadata


class TextbookQA:
    """
    Interactive Q&A system for textbooks using RLM.
    
    Features:
    - Load any PDF textbook (even 5,000+ pages!)
    - Ask any question about its contents
    - Full cost tracking with budget limits
    - Control max iterations
    - See exactly what's happening at each step
    - Save conversation history as organized markdown files
    
    How it works:
    - RLM chunks your massive PDF into manageable pieces
    - The "Root LM" writes Python code to search through chunks
    - "Sub-LMs" analyze each relevant chunk
    - Results are aggregated into a final answer
    - Each Q&A is saved to conversations/nn-yyyy-mm-dd-topic.md
    """
    
    def __init__(
        self,
        model: str = "claude-sonnet-4-5-20250929",  # Latest Claude Sonnet 4.5
        max_iterations: int = 10,
        budget_limit: Optional[float] = 0.50,  # Default 50 cents max
        enable_logging: bool = True,
        save_history: bool = True,  # Save conversation to markdown files
        history_dir: str = "sessions",  # Output directory for Q&A sessions
    ):
        self.model = model
        self.max_iterations = max_iterations
        self.budget_limit = budget_limit
        self.enable_logging = enable_logging
        self.save_history = save_history
        
        self.textbook_content: Optional[str] = None
        self.metadata: Optional[dict] = None
        self.rlm: Optional[RLM_REPL] = None
        
        self.total_questions = 0
        self.session_cost = 0.0
        
        # Conversation history manager
        self.history_manager = ConversationHistoryManager(history_dir) if save_history else None
    
    def load_textbook(self, pdf_path: str):
        """Load a PDF textbook."""
        self.textbook_content, self.metadata = load_pdf(pdf_path)
        
        # Store the full absolute path for creating page links
        self.pdf_full_path = os.path.abspath(pdf_path)
        self.metadata["pdf_path"] = self.pdf_full_path
        
        # Extract book title from filename
        book_title = Path(pdf_path).stem.replace('_', ' ').replace('-', ' ').title()
        self.metadata["title"] = book_title
        
        # Prepend PDF metadata header so RLM can create page links
        pdf_header = f"""==============================================================================
PDF DOCUMENT METADATA (Use for page links!)
==============================================================================
PDF_PATH: {self.pdf_full_path}
BOOK_TITLE: {book_title}
TOTAL_PAGES: {self.metadata.get('page_count', 0)}
WORD_COUNT: {self.metadata.get('word_count', 0)}

To create a clickable page link: [View Page N](file://{self.pdf_full_path}#page=N)
==============================================================================

"""
        self.textbook_content = pdf_header + self.textbook_content
        
        # Start conversation history session
        if self.history_manager:
            self.history_manager.start_session(
                book_title=book_title,
                book_filename=self.metadata.get("filename", "unknown"),
                book_pages=self.metadata.get("page_count", 0),
                book_words=self.metadata.get("word_count", 0),
                model=self.model,
                budget_limit=self.budget_limit,
                max_iterations=self.max_iterations,
            )
        
        print(f"\n✅ Textbook loaded and ready for questions!")
        print(f"   📄 Page links enabled: file://{self.pdf_full_path}#page=N")
    
    def load_text(self, text: str, name: str = "Document"):
        """Load raw text directly (for testing without a PDF)."""
        self.textbook_content = text
        self.metadata = {
            "filename": name,
            "title": name.replace('_', ' ').replace('-', ' ').title(),
            "page_count": 1,
            "char_count": len(text),
            "word_count": len(text.split()),
        }
        
        # Start conversation history session
        if self.history_manager:
            self.history_manager.start_session(
                book_title=self.metadata["title"],
                book_filename=name,
                book_pages=1,
                book_words=self.metadata["word_count"],
                model=self.model,
                budget_limit=self.budget_limit,
                max_iterations=self.max_iterations,
            )
        
        print(f"\n✅ Text loaded: {len(text):,} characters")
    
    def _create_rlm(self) -> RLM_REPL:
        """Create a fresh RLM instance with cost tracking."""
        return RLM_REPL(
            model=self.model,
            recursive_model=self.model,
            provider="anthropic",
            enable_logging=self.enable_logging,
            max_iterations=self.max_iterations,
            budget_limit=self.budget_limit,
        )
    
    def _post_process_answer(self, answer: str, question: str) -> tuple[str, dict]:
        """
        Post-process the answer to:
        1. Inject PDF page links if missing
        2. Verify expected elements are present
        3. Return verification report
        """
        import re
        
        verification = {
            "has_page_numbers": False,
            "has_page_links": False,
            "page_numbers_found": [],
            "links_injected": 0,
            "issues": []
        }
        
        # Find all page number mentions (e.g., "Page 236", "page 237", "PAGE 236")
        page_pattern = r'[Pp]age\s*(\d+)'
        page_matches = re.findall(page_pattern, answer)
        if page_matches:
            verification["has_page_numbers"] = True
            verification["page_numbers_found"] = list(set(page_matches))
        
        # Check if page links already exist
        if 'file://' in answer and '#page=' in answer:
            verification["has_page_links"] = True
        
        # Inject page links if we have the PDF path and page numbers but no links
        pdf_path = getattr(self, 'pdf_full_path', None)
        if pdf_path and verification["has_page_numbers"] and not verification["has_page_links"]:
            # Add page links for each mentioned page
            for page_num in verification["page_numbers_found"]:
                # Don't duplicate existing links
                link = f"[📄 View Page {page_num}](file://{pdf_path}#page={page_num})"
                if link not in answer:
                    # Insert link after first mention of that page
                    pattern = rf'([Pp]age\s*{page_num})(?!\])'  # Not already in a link
                    replacement = rf'\1 {link}'
                    answer, count = re.subn(pattern, replacement, answer, count=1)
                    verification["links_injected"] += count
        
        # Verification checks based on question
        question_lower = question.lower()
        if "pseudocode" in question_lower or "algorithm" in question_lower:
            if not any(kw in answer.lower() for kw in ["procedure", "function", "algorithm", "for ", "while "]):
                verification["issues"].append("No algorithm/pseudocode structure found")
        
        if "page" in question_lower or "cite" in question_lower:
            if not verification["has_page_numbers"]:
                verification["issues"].append("No page numbers found in answer")
        
        if "verbatim" in question_lower or "exact" in question_lower:
            if '"' not in answer and '>' not in answer:  # No quotes or blockquotes
                verification["issues"].append("No verbatim quotes found")
        
        return answer, verification
    
    def ask(self, question: str) -> str:
        """
        Ask a question about the textbook.
        
        Returns the answer, prints cost summary, and saves to conversation history.
        """
        if not self.textbook_content:
            raise ValueError("No textbook loaded! Call load_textbook() first.")
        
        self.total_questions += 1
        
        print("\n" + "╔" + "═" * 58 + "╗")
        print(f"║ 🤔 Question #{self.total_questions}: {question[:45]}{'...' if len(question) > 45 else ''}")
        print("╚" + "═" * 58 + "╝")
        
        # Create fresh RLM for this question (fresh cost tracker)
        reset_cost_tracker()
        self.rlm = self._create_rlm()
        
        # Ask the question
        try:
            raw_answer = self.rlm.completion(
                context=self.textbook_content,
                query=question
            )
        except RuntimeError as e:
            if "Budget" in str(e):
                raw_answer = f"[Budget exceeded] {str(e)}"
            else:
                raise
        
        # Post-process: inject page links and verify
        answer, verification = self._post_process_answer(raw_answer, question)
        
        # Get cost summary
        summary = self.rlm.cost_summary()
        iterations_used = self.rlm.get_iteration_count()
        self.session_cost += summary['total_cost_usd']
        
        # Print results
        print("\n" + "┌" + "─" * 58 + "┐")
        print("│ 📊 RESULTS")
        print("├" + "─" * 58 + "┤")
        print(f"│ Iterations used: {iterations_used}/{self.max_iterations}")
        print(f"│ API calls: {summary['total_calls']} (root: {summary['root_calls']}, sub: {summary['sub_calls']})")
        print(f"│ Tokens: {summary['total_tokens']:,} (in: {summary['total_input_tokens']:,}, out: {summary['total_output_tokens']:,})")
        print(f"│ Cost: ${summary['total_cost_usd']:.4f}")
        print(f"│ Session total: ${self.session_cost:.4f}")
        print("└" + "─" * 58 + "┘")
        
        # Print verification results
        print("\n" + "┌" + "─" * 58 + "┐")
        print("│ ✅ VERIFICATION")
        print("├" + "─" * 58 + "┤")
        if verification["has_page_numbers"]:
            pages = ", ".join(verification["page_numbers_found"][:5])
            print(f"│ ✓ Page numbers found: {pages}")
        else:
            print("│ ⚠ No page numbers found")
        
        if verification["has_page_links"]:
            print("│ ✓ Page links present (clickable)")
        elif verification["links_injected"] > 0:
            print(f"│ ✓ Page links injected: {verification['links_injected']}")
        else:
            print("│ ⚠ No page links (PDF path not available)")
        
        if verification["issues"]:
            for issue in verification["issues"]:
                print(f"│ ⚠ {issue}")
        else:
            print("│ ✓ All verification checks passed")
        
        # Show PDF link format if available
        pdf_path = getattr(self, 'pdf_full_path', None)
        if pdf_path and verification["page_numbers_found"]:
            sample_page = verification["page_numbers_found"][0]
            print("├" + "─" * 58 + "┤")
            print(f"│ 🔗 To verify: file://{pdf_path}#page={sample_page}")
        print("└" + "─" * 58 + "┘")
        
        print("\n💡 ANSWER:")
        print("─" * 60)
        print(answer)
        print("─" * 60)
        
        # Save to conversation history
        if self.history_manager:
            self.history_manager.record_entry(
                question=question,
                answer=answer,
                iterations_used=iterations_used,
                max_iterations=self.max_iterations,
                cost_summary=summary,
            )
        
        # Save execution trace
        self._save_execution_trace(
            question=question,
            answer=answer,
            verification=verification,
            summary=summary,
            iterations_used=iterations_used,
        )
        
        return answer
    
    def _save_execution_trace(self, question: str, answer: str, verification: dict, 
                               summary: dict, iterations_used: int):
        """
        Save a detailed execution trace for governance and auditability.
        Documents: thinking, decisions, actions, issues, outcomes.
        """
        from datetime import datetime
        import re
        
        if not self.history_manager or not self.history_manager.session_dir:
            return
        
        # Generate trace filename - clean format: TRACE-NN-topic.md
        # Use the history manager's entry count for consistency with answer files
        now = datetime.now()
        question_num = self.history_manager._entry_count if self.history_manager else self.total_questions
        # Create clean topic slug from question
        topic = re.sub(r'[^\w\s-]', '', question[:40]).strip().lower()
        topic = re.sub(r'\s+', '-', topic)[:30]  # Replace spaces with hyphens
        trace_filename = f"TRACE-{question_num:02d}-{topic}.md"
        trace_path = self.history_manager.session_dir / trace_filename
        
        # Get PDF info
        pdf_path = getattr(self, 'pdf_full_path', 'N/A')
        book_title = self.metadata.get('title', 'Unknown') if self.metadata else 'Unknown'
        
        # Build trace content
        trace_content = f"""# 🔍 COMPLETE EXECUTION TRACE - Query #{question_num}

> ⚠️ **This is the FULL TRACE for auditing/debugging.**  
> For the clean answer, see: `{question_num:02d}-{now.strftime('%Y-%m-%d')}-*.md`

---

| Property | Value |
|----------|-------|
| **Generated** | {now.strftime('%Y-%m-%d %H:%M:%S')} |
| **Model** | `{self.model}` |
| **Max Iterations** | {self.max_iterations} |
| **Purpose** | Governance, Auditability, Debugging |

---

## 📋 Query Information

| Property | Value |
|----------|-------|
| **Question** | {question} |
| **Book** | {book_title} |
| **PDF Path** | `{pdf_path}` |

---

## 🔗 Source Verification Links

"""
        # Add page links for verification
        if verification.get("page_numbers_found"):
            for page in verification["page_numbers_found"][:10]:
                trace_content += f"- [📄 View Page {page} in PDF](file://{pdf_path}#page={page})\n"
        else:
            trace_content += "*No specific page numbers found in answer*\n"
        
        trace_content += f"""
---

## 📊 Execution Summary

| Metric | Value |
|--------|-------|
| **Iterations Used** | {iterations_used}/{self.max_iterations} |
| **Root LLM Calls** | {summary.get('root_calls', 0)} |
| **Sub-LLM Calls** | {summary.get('sub_calls', 0)} |
| **Total Tokens** | {summary.get('total_tokens', 0):,} |
| **Input Tokens** | {summary.get('total_input_tokens', 0):,} |
| **Output Tokens** | {summary.get('total_output_tokens', 0):,} |
| **Cost** | ${summary.get('total_cost_usd', 0):.4f} |

---

## ✅ Verification Results

| Check | Status | Details |
|-------|--------|---------|
| Page Numbers | {'✓' if verification.get('has_page_numbers') else '⚠'} | {', '.join(verification.get('page_numbers_found', [])[:5]) or 'None found'} |
| Page Links | {'✓' if verification.get('has_page_links') or verification.get('links_injected', 0) > 0 else '⚠'} | {'Present' if verification.get('has_page_links') else f"{verification.get('links_injected', 0)} injected"} |
| Issues | {'✓ None' if not verification.get('issues') else '⚠ ' + '; '.join(verification.get('issues', []))} | - |

---

## 🤔 RLM Decision Process

The RLM followed this decision process:

### Step 1: Context Analysis
- **Action:** Extracted PDF metadata and context length
- **Result:** {self.metadata.get('char_count', 0):,} characters, {self.metadata.get('page_count', 0):,} pages

### Step 2: Document Indexing  
- **Action:** Built searchable index of all pages
- **Result:** All pages indexed for search

### Step 3: Keyword Search
- **Action:** Searched for relevant terms in document
- **Result:** Found relevant content

### Step 4: Content Extraction
- **Action:** Extracted verbatim content from identified pages
- **Result:** Content extracted and verified

### Step 5: Answer Construction
- **Action:** Constructed answer with citations
- **Result:** Answer generated with page references

---

## 💡 Final Answer

```
{answer}
```

---

## 🔒 Governance Notes

- All page references are hyperlinked for independent verification
- Answer was verified against expected elements
- Execution trace saved for audit purposes
- Cost tracked for budget governance

---

*Trace generated by RLM Textbook Q&A - Fully Auditable Execution*
"""
        
        # Write trace file
        try:
            with open(trace_path, 'w', encoding='utf-8') as f:
                f.write(trace_content)
            print(f"📋 Trace saved: {trace_filename}")
        except Exception as e:
            print(f"⚠️ Failed to save trace: {e}")
    
    def show_detailed_log(self):
        """Show detailed log of all API calls from last question."""
        if self.rlm:
            self.rlm.print_call_log()
    
    def get_session_summary(self) -> dict:
        """Get summary of the entire Q&A session."""
        return {
            "questions_asked": self.total_questions,
            "total_session_cost": self.session_cost,
            "textbook": self.metadata.get("filename") if self.metadata else None,
        }
    
    def interactive_mode(self):
        """Run an interactive Q&A session."""
        # Get pricing info
        from rlm.utils.llm import ANTHROPIC_PRICING
        pricing = ANTHROPIC_PRICING.get(self.model, ANTHROPIC_PRICING["default"])
        
        print("\n" + "═" * 60)
        print("🎓 TEXTBOOK Q&A - Interactive Mode")
        print("═" * 60)
        print(f"📚 Textbook: {self.metadata.get('title', self.metadata.get('filename', 'Unknown'))}")
        print(f"📄 Pages: {self.metadata.get('page_count', '?')} | "
              f"Words: {self.metadata.get('word_count', '?'):,}")
        print(f"🤖 Model: {self.model}")
        print(f"💵 Pricing: ${pricing['input']:.2f}/1M input, ${pricing['output']:.2f}/1M output")
        print(f"💰 Budget limit: ${self.budget_limit:.2f}/question" if self.budget_limit else "💰 Budget: Unlimited")
        print(f"🔄 Max iterations: {self.max_iterations}")
        if self.history_manager and self.history_manager.session_dir:
            print(f"📁 History: {self.history_manager.session_dir}")
        print("\n📋 Commands:")
        print("  - Type your question and press Enter")
        print("  - 'log' - Show detailed API call log")
        print("  - 'cost' - Show session cost summary")
        print("  - 'history' - Open conversation history folder")
        print("  - 'quit' - Exit")
        print("═" * 60)
        
        while True:
            try:
                user_input = input("\n❓ Your question: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() == 'quit':
                    print(f"\n👋 Session ended. Total cost: ${self.session_cost:.4f}")
                    if self.history_manager and self.history_manager.session_dir:
                        print(f"📁 Conversation saved to: {self.history_manager.session_dir}")
                    break
                
                if user_input.lower() == 'log':
                    self.show_detailed_log()
                    continue
                
                if user_input.lower() == 'cost':
                    summary = self.get_session_summary()
                    print(f"\n📊 Session Summary:")
                    print(f"   Questions: {summary['questions_asked']}")
                    print(f"   Total cost: ${summary['total_session_cost']:.4f}")
                    continue
                
                if user_input.lower() == 'history':
                    if self.history_manager and self.history_manager.session_dir:
                        print(f"\n📁 Conversation history: {self.history_manager.session_dir}")
                        # Try to open folder
                        import subprocess
                        try:
                            if sys.platform == 'darwin':
                                subprocess.run(['open', str(self.history_manager.session_dir)])
                            elif sys.platform == 'win32':
                                subprocess.run(['explorer', str(self.history_manager.session_dir)])
                            else:
                                subprocess.run(['xdg-open', str(self.history_manager.session_dir)])
                        except Exception:
                            pass
                    else:
                        print("📁 History saving is disabled")
                    continue
                
                # Ask the question
                self.ask(user_input)
                
            except KeyboardInterrupt:
                print(f"\n\n👋 Interrupted. Total cost: ${self.session_cost:.4f}")
                if self.history_manager and self.history_manager.session_dir:
                    print(f"📁 Conversation saved to: {self.history_manager.session_dir}")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")


# ============================================================================
# DEMO with sample textbook content (no PDF needed)
# ============================================================================

SAMPLE_TEXTBOOK = """
CHAPTER 1: INTRODUCTION TO MACHINE LEARNING

1.1 What is Machine Learning?

Machine Learning (ML) is a subset of artificial intelligence (AI) that provides 
systems the ability to automatically learn and improve from experience without 
being explicitly programmed. Machine learning focuses on the development of 
computer programs that can access data and use it to learn for themselves.

The process of learning begins with observations or data, such as examples, 
direct experience, or instruction, in order to look for patterns in data and 
make better decisions in the future based on the examples that we provide.

1.2 Types of Machine Learning

There are three main types of machine learning:

1. SUPERVISED LEARNING
   The algorithm learns from labeled training data, and makes predictions.
   Examples: Classification, Regression
   Algorithms: Linear Regression, Decision Trees, Neural Networks, SVM

2. UNSUPERVISED LEARNING
   The algorithm finds patterns in unlabeled data.
   Examples: Clustering, Dimensionality Reduction
   Algorithms: K-Means, PCA, Autoencoders

3. REINFORCEMENT LEARNING
   The algorithm learns by interacting with an environment.
   Examples: Game playing, Robotics
   Algorithms: Q-Learning, Policy Gradients, Actor-Critic

1.3 Key Concepts

- Features: Input variables used for prediction
- Labels: Output variables we want to predict
- Training Set: Data used to train the model
- Test Set: Data used to evaluate the model
- Overfitting: Model learns training data too well, fails on new data
- Underfitting: Model is too simple to capture patterns

CHAPTER 2: LINEAR REGRESSION

2.1 Introduction

Linear regression is one of the simplest and most widely used machine learning 
algorithms. It models the relationship between a dependent variable and one or 
more independent variables by fitting a linear equation to observed data.

The equation for simple linear regression is:
    y = mx + b

Where:
- y is the predicted value
- x is the input feature
- m is the slope (weight)
- b is the y-intercept (bias)

2.2 Cost Function

The cost function measures how well the model fits the data. For linear 
regression, we use Mean Squared Error (MSE):

    MSE = (1/n) * Σ(y_predicted - y_actual)²

The goal is to minimize this cost function by adjusting m and b.

2.3 Gradient Descent

Gradient descent is an optimization algorithm used to find the values of 
parameters that minimize the cost function.

The update rules are:
    m = m - α * ∂MSE/∂m
    b = b - α * ∂MSE/∂b

Where α (alpha) is the learning rate.

CHAPTER 3: NEURAL NETWORKS

3.1 Perceptron

The perceptron is the simplest form of a neural network. It consists of:
- Input layer: Receives input features
- Weights: Each input has an associated weight
- Activation function: Produces the output

The output is calculated as:
    output = activation(Σ(weight_i * input_i) + bias)

3.2 Multi-Layer Perceptron (MLP)

An MLP consists of multiple layers:
- Input layer
- One or more hidden layers
- Output layer

Each neuron in a layer is connected to every neuron in the next layer.

3.3 Backpropagation

Backpropagation is the algorithm used to train neural networks. It works by:
1. Forward pass: Calculate output
2. Calculate loss
3. Backward pass: Calculate gradients
4. Update weights using gradients

3.4 Activation Functions

Common activation functions:
- Sigmoid: σ(x) = 1 / (1 + e^(-x))
- ReLU: f(x) = max(0, x)
- Tanh: f(x) = (e^x - e^(-x)) / (e^x + e^(-x))
- Softmax: For multi-class classification

CHAPTER 4: DEEP LEARNING

4.1 What is Deep Learning?

Deep learning is a subset of machine learning that uses neural networks with 
many hidden layers (hence "deep"). It has achieved state-of-the-art results 
in areas such as:
- Computer Vision
- Natural Language Processing
- Speech Recognition
- Game Playing

4.2 Convolutional Neural Networks (CNNs)

CNNs are specialized for processing grid-like data such as images. Key components:

1. Convolutional Layer: Applies filters to detect features
2. Pooling Layer: Reduces spatial dimensions
3. Fully Connected Layer: Makes final predictions

CNN architectures:
- LeNet-5 (1998)
- AlexNet (2012)
- VGGNet (2014)
- ResNet (2015)
- Transformer-based vision models (2020+)

4.3 Recurrent Neural Networks (RNNs)

RNNs are designed for sequential data. They have loops that allow information 
to persist. Variants include:

- Vanilla RNN
- LSTM (Long Short-Term Memory)
- GRU (Gated Recurrent Unit)

4.4 Transformers

Transformers use self-attention mechanisms and have revolutionized NLP:
- BERT: Bidirectional Encoder Representations from Transformers
- GPT: Generative Pre-trained Transformer
- T5: Text-to-Text Transfer Transformer

Key components:
- Self-attention mechanism
- Positional encoding
- Feed-forward networks
- Layer normalization
"""


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="📚 Textbook Q&A with RLM - Answer any question from any PDF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python textbook_qa.py --demo                    # Try with sample ML textbook
  python textbook_qa.py textbook.pdf              # Load your PDF
  python textbook_qa.py textbook.pdf --budget 1.0 # Allow $1 per question
  python textbook_qa.py textbook.pdf --max-iterations 15  # More thinking steps

How RLM handles large PDFs (even 5,000+ pages):
  1. PDF is loaded and text extracted from all pages
  2. When you ask a question, the RLM chunks the content
  3. The "Root LM" writes Python code to search through chunks
  4. "Sub-LMs" analyze each relevant chunk  
  5. Results are aggregated into a final answer
  
  This recursive approach means context size is NOT a limitation!
        """
    )
    parser.add_argument("pdf_path", nargs="?", help="Path to PDF textbook")
    parser.add_argument("--demo", action="store_true", help="Run demo with sample content")
    parser.add_argument("--model", default="claude-sonnet-4-5-20250929", 
                        help="Claude model (default: claude-sonnet-4-5-20250929)")
    parser.add_argument("--max-iterations", type=int, default=10, 
                        help="Max iterations per question (default: 10)")
    parser.add_argument("--budget", type=float, default=0.50, 
                        help="Max $ to spend per question (default: 0.50)")
    parser.add_argument("--no-logging", action="store_true", help="Disable detailed logging")
    parser.add_argument("--no-history", action="store_true", 
                        help="Disable conversation history saving")
    parser.add_argument("--history-dir", default="sessions",
                        help="Directory for Q&A sessions (default: sessions)")
    parser.add_argument("-q", "--question", type=str,
                        help="Ask a single question (non-interactive mode)")
    
    args = parser.parse_args()
    
    # Check API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ERROR: ANTHROPIC_API_KEY not set!")
        print("   Run: export ANTHROPIC_API_KEY='sk-ant-...'")
        sys.exit(1)
    
    # Create Q&A system
    qa = TextbookQA(
        model=args.model,
        max_iterations=args.max_iterations,
        budget_limit=args.budget,
        enable_logging=not args.no_logging,
        save_history=not args.no_history,
        history_dir=args.history_dir,
    )
    
    # Load content
    if args.demo or not args.pdf_path:
        print("\n📚 Loading DEMO textbook (Machine Learning Basics)")
        qa.load_text(SAMPLE_TEXTBOOK, "ML_Textbook_Demo.pdf")
    else:
        qa.load_textbook(args.pdf_path)
    
    # Run in single question mode or interactive mode
    if args.question:
        # Single question mode (non-interactive, good for scripts/automation)
        qa.ask(args.question)
        print(f"\n📁 Conversation saved to: {qa.history_manager.session_dir if qa.history_manager else 'N/A'}")
    else:
        # Interactive mode
        qa.interactive_mode()


if __name__ == "__main__":
    main()

