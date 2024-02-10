#!/usr/bin/env python3
from cozify import hub, cloud
import sys
import pprint

def main(capability=None):
    devs = None
    users = hub.users()

    pprint.pprint(users)
    for userid in users:
        print(f"{userid} {users[userid]}")
        #print(f"{ruleid['id']}: {ruleid['config']['name']}")
    #for key, dev in devs.items():
    #    print('{0}: {1}'.format(key, dev['name']))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
