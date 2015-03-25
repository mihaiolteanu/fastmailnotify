#!/usr/bin/python3
"""
Checkout new email received using the IMAP protocol for fastmail.com accounts.
Send the notifications using the Ubuntu notify-send application:
http://manpages.ubuntu.com/manpages/gutsy/man1/notify-send.1.html

Python imaplib documentation: https://docs.python.org/3.4/library/imaplib.html
IMAPv4 protocol documentation: http://tools.ietf.org/html/rfc3501
"""

# Your email address at fastmail.com.
USER_NAME = "mihai_olteanu@fastmail.fm"

# Choose how to input your password.

## Uncomment this line if you want the password stored in a file.
## The string should point to the file path, either relative or absolute.
## The file should contain the password on the first line.
PASSWORD_HOW = "my_password_file"

## Uncomment this line if you want to be asked for the password 
## every time this script is run.
#PASSWORD_HOW = "ask_at_login"

# Set a nice little email icon for the notification message.
# You can change this to another icon from /usr/share/icons/gnome/32x32
NOTIFICATION_ICON = 'stock_mail-unread'

# Check for new email frequency, in seconds
REFRESH_RATE = 3


import getpass
import imaplib
import os
import sys
import subprocess
import time
from email.parser import HeaderParser


def get_folder_names(mail):
    '''
    Return all folder names that can contain email objects.
    '''
    names = []
       
    try:
        # 6.3.8. LIST Command
        result, response = mail.list()
    except imaplib.IMAP4.error:
        return[]

    #The response if of the form [b'(\\HasChildren) "." INBOX', ..]
    for entry in response:
        entry = entry.decode()
        entry = entry.split(sep="\".\"")
        if not len(entry) == 2:
            continue
        name = entry[1]
        names.append(name.strip())

    return names


def get_server_uids(mail, folder, from_uid = 0):
    """
    Return a list of unique ids for the current folder.
    @param from_uid: only return uids greater than this
    """
    if not select_folder(mail, folder):
        return []

    try:
        # https://blog.jtlebi.fr/2013/04/12/fetching-all-messages-since-last-check-with-python-imap/
        result, response = mail.uid('search', None, 'UID {}:*'.format(from_uid))
    except imaplib.IMAP4.error as err:
        print(err)
        return []

    return response[0].decode().split()


def select_folder(mail, folder):
    """
    Make the given folder the active folder.
    All future actions are to be carried out relative to this folder.
    """
    try:
        result, response = mail.select(folder, readonly = True)
    except imaplib.IMAP4.error as err:
        print(err)
        print(folder)
        return False
    # If no such folder exists
    if result == "NO":
        return False
    return True


def get_email_header(mail, folder, uid):
    """
    Returns the header of the email based on the message sequence number.
    The numbering starts from 1 through the number of emails in the folder.
    """
    if not select_folder(mail, folder):
        return []

    try:
        # 6.4.5. FETCH Command
        result, response = mail.uid('fetch', uid, '(BODY[HEADER])')
    except imaplib.IMAP4.error as err:
        print(err)
        return []

    return response


def parse_email_header(header):
    """
    Return the From and Subject from an email header.
    """
    # http://stackoverflow.com/questions/703185/using-email-headerparser-with-imaplib-fetch-in-python
    parser = HeaderParser()
    try:
        msg = parser.parsestr(header[0][1].decode())
    except (IndexError, UnicodeError, AttributeError) as err:
        print(err)
        return {'from': '', 'subject': ''}

    return {'from': msg['From'], 'subject': msg['Subject']}


def send_notification(info):
    # Send two separate arguments, the first will be the title (bolded).
    subprocess.call(['notify-send', '--icon', NOTIFICATION_ICON, info['from'], info['subject']])


def get_password():
    """
    Get the password from a local file or prompt the user for the password.
    """
    password = ""
    if PASSWORD_HOW == "ask_at_login":
        password = getpass.getpass()
    else:
        if os.path.exists(PASSWORD_HOW):
            with open(PASSWORD_HOW, 'r') as f:
                # Remove tabs, whitespace and newline.
                password = f.readline().strip(' \t\n\r')
    return password

def login():
    mail = imaplib.IMAP4_SSL("mail.messagingengine.com")
    
    password = get_password()
    if len(password) == 0:
        print("The password could not be found.")
        sys.exit()

    try:
        mail.login(USER_NAME, password)
    except imaplib.IMAP4.error as err:
        print(err)
        sys.exit()

    return mail


def get_local_uid(folder):
    """
    Return the locally stored email UID for the specified folder name.
    """
    return local_uids[folder]

def set_local_uid(folder, uid):
    """
    Set the new local email UID for the specified folder name.
    """
    global local_uids
    local_uids[folder] = uid

def initialize_local_uids(folders, local_uids):
    """
    Set the available local UID value for each folder in the given list.
    Set the UID to zero if a local folder name / value pair does not exist for that entry.
    """
    for folder in folders:
        uids = get_server_uids(mail, folder)
        try:
            uid = uids[-1]
        except IndexError:
            # No email in this folder.
            uid = 0
        local_uids[folder] = uid


def start_monitoring(mail, folders):
    try:
        while True:
            for folder in folders:
                local_uid = get_local_uid(folder)
                server_uids = get_server_uids(mail, folder, from_uid=local_uid)
                # The list of uids include the from_uid specified in the above call.
                if not server_uids:
                    # No mail in this folder. Go to the next one.
                    continue
                    
                # If no new mails, only the from_uid from the above call is returned.
                if len(server_uids) == 1 and local_uid == server_uids[0]:
                    # We've already seen this mail. Go to the next folder.
                    continue

                # Send a notification for each new mail found in this folder.
                # The first UID is for an email we already know of.
                for uid in server_uids[1:]:
                    header = get_email_header(mail, folder, uid)
                    header_info = parse_email_header(header)
                    send_notification(header_info)
            
                # Update the local folder UID with the greatest UID found on the server.
                set_local_uid(folder, server_uids[-1])
    
            time.sleep(REFRESH_RATE)
    except KeyboardInterrupt:
        print("Bye-bye!")
        return


##### Main program #####

password = get_password()
mail = login()
# All the folders (or mailboxes) in the current email account.
folders = get_folder_names(mail)
# Always set to the greatest uid for each email folder.
# If new emails arrive after we've set this, their ids will be greater than this.
# UIDs are only unique for the selected folder and NOT for the whole account,
# so keep the largest uid for each folder
local_uids = {}
initialize_local_uids(folders, local_uids)
start_monitoring(mail, folders)
