# Repository Restructure Plan (Committed Guidance)

This document encodes the agreed structural conventions so future automation (agents / contributors) remain consistent.

## Target Top-Level Layout

```text
FINANCIAL-TOOLS/
  Projects/                     # All project code grouped here
    goldbach/                   # Former `Goldbach/`
    options-backtest-engine/    # Former `Options-Backtest-Engine/`
    etf-portfolio-builder/      # Former `ETF-Porfolio-Builder/` (renamed)
  notebooks/                    # Centralized Jupyter notebooks (mirrors project subfolders)
    goldbach/
    etf-portfolio-builder/
    shared/
  scripts/                      # Cross-project operational & maintenance scripts
  analyzed-reports/             # PDF reports only (no md/json/png)
  agent-trader/                 # Agent trader kept at root per numbered list (can move under Projects later if desired)
  tests/                        # Unified tests; subfolders per project
    goldbach/
    options-backtest-engine/
    etf-portfolio-builder/
    shared/
  tools/                        # Utilities, embedding builders, polygon setup, etc.
  database/                     # SQLite databases, persistent caches
  environments/                 # (Optional) central venv/env management (future)
```

## Naming Conventions

- Directories: `kebab-case` (lowercase with dashes).
- Python packages inside `Projects/` may use snake_case module names if needed; outer folder stays kebab-case.
- Only PDF artifacts retained; legacy `analysis_reports` deprecated.
- Notebook centralization: move all `.ipynb` from projects into `notebooks/<project-name>/`.

## Imports Strategy

- Add a `projects` package namespace (optional) or adjust `sys.path` in scripts.
- Example new import: `from projects.goldbach.goldbach_core import ...`.
- Where relative imports were used within a project, they remain valid after directory move if package `__init__.py` files are added.

## Git / History

- Use `git mv` semantics via committed file path changes to preserve history.
- Perform restructure in a single commit after validation.

## Tests Consolidation

- Move each project's tests into `tests/<project>/` retaining filenames.
- Adjust any hardcoded relative paths inside tests referencing old locations.

## Data & Database

- Introduce `database/` for SQLite files (future). No destructive moves until DB files exist.

## Migration Steps (Scriptable)

1. Create new directories.
2. Move project folders into `Projects/` with normalized names.
3. Create `notebooks/` structure and move notebooks.
4. Rename `analysis_reports` -> `analyzed-reports` (already referenced in code).
5. Move tests into unified `tests/` substructure.
6. Add placeholder `__init__.py` for new package paths if needed.
7. Run lint/tests to ensure imports resolve.
8. Remove obsolete references (e.g., old path names in docs).

## Agent Reminder

- DO NOT recreate markdown/json/png report artifacts.
- Always store generated ETH 15m reports under `analyzed-reports/`.
- Respect real data rule; abort on simulated data.

---
This file is authoritative for future structural automation.
