# Linting and Formatting

This project uses:

- `flake8` for linting
- `black` for code formatting

Both are already listed in [requirements.txt](../requirements.txt).

Linting is run through the helper script [scripts/lint.py](../scripts/lint.py).

## Quick commands

Run lint checks:

```bash
python ./scripts/lint.py
```

Run lint + auto-format before linting:

```bash
python ./scripts/lint.py --fix
```

Notes:

- `python ./scripts/lint.py` runs `flake8` on `src`, `tests`, and `scripts`.
- `python ./scripts/lint.py --fix` first runs `black`, then runs `flake8`.

## Recommended pre-PR workflow

Before opening a pull request:

1. Run lint script in fix mode
2. Re-run lint checks
3. Run tests

```bash
python ./scripts/lint.py --fix
python ./scripts/lint.py
pytest
```

## Common fixes

- Line too long (`E501`):
  - Re-wrap long lines or run `python ./scripts/lint.py --fix`
- Unused imports/variables (`F401`, `F841`):
  - Remove unused symbols
- Whitespace/style issues:
  - Run `python ./scripts/lint.py --fix`

## Notes

- Keep formatting/lint-only commits separate when possible.
- If a lint rule conflicts with readability, prefer clear code and add a targeted exception only when justified.
