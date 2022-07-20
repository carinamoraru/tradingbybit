from flask import Flask, render_template, request
application = Flask(__name__)
app = application
import my_bybit
import config
import pymysql
import datetime
import json
import logging

live = 0
# mysql_host = "us-cdbr-east-06.cleardb.net"
# mysql_dbname = "heroku_42b1a7a586099e3"
# mysql_username = "b9bf09310bc7a9"
# mysql_password = "a03f30ecf1dee90"
# mysql_host = "localhost"
# mysql_dbname = "trading"
# mysql_username = "root"
# mysql_password = ""
# today = datetime.datetime.now()
#
# # write and load log data for bot log table
# conn = pymysql.connect(host=mysql_host,
#                        user=mysql_username,
#                        password=mysql_password,
#                        db=mysql_dbname,
#                        charset='utf8')
# cur = conn.cursor()

@app.route('/', methods=['GET', 'POST'])
# @app.route('/<int:uid>', methods=['GET','POST'])
def index():
    if request.method == 'POST':
        data = json.loads(request.data)
        bot_name = data['bot_name']
        passphrase = data['passphrase']
        timenow = data['time']
        exchange = data['exchange']
        ticker = data['ticker']
        position_size = data['strategy']['position_size']
        order_action = data['strategy']['order_action']
        order_contracts = data['strategy']['order_contracts']
        order_price = data['strategy']['order_price']
        order_id = data['strategy']['order_id']
        market_position = data['strategy']['market_position']
        market_position_size = data['strategy']['market_position_size']
        prev_market_position = data['strategy']['prev_market_position']
        prev_market_position_size = data['strategy']['prev_market_position_size']

        bartime = ""
        open = ""
        high = ""
        low = ""
        close = ""
        volume = ""

        return render_template('home.html', data=data)
    else:
        # ticker = "no post"
        # myBybit = my_bybit.Mybybit(live)
        # json_result = myBybit.inverse_get_json("BTCUSD", "D", "1653408000")
        return "hello"
    # return render_template('home.html', ticker=ticker, json_result=json_result['result'], len=len(json_result['result']))

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
