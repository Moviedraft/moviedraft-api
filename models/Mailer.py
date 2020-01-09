# -*- coding: utf-8 -*-
"""
Created on Wed Jan  8 14:11:00 2020

@author: Jason
"""

from flask_mail import Mail, Message

mail = Mail()

class Emailer:
    def send_email(subject, sender, recipients, text_body, html_body):
        msg = Message(subject, sender=sender, recipients=recipients)
        msg.body = text_body
        msg.html = html_body
        mail.send(msg)