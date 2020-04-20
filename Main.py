import pandas as pd
import os
from os import path
import json

main_commands = {'exit': 'exit',
                 'save': 'save - Saves your changes to the database. '
                         '\n\t - A save operation can be appended to any other main command with -s'
                         '\n\t - A copy of the current data frame may be created by providing the -S '
                         '\n\t   switch followed by a filename for the output.',
                 'update': '',
                 'insert': '',
                 'delete': '',
                 'help': '',
                 'select': '',
                 'frame': '',
                 'switch': ''
                 }

schema_string = open("student_schema.json", "r").read()
schema = json.loads(schema_string)
if 'ID' not in schema:
    print('The provided schema does not have an identifier property named ID. '
          'This is required by this application. Please provide another schema '
          'file if you wish to use this application')
main_database_file = 'student_database.csv'
if path.exists("./"+main_database_file):
    print('Found db')
else:
    new_db = open('./student_database.csv', "w+")
    first_line = ''
    for field in schema:
        first_line += field + ","
    first_line = first_line[:-1]
    first_line += '\n'
    new_db.write(first_line)
    new_db.close()

origin = pd.read_csv('./student_database.csv', index_col='ID')

dataframes = {'origin': origin}
current_frame = 'origin'
switches = {
            '-f':
                {'arg_num': 999,
                 'message':'-f - used to specify fields for selection, update, insert, and delete statements'},
            '-i': {'arg_num': 2,
                   'message': '-i - used to specify ID. Short hand for deletion statements.'},
           '-w': {'arg_num': 999,
                  'message': '-w - shorthand for specifying vales. must use the form -w field:value and:field:value'},
            '-s': {'arg_num': 0,
                   'message': '-s - saves changes to the database'},
            '-S': {'arg_num': 1,
                   'message': '-S - saves the current data frame to a new file given a new file-name'},
            '-v': {'arg_num': 999,
                   'message': '-v - used to specify values. Used in conjunction with -f'}
            }


def print_help_message():
    for message in main_commands:
        print(main_commands[message], "\n")
    for info in switches:
        print(switches[info]['message'], '\n')


def can_be_type(var, type):
    try:
        y = type(var)
        return True
    except(ValueError, TypeError):
        return False



def verify_schema(row):
    count = 0
    print(row)
    for field in schema:
        print(field + " " + str(pd.isna(row[count])))
        if schema[field]['required'] & pd.isna(row[count]):
            return False, f"No value: The field {field} is required but not supplied at row {row[0]}"
        if schema[field]['type'] == 'string':
            if not can_be_type(row[count], str):
                return False, f"Type error: Expected type string\n\tError occurred in row {row[0]} at field {field}"


        count += 1
    return True, "Success"


def parse_commands(input):
    command_input = input.split(' ')
    command_dict = {}
    if not command_input[0] in main_commands:
        return False, command_input[0]
    command_dict['main'] = command_input[0]
    last_switch = ''
    for term in command_input[1:]:
        if term[0] == '-':
            if term not in switches:
                return False, term
            command_dict[term] = ['args']
            last_switch = term
        else:
            command_dict[last_switch].append(term)

    return True, command_dict

def filter_rows(filter_command):
    output = pd.DataFrame()
    hold = pd.DataFrame()
    for pair in filter_command:
        pair = pair.split(':')
        if len(pair) == 2:
            output.append(dataframes[current_frame].loc(dataframes[current_frame][pair[0]] == pair[1]))
        else:
            if pair[0] == 'and':
                output.drop(output[pair[1]] != pair[2])
            elif pair[0] == 'or':
                output.append(dataframes[current_frame].loc(dataframes[current_frame][pair[1]] == pair[2]))
    return output

while True:
    print('Enter help to display the help message or exit to close the program.')
    command = input("Please enter a command:")

    success, commands = parse_commands(command)

    if not success:
        print(f'Malformed command string, error at switch or main argument {commands}')
        print(f'Command must start with a main command of {main_commands}'
              f'\nand may only contain switches {switches.keys()}')
        continue

    if commands['main'] == "exit":
        break
    if commands['main'] == "help":
        print_help_message()
    if commands['main'] == "save":
        can_save = True
        for row in dataframes[current_frame].iterrows():
            can_save, message = verify_schema(row)
            if not can_save:
                print(message)
                break
        if can_save:
            dataframes[current_frame].to_csv(main_database_file)
    if commands['main'] == "update":
        if len(commands) == 1:
            print('Please provide an ID with the -i command to specify the '
                  'row you want to edit, or search by field using -f <field name> <value>')
            if '-i' in commands:
                print(commands['-i'])
                # find row by id
            if '-f' in commands:
                print(commands['-f'])
                # display rows matching search term
    if commands['main'] == "insert":
        if '-f' not in commands:
            fields = input('Enter the fields you want to initialize as a comma delimited list. No spaces.')
            fields = fields.split(',')
        else:
            fields = commands['-f'][1:]

        if '-v' not in commands:
            values = input('Enter the values you want to initialize as a comma delimited list. No spaces.')
            values = values.split(',')
        else:
            values = commands['-v'][1:]
        if len(values) != len(fields):
            print('')
        dataframes[current_frame] = dataframes[current_frame].append(dict(zip(fields, values)), ignore_index=True)


    if commands['main'] == "delete":
        dataframes[current_frame].drop(dataframes[current_frame].loc(dataframes[current_frame]['ID'] == commands['-i']))
    if commands['main'] == "select":
        if '-w' not in commands:
            print(dataframes[current_frame].to_string())
        else:
            new_frame = filter_rows(commands['-w'][1:])
            print(new_frame)
            save_frame = input('Would you like to save this frame? [y] [n]')
            if save_frame == 'y':
                new_name = input("Please give it a name")
                dataframes[new_name] = new_frame
    if commands['main'] == "frame":
        print()
    if commands['main'] == "switch":
        print()

    print(dataframes[current_frame].to_string())
