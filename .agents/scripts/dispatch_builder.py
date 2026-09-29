"""
dispatch_builder.py
Script atômico para selecionar e direcionar o subagente construtor em background.
"""
import sys
import json
import argparse

def dispatch_builder(builder_type: str, item_name: str) -> dict:
    builder_map = {
        "skill": "SKILL_CREATOR_AGENT",
        "script": "SCRIPT_CREATOR_AGENT",
        "command": "COMMAND_CREATOR_AGENT",
        "hook": "HOOK_CREATOR_AGENT"
    }
    target_builder = builder_map.get(builder_type.lower(), "SKILL_CREATOR_AGENT")
    return {
        "status": "dispatched",
        "builder": target_builder,
        "item": item_name
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--builder", default="skill")
    parser.add_argument("--item", default="exemplo_item")
    args = parser.parse_args()
    print(json.dumps(dispatch_builder(args.builder, args.item), indent=2))
