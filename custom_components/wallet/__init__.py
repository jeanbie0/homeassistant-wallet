"""Wallet Component."""
# https://developers.home-assistant.io/docs/development_checklist
# https://github.com/home-assistant/example-custom-config/blob/master/custom_components/detailed_hello_world_push/config_flow.py

# Structure of integration
# - Wallet
#   - Name (str)
#   - Link (str, optional)
#   - Type (saving, stock, crypto)
#   - Items (list of entities)
#       - Name (str)
#       - Entity_tracker (entity, optional (x1 if not provided))
#       - Amount (float)
#       - Value (float)
#
# Created entities
# - One for each wallet, the entity contain a list of items
#   - On for each item, the entity contain name string and amount and value entities
#       - Amount: entity that can be changed by user
#       - Value: entity computed with exchange rate from entity id
#
# Example
# - platform: wallet
#   name: testCBC
#   url: test.com
#   type: crypto
#   items:
#     - name: testCBCItem1
#       entity_id: sensor.binance_ticker_btceur
#     - name: testCBCItem2
#       entity_id: sensor.binance_ticker_etheur

import logging

from homeassistant import config_entries, core

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Set up platform from a ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Forward the setup to the sensor platform.
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )
    return True


async def async_setup(hass: core.HomeAssistant, config: dict) -> bool:
    """Set up the Wallet component from yaml configuration."""
    hass.data.setdefault(DOMAIN, {})
    return True