"""
Shortlist — Repo Analysis Prompts

System and user prompt templates for the GitHub Repository Scorer.
Designed for structured JSON output from LLM.
"""


REPO_SCORING_SYSTEM_PROMPT = """You are an expert engineering manager and technical recruiter with 15+ years of experience evaluating candidates' GitHub portfolios.

Your task: Analyze a GitHub repository and produce a RECRUITER-FOCUSED SCORECARD in JSON format.

You MUST return valid JSON matching this exact schema:
{
  "code_quality": {
    "score": 0.0-10.0,
    "details": "Detailed assessment of code quality",
    "suggestions": ["improvement 1", "improvement 2"]
  },
  "test_coverage": {
    "score": 0.0-10.0,
    "details": "Assessment of testing practices",
    "suggestions": ["improvement 1"]
  },
  "complexity": {
    "score": 0.0-10.0,
    "details": "Assessment of project complexity and architecture",
    "suggestions": []
  },
  "structure": {
    "score": 0.0-10.0,
    "details": "Assessment of project organization and documentation",
    "suggestions": []
  },
  "deployment_readiness": {
    "score": 0.0-10.0,
    "details": "Assessment of CI/CD, Docker, deployment configs",
    "suggestions": []
  },
  "overall_score": 0.0-10.0,
  "summary": "2-3 sentence executive summary for recruiters",
  "top_improvements": ["Most impactful improvement 1", "improvement 2", "improvement 3"]
}

SCORING GUIDELINES:
1. CODE QUALITY (weight: 25%)
   - Clean, readable, idiomatic code
   - Consistent naming conventions
   - Proper error handling
   - No obvious security issues
   - Good comments where needed
   
2. TEST COVERAGE (weight: 20%)
   - Presence of test files
   - Test organization (unit, integration)
   - Test naming clarity
   - Mock usage and isolation
   
3. COMPLEXITY (weight: 20%)
   - Non-trivial logic and algorithms
   - Real-world problem solving
   - Architecture decisions
   - Scale considerations
   
4. STRUCTURE (weight: 20%)
   - Clear project organization
   - Meaningful README
   - Proper .gitignore
   - Separation of concerns
   - Configuration management
   
5. DEPLOYMENT READINESS (weight: 15%)
   - Dockerfile or container config
   - CI/CD pipelines (GitHub Actions, etc.)
   - Environment configuration
   - Health checks / monitoring hooks

SCORE INTERPRETATION:
- 9-10: Exceptional, production-grade, impressive to any recruiter
- 7-8: Strong, demonstrates professional-level skills
- 5-6: Adequate, shows competence but room to improve
- 3-4: Weak, missing key practices
- 1-2: Minimal effort, red flag for recruiters

Be honest but constructive. Focus on what RECRUITERS care about:
- Can this person write clean, maintainable code?
- Do they follow industry best practices?
- Would I want them on my team?
- Does this project show thoughtfulness and care?

IMPORTANT: Do NOT be overly generous. A simple TODO app should score 3-5, not 8.
A production-ready project with tests, CI/CD, and good docs should score 7-9.
Only truly exceptional projects score 9-10."""


def build_repo_user_prompt(
    repo_name: str,
    description: str,
    primary_language: str,
    languages: dict[str, int],
    stars: int,
    topics: list[str],
    has_readme: bool,
    has_license: bool,
    has_tests: bool,
    has_ci: bool,
    has_docker: bool,
    total_files: int,
    code_files: int,
    test_files: int,
    config_files: list[str],
    quality_files: list[str],
    estimated_loc: int,
    readme_content: str | None,
    sample_code: dict[str, str],
) -> str:
    """Build the user prompt with repository details."""
    
    # Format languages breakdown
    total_bytes = sum(languages.values()) or 1
    lang_breakdown = ", ".join(
        f"{lang}: {bytes_/total_bytes*100:.1f}%"
        for lang, bytes_ in sorted(languages.items(), key=lambda x: -x[1])[:5]
    )
    
    # Format sample code (truncated)
    code_samples = ""
    for path, content in list(sample_code.items())[:3]:
        truncated = content[:2000] + "..." if len(content) > 2000 else content
        code_samples += f"\n\n### File: {path}\n```\n{truncated}\n```"
    
    # Format README (truncated)
    readme_section = ""
    if readme_content:
        truncated_readme = readme_content[:3000] + "..." if len(readme_content) > 3000 else readme_content
        readme_section = f"\n\n## README.md Content:\n{truncated_readme}"
    
    return f"""Analyze this GitHub repository and provide a recruiter-focused scorecard.

## Repository Info
- **Name**: {repo_name}
- **Description**: {description or 'No description'}
- **Primary Language**: {primary_language or 'Unknown'}
- **Languages**: {lang_breakdown or 'Unknown'}
- **Stars**: {stars}
- **Topics**: {', '.join(topics) if topics else 'None'}

## Repository Health
- README: {'✓ Present' if has_readme else '✗ Missing'}
- LICENSE: {'✓ Present' if has_license else '✗ Missing'}
- Tests: {'✓ Found' if has_tests else '✗ None found'}
- CI/CD: {'✓ Configured' if has_ci else '✗ None'}
- Docker: {'✓ Present' if has_docker else '✗ None'}

## File Statistics
- Total Files: {total_files}
- Code Files: {code_files}
- Test Files: {test_files}
- Estimated Lines of Code: {estimated_loc:,}

## Config Files Found
{chr(10).join(f'- {cf}' for cf in config_files) if config_files else '- None'}

## Quality Indicators
{chr(10).join(f'- {qf}' for qf in quality_files) if quality_files else '- None'}
{readme_section}

## Sample Code{code_samples if code_samples else chr(10) + 'No code samples available.'}

---

Based on the above, provide a detailed JSON scorecard. Be realistic and honest in your scoring.
Remember: This assessment will be shown to recruiters evaluating the candidate."""
