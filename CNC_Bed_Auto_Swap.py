#!/usr/bin/env python3
# Import modules
import os
import re
import sys
import logging
from time import sleep
from time import asctime
from time import localtime
from pywinauto.application import Application


def except_log(err):
    logging.basicConfig(
        filename='myLog.log', level=logging.DEBUG,
        format='%(asctime)s %(levelname)s %(name)s %(message)s'
        )
    logger = logging.getLogger(__name__)
    logger.error(err)


# Function loading scanned .pgm programme to PanelMac
def auto_load(file, local, bed):
    # connecto to application
    app = Application().connect(title_re='.*Machine*')
    # create dialogs for main window, file selection window,
    # header and prog type window
    main_dlg = app.window(title_re='.*Machine panel*')
    select_dlg = app.window(title_re='^Select*')
    header_dlg = app.window(title_re='.*Change header*')
    prog_dlg = app.window(title_re='^Select automatic*')

    try:
        # try pressing shift+F8 to load the programme -
        # works only on first running the machine!
        main_dlg.wait('enabled', timeout=0.1).type_keys('+{VK_F8}')
        prog_dlg.wait('enabled', timeout=0.1).type_keys('{ENTER}')
    except:
        pass

    try:
        # press shift+f2 main dialog to open file selection window
        main_dlg.wait('enabled', timeout=0.1).type_keys('+{VK_F2}')
    except Exception as err:
        except_log(err)
        pass
    try:
        # if file selection window type file name followed
        # by ENTER to open scanned file
        select_dlg.Edit.wait('enabled', timeout=1) \
            .type_keys(local+file+'{ENTER}', with_spaces=True)
        header_dlg.set_focus()
        header_dlg.Edit4.wait('enabled', timeout=1) \
            .type_keys(bed, with_spaces=True)
    except Exception as err:
        except_log(err)
        pass


# function loading paths to be used in programme from a text/config file
def file_path():
    # declaring variables
    pattern = r'(^#[a-z]{5,6}#)([A-Z]\:\\.*)'
    local = ''
    remote = ''
    try:
        # open text file with paths to be used in programme, find lines
        # starting with drive letter and use first line as 'local' variable
        # and second as 'remote' variable
        with open('file_path.txt', 'r') as f:
            reader = f.readlines()
            for item in reader:
                find = re.search(pattern, item)
                if find[1] == '#local#':
                    local = find[2].strip()
                elif find[1] == '#remote#':
                    remote = find[2].strip()
        return local, remote
    # if file not found print error message, wait 10 seconds and exit the app
    except Exception as err:
        except_log(err)
        pass
        # sys.exit()


# Start Position function change the header file bed position to -AB when this
# app is being first started
def start_pos(local, remote):
    # declare variables
    pattern_text_file = r'([ABDC]*)'
    # Open remote header file
    try:
        with open(remote, 'r') as file:
            reader = file.read()
        file.close()
        output = ''
        # check for pattern (-AB or -DC)
        search = re.search(pattern_text_file, reader)
        # if no pattern found continue with file as is
        if search is None:
            print('No Match!')
            output = reader
        # else replaces existing bed in file with -AB
        else:
            output = reader.replace(search.group(1), 'AB')
        # Write output to file
        with open(remote, 'w') as file:
            file.write(output)
        file.close()
    # if file not found print error message and continues with programme (start
    # position is not essential part - it's here for convinience only)
    except Exception as err:
        except_log(err)
        pass


# Read Write function reads header file, check for current bed position and
# changes to the opposite
def read_write(pattern_text_file, local, remote):
    # declare variables
    output = ''
    bed = ''
    try:
        # open remote header file and reads it to 'reader' variable
        with open(remote, 'r') as file:
            reader = file.read()
        file.close()
        # look for pattern in header file
        search = re.search(pattern_text_file, reader)
        # if no pattern found prints message and output file as is
        if search is None:
            print('No required bed position to modify!')
            output = reader
        # if pattern match '-AB' change it to '-DC'
        elif search.group(1) == 'AB':
            bed = 'AB'
            output = reader.replace(search.group(1), 'DC')
        # if pattern match '-DC' change it to '-AB'
        elif search.group(1) == 'DC':
            bed = 'DC'
            output = reader.replace(search.group(1), 'AB')
        # Writes the output to the file

        with open(remote, 'w') as file:
            file.write(output)
        file.close()
        return bed
    # if file not found print error message and continue
    except Exception as err:
        except_log(err)
        pass


# Function watching local folder for changes (adding file matchin a pattern)
# and changing
# remote header file with correct bed position
def watcher():
    # variables declaration
    local, remote = file_path()
    current_time = asctime()
    pattern_file_type = r'([\w]*)([\d]*)(-)([\d]*)(\.pgm)'
    pattern_text_file = r'([ABDC]*)'
    oldDir = []
    newDir = []
    result = ''
    # create a list of existing files in local folder at the start of programme
    oldDir = os.listdir(local)
    # on starting the script set bed position to -AB
    start_pos(local, remote)
    print('Remote path:', remote)
    print('Watching local folder: ' + local + ' at:', current_time, '\n')
    # start a continous loop checkin the folder for changes every 0.2 second
    while 1:
        # pause loop for 0.2 sec to stop hogging the cpu
        sleep(0.2)
        now = localtime()
        # create a new list of files in local folder
        newDir = os.listdir(local)
        for item in newDir:
            # if item in the list match search pattern
            # (are valid programme files)
            # and is not in the old list
            # add item to the old list and run read_write and auto_load
            # functions (change current bed and queue scanned
            # program in PanelMac)
            file_type = re.search(pattern_file_type, item)
            if item not in oldDir and file_type is not None:
                current_time = asctime()
                print('Added:', item, 'at:', current_time)
                oldDir.append(item)
                # print(oldDir)
                bed = read_write(pattern_text_file, local, remote)
                auto_load(item, local, bed)


def main():
    try:
        watcher()
    except Exception as err:
        except_log(err)

if __name__ == '__main__':
    main()
