# Documentation Maintenance

Maintain project documentation in sync with code changes.

## Documentation Structure

| File                 | Purpose                     | Trigger                           |
| -------------------- | --------------------------- | --------------------------------- |
| `README.md`          | User docs (usage, examples) | New CLI commands, flags, options  |
| `CLAUDE.md`          | Claude Code context         | Architecture changes, new modules |
| `docs/ROADMAP.md`    | Dev plan with `[x]`/`[ ]`   | Tasks completed, new phases       |
| `docs/TECH_STACK.md` | Tech stack table            | New dependencies, providers       |
| `docs/TESTING.md`    | Test coverage table         | New tests, fixtures               |
| `.env.example`       | Environment variables       | New config options                |

## Style Guidelines

- Tables for reference info, code blocks for examples
- Checklists: `[x]` for done, `[ ]` for pending
- Keep it minimal — document only what's useful
- English for all docs (except PROJECT_OVERVIEW.md is Russian)

## Workflow

1. Read `CLAUDE.md` for project context
2. Identify what changed (new code, completed feature, etc.)
3. Update the relevant doc file(s)
4. Show diff of changes

If asked to document a specific feature: read the relevant source files first, then update the appropriate doc.
