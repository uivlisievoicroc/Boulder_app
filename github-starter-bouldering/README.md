
# Bouldering Competition Admin (Python)

Admin app for managing bouldering competitions (rotații, timer, scoruri, clasament).

## Quick start

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
python -m your_package_or_entrypoint  # replace with the real entry point
```

## Testing

```bash
pytest -q
```

## Repo structure (suggested)

```
bouldering_app/
  __init__.py
  # your modules: ranking, rotations, timing, io, ui, etc.
tests/
  test_rankings.py
  test_rotations.py
.github/
  workflows/
    ci.yml
requirements.txt
README.md
```

## Notes
- Keep virtualenv and caches out of git (.gitignore included).
- The CI workflow runs pytest on pushes and PRs.
- Add your **entry point** (CLI or UI) in the README when ready.
