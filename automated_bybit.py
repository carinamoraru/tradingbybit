from flask import Flask, render_template, request
application = Flask(__name__)
app = application
import my_bybit
import config
import pymysql
import datetime
import json
import logging
import hashlib
import base64
import requests
import time
import hmac

live = 0
api_key = config.API_KEY
api_secret = config.API_SECURET
api_passphrase = config.API_PASSWORD
base_uri = config.DEMO_URL
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

def get_headers(method, endpoint):
    now = int(time.time() * 1000)
    str_to_sign = str(now) + method + endpoint
    signature = base64.b64encode(
        hmac.new(api_secret.encode(), str_to_sign.encode(), hashlib.sha256).digest()).decode()
    passphrase = base64.b64encode(
        hmac.new(api_secret.encode(), api_passphrase.encode(), hashlib.sha256).digest()).decode()
    return {'KC-API-KEY': api_key,
            'KC-API-KEY-VERSION': '2',
            'KC-API-PASSPHRASE': passphrase,
            'KC-API-SIGN': signature,
            'KC-API-TIMESTAMP': str(now)
            }

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

        # if passphrase == config.WEBHOOK_PASSPHRASE:
        #
        #     sql = """insert into `bot_log` (id, bot_name, tradingpairs, bot_time, exchange, ticker, timeframe,
        #          bar_time, bar_open, bar_high, bar_low, bar_close, bar_volumn,
        #          position_size, order_action, order_contracts, order_price, order_id, market_position,
        #         market_position_size, prev_market_position, prev_market_position_size, transaction_order_id, created_at, updated_at) values (
        #         NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
        #         %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) """
        #
        #     # running query command
        #     conn.ping()  # reconnecting mysql
        #     conn.cursor().execute(sql, (
        #         bot_name, tradingpairs, timenow, exchange, ticker, timeframe,
        #         bartime,  open, high, low, close, volume,
        #         position_size, order_action, order_contracts, order_price, order_id, market_position,
        #         market_position_size, prev_market_position, prev_market_position_size,
        #         "", today, today))
        #     conn.commit()

    return "ok"

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    # running query command
    # conn.ping()  # reconnecting mysql
    # sql = "SELECT * FROM bot_log ORDER BY id asc"
    # with conn:
    #     with conn.cursor() as cur:
    #         cur.execute(sql)
    #         result = cur.fetchall()
            # for data in result:
            #     first_name = data[1]

    myBybit = my_bybit.Mybybit(live)
    json_result = myBybit.usdt_perpetual_get_json("BTCUSDT")

    # conn.commit()
    return render_template('dashboard.html', result=json_result)


if __name__ == "__main__":
    # application.debug = True
    application.run(threaded=True)
