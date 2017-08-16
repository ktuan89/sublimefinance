import sublime, sublime_plugin

import re
import urllib.request
from urllib.error import HTTPError
import string
import json

def coinSettings():
    return sublime.load_settings('Coin.sublime-settings')

last_prices = {}

def shorten(x):
    pos = x.find('/')
    if pos != -1:
        return x[:pos]
    return x

def get_data():
    print("===== get data")
    api_key = coinSettings().get('api_key')
    url = 'http://www.worldcoinindex.com/apiservice/json?key={0}'.format(api_key)
    data = None
    try:
        user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
        headers={'User-Agent':user_agent,}
        request=urllib.request.Request(url, None, headers)
        f = urllib.request.urlopen(request)
        tmp_data = f.read().decode('utf-8')
        data = json.loads(tmp_data)
    except HTTPError:
        print("HTTPError~~~~~~~~~")
        data = None

    rows = []

    if data is not None:
        data = data["Markets"]
        for row in data:
            label = shorten(row["Label"])
            price = float(row["Price_usd"])
            volume = row["Volume_24h"]
            rows.append((label, price, volume))
        rows = sorted(rows, key = lambda rr: -rr[2])
        rows = rows[:20]

        new_rows = []
        for row in rows:
            (label, price, volume) = row
            percentage = 0
            if label in last_prices:
                percentage = price / last_prices[label][0] - 1
                percentage = percentage * 100
            else:
                last_prices[label] = []

            last_prices[label].append(price)
            if len(last_prices[label]) > 5:
                last_prices[label] = last_prices[label][-5:]
            print(last_prices[label])
            new_rows.append((label, price, volume, percentage))

        rows = new_rows

    return rows

current_view_id = -1

def fetch_coin_data_for_view(view):
    print("fetch_coin_data_for_view ", view.id())
    data_rows = get_data()
    results = []
    for data in data_rows:
        (label, price, volume, percentage) = data
        s = "{0:>8}{1:8.2f}{2:11.2f}{3:+8.2f}%".format(label, float(price), float(volume), float(percentage))
        results.append(s)

    new_content = '\n'.join(results)
    sublime.set_timeout(lambda: view.run_command('replace_content', {'new_content': new_content}), 0)

def fetch_coin_data(window, current_view_id):
    view = None
    print("Current view id = ", current_view_id)
    for i in range(0, window.num_groups()):
        active_view = window.active_view_in_group(i)
        print("Active view = ", active_view.id())
        if active_view.id() == current_view_id:
            view = active_view
            break

    if view is not None:
        print("Fetch coin")
        sublime.set_timeout_async(lambda: fetch_coin_data_for_view(view), 50)

    view_is_valid = False
    for v in window.views():
        if v.id() == current_view_id:
            view_is_valid = True

    if view_is_valid:
        print("Continue timer")
        sublime.set_timeout(lambda: fetch_coin_data(window, current_view_id), 120 * 1000)
    else:
        print("Stop timer")

class SetCoinView(sublime_plugin.TextCommand):
    def run(self, edit):
        current_view_id = self.view.id()
        self.view.set_scratch(True)
        self.view.set_syntax_file('Packages/sublimefinance/Stock.sublime-syntax')
        self.view.set_name("CoinWatch")

        sublime.set_timeout(lambda: fetch_coin_data(self.view.window(), current_view_id), 1 * 1000)
