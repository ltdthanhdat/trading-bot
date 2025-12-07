# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
# --- Do not remove these imports ---
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from pandas import DataFrame
from typing import Optional, Union

from freqtrade.strategy import (
    IStrategy,
    Trade,
    Order,
    PairLocks,
    informative,
    # Hyperopt Parameters
    BooleanParameter,
    CategoricalParameter,
    DecimalParameter,
    IntParameter,
    RealParameter,
    # timeframe helpers
    timeframe_to_minutes,
    timeframe_to_next_date,
    timeframe_to_prev_date,
    # Strategy helper functions
    merge_informative_pair,
    stoploss_from_absolute,
    stoploss_from_open,
)

# --------------------------------
# Add your lib to import here
import talib.abstract as ta
from technical import qtpylib


class MyStrategy(IStrategy):
    """
    My Custom Trading Strategy
    
    This is a simple strategy example using RSI and Bollinger Bands.
    More information: https://www.freqtrade.io/en/latest/strategy-customization/
    """

    # Strategy interface version
    INTERFACE_VERSION = 3

    # Can this strategy go short?
    can_short: bool = False

    # Minimal ROI designed for the strategy
    minimal_roi = {
        "60": 0.01,   # 1% after 60 minutes
        "30": 0.02,   # 2% after 30 minutes
        "0": 0.04,    # 4% immediately
    }

    # Optimal stoploss
    stoploss = -0.10  # 10% stoploss

    # Trailing stoploss
    trailing_stop = False

    # Optimal timeframe
    timeframe = "5m"

    # Run "populate_indicators()" only for new candle
    process_only_new_candles = True

    # These values can be overridden in the config
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    # Hyperoptable parameters
    buy_rsi = IntParameter(low=1, high=50, default=30, space="buy", optimize=True, load=True)
    sell_rsi = IntParameter(low=50, high=100, default=70, space="sell", optimize=True, load=True)

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 30

    # Optional order type mapping
    order_types = {
        "entry": "limit",
        "exit": "limit",
        "stoploss": "market",
        "stoploss_on_exchange": False,
    }

    # Optional order time in force
    order_time_in_force = {"entry": "GTC", "exit": "GTC"}

    def informative_pairs(self):
        """
        Define additional, informative pair/interval combinations to be cached from the exchange.
        :return: List of tuples in the format (pair, interval)
        """
        return []

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Adds several different TA indicators to the given DataFrame
        :param dataframe: Dataframe with data from the exchange
        :param metadata: Additional information, like the currently traded pair
        :return: a Dataframe with all mandatory indicators for the strategies
        """
        # RSI
        dataframe["rsi"] = ta.RSI(dataframe)

        # Bollinger Bands
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe["bb_lowerband"] = bollinger["lower"]
        dataframe["bb_middleband"] = bollinger["mid"]
        dataframe["bb_upperband"] = bollinger["upper"]
        dataframe["bb_percent"] = (
            (dataframe["close"] - dataframe["bb_lowerband"])
            / (dataframe["bb_upperband"] - dataframe["bb_lowerband"])
        )

        # EMA
        dataframe["ema12"] = ta.EMA(dataframe, timeperiod=12)
        dataframe["ema26"] = ta.EMA(dataframe, timeperiod=26)

        # MACD
        macd = ta.MACD(dataframe)
        dataframe["macd"] = macd["macd"]
        dataframe["macdsignal"] = macd["macdsignal"]
        dataframe["macdhist"] = macd["macdhist"]

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the entry signal for the given dataframe
        :param dataframe: DataFrame
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with entry columns populated
        """
        dataframe.loc[
            (
                # Signal: RSI crosses above buy_rsi (default 30)
                (qtpylib.crossed_above(dataframe["rsi"], self.buy_rsi.value))
                # Guard: price is below BB middle band (oversold)
                & (dataframe["close"] <= dataframe["bb_middleband"])
                # Guard: MACD is positive
                & (dataframe["macd"] > dataframe["macdsignal"])
                # Guard: volume is not zero
                & (dataframe["volume"] > 0)
            ),
            "enter_long",
        ] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the exit signal for the given dataframe
        :param dataframe: DataFrame
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with exit columns populated
        """
        dataframe.loc[
            (
                # Signal: RSI crosses above sell_rsi (default 70)
                (qtpylib.crossed_above(dataframe["rsi"], self.sell_rsi.value))
                # Guard: price is above BB middle band (overbought)
                & (dataframe["close"] >= dataframe["bb_middleband"])
                # Guard: MACD is negative
                & (dataframe["macd"] < dataframe["macdsignal"])
                # Guard: volume is not zero
                & (dataframe["volume"] > 0)
            ),
            "exit_long",
        ] = 1

        return dataframe

