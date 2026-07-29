# Releasing propwrap

## Checklist

1. Version in `pyproject.toml` matches intended tag (e.g. `0.1.0` → `v0.1.0`)
2. `CHANGELOG.md` updated
3. Tests green: `pytest -q`
4. Build clean:

```bash
pip install -e ".[dev]"
python -m build
twine check dist/*
```

5. Smoke-test the wheel in a **fresh** venv:

```bash
python -m venv .venv-smoke
# activate …
pip install dist/propwrap-*-py3-none-any.whl
propwrap run RP-1 LOX --of 2.56 --pc-bar 70 --eps 20
python -c "import cantera, matplotlib, propwrap; print(propwrap.__version__)"
```

6. Commit, tag, push:

```bash
git add -A
git commit -m "Release v0.1.0"
git tag -a v0.1.0 -m "propwrap 0.1.0"
git push origin main
git push origin v0.1.0
```

7. Create a GitHub Release from the tag (optional but recommended).

8. Upload to PyPI (needs a PyPI API token):

```bash
# Test PyPI first (recommended once):
# twine upload --repository testpypi dist/*

twine upload dist/*
```

Set `TWINE_USERNAME=__token__` and `TWINE_PASSWORD=pypi-...` (or use `~/.pypirc`).

## Notes

- Cantera and matplotlib are **required** dependencies (not extras).
- propwrap source is MIT; RocketCEA is GPL-family — keep that in the long description.
- After upload, verify: `pip install propwrap==0.1.0` in a clean environment.
