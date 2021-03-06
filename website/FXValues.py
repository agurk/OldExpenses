#!/usr/bin/python

import sys
import sqlite3
import time
import datetime
from datetime import date, timedelta, datetime
import config
import expensesSQL

class FXValues:

    def __init__(self):
        self.months={}

    def FXAmount(self, amount, baseCCY, ccy, date):
        baseCCY = baseCCY.upper()
        ccy = ccy.upper()
        if baseCCY == ccy:
            return amount
        dateObj = datetime.strptime(date, '%Y-%m-%d')
        month = str(dateObj.month)
        if len(month) == 1:
            month = '0' + month 
        year = str(dateObj.year)
        day = dateObj.day
        key = str(month) + '-' + str(year)
        if key not in self.months.keys():
            self.months[key] = FXMonth(month, year)
        if (self.months[key].getRate(baseCCY, ccy, day) < 0):
            print ('not found, looking back a month for: ' + str(amount) +', ' +baseCCY +', '+ccy+', '+date, file=sys.stderr)
            previousDate = dateObj - timedelta(days=day)
            return self.FXAmount(amount, baseCCY, ccy, previousDate.strftime("%Y-%m-%d"))
        return amount * self.months[key].getRate(baseCCY, ccy, day)

class FXMonth:

    def __init__(self, month, year):
        self.days = {}
        self.month = month
        self.year = year
        conn = sqlite3.connect(config.SQLITE_DB, uri=True)
        conn.text_factory = str 
        cursor = conn.execute(expensesSQL.getFXMonth(month, year))
        for row in cursor:
            date = row[0]
            ccy1 = row[1] 
            ccy2 = row[2] 
            amount = row[3]
            key = ccy1 + ccy2
            if key not in self.days.keys():
                self.days[key] = FXDay(key)
            self.days[key].addValue(date, amount)
        conn.close()

    def getRate(self, ccy1, ccy2, day=None, date=None):
        if (day == None):
            day = date
        key = ccy1 + ccy2
        key_r = ccy2 + ccy1
        if key in self.days.keys():
            return self.days[key].getValue(day)
        if key_r in self.days.keys(): 
            return 1/(self.days[key_r].getValue(day))
        print ('********Missing Rate: ' +ccy1+ccy2, file=sys.stderr)
        return -1

class FXDay:

    def __init__(self, name):
        self.name = name
        self.values = [None] * 32

    def addValue(self, date, amount):
        self.values[datetime.strptime(date, '%Y-%m-%d').day] = amount

    def getValue(self, day=None, date=None):
        if (day == None):
            day = datetime.strptime(date, '%Y-%m-%d').day
        if (self.values[day] != None):
           return self.values[day]
        for i in range (1, 32):
            if ((day + i < 32) and (self.values[day + i] != None)):
                return self.values[day + i]
            if ((day - i > 0) and (self.values[day - i] != None)):
                return self.values[day - i]
        print ('Shouldn\'t end up here, no fx value found....', file=sys.stderr)

