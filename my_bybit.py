from pybit import inverse_perpetual
from pybit import usdt_perpetual
import config


class Mybybit():
    def __init__(self, live):
        if live == 1:
            self.endpoint = config.LIVE_URL
            self.apiKey = config.API_KEY
            self.secret = config.API_SECURET
        else:
            self.endpoint = config.DEMO_URL
            self.apiKey = config.DEMO_API_KEY
            self.secret = config.DEMO_API_SECURET


    def inverse_get_json(self, symbol, interval, from_time):
        session_auth = inverse_perpetual.HTTP(
            endpoint=self.endpoint,
            api_key=self.apiKey,
            api_secret=self.secret
        )

        json_data = session_auth.query_kline(
            symbol=symbol,
            interval=interval,
            from_time=from_time
        )
        return json_data

    def usdt_perpetual_get_json(self, symbol):
        session_auth = usdt_perpetual.HTTP(
            endpoint=self.endpoint,
            api_key=self.apiKey,
            api_secret=self.secret
        )

        # session_auth.place_active_order(
        #     symbol=symbol,
        #     side="Sell",
        #     order_type="Limit",
        #     qty=0.01,
        #     price=8083,
        #     time_in_force="GoodTillCancel",
        #     reduce_only=False,
        #     close_on_trigger=False
        # )

        json_data = session_auth.query_active_order(
            symbol=symbol,
            order_id=""
        )
        return json_data
