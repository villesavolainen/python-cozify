#!/usr/bin/env python3
from cozify import hub, cloud
import sys
from time import time, sleep
import pprint


def addDevice(rule_inputs):
    if 'sensors' in rule_inputs:
        for sensor in rule_inputs['sensors']:
            watchList[sensor] = True


def removeDevice(rule_inputs):
    if 'sensors' in rule_inputs:
        for sensor in rule_inputs['sensors']:
            watchList[sensor] = False


def process_rule_change(rule):
    pprint.pprint(rule)
    rule_name = rule['config']['name']
    rule_inputs = rule['config']['inputs']
    if 'is_on' in rule:
        if rule['is_on'] == True:
            print(f'Rule active: {rule_name} Inputs: {rule_inputs}')
            addDevice(rule_inputs)
        else:
            print(f'Rule inactive: {rule_name} Inputs: {rule_inputs}')
            removeDevice(rule_inputs)


def process_rules(poll):
    for rule in poll['rules']:
        if rule in rulesToWatch:
            print(f'Rule match: {rule}')
            process_rule_change(poll['rules'][rule])


def process_devices(poll):
    for device in poll['devices']:
        if device in watchList:
            if watchList[device]:
                print(f'Device {device} triggered')


def process_poll(poll_response):
    if 'polls' in poll_response:
        print('Received poll')
        for poll in poll_response['polls']:
            print('Processing polls')
            if 'devices' in poll:
                print('Processing devices poll result')
                process_devices(poll)

            if 'rules' in poll:
                print('Processing rules poll result')
                process_rules(poll)


if __name__ == '__main__':

    res = {'timestamp': 0}
    ruleStates = {}
    watchList = {}

    rulesToWatch = ('b9ce3105-0438-4a94-83cc-1ab51d67d7fe')

    while True:
        res = hub.poll(scope='all', timestamp=res['timestamp'])
        process_poll(res)
        sleep(2)