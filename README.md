emailLogger
===========

Send SMS messages to your gmail account in the form log:[Type of log]:[Data value (optional)]:[Note] and this program will parse them into a csv file

Example: log:pushups:30:Got very sore
Example: log:woke up
Example: log:pushups:100

You will need to double check you email account to see what format your SMS texts are recieved. This program does an imap search for any emails with the phone number you input as a substring. 
It expects that the message body will contain your text.

usage: main.py [-h] [-v] [-e EMAIL] [-p PASSWORD] [-d DAYS] [--phone PHONE] [-o OUTPUTFILE]

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         increase output verbosity
  -e EMAIL, --email EMAIL
                        GMail email address
  -p PASSWORD, --password PASSWORD
                        GMail password
  -d DAYS, --days DAYS  Days back to search for logs
  --phone PHONE         Phone number that sends the logs
  -o OUTPUT, --output OUTPUT
                        Output file to generate