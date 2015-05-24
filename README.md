# fastmailnotify

This is a simple email notification script for [FastMail](https://www.fastmail.com) accounts for Ubuntu.

Is uses the [`notify-send`](http://manpages.ubuntu.com/manpages/hardy/man1/notify-send.1.html) application to send the notifications, like this (sender and subject):

![alt tag](https://raw.githubusercontent.com/mihaiolteanu/fastmailnotify/master/screenshot.png)

## Installation

- Copy the `fastmailnotify.py` to your desired location.
- `$ chmod +x fastmailnotify.py`(add execute permission)
- `$ ./fastmailnotify.py` (run the script)

## Settings

Modify the downloaded file and
- Change your email address
- Choose the file where you want your password stored or let the script ask for the password every time you run it
- Pick the time interval for checking new email
- Select which folders from your inbox to ignore
- Pick another icon for the new mail notification box
