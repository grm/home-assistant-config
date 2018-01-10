"""
Details about mining Monero at minexmr currencies from Node Crypto Pool.
"""
import logging
from datetime import timedelta

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.helpers.entity import Entity

REQUIREMENTS = ['requests==2.18.4', 'datetime']

_LOGGER = logging.getLogger(__name__)

STAT_HASHES = 'hashes'
LAST_SHARE_TIME = 'last_share'
BALANCE = 'balance'
EXPIRED = 'expired_shares'
PAYMENT_THRESHOLD = 'payment_threshold'
INVALID_SHARES = 'invalid_shares'
PAID = 'paid'
HASHRATE = 'hashrate'
LAST_PAYMENT_DATE = 'last_payment_date'
LAST_PAYMENT_VALUE = 'last_payment_value'

CONF_ATTRIBUTION = "Data provided by Node Cryptonote Pool"
CONF_POOL_ADDRESS = 'pool_address'
CONF_WALLET_ADDRESS = 'wallet_address'
CONF_POOL_NAME = 'pool_name'



ICON = 'mdi:currency-usd'

SCAN_INTERVAL = timedelta(minutes=1)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_POOL_NAME): cv.string,
    vol.Required(CONF_POOL_ADDRESS): cv.string,
    vol.Required(CONF_WALLET_ADDRESS): cv.string,
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the CoinMarketCap sensor."""
    address = config.get(CONF_POOL_ADDRESS) + "stats_address?longpoll=false&address=" + config.get(CONF_WALLET_ADDRESS)

    # try:
    #     CryptoCompareData(currency, display_currency).update()
    # except HTTPError:
    #     _LOGGER.warning("Currency %s or display currency %s is not available. "
    #                     "Using bitcoin and USD.", currency, display_currency)
    #     currency = DEFAULT_CURRENCY
    #     display_currency = DEFAULT_DISPLAY_CURRENCY

    add_devices([CryptoNodePoolSensor(
        CryptoNodePoolData(address, config.get(CONF_POOL_NAME)))], True)


class CryptoNodePoolSensor(Entity):
    """Representation of a CoinMarketCap sensor."""

    def __init__(self, data):
        """Initialize the sensor."""
        self.data = data
        self._ticker = None
        self._unit_of_measurement = 'KiloHash'
        self._name = self.data.pool_name.upper()

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._ticker['stats']['hashrate']

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return self._unit_of_measurement

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return ICON

    @property
    def device_state_attributes(self):
        """Return the state attributes of the sensor."""
        import datetime
        last_share = datetime.datetime.fromtimestamp(int(self._ticker['stats']["lastShare"]))\
            .strftime('%Y-%m-%d %H:%M:%S')
        last_payment_date = datetime.datetime.fromtimestamp(int(self._ticker['payments'][1]))\
            .strftime('%Y-%m-%d %H:%M:%S')
        last_payment_value = int(self._ticker['payments'][0].split(':')[2]) / 1000000000000
        return {
            STAT_HASHES: self._ticker['stats']['hashes'],
            ATTR_ATTRIBUTION: CONF_ATTRIBUTION,
            LAST_SHARE_TIME: last_share,
            BALANCE: self._ticker['stats']['balance'],
            EXPIRED: self._ticker['stats']['expired'],
            PAYMENT_THRESHOLD: self._ticker['stats']['thold'] / 1000000000000,
            INVALID_SHARES: self._ticker['stats']['invalid'],
            PAID: self._ticker['stats']['paid'],
            HASHRATE: int(self._ticker['stats']['hashrate']) / 1000,
            LAST_PAYMENT_DATE: last_payment_date,
           LAST_PAYMENT_VALUE: last_payment_value
        }

    def update(self):
        """Get the latest data and updates the states."""
        self.data.update()
        self._ticker = self.data.ticker


class CryptoNodePoolData(object):
    """Get the latest data and update the states."""

    def __init__(self, address, pool_name):
        """Initialize the data object."""
        self.address = address
        self.pool_name = pool_name
        self.ticker = None

    def update(self):
        """Get the latest data from the pool"""
        import requests
        import json
        response = requests.get(self.address)
        if response.ok:
            # Loading the response data into a dict variable
            # json.loads takes in only binary or string variables so using content to fetch binary content
            # Loads (Load String) takes a Json file and converts into python data structure (dict or list, depending on JSON)
            self.ticker = json.loads(response.content)
