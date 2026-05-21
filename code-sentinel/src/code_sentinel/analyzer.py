"""Code review analyzer."""

import json
import time
import structlog
from dataclasses import dataclass
from pathlib import Path

logger = structlog.get_logger()


@dataclass
class ReviewFinding:
    """A single review finding."""

    file: str
    line: int
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    category: str  # security, bugs, patterns, performance
    issue: str
    fix: str
    explanation: str


@dataclass
class ReviewResult:
    """Result of code review."""

    path: Path
    findings: list[ReviewFinding]
    files_reviewed: int
    duration_seconds: float


# Prompt templates
SYSTEM_PROMPT = """You are an expert code reviewer analyzing code changes.

## Review Categories
1. SECURITY: Vulnerabilities, injection, auth issues
2. BUGS: Logic errors, null checks, race conditions
3. ANTI-PATTERNS: Code smells, maintainability
4. PERFORMANCE: Efficiency issues
5. BEST PRACTICES: Modern patterns, type hints

## Severity
CRITICAL > HIGH > MEDIUM > LOW

## Output Format
JSON array of findings with: file, line, severity, category, issue, fix, explanation
"""

USER_TEMPLATE = """Review this {language} code:

```{language}
{code}
```

Provide structured JSON findings for all issues found."""


# Language detection
EXT_TO_LANG = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "javascript",
    ".tsx": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".kt": "kotlin",
    ".cs": "csharp",
    ".cpp": "cpp",
    ".c": "c",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
}

SUPPORTED_EXTENSIONS = set(EXT_TO_LANG.keys())


class ReviewAnalyzer:
    """Analyzer for code review."""

    def __init__(self, engine, focus: str = "all"):
        self.engine = engine
        self.focus = focus

    def analyze_path(self, path: Path) -> ReviewResult:
        """Analyze a file or directory."""
        start = time.time()
        files_to_review: list[Path] = []

        if path.is_file():
            files_to_review = [path]
            findings = self._analyze_file(path)
        else:
            findings = []
            for file in path.rglob("*"):
                if file.is_file() and self._should_analyze(file):
                    files_to_review.append(file)
                    findings.extend(self._analyze_file(file))

        return ReviewResult(
            path=path,
            findings=findings,
            files_reviewed=len(files_to_review),
            duration_seconds=time.time() - start,
        )

    def _analyze_file(self, file: Path) -> list[ReviewFinding]:
        """Analyze a single file."""
        try:
            code = file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            logger.warning("failed_to_read_file", file=str(file), error=str(e))
            return [
                ReviewFinding(
                    file=str(file),
                    line=0,
                    severity="MEDIUM",
                    category="unknown",
                    issue=f"Failed to read file: {e}",
                    fix="Check file encoding and permissions",
                    explanation=str(e),
                )
            ]
        lang = self._detect_language(file)

        # Build prompt
        user_prompt = USER_TEMPLATE.format(language=lang, code=code)
        full_prompt = SYSTEM_PROMPT + "\n\n" + user_prompt

        # Generate review
        response = self.engine.generate(
            full_prompt,
            temperature=0.2,
            max_tokens=2048,
        )

        # Parse response
        return self._parse_response(response, file)

    def _parse_response(self, response: str, file: Path) -> list[ReviewFinding]:
        """Parse LLM response into findings."""
        try:
            data = json.loads(response)
            if isinstance(data, list):
                return [
                    ReviewFinding(
                        file=str(file),
                        line=item.get("line", 0),
                        severity=item.get("severity", "MEDIUM"),
                        category=item.get("category", "unknown"),
                        issue=item.get("issue", item.get("message", "")),
                        fix=item.get("fix", ""),
                        explanation=item.get("explanation", ""),
                    )
                    for item in data
                ]
        except json.JSONDecodeError:
            pass

        # Fallback: return response as-is if no valid JSON
        return (
            [
                ReviewFinding(
                    file=str(file),
                    line=0,
                    severity="MEDIUM",
                    category="unknown",
                    issue=response[:500],
                    fix="",
                    explanation="Parse error - raw response",
                )
            ]
            if response.strip()
            else []
        )

    def _should_analyze(self, file: Path) -> bool:
        """Check if file should be analyzed."""
        return file.suffix in SUPPORTED_EXTENSIONS

    def _detect_language(self, file: Path) -> str:
        """Detect programming language."""
        return EXT_TO_LANG.get(file.suffix, "text")
