import sublime, sublime_plugin

import re
import urllib.request
from urllib.error import HTTPError
import string

def stockSettings():
    return sublime.load_settings('Stock.sublime-settings')

def get_data():
    symbols = stockSettings().get('stock_list').split()
    data = []
    url = 'http://finance.yahoo.com/d/quotes.csv?s='
    for s in symbols:
        url += s+"+"
    url = url[0:-1]
    url += "&f=pc"

    try:
        f = urllib.request.urlopen(url)
        rows = f.readlines()
    except HTTPError:
        print("HTTPError~~~~~~~~~")
        rows = []

    index = 0
    for r in rows:
        stock = symbols[index]
        index = index + 1
        values = [x for x in r.strip().decode('utf-8').split(',')]
        print(values)
        price = values[0]
        result = re.match(r'\"((?:\+|\-)?[0-9\.]+) \- ((?:\+|\-)?[0-9\.]+\%)\"', values[1])
        if result is not None:
            delta = result.group(1)
            percentage = result.group(2)
            data.append((stock.upper(), price, delta, percentage))
    return data

current_view_id = -1

def fetch_stock_data_for_view(view):
    data_rows = get_data()
    results = []
    for data in data_rows:
        (stock, price, delta, percentage) = data
        price = str(float(price) + float(delta))
        percentage = percentage[:-1]
        s = "{0:>8}{1:8.2f}{2:+8.2f}{3:+8.2f}%".format(stock, float(price), float(delta), float(percentage))
        results.append(s)

    new_content = '\n'.join(results)
    sublime.set_timeout(lambda: view.run_command('replace_content', {'new_content': new_content}), 0)

def fetch_stock_data(window, current_view_id):
    view = None
    print("Current view id = ", current_view_id)
    for i in range(0, window.num_groups()):
        active_view = window.active_view_in_group(i)
        print("Active view = ", active_view.id())
        if active_view.id() == current_view_id:
            view = active_view
            break

    if view is not None:
        print("Fetch stock")
        sublime.set_timeout_async(lambda: fetch_stock_data_for_view(view), 0)

    view_is_valid = False
    for v in window.views():
        if v.id() == current_view_id:
            view_is_valid = True

    if view_is_valid:
        print("Continue timer")
        sublime.set_timeout(lambda: fetch_stock_data(window, current_view_id), 60 * 1000)
    else:
        print("Stop timer")

class SetStockView(sublime_plugin.TextCommand):
    def run(self, edit):
        current_view_id = self.view.id()
        self.view.set_scratch(True)
        self.view.set_syntax_file('Packages/sublimefinance/Stock.sublime-syntax')
        self.view.set_name("StockWatch")

        sublime.set_timeout(lambda: fetch_stock_data(self.view.window(), current_view_id), 1 * 1000)