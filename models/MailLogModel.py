# -*- coding: utf-8 -*-
"""
Created on Thu Jan  9 15:46:25 2020

@author: Jason
"""

class MailLogModel():
    def __init__(self, dateSentUtc, sender, recipients, subject, textBody, textHtml, exception):
        self.dateSentUtc = dateSentUtc
        self.sender = sender
        self.recipients = recipients
        self.subject = subject
        self.textBody = textBody
        self.textHtml = textHtml
        self.exception = exception