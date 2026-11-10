# What surprised me and what still concerns me

Draft material for the paragraph in the email.

After renaming the package, the old name was still in the entry point. Build and install passed and the command crashed, while importing a module still worked. Later I left `from datetime import UTC` in `main` with lint and tests green on Python 3.13, and it was found only when the wheel was run on 3.10. The red runs from setup are still in the history.
