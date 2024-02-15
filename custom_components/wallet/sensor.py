"""Wallet sensor platform."""
import logging
from datetime import timedelta
from typing import Any, Callable, Dict, Optional

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    ATTR_NAME,
    CONF_NAME,
    CONF_VALUE,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import (
    ConfigType,
    DiscoveryInfoType,
    HomeAssistantType,
)

from .const import (
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)
# Update every 10 minutes
SCAN_INTERVAL = timedelta(minutes=10)

# https://developers.home-assistant.io/docs/development_validation/
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_VALUE): cv.positive_int,
    }
)

async def async_setup_platform(
    hass: HomeAssistantType,
    config: ConfigType,
    async_add_entities: Callable,
    discovery_info: Optional[DiscoveryInfoType] = None,
) -> None:
    """Set up the sensor platform."""
    session = async_get_clientsession(hass)
    sensors = [ItemWalletSensor(config[CONF_NAME], config[CONF_VALUE])]
    async_add_entities(sensors, update_before_add=True)

class ItemWalletSensor(Entity):
    """Representation of a Item wallet sensor."""

    def __init__(self, name: str, value: int):
        super().__init__()
        self.name = name
        self.value = value
        self.attrs = Dict[str, Any]
        self._name = name
        self._state = None
        self._available = True

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self.name

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    @property
    def state(self) -> Optional[str]:
        return self._state

    @property
    def device_state_attributes(self) -> Dict[str, Any]:
        return self.attrs

    async def async_update(self):
        try:
            self.value = self.value + 1
            
        except ():
            self._available = False
            _LOGGER.exception("Error in Wallet.")
