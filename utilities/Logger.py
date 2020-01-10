# -*- coding: utf-8 -*-
"""
Created on Thu Jan  9 15:56:54 2020

@author: Jason
"""

from utilities.Database import mongo
from models.MailLogModel import MailLogModel
from datetime import datetime

class Logger():
    @staticmethod
    def log_send_email(msg, exceptionMessage):
        mailLog = MailLogModel(datetime.utcnow(),
                          msg.sender, 
                          msg.recipients, 
                          msg.subject, 
                          msg.body, 
                          msg.html, 
                          exceptionMessage)
        mongo.db.maillogs.insert_one(mailLog.__dict__)
        