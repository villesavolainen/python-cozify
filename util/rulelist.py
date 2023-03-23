#!/usr/bin/env python3
from cozify import hub, cloud
import sys
import pprint

def main(capability=None):
    devs = None
    rules = hub.rules()

    pprint.pprint(rules)
    for ruleid in rules:
        print(f"{ruleid} \"{rules[ruleid]['config']['name']}\" {rules[ruleid]['config']['configType']}")
        #print(f"{ruleid['id']}: {ruleid['config']['name']}")
    #for key, dev in devs.items():
    #    print('{0}: {1}'.format(key, dev['name']))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
