# Notes on the release pipeline

## What I built

`envcheck` is a small CLI that prints facts about the machine it runs on: Python version, OS, architecture, whether git is installed.

`naive.yml` runs on one OS and one Python version: editable install, pytest, build. `ci-cd.yml` runs lint, then one build, then three checks in parallel: unit tests on three OSes and three Python versions, the built wheel in a clean environment on the same matrix plus Linux ARM, and the same wheel in a slim container as a non-root user. On a version tag it publishes to TestPyPI with OIDC, then installs the published package from TestPyPI and runs it on the matrix.

I changed the stage order myself. At first the build came after the tests and the tag check ran in the publish job, so a wrong tag was found after about twenty jobs. Now the build follows lint and the tag check runs there. The cost is that a package is built even when tests later fail. It is never published, because publishing needs every check to pass.

## The bugs

Each bug is one commit on its own branch, with the same workflows as `main`. Claude suggested this design, I decided to keep it because it would show us where each bug occurs. Naive CI is green on all seven branches.

| Branch | Change | Caught by |
|---|---|---|
| [`bug/utc-import`](https://github.com/bmukhambetiyar/soup-challenge/actions/runs/42812077753) | `from datetime import UTC` | tests and wheel check, Python 3.10 only |
| [`bug/unicode-output`](https://github.com/bmukhambetiyar/soup-challenge/actions/runs/42812076406) | printed a `✓` in text mode | wheel check, Windows only |
| [`bug/undeclared-dep`](https://github.com/bmukhambetiyar/soup-challenge/actions/runs/42812078749) | removed `packaging` from dependencies | wheel check and container |
| [`bug/gitignored-data`](https://github.com/bmukhambetiyar/soup-challenge/actions/runs/42812077855) | added `*.json` to `.gitignore` | tests, wheel check and container |
| [`bug/missing-git`](https://github.com/bmukhambetiyar/soup-challenge/actions/runs/42812076738) | called `git` without checking it exists | container only |
| [`bug/strict-arch`](https://github.com/bmukhambetiyar/soup-challenge/actions/runs/42812076464) | strict lookup in the architecture map | wheel check, Linux ARM only |
| [`incident/release-0.9.3`](https://github.com/bmukhambetiyar/soup-challenge/actions/runs/42812077988) | all six | tests, wheel check and container |

`main` is [green](https://github.com/bmukhambetiyar/soup-challenge/actions/runs/42812078355), and [this run](https://github.com/bmukhambetiyar/soup-challenge/actions/runs/42811313788) published 0.0.1 to TestPyPI.

- `.gitignore`: git keeps tracking `rules.json` and the build succeeds, but the build tool reads `.gitignore` and leaves the file out of the wheel. The naive pipeline runs the build and never installs the result.
- Dependency: pytest installs `packaging` for itself, so any environment with pytest hides the missing declaration. The same broken wheel worked in the `python:3.10-slim` image, which ships `packaging`, and failed in a fresh venv. This is "works for some users".
- Windows: the unit tests passed on Windows. Only the installed command failed, because pytest captures output as UTF-8 and the Windows runner uses cp1252.

## What it does not catch

`bug/strict-arch` was [fully green](https://github.com/bmukhambetiyar/soup-challenge/actions/runs/42794628906) at first, while the same wheel crashed with `KeyError: 'aarch64'` in a Linux ARM container on my Mac. macOS and Linux name the same architecture differently, so the macOS runner did not help. I added a Linux ARM runner and the branch now fails there.

A matrix only catches what is listed in it. The check of the published package runs after the upload, so it can report a bad release but cannot stop it.

## Silent supply-chain failures

| Failure | Status | How |
|---|---|---|
| Version does not match the tag | closed | The build job compares the tag with the version in the built file names. [Red run for `v9.9.9`](https://github.com/bmukhambetiyar/soup-challenge/actions/runs/42808989114), nothing uploaded. |
| Stale artifact | closed | One build per run, used by every later stage. After publishing, a step compares the SHA-256 of the wheel on TestPyPI with the built one. For 0.0.1 I compared by hand and they matched. The step was added after that release. |
| Secret reachable from a fork PR | closed | No stored secrets. Only the publish job has `id-token: write`, and it needs a `v*` tag and the `testpypi` environment. The trigger is `pull_request`, not `pull_request_target`. |
| Cache hiding a resolver error | closed | Nothing is cached. The cost is slower runs. |
| Unpinned dependencies | partly | Actions by commit SHA, tools by version, base image by digest. The build backend is a range, `hatchling >= 1.26`. |
| Swapped dependency | open | Needs hash pinning, which I did not do. |

A version on a package index cannot be deleted, so I closed the two that end with a wrong package there: a tag that does not match and a file that was not the one tested. The fork secret is the one that could let someone else publish. Hash pinning is open because of time: the CI tools need different packages per OS and Python version. The runtime dependency `packaging>=22` is a range on purpose, because a library declares what it is compatible with and exact pins belong in CI.

The tag check also caught a real mistake. I changed the version to 0.0.2, forgot to commit it, and pushed the tag `v0.0.2`. [That run](https://github.com/bmukhambetiyar/soup-challenge/actions/runs/42819399734) failed in the build job and no matrix job started.

## What I would fix first

The first thing to fix before real PyPI is the build job. Its tools are pinned by version but not by hash, and the build backend is an open range. A compromised build tool could change the wheel while every check stays green.

How I used AI is in [AI_USE.md](AI_USE.md).

## Still to write

GPU CI costs (part 4) and the verdict (part 5).
