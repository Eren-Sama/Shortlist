"""
Shortlist — Scaffold Generation Prompts

Prompts for the Scaffold Generator Agent that produces
production-ready project file structures and boilerplate code.
"""

import json
from typing import Optional


SCAFFOLD_SYSTEM_PROMPT = """You are a senior full-stack engineer who scaffolds production-ready projects.

Your task: Generate a complete, well-structured repository scaffold for a given project description and tech stack.

You MUST return valid JSON matching this exact schema:
{
  "project_name": "kebab-case-project-name",
  "files": [
    {
      "path": "relative/path/to/file.ext",
      "content": "full file content as a string",
      "language": "python",
      "description": "What this file does"
    }
  ],
  "file_tree": "ASCII tree representation of the directory structure"
}

SCAFFOLD RULES:

1. STRUCTURE
   - Use clean, conventional project layouts (e.g., src/, tests/, docs/)
   - Include a comprehensive README.md with setup instructions, features, and architecture overview
   - Include a .gitignore appropriate for the tech stack
   - Include requirements.txt / package.json / go.mod based on stack
   - Include a LICENSE file (MIT by default)

2. CODE QUALITY
   - All code files must be syntactically valid and runnable
   - Use proper typing/type hints for all languages
   - Include docstrings/comments on all exported functions and classes
   - Follow language-specific conventions (PEP 8, ESLint defaults, etc.)
   - No placeholder "TODO" blocks — write actual working logic or meaningful stubs

3. TESTING (if include_tests = true)
   - Include a test directory with at least 2 test files
   - Write realistic test cases that cover happy path + one edge case
   - Include a test config file (pytest.ini, jest.config.js, etc.)

4. DOCKER (if include_docker = true)
   - Include a Dockerfile with multi-stage build
   - Include a docker-compose.yml if the project has multiple services
   - Include a .dockerignore file

5. CI/CD (if include_ci = true)
   - Include a GitHub Actions workflow (.github/workflows/ci.yml)
   - Workflow should: install deps, lint, test, and conditionally build

6. SECURITY
   - Never include real secrets, API keys, or credentials
   - Include an .env.example with placeholder values
   - Include proper input validation in any API/endpoint code

7. FILE COUNT
   - Generate between 8 and 25 files — enough for a real project, not a toy
   - Every file must have a clear purpose — no filler files
   - The file_tree must accurately reflect all files in the files array

ANTI-PATTERNS:
- Empty files or files with only comments
- Overly simplistic implementations that wouldn't impress a recruiter
- Missing configuration files that would prevent the project from running
- Inconsistent naming conventions

Return ONLY valid JSON. No markdown. No explanation outside the JSON."""


def build_scaffold_user_prompt(
    project_title: str,
    project_description: str,
    tech_stack: list[str],
    *,
    include_docker: bool = True,
    include_ci: bool = True,
    include_tests: bool = True,
    architecture: Optional[str] = None,
    key_features: Optional[list[str]] = None,
    complexity_level: Optional[int] = None,
    recruiter_context: Optional[str] = None,
) -> str:
    """Build the user prompt for scaffold generation."""

    features_section = ""
    if key_features:
        features_section = f"""
Key Features to Implement:
{json.dumps(key_features, indent=2)}
"""

    arch_section = ""
    if architecture:
        arch_section = f"""
Architecture Overview:
{architecture}
"""

    recruiter_section = ""
    if recruiter_context:
        recruiter_section = f"""
Recruiter Context (tailor the scaffold to impress):
{recruiter_context}
"""

    complexity_label = {
        1: "Beginner (simple, well-documented)",
        2: "Intermediate (clean patterns, good structure)",
        3: "Advanced (production patterns, proper architecture)",
        4: "Senior (microservices/distributed patterns)",
        5: "Expert (highly scalable, enterprise-grade)",
    }.get(complexity_level or 3, "Advanced")

    return f"""Generate a production-ready project scaffold for:

Project Title: {project_title}
Description: {project_description}
Complexity: {complexity_label}

Tech Stack: {json.dumps(tech_stack)}

Options:
- Include Docker: {include_docker}
- Include CI/CD: {include_ci}
- Include Tests: {include_tests}
{arch_section}{features_section}{recruiter_section}
Generate a complete, well-structured scaffold that a developer can clone and start building immediately.
Return ONLY valid JSON."""
