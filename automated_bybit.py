from flask import Flask, render_template, request
application = Flask(__name__)
app = application
import config
import pymysql
import datetime
import json
import hashlib
import requests
import time
import hmac
import logging
from pybit import usdt_perpetual

live = 0
if live == 0:
    endpoint = config.DEMO_URL
    apikey = config.DEMO_API_KEY
    securet = config.DEMO_API_SECURET
else:
    endpoint = config.LIVE_URL
    apikey = config.API_KEY
    securet = config.API_SECURET

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

# when going long, will become buy
@app.route('/', methods=['GET', 'POST'])
def index():
    resultStr = "ok"
    if request.method == 'POST':
        data = request.data
        str1 = data.replace(b"message (", b"")
        str2 = str1.replace(b").", b"")
        data1 = json.loads(str2)
        bot_name = data1['bot_name']
        passphrase = data1['passphrase']
        timenow = data1['bot_time']
        exchange = data1['exchange']
        ticker = data1['ticker']
        timeframe = data1['timeframe']
        qty = data1['qty']
        side = data1['side']
        order_price = data1['order_price']
        order_id = data1['order_id']
        pivot = data1['pivot']
        transaction_order_id = ''

        if passphrase == config.WEBHOOK_PASSPHRASE:
            # try:
            session_auth = usdt_perpetual.HTTP(
                endpoint=endpoint,
                api_key=apikey,
                api_secret=securet
            )

            # Getting wallet balance, symbol
            wallet = session_auth.get_wallet_balance()
            logging.error('Wallet %s', wallet)
            totalWalletBalance = wallet['result']['USDT']['wallet_balance']
            totalAvailableBalance = wallet['result']['USDT']['available_balance']
            logging.error('Total Wallet Balance %s', totalWalletBalance)
            logging.error('Total Available Balance %s', totalAvailableBalance)

            # Getting final order price
            # Only BTCUSD symbol(others are BTCUSDM21, CROUSDT, QTUMUSDT, LRCUSDT)
            latestInfo = session_auth.latest_information_for_symbol(symbol="BTCUSD")
            logging.error('LatestInfo %s', latestInfo)
            index_price = latestInfo['result'][0]['index_price']
            logging.error('index_price %s', index_price)

            # set up new order
            # newOrder = session_auth.place_active_order(
            #     symbol=ticker,
            #     side=side,
            #     order_type="Market",
            #     qty=qty,
            #     time_in_force="GoodTillCancel",
            # )
            # transaction_order_id = newOrder.json()['result']['order_id']
            sql = """insert into `bot_log` (id, bot_name, bot_time, exchange, ticker, timeframe,
                                             qty, side, order_price, order_id, transaction_order_id, created_at, updated_at) values (
                                            NULL, %s, %s, %s, %s, %s, 
                                            %s, %s, %s, %s, %s, %s, %s) """

            # running query command
            conn.ping()  # reconnecting mysql
            conn.cursor().execute(sql, (
                bot_name, timenow, exchange, ticker, timeframe,
                qty, side, order_price, order_id,
                transaction_order_id, today, today))
            conn.commit()
            # except:
            #     logging.error('Error while make order!!!')
    else:
        resultStr = "no post"
    return resultStr

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    symbol = "BTCUSDT"
    session_auth = usdt_perpetual.HTTP(
        endpoint=endpoint,
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
        logging.error('entire data %s', request.data)
        data = request.data
        str1 = data.replace(b"message (", b"")
        str2 = str1.replace(b").", b"")
        data1 = json.loads(str2)
        order_id = data1['order_id']
        logging.error('%s order_id', order_id)

    return "ok"

if __name__ == "__main__":
    # application.debug = True
    application.run(threaded=True)
