#!/usr/bin/python

import sqlite3
import config

class MetaData:

    def Classifications(self, eid=''):
        conn = sqlite3.connect(config.SQLITE_DB)
        conn.text_factory = str 
        if eid:
            query = "select cid,name from classificationdef,expenses e where e.eid={0} and date(validfrom) <= date(e.date) and (validto = '' or date(validto) >= date(e.date)) order by name".format(eid)
        else:
            # TODO: improve the selection when no eid given
            query = "select cid,name from classificationdef order by name"
        cursor = conn.execute(query)
        return cursor

    def AllClassifications(self):
        conn = sqlite3.connect(config.SQLITE_DB)
        conn.text_factory = str 
        query = 'select cid, name, validfrom, validto, isexpense from classificationdef';
        return conn.execute(query)

    def AccountLoaders(self):
        conn = sqlite3.connect(config.SQLITE_DB)
        conn.text_factory = str 
        query = 'select a.name, al.enabled, al.alid from accountdef a, accountloaders al where a.aid = al.aid';
        accountloaders = []
        for row in conn.execute(query):
            accountloader = {}
            accountloader['name'] = row[0]
            accountloader['enabled'] = row[1]
            accountloader['alid'] = row[2]
            accountloaders.append(accountloader)
        return accountloaders

    def Accounts(self):
        conn = sqlite3.connect(config.SQLITE_DB)
        conn.text_factory = str 
        query = 'select a.name, a.ccy from accountdef a';
        accounts= []
        for row in conn.execute(query):
            account = {}
            account['name'] = row[0]
            account['ccy'] = row[1]
            accounts.append(account)
        return accounts
