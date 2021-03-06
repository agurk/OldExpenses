#!/usr/bin/python

import sqlite3
import time
import datetime
from datetime import date, timedelta
import config
from Expense import Expense

class MonthView:

    def __init__(self, date, period):
        self.date = date
        self.period = period
        #date=time.strftime("%Y-%m-%d"

    def TotalAmount(self):
        conn = sqlite3.connect(config.SQLITE_DB, uri=True)
        conn.text_factory = str 
        query = 'select printf("%.2f", sum(amount) * -1) from expenses, classifications, classificationdef where strftime(date) >= date(\'{0}\',\'start of month\') and strftime(date) < date(\'{0}\',\'start of month\',\'+1 month\') and expenses.eid = classifications.eid and classifications.cid = classificationdef.cid and classificationdef.isexpense;'.format(self.date)
        cursor = conn.execute(query)
        for row in cursor:
            totalAmount = row[0]
        conn.close()
        return totalAmount

    def add_months(self, sourcedate, months):
        month = sourcedate.tm_mon - 1 + months
        year = int(sourcedate.tm_year + month / 12)
        month = month % 12 + 1
        day = 1
        return datetime.date(year,month,day)

    def get_date(self, sourcedate):
        month = sourcedate.tm_mon
        year = sourcedate.tm_year
        day = 1
        return datetime.date(year,month,day)

    def PreviousPeriod(self, period):
        if period == 'year':
            return self.PreviousYear()
        else:
            return self.PreviousMonth()

    def PreviousMonth(self):
        previous = time.strptime(self.date, "%Y-%m-%d")
        return self.add_months(previous, -1)

    def PreviousYear(self):
        previous = time.strptime(self.date, "%Y-%m-%d")
        return self.add_months(previous, -12)

    def ThisMonth(self):
        thisM = time.strptime(self.date, "%Y-%m-%d")
        return self.get_date(thisM)

    def NextPeriod(self, period):
        if period == 'year':
            return self.NextYear()
        else:
            return self.NextMonth()

    def NextMonth(self):
        nextM = time.strptime(self.date, "%Y-%m-%d")
        return self.add_months(nextM, 1)

    def NextYear(self):
        nextM = time.strptime(self.date, "%Y-%m-%d")
        return self.add_months(nextM, 12)

    def MonthName(self):
        year = time.strptime(self.date, "%Y-%m-%d").tm_year
        if self.period == 'year':
            return year
        month = time.strptime(self.date, "%Y-%m-%d").tm_mon
        return {
             1 : 'January',
             2 : 'February',
             3 : 'March',
             4 : 'April',
             5 : 'May',
             6 : 'June',
             7 : 'July',
             8 : 'August',
             9 : 'September',
            10 : 'October',
            11 : 'November',
            12 : 'December',
         }[month] + ' ' + str(year)
