import json
import os
import sys

from research_runtime.adapters import run_codex


def main() -> None:
    request = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else (
        "Find the latest stable Python release version and list key new features."
    )

    codex_session = os.environ.get("CODEX_SESSION_ID", os.environ.get("SESSION_ID", "unverified"))
    codex_agent = os.environ.get("CODEX_AGENT_ID", os.environ.get("AGENT_ID", "codex:researcher"))

    result = run_codex(request, caller=codex_agent, task_class="lookup")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()