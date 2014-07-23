'''
Created on Jul 23, 2014

@author: calebrob6
'''

import sys
import os
import getpass
import imaplib
import datetime

import argparse
import logging

import email
import email.header
import email.utils


BOX_GMAIL_ALL = "[Gmail]/All Mail"
BOX_GMAIL_INBOX = "Inbox"

LOG_TO_FILE = False

DEVMODE = True

def initializeLogger(output_dir):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
     
    # create console handler and set level to info
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
 
    if LOG_TO_FILE:
        # create error file handler and set level to error
        handler = logging.FileHandler(os.path.join(output_dir, "error.log"),"w", encoding=None, delay="true")
        handler.setLevel(logging.ERROR)
        formatter = logging.Formatter("%(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
     
        # create debug file handler and set level to debug
        handler = logging.FileHandler(os.path.join(output_dir, "all.log"),"w")
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def processEmail(message):
    logger = logging.getLogger()
    
    messageText = ""
    messageTime = ""
    
    msg = email.message_from_string(message)
    
    '''
    This is how we would get the subject if we needed it
    '''
    #decode = email.header.decode_header(msg['Subject'])[0]
    #subject = unicode(decode[0])
        
    #get the local time from the email time
    date_tuple = email.utils.parsedate_tz(msg['Date'])
    if date_tuple:
        local_date = datetime.datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
        messageTime = local_date.strftime("%a, %d %b %Y %H:%M:%S")
           
    maintype = msg.get_content_maintype()
    if maintype == 'multipart':
        for part in msg.get_payload():
            if part.get_content_maintype() == 'text':
                messageText = part.get_payload()
    elif maintype == 'text':
        messageText = msg.get_payload()
    logger.info("Email processed with local time: %s", messageTime)
    return (messageText,messageTime,)

def main():
    
    #setup our logging
    initializeLogger("./")
    logger = logging.getLogger()
    
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    parser.add_argument("-e", "--email", help="GMail email address")
    parser.add_argument("-p", "--password", help="GMail password")
    parser.add_argument("-d", "--days", help="Days back to search for logs", type=int, default=7)
    parser.add_argument("--phone", help="Phone number that sends the logs")
    parser.add_argument("-o","--output", help="Output file to generate", default="out.csv")
    args = parser.parse_args()
    
    emailAddress = args.email
    emailPassword = args.password
    phoneNumber = args.phone
    
    if args.email == None:
        logger.debug("An email address was not specified on the command line")
        emailAddress = raw_input("Enter your email address: ").strip()
    if args.password == None:
        logger.debug("An email password was not specified on the command line")
        emailPassword = getpass.getpass("Enter your password: ")
    if args.phone == None:
        logger.debug("A phone number was not specified on the command line")
        phoneNumber = raw_input("Enter your phone number: ").strip()

    
    if DEVMODE:
        if os.path.isfile("config.txt"):
            f=open("config.txt","r")
            emailAddress = f.readline().strip()
            emailPassword = f.readline().strip()
            phoneNumber = f.readline().strip()
            f.close()
    
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    try:
        logger.debug("Trying to login with email address: %s, and password: %s",emailAddress,emailPassword)
        mail.login(emailAddress, emailPassword)
        print "Login successful %s" % (emailAddress)
        logger.info("Login was successful for %s", emailAddress)
    except imaplib.IMAP4.error, e:
        logger.error("Login failed: %s",e)
        return 1
    
    
    rv, data = mail.select(BOX_GMAIL_ALL)
    if rv == 'OK':
        
        date = (datetime.date.today() - datetime.timedelta(days=args.days)).strftime("%d-%b-%Y")
        logger.info("Searching for emails sent by %s in the past %d day(s) (since %s)", phoneNumber, args.days, date)
        rv, data = mail.uid('search', None, '(SENTSINCE {date} FROM "{number}")'.format(date=date,number=phoneNumber))
        if rv == 'OK':
            uidList = data[0].split(" ")
            
            logger.info("Found %d messages on the server", len(uidList))
            if len(uidList) > 0:
            
                dataList = []
                for uid in uidList:
                    rv, data = mail.uid('fetch', uid, '(RFC822)')
                    try:
                        rawEmail = data[0][1]
                        dataList.append(processEmail(rawEmail))
                    except Exception, e:
                        logger.error("Error processing message for uid=%s", uid)
                        logger.error("%s",e)
                        
                f=open(args.output,"w")
                f.write("Weekday,Date,Name,Value,Notes\n")
                for dataEntry in dataList:
                    if dataEntry[0].startswith("log:"):
                        parts = dataEntry[0].split(":")
                        if len(parts)>1:
                            dataValue = 0
                            comment =""
                            try:
                                dataValue = int(parts[2])
                                comment = parts[3]
                            except Exception:
                                dataValue = 0
                                comment = parts[2]
                            
                            f.write("%s,%s,%s,%s\n" % (dataEntry[1],parts[1],dataValue,comment)) #the date is formated as Weekday, Date already
                        else:
                            logger.info("Malformed log entry: %s", dataEntry[0])
                f.close()
            else:
                logger.info("Did not find any messages on the server from the phone number %s, are you sure you have logs", phoneNumber)
        else:
            logger.error("Error searching for messages, IMAP return code %s, can't continue", rv)
            return 1
        
        mail.close()
    else:
        logger.error("Error opening mailbox %s, IMAP return code %s, can't continue", BOX_GMAIL_ALL, rv)
        return 1
    
    mail.logout()
    return 0

if __name__ == '__main__':
    #non zero return values indicate error
    sys.exit(main())