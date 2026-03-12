import os
import logging
from typing import Any

logger = logging.getLogger(__name__)

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", ".."))


class FolderEngine:
    """Builds prompts for folder structure generation.

    Designed for token economy: the AI returns a compact JSON with just
    tree text, a ready-to-run mkdir command, and a short Russian note.
    max_output_tokens is kept low (1200) because a good project tree
    rarely needs more than ~300-400 tokens.
    """

    MAX_OUTPUT_TOKENS = 4000  # keeps costs low but prevents truncation

    def _clip(self, text: str, max_chars: int) -> str:
        t = (text or "").strip()
        if len(t) <= max_chars:
            return t
        clipped = t[:max_chars]
        cut = clipped.rfind("\n")
        if cut >= max_chars * 0.5:
            clipped = clipped[:cut]
        return clipped.rstrip() + "…"

    def build_prompt(self, project_info: str, stack: str, scope: str) -> str:
        project_clipped = self._clip(project_info, 600)
        stack_clean = (stack or "not specified").replace("_", " + ").strip()

        scope_hint = {
            "backend": "Focus ONLY on backend: API routes, services, models, config, tests. No frontend folders.",
            "frontend": "Focus ONLY on frontend: components, pages, hooks, assets, styles. No backend folders.",
            "fullstack": "Include both frontend and backend parts with a clear separation (e.g. /client and /server or monorepo packages).",
        }.get(scope, "")

        prompt = f"""\
You are an expert software architect. Generate a balanced, production-ready folder structure.

PROJECT: {project_clipped}
STACK: {stack_clean}
SCOPE: {scope} — {scope_hint}

RULES (follow strictly):
1. No god-files. Max ~200-300 lines per file responsibility.
2. Separate concerns: routes ≠ business logic ≠ data layer.
3. Include: .env.example at root, README.md, proper config files for the stack.
4. No secrets in root (no hardcoded credentials, only .env.example).
5. Tree depth: 2-3 levels max (don't over-engineer).
6. FORBIDDEN in tree: node_modules, venv, .git, .idea, __pycache__, dist, build.
7. The mkdir command must use POSIX-style paths (forward slashes), prefixed with `mkdir -p `.

Return ONLY valid JSON — no markdown fences, no text outside JSON:
{{
  "tree": "<ASCII folder tree, use ├── └── │ symbols, max 35 lines>",
  "mkdir_cmd": "<single bash line: mkdir -p path1 path2 path3 ...>"
}}

All JSON string values: escape newlines as \\n, no literal newlines inside strings.
"""
        return prompt.strip()


folder_engine = FolderEngine()
