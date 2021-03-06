#!/usr/bin/python

import sqlite3
import time
import datetime
from datetime import date, timedelta
import config
import documentsSQL

class Document:

    def Document(self, did):
        conn = sqlite3.connect(config.SQLITE_DB, uri=True)
        conn.text_factory = str 
        for row in conn.execute(documentsSQL.getDocument(did)):
            document = self.makeDocument(row, conn)
        conn.close()
        return document

    def Documents(self):
        conn = sqlite3.connect(config.SQLITE_DB, uri=True)
        conn.text_factory = str 
        sql = documentsSQL.getUnmappedDocuments()
        cursor = conn.execute(sql)
        documents=[]
        for row in cursor:
            documents.append(self.makeDocument(row, conn))
        conn.close()
        return documents  

    def Search (self, search):
        conn = sqlite3.connect(config.SQLITE_DB, uri=True)
        conn.text_factory = str 
        cursor = conn.execute(documentsSQL.getSimilarDocuments(search))
        documents=[]
        for row in cursor:
            documents.append(self.makeDocument(row, conn))
        conn.close()
        return documents  

    def makeDocument(self, row, conn):
        document = {}
        document['did'] = row[0]
        document['date'] = row[1]
        document['filename'] = row[2]
        document['text'] = row[3]
        document['textmoddate'] = row[4]
        document['deleted'] = row[5]
        self._addExpenses(document, conn)
        self._addNextDocID(document, conn)
        self._addPreviousDocID(document, conn)
        self._addLinkedDocs(document, conn)
        return document
    

    def _addExpenses(self, document, db):
        results = []
        for row in db.execute(documentsSQL.getExpenses(document['did'])):
            results.append(row)
        document['expenses'] = results 

    def _addNextDocID(self, document, db):
        cursor = db.execute(documentsSQL.getNextDocID(document['did']))
        for row in cursor:
            document['nextID'] = row[0]

    def _addPreviousDocID(self, document, db):
        cursor = db.execute(documentsSQL.getPreviousDocID(document['did']))
        for row in cursor:
            document['previousID'] = row[0]

    def _addLinkedDocs(self, document, db):
        if db:
            cursor = db.execute(documentsSQL.getLinkedDocs(document['did']))
            documents=[]
            for row in cursor:
                documents.append({'did': row[0], 'filename': row[1]})
            document['linkedDocs'] = documents

