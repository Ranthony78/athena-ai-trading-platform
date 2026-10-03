import os

from .base import *

DEBUG = True

# Local market data may use Zerodha, but local broker order placement stays
# disabled regardless of environment variables.
LIVE_TRADING_ENABLED = False
