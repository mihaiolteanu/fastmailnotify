"""

- imaplib documentation
https://docs.python.org/3.4/library/imaplib.html
- IMAPv4 protocol
http://tools.ietf.org/html/rfc3501
"""

import imaplib
import password
from email.parser import HeaderParser


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
        names.append(name)

    return names


def get_unseen_emails_id(mail, folder):
    """
    Return a list of ids for the unseen emails in the specified folder.
    """
    # Asume the name of the folder is correct, the search function will throw 
    # an error if the folder is not found.
    if not select_folder(mail, folder):
        return []

    try:
        # 6.4.4. SEARCH Command
        result, response = mail.search(None, 'UNSEEN')
    except imaplib.IMAP4.error as err:
        print(err)
        return []

    # The response is of the form [b'23 24 25..'], 
    # where 23,24, 25 are the ids we're after
    try:
        response = response[0].decode().split()
    except (IndexError, UnicodeError) as err:
        print(err)
        return[]

    return response


def select_folder(mail, folder):
    """
    Make the given folder the active folder.
    All future actions are to be carried out relative to this folder.
    """
    result, response = mail.select(folder)
    # If no such folder exists
    if result == "NO":
        return False
    return True


def get_email_header(mail, number, folder):
    """
    Returns the header of the email based on the message sequence number.
    The numbering starts from 1 through the number of emails in the folder.
    """
    if not select_folder(mail, folder):
        return []

    try:
        # 6.4.5. FETCH Command
        result, response = mail.fetch(number, '(BODY[HEADER])')
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


mail_instance = imaplib.IMAP4_SSL(host=MAIL_CLIENT, port=PORT)
mail_instance.login(user=USER_NAME, password=PASSWORD)
    
#folders = get_folder_names(mail_instance)

folder = "INBOX"


unseen_ids = get_unseen_emails_id(mail, folder)
print(unseen_ids)
#email_response = get_email_header(mail, unseen_ids[0], folder)
#info = parse_email_header(email_response)
#print(info)


#print(email_response[0][1].decode())
#print(unseen_ids)
