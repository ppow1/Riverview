"""Create Riverview-owned RV-008.3 local runtime configuration."""

from __future__ import annotations

import argparse

from .config import bootstrap_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap the Riverview doorbell runtime.")
    parser.add_argument("--conversation-id", required=True)
    parser.add_argument("--browser-executable")
    args = parser.parse_args()
    print(bootstrap_config(args.conversation_id, args.browser_executable))


if __name__ == "__main__":
    main()
