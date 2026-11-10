# envcheck

A small command-line tool that prints facts about the machine it runs on: Python version, OS, architecture, container architecture and whether git is installed.

This repository is my take-home task for the DevOps internship at Soup. The package is small on purpose. The task is about the release pipeline around it: can it be trusted to publish to PyPI with no human involved?

- Notes (the write-up): [docs/NOTE.md](https://github.com/bmukhambetiyar/soup-challenge/blob/main/docs/NOTE.md)
- How I used AI: [docs/AI_USE.md](https://github.com/bmukhambetiyar/soup-challenge/blob/main/docs/AI_USE.md)
- Package on TestPyPI: [envcheck-101126](https://test.pypi.org/project/envcheck-101126/)

## Try the package

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ envcheck-101126
envcheck
envcheck --json
```

The second index is needed because the one dependency, `packaging`, is on PyPI and not on TestPyPI. Python 3.10 or newer.

## The two pipelines

| Workflow | What it does |
|---|---|
| [`naive.yml`](https://github.com/bmukhambetiyar/soup-challenge/blob/main/.github/workflows/naive.yml) | One OS, one Python version. Installs the project in editable mode, runs pytest, builds. It never installs what it built. |
| [`ci-cd.yml`](https://github.com/bmukhambetiyar/soup-challenge/blob/main/.github/workflows/ci-cd.yml) | The pipeline I am submitting. Stages below. |

Stages of `ci-cd.yml`:

1. **Lint.** ruff check and format check.
2. **Build.** One build of the sdist and wheel. On a tag, it fails here if the tag does not match the built version.
3. **Three checks in parallel**, all against that one build:
   - unit tests on Linux, Windows and macOS with Python 3.10, 3.12 and 3.14;
   - the built wheel installed in a clean environment on the same matrix plus Linux ARM, then the real `envcheck` command is run;
   - the same wheel in a slim container as a non-root user.
4. **Publish to TestPyPI.** Only on a `v*` tag, with a short-lived OIDC token. No stored secrets.
5. **Check the published package.** Installs it from TestPyPI on the matrix, runs it, and compares its SHA-256 with the wheel that was tested.

## Evidence

Each bug is one commit on its own branch. The workflows are the same on every branch. For every bug the naive pipeline is green and `ci-cd.yml` is red.

| Branch | The bug | Naive CI | CI/CD | Caught by |
|---|---|---|---|---|
| `bug/utc-import` | `from datetime import UTC`, which needs Python 3.11 | [green](https://github.com/bmukhambetiyar/soup-challenge/actions/runs/42812077521) | [red](https://github.com/bmukhambetiyar/soup-challenge/actions/runs/42812077753) | tests and wheel check, Python 3.10 only |
| `bug/unicode-output` | prints a `✓` in text mode | [green](https://github.com/bmukhambetiyar/soup-challenge/actions/runs/42812076442) | [red](https://github.com/bmukhambetiyar/soup-challenge/actions/runs/42812076406) | wheel check, Windows only |
| `bug/undeclared-dep` | `packaging` removed from dependencies | [green](https://github.com/bmukhambetiyar/soup-challenge/actions/runs/42812079401) | [red](https://github.com/bmukhambetiyar/soup-challenge/actions/runs/42812078749) | wheel check and container |
| `bug/gitignored-data` | `*.json` added to `.gitignore`, so a data file is left out of the wheel | [green](https://github.com/bmukhambetiyar/soup-challenge/actions/runs/42812077793) | [red](https://github.com/bmukhambetiyar/soup-challenge/actions/runs/42812077855) | tests, wheel check and container |
| `bug/missing-git` | calls `git` without checking it exists | [green](https://github.com/bmukhambetiyar/soup-challenge/actions/runs/42812077019) | [red](https://github.com/bmukhambetiyar/soup-challenge/actions/runs/42812076738) | container only |
| `bug/strict-arch` | strict lookup in the architecture map, no `aarch64` | [green](https://github.com/bmukhambetiyar/soup-challenge/actions/runs/42812076456) | [red](https://github.com/bmukhambetiyar/soup-challenge/actions/runs/42812076464) | wheel check, Linux ARM only |
| `incident/release-0.9.3` | all six together, named after the release in the task | [green](https://github.com/bmukhambetiyar/soup-challenge/actions/runs/42812077946) | [red](https://github.com/bmukhambetiyar/soup-challenge/actions/runs/42812077988) | tests, wheel check and container |
| `main` | none | [green](https://github.com/bmukhambetiyar/soup-challenge/actions/runs/42872374541) | [green](https://github.com/bmukhambetiyar/soup-challenge/actions/runs/42872374456) | |

Release runs:

| Tag | Result | What it shows |
|---|---|---|
| `v0.0.1` | [green](https://github.com/bmukhambetiyar/soup-challenge/actions/runs/42811313788) | Published to TestPyPI with OIDC, then installed from TestPyPI and run on nine machines |
| `v9.9.9` | [red](https://github.com/bmukhambetiyar/soup-challenge/actions/runs/42808989114) | Deliberate wrong tag. Stopped before the upload. |
| `v0.0.2`, first attempt | [red](https://github.com/bmukhambetiyar/soup-challenge/actions/runs/42819399734) | My mistake: the version bump was not committed. Stopped in the build job, before the matrix. |

`bug/strict-arch` was [fully green](https://github.com/bmukhambetiyar/soup-challenge/actions/runs/42794628906) until I added the Linux ARM runner. Earlier red runs, including setup mistakes, are still in the Actions history. Nothing was deleted or force-pushed.

## Run the checks locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e . pytest==9.2.0 ruff==0.17.4 build==1.6.1
ruff check src tests && ruff format --check src tests
pytest
python -m build
```

To see what the naive pipeline misses, install the built wheel in a clean environment and run the command from another folder:

```bash
python -m venv /tmp/clean && /tmp/clean/bin/pip install dist/*.whl
cd /tmp && /tmp/clean/bin/envcheck
```

## Layout

```
.github/workflows/   naive.yml and ci-cd.yml
src/envcheck_101126/ the package and its data file rules.json
tests/               unit tests
scripts/env_dump.py  prints environment facts, used to compare CI runners
Dockerfile           installs the built wheel and runs it as a non-root user
docs/                the notes
```

## License

MIT
