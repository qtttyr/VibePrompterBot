import os
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Resolve the data directory relative to this file's location,
# so it works regardless of the working directory when the bot is launched.
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", ".."))
_DEFAULT_BASE_DIR = os.path.join(_PROJECT_ROOT, "data", "prompts_ref")


class PromptEngine:
    def __init__(self, base_dir: str = _DEFAULT_BASE_DIR):
        self.base_dir = base_dir

    def _read_file(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            logger.warning("Prompt file not found: %s", file_path)
            return ""
        try:
            with open(file_path, mode="r", encoding="utf-8") as f:
                return f.read()
        except Exception as exc:
            logger.error("Error reading file %s: %s", file_path, exc)
            return ""

    def _clip(self, text: str, max_chars: int) -> str:
        """Trim text to max_chars, cutting on a newline boundary where possible."""
        t = (text or "").strip()
        if max_chars <= 0:
            return ""
        if len(t) <= max_chars:
            return t
        clipped = t[:max_chars]
        cut = clipped.rfind("\n")
        if cut >= max_chars * 0.6:
            clipped = clipped[:cut]
        return clipped.rstrip() + "\n…"

    async def build_prompt(self, data: dict[str, Any]) -> str:
        editor = (data.get("editor") or "cursor").strip().lower()
        stack = (data.get("stack") or "not specified").strip()
        ai_model = (data.get("model") or "not specified").strip()
        project_info = str(data.get("project_info") or "").strip()
        idea = str(data.get("idea") or "").strip()

        # 1. Load global rules (Master Vibe)
        master_vibe = self._read_file(os.path.join(self.base_dir, "master_vibe.md"))

        # 2. Load editor-specific reference prompt
        editor_path = os.path.join(self.base_dir, editor, "base.md")
        editor_rules = self._read_file(editor_path)

        # Clip inputs to keep the prompt within a reasonable token budget.
        # Output tokens are set separately and should be large (see generator.py).
        editor_rules_clipped = self._clip(editor_rules, 1200)
        project_info_clipped = self._clip(project_info, 1500)
        idea_clipped = self._clip(idea, 800)

        # Determine which rules field to populate
        if editor == "cursor":
            rules_field_name = "cursorrules"
            other_rules_field = "windsurfrules"
        elif editor == "windsurf":
            rules_field_name = "windsurfrules"
            other_rules_field = "cursorrules"
        elif editor == "trae":
            rules_field_name = "cursorrules"   # Trae uses its own but we repurpose cursorrules
            other_rules_field = "windsurfrules"
        else:
            # claude_code, vscode, antigravity, etc. — no .rules file needed
            rules_field_name = "cursorrules"
            other_rules_field = "windsurfrules"

        final_prompt = f"""\
{master_vibe}

---

## USER PROJECT DATA

**Editor:** {editor}
**Tech Stack:** {stack}
**AI Model inside editor:** {ai_model}

### Editor Reference Rules (for your inspiration, adapt to the project)
{editor_rules_clipped}

### Project Description
{project_info_clipped}

### Task / Idea to implement
{idea_clipped}

---

## YOUR TASK

Based on all the data above, generate a **personalised, ready-to-use prompt package** for this developer.

Return **only** a valid JSON object — no markdown fences, no extra text outside the JSON.

JSON schema:
{{
  "system_prompt": "<string: the main system prompt for the AI editor, specific to this project and stack. Must be at least 30 lines, written in English. Must NOT be generic — every paragraph must reference the project context.>",
  "{rules_field_name}": "<string: editor rules file content tailored to this project (.{rules_field_name} format). 20-80 lines. English.>",
  "{other_rules_field}": "",
  "notes": "<string: 5-8 bullet points in Russian explaining what was generated and how to use it. Start each bullet with '• '.>"
}}

Rules:
- system_prompt MUST be specific and project-aware (never a generic template).
- {rules_field_name} MUST reflect the actual stack ({stack}) and editor ({editor}).
- notes MUST be in Russian.
- All JSON string values must be properly escaped (newlines as \\n, quotes as \\", etc.).
- Return ONLY the JSON object. No backticks, no commentary outside JSON.
"""
        return final_prompt.strip()


prompt_engine = PromptEngine()
