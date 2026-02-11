"""GitHub repository analyzer. Fetches metadata via API and generates LLM-scored recruiter scorecards."""

import asyncio
import base64
import re
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime

import httpx

from app.config import get_settings
from app.security import validate_github_url, sanitize_string
from app.logging_config import get_logger

logger = get_logger("services.github_analyzer")

# GitHub API base URL
GITHUB_API = "https://api.github.com"

# File extensions we care about for analysis
CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs", ".rb",
    ".cpp", ".c", ".h", ".hpp", ".cs", ".swift", ".kt", ".scala", ".php",
    ".vue", ".svelte", ".html", ".css", ".scss", ".sass", ".less",
}

CONFIG_FILES = {
    "package.json", "requirements.txt", "pyproject.toml", "Cargo.toml",
    "go.mod", "pom.xml", "build.gradle", "Gemfile", "composer.json",
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
    ".github/workflows", "Makefile", "CMakeLists.txt",
    "tsconfig.json", "vite.config", "webpack.config",
    "pytest.ini", "setup.py", "setup.cfg", "jest.config",
}

QUALITY_INDICATORS = {
    "README.md", "README", "LICENSE", "CONTRIBUTING.md",
    ".gitignore", ".editorconfig", ".prettierrc", ".eslintrc",
    "CHANGELOG.md", "SECURITY.md", "CODE_OF_CONDUCT.md",
}

TEST_PATTERNS = {
    "test_", "_test.py", ".test.js", ".test.ts", ".spec.js", ".spec.ts",
    "tests/", "__tests__/", "spec/", "test/",
}


@dataclass
class RepoMetadata:
    """Repository metadata from GitHub API."""
    owner: str
    name: str
    full_name: str
    description: Optional[str]
    primary_language: Optional[str]
    languages: dict[str, int] = field(default_factory=dict)
    stars: int = 0
    forks: int = 0
    open_issues: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    default_branch: str = "main"
    topics: list[str] = field(default_factory=list)
    license_name: Optional[str] = None
    has_readme: bool = False
    has_license: bool = False


@dataclass
class FileAnalysis:
    """Analysis of repository file structure."""
    total_files: int = 0
    total_dirs: int = 0
    code_files: int = 0
    test_files: int = 0
    config_files: list[str] = field(default_factory=list)
    quality_files: list[str] = field(default_factory=list)
    file_tree: list[str] = field(default_factory=list)
    has_ci: bool = False
    has_docker: bool = False
    has_tests: bool = False
    estimated_loc: int = 0


@dataclass
class RepoAnalysisResult:
    """Complete repository analysis result."""
    metadata: RepoMetadata
    file_analysis: FileAnalysis
    readme_content: Optional[str] = None
    sample_code_files: dict[str, str] = field(default_factory=dict)


def _parse_github_url(url: str) -> tuple[str, str]:
    """Extract owner and repo name from GitHub URL. Raises ValueError if invalid."""
    url = validate_github_url(url)
    match = re.match(r"https://github\.com/([^/]+)/([^/]+)/?$", url)
    if not match:
        raise ValueError(f"Invalid GitHub URL format: {url}")
    return match.group(1), match.group(2)


class GitHubAnalyzer:
    """
    Analyzes GitHub repositories using the GitHub API.
    
    Does NOT clone repositories — uses REST API for all data.
    This is safer and respects GitHub's terms of service.
    """

    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize the analyzer.
        
        Args:
            github_token: Optional GitHub personal access token for higher rate limits.
                          If not provided, uses unauthenticated API (60 req/hour).
        """
        self.token = github_token
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            headers = {
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "Shortlist-Portfolio-Analyzer/1.0",
            }
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            
            self._client = httpx.AsyncClient(
                base_url=GITHUB_API,
                headers=headers,
                timeout=30.0,
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def _api_get(self, path: str) -> Optional[dict]:
        """Make a GET request to GitHub API. Returns None on 404."""
        client = await self._get_client()
        try:
            response = await client.get(path)
            if response.status_code == 404:
                return None
            if response.status_code == 403:
                logger.warning("GitHub API rate limit may be exceeded")
                raise RuntimeError("GitHub API rate limit exceeded. Please try again later.")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"GitHub API error: {e.response.status_code} for {path}")
            raise

    async def get_repo_metadata(self, owner: str, repo: str) -> RepoMetadata:
        """Fetch repository metadata from GitHub API."""
        data = await self._api_get(f"/repos/{owner}/{repo}")
        if not data:
            raise ValueError(f"Repository not found: {owner}/{repo}")

        # Fetch languages
        languages = await self._api_get(f"/repos/{owner}/{repo}/languages") or {}

        # Parse dates
        created_at = None
        updated_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
        if data.get("updated_at"):
            updated_at = datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))

        return RepoMetadata(
            owner=owner,
            name=repo,
            full_name=data.get("full_name", f"{owner}/{repo}"),
            description=sanitize_string(data.get("description") or "", max_length=500),
            primary_language=data.get("language"),
            languages=languages,
            stars=data.get("stargazers_count", 0),
            forks=data.get("forks_count", 0),
            open_issues=data.get("open_issues_count", 0),
            created_at=created_at,
            updated_at=updated_at,
            default_branch=data.get("default_branch", "main"),
            topics=data.get("topics", []),
            license_name=data.get("license", {}).get("name") if data.get("license") else None,
            has_readme=True,  # Will verify below
            has_license=data.get("license") is not None,
        )

    async def get_file_tree(
        self,
        owner: str,
        repo: str,
        branch: str = "main",
        max_files: int = 500,
    ) -> FileAnalysis:
        """
        Fetch repository file tree using the Git Trees API.
        
        Uses recursive tree fetch for efficiency (single API call).
        """
        data = await self._api_get(f"/repos/{owner}/{repo}/git/trees/{branch}?recursive=1")
        if not data or "tree" not in data:
            logger.warning(f"Could not fetch tree for {owner}/{repo}:{branch}")
            return FileAnalysis()

        tree = data["tree"][:max_files]  # Limit to prevent abuse
        
        analysis = FileAnalysis()
        analysis.file_tree = []
        
        for item in tree:
            path = item.get("path", "")
            item_type = item.get("type", "")
            size = item.get("size", 0)
            
            if item_type == "tree":
                analysis.total_dirs += 1
            elif item_type == "blob":
                analysis.total_files += 1
                analysis.file_tree.append(path)
                
                # Check file type
                ext = "." + path.split(".")[-1] if "." in path else ""
                filename = path.split("/")[-1]
                
                if ext.lower() in CODE_EXTENSIONS:
                    analysis.code_files += 1
                    analysis.estimated_loc += size // 40  # Rough estimate
                
                # Check for tests
                if any(pattern in path.lower() for pattern in TEST_PATTERNS):
                    analysis.test_files += 1
                    analysis.has_tests = True
                
                # Check for config files
                for cf in CONFIG_FILES:
                    if cf in path:
                        if cf not in analysis.config_files:
                            analysis.config_files.append(cf)
                        if "dockerfile" in cf.lower():
                            analysis.has_docker = True
                        if ".github/workflows" in cf:
                            analysis.has_ci = True
                
                # Check for quality indicators
                for qf in QUALITY_INDICATORS:
                    if filename.lower() == qf.lower() or path.lower() == qf.lower():
                        if qf not in analysis.quality_files:
                            analysis.quality_files.append(qf)

        return analysis

    async def get_file_content(
        self,
        owner: str,
        repo: str,
        path: str,
        max_size: int = 50_000,
    ) -> Optional[str]:
        """
        Fetch a single file's content from the repository.
        
        Returns None if file is too large or doesn't exist.
        """
        data = await self._api_get(f"/repos/{owner}/{repo}/contents/{path}")
        if not data:
            return None
        
        # Check size
        size = data.get("size", 0)
        if size > max_size:
            logger.info(f"File {path} too large ({size} bytes), skipping")
            return None
        
        # Decode content
        content = data.get("content", "")
        encoding = data.get("encoding", "")
        
        if encoding == "base64":
            try:
                return base64.b64decode(content).decode("utf-8", errors="replace")
            except Exception as e:
                logger.warning(f"Failed to decode {path}: {e}")
                return None
        
        return content

    async def analyze_repository(self, github_url: str) -> RepoAnalysisResult:
        """
        Perform complete repository analysis.
        
        Args:
            github_url: Full GitHub URL (https://github.com/owner/repo)
            
        Returns:
            RepoAnalysisResult with metadata, file analysis, and sample code.
        """
        owner, repo = _parse_github_url(github_url)
        logger.info(f"Starting analysis of {owner}/{repo}")

        # Fetch metadata
        metadata = await self.get_repo_metadata(owner, repo)
        
        # Fetch file tree
        file_analysis = await self.get_file_tree(
            owner, repo, metadata.default_branch
        )
        
        # Fetch README
        readme_content = None
        for readme_name in ["README.md", "README.rst", "README.txt", "README"]:
            content = await self.get_file_content(owner, repo, readme_name)
            if content:
                readme_content = sanitize_string(content, max_length=15_000)
                break
        
        metadata.has_readme = readme_content is not None
        
        # Fetch sample code files (up to 3 interesting files)
        sample_files: dict[str, str] = {}
        interesting_files = [
            f for f in file_analysis.file_tree
            if any(f.endswith(ext) for ext in [".py", ".ts", ".js", ".go", ".rs"])
            and not any(skip in f.lower() for skip in ["test", "spec", "mock", "__pycache__"])
            and "/" in f  # Skip root-level config files
        ][:3]
        
        for file_path in interesting_files:
            content = await self.get_file_content(owner, repo, file_path, max_size=20_000)
            if content:
                sample_files[file_path] = content

        logger.info(
            f"Analysis complete for {owner}/{repo}: "
            f"{file_analysis.total_files} files, "
            f"{file_analysis.code_files} code files, "
            f"{file_analysis.test_files} test files"
        )

        return RepoAnalysisResult(
            metadata=metadata,
            file_analysis=file_analysis,
            readme_content=readme_content,
            sample_code_files=sample_files,
        )


async def analyze_github_repo(github_url: str) -> RepoAnalysisResult:
    """
    Convenience function to analyze a repository.
    
    Creates a new analyzer instance, performs analysis, and cleans up.
    """
    settings = get_settings()
    
    # Use GitHub token if available (higher rate limits)
    token = getattr(settings, "GITHUB_TOKEN", None)
    
    analyzer = GitHubAnalyzer(github_token=token)
    try:
        return await analyzer.analyze_repository(github_url)
    finally:
        await analyzer.close()
