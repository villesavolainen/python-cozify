#!/usr/bin/env python3
from cozify import hub, cloud
import sys
import pprint

def main(filters=None):
    """List all rules from the hub, optionally filtered by their values.

    Args:
        filters(dict): Filter rules by their values by defining key value pairs as a dict.
                      Defaults to all rules.
    """
    rules = hub.rules(filters=filters)

    pprint.pprint(rules)
    for ruleid in rules:
        print(f"{ruleid} \"{rules[ruleid]['config']['name']}\" {rules[ruleid]['config']['configType']}")


if __name__ == "__main__":
    # If command-line arguments are provided, use them as filters
    # Format: key=value (e.g., isOn=True)
    filters = None
    if len(sys.argv) > 1:
        filters = {}
        for arg in sys.argv[1:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                # Convert string values to appropriate types
                if value.lower() == 'true':
                    value = True
                elif value.lower() == 'false':
                    value = False
                elif value.isdigit():
                    value = int(value)
                filters[key] = value
    main(filters)
