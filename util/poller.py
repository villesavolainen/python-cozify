#!/usr/bin/env python3
from cozify import hub, hub_api, cloud
import sys
from time import time, sleep


def main():
    res = {'timestamp': 0}
    while True:
        res = hub.hub_poll(ts=res['timestamp'])
        print(res)
        sleep(2)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
