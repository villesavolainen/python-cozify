#!/usr/bin/env python3
from cozify import hub, cloud
import sys
import pprint

def main(capability=None):
    devs = None
    scenes = hub.scenes()

    pprint.pprint(scenes)
    for sceneid in scenes:
        print(f"{sceneid} {scenes[sceneid]}")
        #print(f"{sceneid['id']}: {sceneid['config']['name']}")
    #for key, dev in devs.items():
    #    print('{0}: {1}'.format(key, dev['name']))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
