#!/usr/bin/env python

import argparse
import json

def parse_arguments():
    parser = argparse.ArgumentParser(prog='Init command converter', description='Converts lists of init codes bytes into esp-idf LCD init commands structure')
    parser.add_argument('filename')
    parser.add_argument('-c', '--config')
    return parser.parse_args()

def finish_command(command, params, delay):
    print('{' + f' 0x{command:02X}, (uint8_t[])' + ' { ', end='')
    for i, param in enumerate(params):
        print(f'0x{param:02X}', end='')
        if i + 1 < len(params):
            print(', ', end='')
    if len(params) == 0:
        print('0x00', end='')
    print(' }, ' + f'{len(params)}, {delay}' + ' },')


args = parse_arguments()

command_format = 'Write(Command, {});'
data_format = 'Write(Parameter, {});'
delay_format = 'Delay({});'

if args.config is not None:
    config = json.loads(open(args.config).read())
    if config['command'] is None:
        print('Config must have \"command\" field')
        quit(1)
    command_format = config['command']
    if config['data'] is None:
        print('Config must have \"data\" field')
        quit(1)
    data_format = config['data']
    if config['delay'] is None:
        print('Config must have \"delay\" field')
        quit(1)
    delay_format = config['delay']

command_find = command_format[0:command_format.find('{}')]
command_end = command_format[command_format.find('{}') + len('{}'):]
data_find = data_format[0:data_format.find('{}')]
data_end = data_format[data_format.find('{}') + len('{}')]
delay_find = delay_format[0:delay_format.find('{}')]
delay_end = delay_format[delay_format.find('{}') + len('{}'):]

cmds = open(args.filename).read()
i = 0
command = -1
params = []
while True:
    next_command = i + cmds[i:].find(command_find)
    next_param = i + cmds[i:].find(data_find)
    next_delay = i + cmds[i:].find(delay_find)
    if next_param < i:
        next_param = float('inf')
    if next_command < i:
        next_command = float('inf')
    if next_delay < i:
        if next_param == float('inf') and next_command == float('inf'):
            break
        next_delay = float('inf')
    minimum = min(next_command, next_param, next_delay)
    if next_command == minimum:
        # finish last command
        if command != -1:
            finish_command(command, params, delay=0)

        # command
        i = next_command + len(command_find)
        end = i + cmds[i:].find(command_end)
        command = int(cmds[i:end], 16)
        params = []
        i = end + len(command_end)
    elif next_param == minimum:
        i = next_param + len(data_find)
        end = i + cmds[i:].find(data_end)
        params.append(int(cmds[i:end], 16))
        i = end + len(data_end)
    else:
        i = next_delay + len(delay_find)
        end = i + cmds[i:].find(delay_end)
        delay = int(cmds[i:end])
        finish_command(command, params, delay)
        command = -1
        i = end + len(delay_end)
