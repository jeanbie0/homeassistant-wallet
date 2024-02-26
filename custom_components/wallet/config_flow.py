import logging
from typing import Any, Dict, Optional

from homeassistant import config_entries, core, exceptions
from homeassistant.core import HomeAssistant
from homeassistant.const import (
    CONF_NAME,
    CONF_URL,
    CONF_TYPE,
    CONF_ENTITY_ID,
    ATTR_NAME,
    ATTR_UNIT_OF_MEASUREMENT,
    ATTR_DEVICE_CLASS,
    CURRENCY_EURO,
)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import entity_registry as er
import voluptuous as vol

from .const import (
    DOMAIN,
    CONF_SAVING,
    CONF_STOCK,
    CONF_CRYPTO,
    CONF_ITEMS,
    CONF_ITEM_NAME,
    CONF_AMOUNT,
    ATTR_AMOUNT,
    ATTR_WALLET,
    ATTR_TYPE,
    ATTR_ENTITY_TRACKER,
    ATTR_STATE_CLASS,
)

_LOGGER = logging.getLogger(__name__)

USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_URL, default=""): cv.string,
        vol.Required(CONF_TYPE) : vol.In( [CONF_SAVING, CONF_STOCK, CONF_CRYPTO] ),
    }
)

ITEM_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ITEM_NAME): cv.string,
        vol.Required(CONF_AMOUNT): cv.string,
        vol.Required(CONF_ENTITY_ID): cv.string,
        vol.Optional("add_another"): cv.boolean
    }
)



async def validate_input(hass: HomeAssistant, data: dict) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from ITEM_SCHEMA with values provided by the user.
    """
    # Validate the data can be used to set up a connection.

    # This is a simple example to show an error in the UI for a short hostname
    # The exceptions are defined at the end of this file, and are used in the
    # `async_step_user` method below.
    entity_id = data[CONF_ENTITY_ID]
    _LOGGER.info("entity_id: " + entity_id)
    
    # TODO https://developers.home-assistant.io/docs/entity_registry_index/
    return data # TODO remove. Not working with non unique entity
    entity_reg = er.async_get(hass)
    if entity_reg is None:
        _LOGGER.exception("entity_reg is None")
        raise BadEntity
    entity = entity_reg.async_get(entity_id)
    if entity is None:
        _LOGGER.exception("entity is None")
        raise BadEntity

    # Return info that you want to store in the config entry.
    # "Title" is what is displayed to the user for this hub device
    # It is stored internally in HA as part of the device config.
    return data


class WalletConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Wallet config flow."""

    data: Optional[Dict[str, Any]]

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        """Invoked when a user initiates a flow via the user interface."""
        errors: Dict[str, str] = {}
        if user_input is not None:
            self.data = user_input
            self.data[CONF_ITEMS] = []
            # Return the form of the next step.
            return await self.async_step_item()

        return self.async_show_form(
            step_id="user", data_schema=USER_SCHEMA, errors=errors
        )
    
    async def async_step_item(self, user_input: Optional[Dict[str, Any]] = None):
        """Second step"""
        errors: Dict[str, str] = {}
        if user_input is not None:
            try:
                await validate_input(self.hass, user_input)
            except BadEntity:
                _LOGGER.exception("Bad entity")
                errors["base"] = "bad_entity"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

            # item is valid
            self.data[CONF_ITEMS].append(
                {
                    "item_name": user_input[CONF_ITEM_NAME],
                    "amount": user_input[CONF_AMOUNT],
                    "entity_id": user_input[CONF_ENTITY_ID],
                }
            )

            # If user ticked the box show this form again so they can add an
            # additional repo.
            if user_input.get("add_another", False):
                return await self.async_step_item()

            return self.async_create_entry(title="Wallet", data=self.data)

        return self.async_show_form(
            step_id="item", data_schema=ITEM_SCHEMA, errors=errors
        )

class BadEntity(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid entity."""