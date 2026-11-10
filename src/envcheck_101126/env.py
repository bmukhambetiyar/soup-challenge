import os
import platform
import json


def get_environment():
    return {
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "operating_system": platform.system(),
        "architecture": platform.machine(),
        "current_directory": os.getcwd(),
    }


def main():
    print(json.dumps(get_environment(), indent=2))


if __name__ == "__main__":
    main()
