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

            page = ''
            transaction_order_id = ''
            while page == '':
                try:
                    # set up new order
                    json_data = session_auth.place_active_order(
                        symbol=tradingpairs,
                        side="Buy",
                        order_type="Limit",
                        qty=1,
                        price=close,
                        time_in_force="GoodTillCancel",
                        reduce_only=True,
                        close_on_trigger=True
                    )
                    transaction_order_id = json_data.json()['result'][1]['order_id']
                    break
                except:
                    print("retries exceeded maximum")
                    time.sleep(5)
                    continue


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
                bartime,  open, high, low, close, volume,
                position_size, order_action, order_contracts, order_price, order_id, market_position,
                market_position_size, prev_market_position, prev_market_position_size,
                transaction_order_id, today, today))
            conn.commit()
    return "ok"

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    # Getting wallet balance
    method = 'GET'
    endpoint = '/unified/v3/private/account/wallet/balance'
    walletBalance = requests.request(method, base_uri + endpoint, headers=get_headers(method, endpoint, ""),
                                     data="")
    # Set up place order
    #     method = 'POST'
    #     endpoint = '/unified/v3/private/order/create'
    #     data = {"category": "linear", "symbol": "BTCUSDT", "orderType": "Limit", "side": "Buy", "price": 20000, "size": 1}
    #     data_json = json.dumps(data)
    #     orderPlacement = requests.request(method, base_uri + endpoint, headers=get_headers(method, endpoint, data_json), data=data_json)

    # Browser orders
    method = 'GET'
    endpoint = '/unified/v3/private/order/list'
    data = "?category=linear&symbol=BTCUSDT&limit=10"
    queryString = "category=linear&symbol=BTCUSDT&limit=10"
    browserOrder = requests.request(method, base_uri + endpoint + data,
                                    headers=get_headers(method, endpoint + data, queryString), data='')

    return browserOrder.json()



if __name__ == "__main__":
    # application.debug = True
    application.run(threaded=True)
