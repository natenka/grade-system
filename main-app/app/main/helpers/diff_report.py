import sys
import string
import difflib
from collections import OrderedDict as odict

# Ignore commands which contains words
ignore = ['---', '+++', '@@', 'duplex', 'description', 'version 15', 'no shutdown', '*********',
          'ipv6', 'sh run', 'Current configuration', 'Building configuration', 'aqm-register-fnf',
          'clock timezone', 'vlan internal allocation', 'banner motd', '-^C', '+^C']
#'no service' , 'service ',

def cleanConfig(config):
    """
    Delete ! sign and lines with commands in ignore list.

    config - file of configuration.
    Return config as a list of commands.
    """
    if type(config) == list:
        clean_config = [i for i in config if not checkIgnore(i, ignore)]
    else:
        with open(config) as f:
            clean_config = [i.rstrip() for i in f.readlines() if i[0] != '!']
            clean_config = [i for i in clean_config if i]
            clean_config = [i for i in clean_config if not '!' in i[:3]]
            clean_config = [i for i in clean_config if not checkIgnore(i, ignore)]
    return clean_config


def makeDiff(answer_commands, student_commands):
    """
    Generate difference with difflib. Unified diff adds context to diff.

    answer_commands - list of commands from answer config to the lab,
    student_commands - list of commands from student answer config to the lab.

    Returns result as a list of commands.
    """
    diff_in_percent = round(difflib.SequenceMatcher(None, answer_commands, student_commands).ratio())
    #print "diff_in_percent", diff_in_percent*100
    difference = difflib.unified_diff(answer_commands, student_commands, n=30)
    return diff_in_percent, list(difference)


def checkIgnore(command, ignore):
    """
    Checks command if it contains words from ignore list.

    command - string, command to check,
    ignore - list of words.

    Return True if command contains word from ignore list, False otherwise.
    """
    ignore_command = False

    for word in ignore:
        if word in command:
            ignore_command = True
    return ignore_command


def childFlat(children, level=1):
    """
    Check if all children in section is in same level.
    children - list of section children.
    level - integer, current level of depth.
    Returns True if all childsren in the same level, False otherwise.
    """
    flat = True
    for child in children:
        if len(child) <= level+1:
            pass
        elif child[(level+1):][0] in string.ascii_letters:
            pass
        else:
            flat = False
    return flat


def allChildrenFlat(section_dict, level):
    """
    Function checks if all children in ALL sections is in same level.
    section_dict - dictionary with sections.
    level - integer, current level of depth.
    Returns True if all children in all sections is in the same level, False otherwise.
    """
    all_children_flat = True
    for key in section_dict.keys():
        if not childFlat(section_dict[key], level):
            return False
    return all_children_flat


def parseSection(section,level=1):
    """
    Function parse section of config.
    In result only sections with changed children returned.

    section - List of commands.
    level - integer, current level of depth.

    Returns dictionary with section header as a keys,
    and a list of commands as a value.
    """
    current_section = ''
    section_children = []
    changed = False
    section_dict = odict()

    for command in section:
        if level == 1 and (len(command) < 2 or checkIgnore(command,ignore)) or len(command) <= level:
            pass
        elif command[level] in string.ascii_letters:
            if current_section:
                if changed:
                    section_dict[current_section] = section_children
                section_children = []
                changed = False
            current_section = command
        else:
           section_children.append(command)
        if command[0] in ['-','+']:
            changed = True
    if changed:
        section_dict[current_section] = section_children
    return section_dict


def parseConfig(section,level=1):
    """
    Function recursively parse config file.

    Return:
    dictionary with section header as a keys, and a list of commands as a value.
    all_flat - True if all children flat, False overwise.
    """
    section_dict = parseSection(section, level)

    all_flat = allChildrenFlat(section_dict, level)

    while not all_flat:
        level += 1
        for key in section_dict.keys():
            if childFlat(section_dict[key]):
                pass
            else:
                s_dict, all_flat = parseConfig(section_dict[key],level)
                if s_dict:
                    section_dict[key] = s_dict
    return section_dict, all_flat


def temp_func_delete_unchanged_section(section_dict):
    changed = False
    section_dict_copy = section_dict.copy()

    for key, value in section_dict_copy.items():
        if len(key) > 1:
            if key[0] in ['-', '+']:
                changed = True
        if type(value) == list:
            for line in value:
                if line[0] in ['-', '+']:
                    changed = True
            if key == ' control-plane' and value == ['+\x03']:
                section_dict.pop(key)
            if key == '-no ip domain-lookup' and '+no ip domain lookup' in section_dict.keys():
                section_dict.pop(key)
                section_dict.pop('+no ip domain lookup')
            if not changed:
                section_dict.pop(key)
        else:
            temp_func_delete_unchanged_section(value)
    return section_dict



def delete_duplicates(diff_dict):
    diff_dict_copy = diff_dict.copy()

    for k, v in diff_dict_copy.items():
        for key, value in diff_dict_copy.items():
            if k[1:] == key[1:] and set(k[0]+key[0]) == set('+-'):
                if (type(v) == list or type(value) == list) and len(v) > 0 or len(value) > 0:
                    if len(v) == len(value):
                        k_comp = [i[1:] for i in v]
                        key_comp = [i[1:] for i in value]
                        if k_comp == key_comp:
                            if k in diff_dict:
                                diff_dict.pop(k)
                            if key in diff_dict:
                                diff_dict.pop(key)
                elif type(v) == dict or type(value) == dict:
                    pass
                else:
                    if k in diff_dict:
                        diff_dict.pop(k)
                    if key in diff_dict:
                        diff_dict.pop(key)
    return diff_dict


def report(parced_diff_dict, level = 0):
    """
    Function converts difference dictionary to list.

    parced_diff_dict - dictionary, result of parseConfig function.
    Return result list.

    If value is dictionary, function is recursively calss itself.
    """
    result = []
    #for key in sorted(parced_diff_dict.keys()):
    for key in parced_diff_dict.keys():
        if level == 0:
            result.append('\n'+key)
        else:
            result.append(key)
        value = parced_diff_dict[key]
        if type(value) == list:
            result.extend(value)
        else:
            result.extend(report(value, level=1))
    return result

def generateLabReport(lab, task, files, path_answer, path_student):
    """
    Function creates report files in current directory for given lab number.

    lab - string, lab name (number)
    task - string, task name (number)
    files - list of config filenames
    path_answer - string, pathname to answer files
    path_student - string, pathname to student files
    """

    #print "Generate report for %s %s. Files: %s" % (lab,task,', '.join(files))

    results = []
    percent = 0

    for config in files:
        answer_file = path_answer + config
        student_file = path_student + config
        a_commands = cleanConfig(answer_file)
        s_commands = cleanConfig(student_file)

        #Cut lines after 'end' as comment
        comments = []
        if 'end' in s_commands:
            end_of_config = s_commands.index('end')
            comments = s_commands[end_of_config+1:]

            s_commands = s_commands[:end_of_config+1]

        percent, diff = makeDiff(a_commands,s_commands)
        diff = cleanConfig(diff)

        diff_dict = parseConfig(diff)[0]
        diff_dict = delete_duplicates(diff_dict)
        diff_dict = temp_func_delete_unchanged_section(diff_dict)
        results.append('='*10 + config + '='*10 + '\n')
        diff_list = report(diff_dict)+comments

        if diff_list:
            for i in diff_list:
                results.append(i+'\n')
        else:
            results.append("No differences. Good job!" + '\n')
    return percent, ''.join(results)
