import json
import argparse

from .env import get_environment


def main():
    parser = argparse.ArgumentParser(
        description="Display the current environment information"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output the environment information in JSON format"
    )

    args = parser.parse_args()

    env = get_environment()

    if args.json:
        print(json.dumps(env, indent=2))
    else:
        for key, value in env.items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
