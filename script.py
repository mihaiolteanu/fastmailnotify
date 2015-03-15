#!/usr/bin/python3
"""

- imaplib documentation
https://docs.python.org/3.4/library/imaplib.html
- IMAPv4 protocol
http://tools.ietf.org/html/rfc3501
"""

import subprocess
import imaplib
import password
from email.parser import HeaderParser
import time


# List of email clients
FASTMAIL = "mail.messagingengine.com" #fastmail.com
GMAIL = "imap.gmail.com"
YAHOO = "imap.mail.yahoo.com"

# Pick your email client from the list of email clients above.
MAIL_CLIENT = FASTMAIL

PORT = "993"

# Your email address.
USER_NAME = "mihai_olteanu@fastmail.fm"
# Set the password in the password.py.

# Check for new email frequency, in seconds
REFRESH_RATE = 3


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


def get_uids(mail, folder, from_uid = 0):
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
        result, response = mail.select(folder)
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
    subprocess.call(['notify-send', info['from'], info['subject']])


##### Main program #####

# Login
mail = imaplib.IMAP4_SSL(MAIL_CLIENT, PORT)
mail.login(USER_NAME, password.PASSWORD)

# Always set to the greatest uid for each email folder.
# If new emails arrive after we've set this, their ids will be greater than this.
# UIDs are only unique for the selected folder and NOT for the whole account,
# so keep the largest uid for each folder
largest_uids = {}
    
# All the folders (or mailboxes) in the current email account.
folders = get_folder_names(mail)

# Initialize.
for folder in folders:
    uids = get_uids(mail, folder)
    try:
        uid = uids[-1]
    except IndexError:
        # No email in this folder.
        uid = 0
    largest_uids[folder] = uid

while(True):
    time.sleep(REFRESH_RATE)
    for folder in folders:
        last_uid = largest_uids[folder]
        uids = get_uids(mail, folder, from_uid=last_uid)
        # The uids returned include the from_uid specified in the above call,
        # if there are any emails in the specified folder, of course.
        if (not uids) or (len(uids) == 1 and last_uid == uids[0]):
            # No mail or no new mail in this folder.
            continue
        for uid in uids[1:]:
            header = get_email_header(mail, folder, uid)
            info = parse_email_header(header)
            send_notification(info)
            
        # Update the local uids for future queries.
        largest_uids[folder] = uids[-1]


#folder = "INBOX"
#uids = get_uids(mail, folder, 5200)
#print(uids)

#for f in largest_uid.keys():
#    print(f + ": " + str(largest_uid[f]))

#email_response = get_email_header(mail, unseen_ids[0], folder)
#info = parse_email_header(email_response)
#print(info)


#print(email_response[0][1].decode())
#print(unseen_ids)
