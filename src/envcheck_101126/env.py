import json
import os
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from importlib import resources

from packaging import version

CONTAINER_ARCH = {
    "x86_64": "amd64",
    "AMD64": "amd64",
    "aarch64": "arm64",
    "arm64": "arm64",
}

RULES = json.loads(
    resources.files("envcheck_101126")
    .joinpath("rules.json")
    .read_text(encoding="utf-8")
)


def get_git_version():
    if shutil.which("git") is None:
        return None
    return subprocess.check_output(["git", "--version"], text=True).strip()


def get_environment():
    machine = platform.machine()
    return {
        "python_supported": version.parse(platform.python_version())
        >= version.parse(RULES["min_python"]),
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "operating_system": platform.system(),
        "architecture": machine,
        "git_version": get_git_version(),
        "container_arch": CONTAINER_ARCH.get(machine, machine),
        "current_directory": os.getcwd(),
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


def main():
    print(json.dumps(get_environment(), indent=2))


if __name__ == "__main__":
    main()
