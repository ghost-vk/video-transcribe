---
name: maintaining-docs
description: Maintains project documentation (README, CLAUDE.md, ROADMAP, TECH_STACK) in sync with code changes. Use after implementing features, adding CLI options, or completing roadmap tasks.
---

# Documentation Maintenance

Keep project documentation synchronized with code changes.

## What to update

| Change | Update |
|--------|--------|
| New CLI command/flag | `README.md` Usage section |
| New environment variable | `README.md` Configuration + `.env.example` |
| Architecture/module change | `CLAUDE.md` Architecture section |
| Task completed | `docs/ROADMAP.md` mark as `[x]` |
| New dependency | `docs/TECH_STACK.md` |
| New tests | `docs/TESTING.md` Current Coverage table |

## Style guidelines

- Tables for reference info, code blocks for examples
- Checklists: `[x]` for done, `[ ]` for pending
- Keep it minimal — document only what's useful
- English for all docs except `PROJECT_OVERVIEW.md` (Russian)

## Workflow

1. Read `CLAUDE.md` for project context
2. Identify what changed from the code
3. Update the relevant doc file(s)
4. Show diff of changes

## Document locations

```
README.md                      # User-facing docs
CLAUDE.md                      # Claude Code context
docs/PROJECT_OVERVIEW.md       # Russian overview
docs/TECH_STACK.md             # Technology stack
docs/ROADMAP.md                # Development plan
docs/TESTING.md                # Test coverage
docs/TEST_PLAN.md              # Detailed test plan
.env.example                   # Environment variables
```
