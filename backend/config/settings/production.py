from .base import *

DEBUG = False

# Production is the one place allowed to flip these on by default; an
# explicit LIVE_TRADING_ENABLED=True in the environment can also do so
# from any settings module — see base.py.
MARKET_PROVIDER = "zerodha"
LIVE_TRADING_ENABLED = True