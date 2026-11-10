# Notes on the release pipeline

## What I built

`envcheck` is a small CLI that prints facts about the machine it runs on. `naive.yml` runs on one OS and one Python version: editable install, pytest, build. `ci-cd.yml` runs lint, then one build, then three checks in parallel: unit tests on three OSes and three Python versions, the built wheel in a clean environment on the same matrix plus Linux ARM, and the same wheel in a slim container as a non-root user. On a version tag it publishes to TestPyPI with OIDC, then installs the published package and runs it on the matrix.

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

- `.gitignore`: git keeps tracking `rules.json`, but the build tool reads `.gitignore` and leaves the file out of the wheel. The naive pipeline builds and never installs the result.
- Dependency: pytest installs `packaging` for itself, so any environment with pytest hides the missing declaration. This is "works for some users".
- Windows: the unit tests passed on Windows. Only the installed command failed, because pytest captures output as UTF-8 and the runner uses cp1252.

## What it does not catch

`bug/strict-arch` was [fully green](https://github.com/bmukhambetiyar/soup-challenge/actions/runs/42794628906) at first, while the same wheel crashed with `KeyError: 'aarch64'` in a Linux ARM container on my Mac. I added a Linux ARM runner and the branch now fails there. A matrix only catches what is listed in it. The check of the published package runs after the upload, so it can report a bad release but cannot stop it.

## Silent supply-chain failures

| Failure | Status | How |
|---|---|---|
| Version does not match the tag | closed | The build job compares the tag with the built file names. [Red run for `v9.9.9`](https://github.com/bmukhambetiyar/soup-challenge/actions/runs/42808989114), nothing uploaded. |
| Stale artifact | closed | One build per run, used by every later stage. After publishing, a step compares the SHA-256 of the wheel on TestPyPI with the built one. |
| Secret reachable from a fork PR | closed | No stored secrets. Only the publish job has `id-token: write`, and it needs a `v*` tag and the `testpypi` environment. |
| Cache hiding a resolver error | closed | Nothing is cached. The cost is slower runs. |
| Unpinned dependencies | partly | Actions by commit SHA, tools by version, base image by digest. The build backend is a range. |
| Swapped dependency | open | Needs hash pinning, which I did not do. |

A version on a package index cannot be deleted, so I closed the two that end with a wrong package there, and the one that could let someone else publish. Hash pinning is open because of time: the CI tools need different packages per OS and Python version.

The tag check also caught a real mistake. I changed the version to 0.0.2, forgot to commit it, and pushed the tag. [That run](https://github.com/bmukhambetiyar/soup-challenge/actions/runs/42819399734) failed in the build job and no matrix job started.

## GPU CI

`envcheck` has no GPU code, so this is a design for an ML package released through the same pipeline. Nothing here was run.

**Assumptions.** One GPU with 16 GB of memory. A nightly run takes 20 minutes and a release run 45 minutes, including startup. 30 nightly runs x 20 min + 4 releases x 45 min = 780 minutes = 13 hours a month.

| Where (prices from 10 Nov 2026) | Price | 13 hours a month | Left on for a month, 720 hours |
|---|---|---|---|
| GitHub GPU runner, Linux 4-core | $0.052 per minute | $40.56 | cannot happen |
| AWS `g4dn.xlarge` (T4, 16 GB), on-demand | $0.526 per hour | $6.84 | $378.72 |
| AWS `g4dn.xlarge`, spot | $0.242 per hour | $3.15 | $174.24 |
| RunPod RTX A5000 (24 GB) | $0.27 per hour | $3.51 | $194.40 |

I would start with the GitHub GPU runner. It is $37 a month more than AWS spot, but there is no runner to maintain and no machine that can be forgotten. One forgotten spot instance costs $174 in a month, 55 times the planned $3.15. It needs a GitHub organization on the Team plan. At 100 GPU hours a month GitHub costs $312 and spot $24, and then I would switch to self-hosted runners on spot.

How to avoid paying for failing runs:

- The GPU job runs last and needs every CPU stage to pass.
- Its first step is a one-minute environment check, like `envcheck` extended to report the GPU. On the GitHub runner a nightly run that fails in the first 2 minutes costs $0.10, and one that fails after 20 minutes costs $1.04.
- `timeout-minutes` on the job, and no automatic retries.
- The nightly run is skipped when there are no new commits.
- No GPU job for pull requests from forks.
- On rented machines: a shutdown timer on the machine itself, and a budget alert.

## Verdict

For TestPyPI, yes, and it already publishes without a human. For real PyPI, not yet.

What the runs support: every bug I injected was stopped before the upload, and a wrong tag was stopped twice. For 0.0.1 I compared the published wheel with the tested one by hand and they were identical.

Why not yet:

- The build tools are pinned by version but not by hash, and the build backend is a range. A compromised build tool could change the wheel while every check stays green.
- Anyone who can push a `v*` tag can release, and a tag can be put on any commit.
- The pipeline only catches what its matrix lists. Linux ARM was green until I added it.
- The check of the published package runs after the upload, which cannot be undone.

What to fix first: hash-pin the build job, then restrict who can create `v*` tags. Until both are done I would keep one human approval on the publishing environment. The pipeline does the checking and the person only confirms the release.

How I used AI is in [AI_USE.md](AI_USE.md).
