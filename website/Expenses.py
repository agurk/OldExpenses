#!/usr/bin/python

from flask import Flask, request, make_response, render_template

from MonthView import MonthView
from MonthGraph import MonthGraph
from Document import Document
from MetaData import MetaData
from Search import Search
from EventGenerator import EventGenerator
from Expense import Expense

import time

app = Flask(__name__)

@app.route('/')
@app.route('/expenses')
def main():
    if 'date' in request.args.keys():
        date = request.args['date']
    else:
        date = time.strftime("%Y-%m-%d")
    mv = MonthView(date)
    mg = MonthGraph(date)
    ex = Expense()
    return render_template('monthview.html', cursor=mv.OverallExpenses(), expenses=ex.Expenses(date, ''), previous_month=mv.PreviousMonth(), next_month=mv.NextMonth(), total_amount=mv.TotalAmount(), month_name=mv.MonthName(),month_graph=mg.Graph(), this_month=mv.ThisMonth())

@app.route('/receipt')
def on_receipt():
    did = request.args['did']
    doc = Document()
    return render_template('receipt.html', document=doc.Document(did), item_id=did, item_type='did')

@app.route('/expense')
def on_edit_expense():
    eid = ''
    if 'eid' in request.args.keys():
        eid = request.args['eid']
    ex = Expense()
    return render_template('expense.html', expense=ex.Expense(eid), item_id=eid, item_type='eid')

@app.route('/detailed_expenses_all')
def on_detailed_expenses_all():
    if 'date' in request.args.keys():
        date = request.args['date']
    else:
        date = time.strftime("%Y-%m-%d")
    ex = Expense()
    return render_template('detailedexpenses_fragment.html', expenses=ex.Expenses(date, 'ALL'))

@app.route('/detailed_expenses')
def on_detailed_expenses():
    if 'date' in request.args.keys():
        date = request.args['date']
    else:
        date = time.strftime("%Y-%m-%d")
    ex = Expense()
    return render_template('detailedexpenses_fragment.html', expenses=ex.Expenses(date, ''))

@app.route('/config')
def on_config():
    md = MetaData()
    return render_template('config.html', classifications=md.AllClassifications());

@app.route('/expense_summary')
def on_expense_summary():
    eid = request.args['eid']
    ex = Expense()
    return render_template('expense_fragment.html', expense=ex.Expense(eid))

@app.route('/expense_details')
def on_expense_details():
    eid = request.args['eid']
    ex = Expense()
    md = MetaData()
    return render_template('expense_details_fragment.html',expense=ex.Expense(eid), classifications=md.Classifications(eid))

@app.route('/search')
def on_search():
    ex = Expense()
    if 'description' in request.args.keys():
        description = request.args['description']
        similar_ex = ex.Search(description)
    else:
        description = ''
        similar_ex = ''
    return render_template('search.html', description=description, similar_ex=similar_ex)

@app.route('/backend/<command>', methods=['GET', 'POST'])
def generateEvent(command):
    extraArgs = {}
    if command == 'MERGE_EXPENSE':
        extraArgs[request.cookies.get('pinned_type') + '_merged'] = request.cookies.get('pinned_id')
    _generateEvent(command, request.args, extraArgs)
    return '200';

def _generateEvent(command, args, extraArgs={}):
    eg = EventGenerator()
    eg.sendEvent(command, args, extraArgs)

@app.route('/pinned', methods=['GET', 'POST', 'DELETE', 'PUT'])
def pinned():
    if request.method == 'POST':
        pt = request.args['pinned_type']
        pid = request.args['pinned_id']
        pin = pt and pid
        resp = make_response(render_template('pinned.html', pin=pin))
        resp.set_cookie('pinned_type', pt)
        resp.set_cookie('pinned_id', pid)
        return resp
    elif request.method == 'DELETE':
        resp = make_response(render_template('pinned.html'))
        resp.set_cookie('pinned_type', '')
        resp.set_cookie('pinned_id', '')
        return resp
    elif request.method == 'PUT':
        eventArgs={}
        eventArgs[request.args['pinned_type']] = request.args['pinned_id']
        eventArgs[request.cookies.get('pinned_type')] = request.cookies.get('pinned_id')
        _generateEvent('PIN_ITEM', eventArgs)
        resp = make_response(render_template('pinned.html'))
        resp.set_cookie('pinned_type', '')
        resp.set_cookie('pinned_id', '')
        return resp
    else:
        pin = request.cookies.get('pinned_type') and request.cookies.get('pinned_id')
        return render_template('pinned.html', pin=pin)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)

