# -*- coding: utf-8 -*-
"""
Created on Thu Feb 27 13:05:01 2020

@author: Jason
"""

from datetime import datetime, timedelta
import arrow

def convert_to_utc(date):
    utcString = arrow.get(date).to('UTC').format('YYYY-MM-DDTHH:mm:ss.SSSZZ')
    formattedDatetime = datetime.strptime(utcString, '%Y-%m-%dT%H:%M:%S.%f+00:00')
    return formattedDatetime

def string_format_date(date):
    formattedDate = arrow.get(date).format('YYYY-MM-DDTHH:mm:ss.SSSZ').replace('+0000', 'Z')
    return formattedDate

def get_most_recent_monday():
    today = datetime.today()
    monday = today - timedelta(days=today.weekday())
    return arrow.get(monday).format('YYYY-MM-DD')

def get_current_time():
    formattedDatetime = arrow.utcnow().format('YYYY-MM-DDTHH:mm:ss.SSSZ').replace('+0000', 'Z')
    return formattedDatetime