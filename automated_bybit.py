from flask import Flask, render_template, request
application = Flask(__name__)
app = application
import config
import pymysql
import datetime
import json
import hashlib
import base64
import requests
import time
import hmac
import logging
from pybit import usdt_perpetual

live = 0
if live == 0:
    base_uri = config.DEMO_URL
    apikey = config.DEMO_API_KEY
    securet = config.DEMO_API_SECURET
    api_password = config.API_PASSWORD
else:
    base_uri = config.LIVE_URL
    apikey = config.API_KEY
    securet = config.API_SECURET
    api_password = config.DEMO_API_PASSWORD

mysql_host = "us-cdbr-east-06.cleardb.net"
mysql_dbname = "heroku_39cbab9600555e9"
mysql_username = "be77cdf07badde"
mysql_password = "d1d3e8a728d6c80"
# mysql_host = "localhost"
# mysql_dbname = "trading"
# mysql_username = "root"
# mysql_password = ""
today = datetime.datetime.now()
#
# write and load log data for bot log table
conn = pymysql.connect(host=mysql_host,
                       user=mysql_username,
                       password=mysql_password,
                       db=mysql_dbname,
                       charset='utf8')
cur = conn.cursor()

def get_headers(method, endpoint, data_json):
    now = int(time.time() * 1000)
    recv_window = 5000
    str_to_sign = str(now) + apikey + str(recv_window) + str(data_json)
    secret_key = securet.encode('utf-8')
    total_params = str_to_sign.encode('utf-8')
    signature = hmac.new(secret_key, total_params, hashlib.sha256).hexdigest()
    return {"X-BAPI-SIGN": signature,
            "X-BAPI-TIMESTAMP": str(now),
            "X-BAPI-API-KEY": apikey,
            "X-BAPI-RECV-WINDOW": "5000",
            "X-BAPI-SIGN-TYPE": "2",
            "Content-Type": "application/json"  # specifying content type or using json=data in request
            }

# when going long, will become buy
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        data = json.loads(request.data)
        bot_name = data['bot_name']
        passphrase = data['passphrase']
        tradingpairs = data['tradingpairs']
        timenow = data['time']
        exchange = data['exchange']
        ticker = data['ticker']
        timeframe = data['timeframe']
        position_size = data['strategy']['position_size']
        order_action = data['strategy']['order_action']
        order_contracts = data['strategy']['order_contracts']
        order_price = data['strategy']['order_price']
        order_id = data['strategy']['order_id']
        market_position = data['strategy']['market_position']
        market_position_size = data['strategy']['market_position_size']
        prev_market_position = data['strategy']['prev_market_position']
        prev_market_position_size = data['strategy']['prev_market_position_size']
        bartime = data['bar']['time']
        open = data['bar']['open']
        high = data['bar']['high']
        low = data['bar']['low']
        close = data['bar']['close']
        volume = data['bar']['volume']

        if passphrase == config.WEBHOOK_PASSPHRASE:
            if live == 0:
                endpoint = config.DEMO_URL
                apikey = config.DEMO_API_KEY
                securet = config.DEMO_API_SECURET

            session_auth = usdt_perpetual.HTTP(
                endpoint=endpoint,
                api_key=apikey,
                api_secret=securet
            )

            transaction_order_id = ''
            # checking condition for price
            conn.ping()  # reconnecting mysql
            cur.execute(
                "SELECT * FROM order_log WHERE side = 'Buy' AND status = '1' AND price <> 'close*10' ORDER BY id DESC LIMIT 1")
            old_buyorder_id = cur.rowcount
            result = cur.fetchall()
            for data in result:
                old_order_id = data[1]
            conn.commit()

            # checking different price condition
            conn.ping()  # reconnecting mysql
            cur.execute(
                "SELECT * FROM order_log WHERE side = 'Buy' AND status = '1' AND price == 'close*10' ORDER BY id DESC LIMIT 1")
            old_diff_buyorder_id = cur.rowcount
            conn.commit()

            # checking sell condition
            conn.ping()  # reconnecting mysql
            cur.execute(
                "SELECT * FROM order_log WHERE side = 'Sell' AND status = '1' AND price = 'close*10' ORDER BY id DESC LIMIT 1")
            old_sellorder_id = cur.rowcount
            result = cur.fetchall()
            conn.commit()

            # duplicate buy price
            if old_buyorder_id != 0 and old_sellorder_id == 0:
                # cancel old order
                oldOrder = session_auth.cancel_active_order(
                    symbol="BTCUSDT",
                    order_id=old_buyorder_id
                )
                # set up new order
                newOrder = session_auth.place_active_order(
                    symbol=tradingpairs,
                    side="Buy",
                    order_type="Limit",
                    qty=0.1,
                    price=close * 10,
                    time_in_force="GoodTillCancel",
                    reduce_only=False,
                    close_on_trigger=False
                )
                transaction_order_id = newOrder['result'][0]['order_id']
                sql = """insert into `bot_log` (id, bot_name, tradingpairs, bot_time, exchange, ticker, timeframe,
                                 bar_time, bar_open, bar_high, bar_low, bar_close, bar_volumn,
                                 position_size, order_action, order_contracts, order_price, order_id, market_position,
                                market_position_size, prev_market_position, prev_market_position_size, transaction_order_id, created_at, updated_at) values (
                                NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) """

                # running query command
                conn.ping()  # reconnecting mysql
                conn.cursor().execute(sql, (
                    bot_name, tradingpairs, timenow, exchange, ticker, timeframe,
                    bartime, open, high, low, close, volume,
                    position_size, order_action, order_contracts, order_price, order_id, market_position,
                    market_position_size, prev_market_position, prev_market_position_size,
                    transaction_order_id, today, today))
                conn.commit()
                return "changed"
            # not duplicate buy price
            if old_buyorder_id == 0 and old_sellorder_id == 0:
                # set up new order
                newOrder = session_auth.place_active_order(
                    symbol=tradingpairs,
                    side="Buy",
                    order_type="Limit",
                    qty=0.1,
                    price=close * 10,
                    time_in_force="GoodTillCancel",
                    reduce_only=False,
                    close_on_trigger=False
                )
                transaction_order_id = newOrder['result'][0]['order_id']
                sql = """insert into `bot_log` (id, bot_name, tradingpairs, bot_time, exchange, ticker, timeframe,
                                 bar_time, bar_open, bar_high, bar_low, bar_close, bar_volumn,
                                 position_size, order_action, order_contracts, order_price, order_id, market_position,
                                market_position_size, prev_market_position, prev_market_position_size, transaction_order_id, created_at, updated_at) values (
                                NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) """

                # running query command
                conn.ping()  # reconnecting mysql
                conn.cursor().execute(sql, (
                    bot_name, tradingpairs, timenow, exchange, ticker, timeframe,
                    bartime, open, high, low, close, volume,
                    position_size, order_action, order_contracts, order_price, order_id, market_position,
                    market_position_size, prev_market_position, prev_market_position_size,
                    transaction_order_id, today, today))
                conn.commit()
                return "changed"
            # duplicate buy price
            if old_diff_buyorder_id != 0 and old_sellorder_id != 0:
                return "no change"
            return "ok"

# when going short, will become sell
@app.route('/short', methods=['GET', 'POST'])
def short():
    if request.method == 'POST':
        data = json.loads(request.data)
        bot_name = data['bot_name']
        passphrase = data['passphrase']
        tradingpairs = data['tradingpairs']
        timenow = data['time']
        exchange = data['exchange']
        ticker = data['ticker']
        timeframe = data['timeframe']
        position_size = data['strategy']['position_size']
        order_action = data['strategy']['order_action']
        order_contracts = data['strategy']['order_contracts']
        order_price = data['strategy']['order_price']
        order_id = data['strategy']['order_id']
        market_position = data['strategy']['market_position']
        market_position_size = data['strategy']['market_position_size']
        prev_market_position = data['strategy']['prev_market_position']
        prev_market_position_size = data['strategy']['prev_market_position_size']
        bartime = data['bar']['time']
        open = data['bar']['open']
        high = data['bar']['high']
        low = data['bar']['low']
        close = data['bar']['close']
        volume = data['bar']['volume']

        if passphrase == config.WEBHOOK_PASSPHRASE:
            if live == 0:
                endpoint = config.DEMO_URL
                apikey = config.DEMO_API_KEY
                securet = config.DEMO_API_SECURET

            session_auth = usdt_perpetual.HTTP(
                endpoint=endpoint,
                api_key=apikey,
                api_secret=securet
            )

            transaction_order_id = ''
            # checking condition for price
            conn.ping()  # reconnecting mysql
            cur.execute(
                "SELECT * FROM order_log WHERE side = 'Sell' AND status = '1' AND price <> 'close*10' ORDER BY id DESC LIMIT 1")
            old_buyorder_id = cur.rowcount
            result = cur.fetchall()
            for data in result:
                old_order_id = data[1]
            conn.commit()

            # checking different price condition
            conn.ping()  # reconnecting mysql
            cur.execute(
                "SELECT * FROM order_log WHERE side = 'Sell' AND status = '1' AND price == 'close*10' ORDER BY id DESC LIMIT 1")
            old_diff_buyorder_id = cur.rowcount
            conn.commit()

            # checking sell condition
            conn.ping()  # reconnecting mysql
            cur.execute(
                "SELECT * FROM order_log WHERE side = 'Buy' AND status = '1' AND price = 'close*10' ORDER BY id DESC LIMIT 1")
            old_sellorder_id = cur.rowcount
            result = cur.fetchall()
            conn.commit()

            # duplicate buy price
            if old_buyorder_id != 0 and old_sellorder_id == 0:
                # cancel old order
                oldOrder = session_auth.cancel_active_order(
                    symbol="BTCUSDT",
                    order_id=old_buyorder_id
                )
                # set up new order
                newOrder = session_auth.place_active_order(
                    symbol=tradingpairs,
                    side="Sell",
                    order_type="Limit",
                    qty=0.1,
                    price=close * 10,
                    time_in_force="GoodTillCancel",
                    reduce_only=False,
                    close_on_trigger=False
                )
                transaction_order_id = newOrder['result'][0]['order_id']
                sql = """insert into `bot_log` (id, bot_name, tradingpairs, bot_time, exchange, ticker, timeframe,
                                 bar_time, bar_open, bar_high, bar_low, bar_close, bar_volumn,
                                 position_size, order_action, order_contracts, order_price, order_id, market_position,
                                market_position_size, prev_market_position, prev_market_position_size, transaction_order_id, created_at, updated_at) values (
                                NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) """

                # running query command
                conn.ping()  # reconnecting mysql
                conn.cursor().execute(sql, (
                    bot_name, tradingpairs, timenow, exchange, ticker, timeframe,
                    bartime, open, high, low, close, volume,
                    position_size, order_action, order_contracts, order_price, order_id, market_position,
                    market_position_size, prev_market_position, prev_market_position_size,
                    transaction_order_id, today, today))
                conn.commit()
                return "changed"
            # not duplicate buy price
            if old_buyorder_id == 0 and old_sellorder_id == 0:
                # set up new order
                newOrder = session_auth.place_active_order(
                    symbol=tradingpairs,
                    side="Sell",
                    order_type="Limit",
                    qty=0.1,
                    price=close * 10,
                    time_in_force="GoodTillCancel",
                    reduce_only=False,
                    close_on_trigger=False
                )
                transaction_order_id = newOrder['result'][0]['order_id']
                sql = """insert into `bot_log` (id, bot_name, tradingpairs, bot_time, exchange, ticker, timeframe,
                                 bar_time, bar_open, bar_high, bar_low, bar_close, bar_volumn,
                                 position_size, order_action, order_contracts, order_price, order_id, market_position,
                                market_position_size, prev_market_position, prev_market_position_size, transaction_order_id, created_at, updated_at) values (
                                NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) """

                # running query command
                conn.ping()  # reconnecting mysql
                conn.cursor().execute(sql, (
                    bot_name, tradingpairs, timenow, exchange, ticker, timeframe,
                    bartime, open, high, low, close, volume,
                    position_size, order_action, order_contracts, order_price, order_id, market_position,
                    market_position_size, prev_market_position, prev_market_position_size,
                    transaction_order_id, today, today))
                conn.commit()
                return "changed"
            # duplicate buy price
            if old_diff_buyorder_id != 0 and old_sellorder_id != 0:
                return "no change"
            return "ok"

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    symbol = "BTCUSDT"
    session_auth = usdt_perpetual.HTTP(
        endpoint=base_uri,
        api_key=apikey,
        api_secret=securet
    )

# creating new order
#     newOrder = session_auth.place_active_order(
#         symbol=symbol,
#         side="Buy",
#         order_type="Limit",
#         qty=0.1,
#         price=20000,
#         time_in_force="GoodTillCancel",
#         reduce_only=False,
#         close_on_trigger=False
#     )

# cancel old order
#     print(session_auth.cancel_active_order(
#         symbol="BTCUSDT",
#         order_id="fbce67cf-28b4-446f-bda9-575005b4186c"
#     ))

# browser orders
    listOrders = session_auth.query_active_order(
        symbol=symbol,
        order_id=""
    )

    # set up status as 1 for all records in order_log
    conn.ping()  # reconnecting mysql
    conn.cursor().execute('''
                    UPDATE order_log
                    SET status = 0
                    ''')
    conn.commit()

    for info in listOrders['result']:
        order_id = info['order_id']
        symbol = info['symbol']
        type = info['order_type']
        side = info['side']
        price = info['price']
        qty = info['qty']
        stop_price = info['stop_loss']
        take_profit_price = info['take_profit']
        timeIn_force = info['time_in_force']
        reduce_only = info['reduce_only']
        order_status = info['order_status']
        order_type = info['order_type']
        created_at = info['created_time']
        updated_at = info['updated_time']
        status = 1
        sql = """insert into `order_log` (id, order_id, symbol, type, side, price, qty,
                         stop_price, take_profit_price, timeIn_force, reduce_only, order_status, order_type,
                         status, created_at, updated_at) values (
                         NULL, %s, %s, %s, %s, %s, %s, %s,
                         %s, %s, %s, %s, %s, %s, %s, %s) """

        # running query command
        conn.ping()  # reconnecting mysql
        conn.cursor().execute(sql, (
            order_id, symbol, type, side, price, qty,
            stop_price, take_profit_price, timeIn_force, reduce_only, order_status, order_type,
            status, created_at, updated_at))
        conn.commit()

    return listOrders

@app.route('/test', methods=['GET', 'POST'])
def test():
    if request.method == 'POST':
        logging.error('%s action', request.data)
        data = request.data
        str1 = data.replace(b"message (", b"")
        str2 = str1.replace(b").", b"")
        logging.error('%s str2', str2)
        # data = json.loads(request.data)
        # data = request.data

        # action = data['action']
        # qty = data['qty']

    return "ok"


if __name__ == "__main__":
    # application.debug = True
    application.run(threaded=True)
