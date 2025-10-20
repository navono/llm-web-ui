# AGENTS.md

## Dev environment tips

- Check the `pyproject.toml` file in each package to confirm project configuration—focus on the `[project]` and `[tool.uv]` sections.
- Run `make install` to install all dependencies including dev tools so your IDE, linters, and type checkers work properly.
- Use `make run` to run app.
- 需要联网查找资料时，可以使用 set_proxy 设置代理

## Testing instructions

- Find the CI plan in the `.github/workflows` folder or `tox.ini` configuration.
- Run `uv run pytest --cov=<package_name>` to run all tests with coverage for that package.
- From the package root you can just call `uv run pytest` or `uv run python -m pytest`.
- The commit should pass all tests before you merge.
- To focus on specific tests, use pytest patterns: `uv run pytest -k "<test_pattern>"` or `uv run pytest tests/test_specific.py::test_function`.
- Fix any test failures, type errors (mypy), or linting issues (ruff) until the whole suite is green.
- After refactoring code or changing imports, run `uv run mypy <package_name>` and `uv run ruff check` to ensure type safety and code quality.
- Add or update tests for the code you change, even if nobody asked. Aim for >90% test coverage.
- Testing files in `tests` folder.

## Code quality checks

- Run `make format` to format code automatically (ruff's built-in formatter).
- Run `make lint` for fast linting and auto-fixable issues.
- Run `make check` for type checking.
- Use `uv run pre-commit run --all-files` if pre-commit hooks are configured.

## Environment setup

- Copy `.env.example` to `.env` and fill in required environment variables.
- Use `uv run python -c "import <package_name>; print('Setup OK')"` to verify installation.
- For Docker development: `docker-compose up -d` to start dependent services (Redis, PostgreSQL, etc.).

## Dependency management

- Add new dependencies: `uv add <package_name>`
- Add dev dependencies: `uv add --dev <package_name>`
- Update dependencies: `uv lock --upgrade`
- Remove dependencies: `uv remove <package_name>`
- Install from lock file: `uv sync` (production) or `uv sync --all-extras` (development)
