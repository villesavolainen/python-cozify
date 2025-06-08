#!/usr/bin/env python3
from cozify import hub, cloud
import sys
import pprint

def main(capability=None):
    scenes = hub.scenes()

    print("All scenes:")
    for sceneid, scene_data in scenes.items():
        scene_name = scene_data.get('name', 'Unknown')
        is_on = scene_data.get('isOn', False)
        status = "ON" if is_on else "OFF"
        print(f"ID: {sceneid}, Name: {scene_name}, Status: {status}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
