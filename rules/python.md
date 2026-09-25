# Python

- Use type hints on all function signatures. Return type required.
- Prefer `pathlib.Path` over `os.path`. Prefer f-strings over `.format()`.
- Use `uv` for package management when available, fallback to `pip`.
- Prefer `raise ValueError("reason")` over bare `raise` or `assert` for validation.
