#!/usr/bin/python

import sqlite3
import time
import datetime
from datetime import date, timedelta
import config

class ReadOnlyData:

    def Expense(self, eid):
        conn = sqlite3.connect(config.SQLITE_DB)
        conn.text_factory = str 
        query = 'select date, description, printf("%.2f", amount), cd.name, e.eid, confirmed, tag from expenses e left join tagged t on e.eid = t.eid, classifications c, classificationdef cd where e.eid = {0} and e.eid = c.eid and c.cid = cd.cid;'.format(eid)
        cursor = conn.execute(query)
        for row in cursor:
            return row

    def Edit_Expense(self, eid):
        if eid == '':
            return row[7]
        conn = sqlite3.connect(config.SQLITE_DB)
        conn.text_factory = str 
        query = 'select date, description, printf("%.2f", amount), cd.name, e.eid, confirmed, tag from expenses e left join tagged t on e.eid = t.eid, classifications c, classificationdef cd where e.eid = {0} and e.eid = c.eid and c.cid = cd.cid;'.format(eid)
        cursor = conn.execute(query)
        for row in cursor:
            return row

    def Receipt_Filename(self, did):
        conn = sqlite3.connect(config.SQLITE_DB)
        conn.text_factory = str 
        query = 'select filename from documents where did = {0}'.format(did)
        cursor = conn.execute(query)
        for row in cursor:
            return '/static/data/documents/' + row[0]

    def Receipt_Text(self, did):
        conn = sqlite3.connect(config.SQLITE_DB)
        conn.text_factory = str 
        query = 'select text from documents where did = {0}'.format(did)
        cursor = conn.execute(query)
        for row in cursor:
            return row[0]
