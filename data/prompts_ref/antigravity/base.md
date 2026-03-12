# Antigravity Editor — Reference Prompt Guide

## About Antigravity
Antigravity is a powerful agentic AI coding assistant by Google DeepMind.
It operates in **AGENTIC mode**: plans work, executes tool calls (file read/write, terminal, browser), then verifies results.
It uses structured task tracking (task_boundary, notify_user tools), creates implementation plans before writing code, and validates changes after each step.

## How Antigravity Works (Key Behaviors)
- Always starts with PLANNING mode: researches the codebase, creates `implementation_plan.md`, asks user for review before coding
- Switches to EXECUTION mode to write code, and VERIFICATION mode to test it
- Uses parallel tool calls aggressively (reads multiple files simultaneously)
- Creates `task.md` artifacts to track progress with `[ ]`, `[/]`, `[x]` checkboxes
- Stores artifacts (plans, walkthroughs, notes) in `~/.gemini/antigravity/brain/<conversation-id>/`
- Follows a walkthrough artifact after completion showing what was done and what was tested

## System Prompt Requirements for Antigravity Projects

When generating a system prompt for a user working with Antigravity, the prompt should:

### 1. Define the Project Role
Tell Antigravity exactly what kind of senior engineer it should act as for THIS project.
Example: "You are a Senior TypeScript/React engineer working on [project name]. Your role is to..."

### 2. Architecture & Tech Stack Rules
List strict rules about:
- Which libraries/frameworks are allowed and which are forbidden
- File/folder structure conventions
- Naming conventions for files, components, functions, and variables
- State management approach
- API integration patterns

### 3. Code Quality Standards
- TypeScript strictness level (strict mode, no `any`, etc.)
- Preferred patterns (functional components, hooks, composition over inheritance)
- Error handling approach
- Performance constraints (no unnecessary re-renders, lazy loading rules)
- Accessibility requirements

### 4. Agentic Task Rules (specific to Antigravity)
These are CRITICAL for Antigravity — include in every prompt:
- How to break down large tasks (always create task.md with subtasks)
- When to stop and ask the user vs. when to proceed autonomously
- How to handle ambiguous requirements (research first, then plan, then ask)
- Verification steps (run tests, check build, preview in browser after each feature)

### 5. Project-Specific Context
- Key domain concepts the AI must understand
- Which files are "sensitive" (never delete, always backup before editing)
- External API rate limits or constraints
- Secrets/env vars to never expose

### 6. Output Format for Code
- Comment style and density
- Docstring format
- Whether to output code with explanations or code-only
- Maximum file size before splitting into modules

## .cursorrules Equivalent for Antigravity
Antigravity does not use `.cursorrules` files. Instead, embed rules directly in the system prompt under a `<project_rules>` XML-like tag block.

Format for Antigravity rules:
```
<project_rules>
1. Always use TypeScript strict mode
2. Never use console.log in production code (use logger utility)
3. All API calls go through /src/api/ layer only
4. Run `npm run type-check` after every file edit
...
</project_rules>
```

## Notes Field (in Russian)
Explain in the `notes` field (in Russian):
- What system prompt was generated and why
- How to paste it into Antigravity (where exactly — at conversation start or in system settings)
- What the `<project_rules>` block controls
- Any important caveats about the stack or project type
- One practical tip for getting the best results from Antigravity