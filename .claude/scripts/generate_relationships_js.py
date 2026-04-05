import json
import tomllib

# Path to registry
REGISTRY_PATH = r"P:/.claude/registry/commands.toml"


def generate_relationships():
    try:
        with open(REGISTRY_PATH, "rb") as f:
            data = tomllib.load(f)

        relationships = {}

        for key, cmd in data.get("commands", {}).items():
            # Use alias or id, strictly matching what's in the tech tree if possible.
            # The tech tree uses the command name usually (e.g. "/design").
            # command.toml keys are "design".
            # The tree mostly uses keys like "/design" or "design"?
            # Looking at previous view_file, CLUSTERS uses "/design".
            # So I should probably check if the keys in TECH_DATA are with or without slash.
            # TECH_DATA keys are "strategy", but the items in 'commands' list are "/analytics", "/breakdown".
            # So the keys in RELATIONSHIPS should probably match the items: "/analytics".

            # Let's verify what the command keys are in the Tech Tree.
            # In TECH_DATA: "commands": ["/analytics", ...]
            # So keys should be "/analytics".

            cmd_id = (
                "/" + key
            )  # simplest assumption, keys in toml are "analytics", "design"

            # Check for explicit aliases if needed, but usually /key is safe.
            if "aliases" in cmd and cmd["aliases"]:
                # Use the first alias as primary key if consistent
                cmd_id = cmd["aliases"][0]

            rel_data = {}

            if "suggests_next" in cmd:
                # suggested items might be "plan", "arch". Need to convert to "/plan", "/arch"
                rel_data["next"] = [
                    ("/" + x if not x.startswith("/") and not x.startswith("@") else x)
                    for x in cmd["suggests_next"]
                ]

            if "triggers_after" in cmd:
                rel_data["prev"] = [
                    ("/" + x if not x.startswith("/") and not x.startswith("@") else x)
                    for x in cmd["triggers_after"]
                ]

            if "handles" in cmd:
                rel_data["capabilities"] = cmd["handles"]

            if rel_data:
                relationships[cmd_id] = rel_data

        # Output as JS constant
        js_output = f"const RELATIONSHIPS = {json.dumps(relationships, indent=4)};"

        with open("P:/.claude/docs/temp_relationships.js", "w", encoding="utf-8") as f:
            f.write(js_output)
        print("Generated P:/.claude/docs/temp_relationships.js")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    generate_relationships()
