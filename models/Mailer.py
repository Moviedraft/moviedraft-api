# -*- coding: utf-8 -*-
"""
Created on Wed Jan  8 14:11:00 2020

@author: Jason
"""

from flask_mail import Mail, Message
from models.Logger import Logger

mail = Mail()

class Emailer:
    def send_email(subject, sender, recipients, text_body, html_body):
        msg = Message(subject, sender=sender, recipients=recipients)
        msg.body = text_body
        msg.html = html_body
        
        exceptionMessage = ''
        
        try:
            mail.send(msg)
        except Exception as ex:
            exceptionMessage = ex.message
        finally:
            Logger.log_send_email(msg, exceptionMessage)
            
            
            