"""Wallet sensor platform."""
import logging
from datetime import timedelta
from typing import Any, Callable, Dict, Optional
import voluptuous as vol
from homeassistant import config_entries, core

from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
)
# https://github.com/home-assistant/core/blob/dev/homeassistant/const.py
from homeassistant.const import (
    CONF_NAME,
    CONF_FRIENDLY_NAME,
    CONF_URL,
    CONF_TYPE,
    CONF_ENTITY_ID,
    ATTR_NAME,
    ATTR_UNIT_OF_MEASUREMENT,
    ATTR_DEVICE_CLASS,
    CURRENCY_EURO,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.storage import Store
from homeassistant.helpers import service
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.typing import (
    ConfigType,
    DiscoveryInfoType,
    HomeAssistantType,
)

from .const import (
    DOMAIN,
    CONF_SAVING,
    CONF_STOCK,
    CONF_CRYPTO,
    CONF_ITEMS,
    CONF_AMOUNT,
    CONF_ITEM_NAME,
    ATTR_AMOUNT,
    ATTR_WALLET,
    ATTR_TYPE,
    ATTR_URL,
    ATTR_RATE,
    ATTR_ENTITY_TRACKER,
    ATTR_STATE_CLASS,
)

_LOGGER = logging.getLogger(__name__)
# Update every 10 minutes TODO change
SCAN_INTERVAL = timedelta(minutes=1)

# https://developers.home-assistant.io/docs/development_validation/
ITEM_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string, 
        vol.Required(CONF_AMOUNT): cv.string, 
        vol.Required(CONF_ENTITY_ID): cv.entity_id
    }
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_URL, default=""): cv.string,
        vol.Required(CONF_TYPE) : vol.In( [CONF_SAVING, CONF_STOCK, CONF_CRYPTO] ),
        vol.Required(CONF_ITEMS): vol.All(cv.ensure_list, [ITEM_SCHEMA]),
    }
)

async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    """Setup sensors from a config entry created in the integrations UI."""
    config = hass.data[DOMAIN][config_entry.entry_id]
    session = async_get_clientsession(hass)
    #sensors = [ ValueWalletSensor(hass, config[CONF_NAME], config[CONF_URL], config[CONF_TYPE], config[CONF_ITEM_NAME], config[CONF_ENTITY_ID])]
    sensors = [ ValueWalletSensor(hass, config[CONF_NAME], config[CONF_URL], config[CONF_TYPE], item) for item in config[CONF_ITEMS]]
    async_add_entities(sensors, update_before_add=True)
    #sensors = [ AmountWalletSensor(hass, config[CONF_NAME], config[CONF_URL], config[CONF_TYPE], config[CONF_ITEM_NAME], config[CONF_ENTITY_ID])]
    sensors = [ AmountWalletSensor(hass, config[CONF_NAME], config[CONF_URL], config[CONF_TYPE], item) for item in config[CONF_ITEMS]]
    async_add_entities(sensors, update_before_add=True)

#async def async_setup_platform(
#    hass: HomeAssistantType,
#    config: ConfigType,
#    async_add_entities: Callable,
#    discovery_info: Optional[DiscoveryInfoType] = None,
#) -> None:
#    """Set up the sensor platform."""
#    session = async_get_clientsession(hass)
#    hass.data[DOMAIN] = {}
#    sensors = [ AmountWalletSensor(hass, config[CONF_NAME], config[CONF_URL], config[CONF_TYPE], config[CONF_ITEM_NAME], config[CONF_ENTITY_ID]),
#                ValueWalletSensor(hass, config[CONF_NAME], config[CONF_URL], config[CONF_TYPE], config[CONF_ITEM_NAME], config[CONF_ENTITY_ID])]
#    async_add_entities(sensors, update_before_add=True)

def get_entity_state_number(hass, entity_id):
    # Get the state of the entity
    entity_state = hass.states.get(entity_id)
    
    if entity_state is not None:
        return float(entity_state.state)
    else:
        return float(0)

# Device https://developers.home-assistant.io/docs/device_registry_index/
class AmountWalletSensor(Entity):
    """Representation of a Wallet sensor."""
    def __init__(self, hass: HomeAssistantType, wallet_name: str, link: str, wallet_type: str, item:  Dict[str, str]):
        super().__init__()
        self.hass = hass
        self.wallet_name = wallet_name
        self.link = link
        self.wallet_type = wallet_type
        self.item = item["item_name"]
        self.item_name = item.get(CONF_NAME, self.item)
        self.entity_tracker = item.get(CONF_ENTITY_ID, self.item)
        self._amount = float(item.get(CONF_AMOUNT, self.item))
        self._name = "Amount " + self.item_name
        self._unique_id = "wallet_" + self.wallet_name + "_" + self._name
        self._state = self._amount
        self._available = True
        self._store = Store(self.hass, 1.0, f"{self._unique_id}.json")

        self.attrs: Dict[str, Any] = {ATTR_NAME: self._name}
        self.attrs[ATTR_STATE_CLASS] = "measurement"
        self.attrs[ATTR_TYPE] = self.wallet_type
        self.attrs[ATTR_URL] = self.link
        self.attrs[ATTR_NAME] = self._name
        self.attrs[CONF_FRIENDLY_NAME] = self.wallet_name + " amount" 
        self.attrs[ATTR_TYPE] = self.wallet_type
        self.attrs[ATTR_WALLET] = self.wallet_name
        self.attrs[ATTR_ENTITY_TRACKER] = self.entity_tracker
        _LOGGER.info('Init finished: for ' + self._name + ': ' + str(self._amount))

    async def async_added_to_hass(self):
        """Call when entity about to be added to hass."""
        state = await self._store.async_load()
        if state is not None:
            self._amount = state
        _LOGGER.info('async_added_to_hass finished: ' + str(self._amount) + ' ' + str(state))

        # Add this entity to the data dictionary
        self.hass.data[DOMAIN][self.entity_id] = self
        
        # Register the "set_amount" service
        self.hass.services.async_register(
            DOMAIN,  # domain
            "set_amount",  # service
            self.set_amount,  # method
            schema=vol.Schema({
                vol.Required("entity_id"): vol.Coerce(str),
                vol.Required("value"): vol.Coerce(float)
            }),
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, "wallet_" + self.wallet_name)
            },
            name=self.wallet_name,
            model=self.wallet_type,
        )

    @property
    def icon(self):
        return "mdi:wallet"

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def amount(self):
        return self._amount

    async def set_amount(self, call):
        """Set the amount."""
        entity_id = call.data.get("entity_id")
        value = call.data.get("value")

        _LOGGER.info('set_amount ' + entity_id + ' to ' + str(value))

        # Find the entity with the given entity_id
        entity = self.hass.data[DOMAIN].get(entity_id)

        if entity is not None:
            entity._amount = value
            await entity._store.async_save(entity._amount)
            await entity.async_update()

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self._unique_id

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    @property
    def state(self) -> float:
        self._state = self._amount
        return self._state

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        return self.attrs

    async def async_update(self):
        try:
            _LOGGER.info('Update ' + self._name + ' to ' + str(self._amount))

        except ():
            self._available = False
            _LOGGER.exception("Error in Wallet.")

class ValueWalletSensor(Entity):
    """Representation of a Wallet sensor."""
    def __init__(self, hass: HomeAssistantType, wallet_name: str, link: str, wallet_type: str, item:  Dict[str, str]):
        super().__init__()
        self.hass = hass
        self.wallet_name = wallet_name
        self.link = link
        self.wallet_type = wallet_type
        self.item = item["item_name"]
        self.item_name = item.get(CONF_NAME, self.item)
        self.entity_tracker = item.get(CONF_ENTITY_ID, self.item)
        self.entity_amount = ("sensor.amount_" + self.item_name).replace(" ", "_")
        self._value = 0
        self._name = "Value " + self.item_name
        self._unique_id = "wallet_" + self.wallet_name + "_" + self._name
        self._state = self._value
        self._available = True
        self._store = Store(self.hass, 1.0, f"{self._unique_id}.json")

        self.attrs: Dict[str, Any] = {ATTR_NAME: self._name}
        self.attrs[ATTR_STATE_CLASS] = "measurement"
        self.attrs[ATTR_DEVICE_CLASS] = "monetary"
        self.attrs[ATTR_UNIT_OF_MEASUREMENT] = CURRENCY_EURO # TODO implementation default
        self.attrs[ATTR_TYPE] = self.wallet_type
        self.attrs[ATTR_URL] = self.link
        self.attrs[ATTR_NAME] = self._name
        self.attrs[CONF_FRIENDLY_NAME] = self.wallet_name + " value" 
        self.attrs[ATTR_TYPE] = self.wallet_type
        self.attrs[ATTR_WALLET] = self.wallet_name
        self.attrs[ATTR_ENTITY_TRACKER] = self.entity_tracker
        _LOGGER.info('Init finished: for ' + self._name + ': ' + str(self._value))

    async def async_added_to_hass(self):
        """Call when entity about to be added to hass."""
        state = await self._store.async_load()
        if state is not None:
            self._value = state
        else:
            self._value = float(0.0)
        _LOGGER.info('async_added_to_hass finished: ' + str(self._value) + ' ' + str(state))

        # Add this entity to the data dictionary
        self.hass.data[DOMAIN][self.entity_id] = self

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, "wallet_" + self.wallet_name)
            },
            name=self.wallet_name,
            model=self.wallet_type,
        )

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self._unique_id

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    @property
    def state(self) -> float:
        self._state = self._value
        return float(self._state) if self._state is not None else float(0.0)

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        return self.attrs

    async def async_update(self):
        try:
            _LOGGER.info('Update ' + self._name)

        except ():
            self._available = False
            _LOGGER.exception("Error in Wallet.")

    async def async_update(self):
        try:
            rate = get_entity_state_number(self.hass, self.entity_tracker)
            amount = get_entity_state_number(self.hass, self.entity_amount)
            #_LOGGER.info(self.entity_amount)

            self.attrs[ATTR_RATE] = rate
            self.attrs[ATTR_AMOUNT] = amount

            self._value = float(rate * amount)
            
            if(rate == 0): # error in tracker
                self._available = False
            else:
                self._available = True

            _LOGGER.info('Update ' + self._name + ' to ' + str(self._value) + '(' + str(rate) + '*' + str(amount) + ')')

            await self._store.async_save(self._value)

        except ():
            self._available = False
            _LOGGER.exception("Error in Wallet.")