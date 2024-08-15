"""
Custom integration to integrate eto_irrigation with Home Assistant.

For more details about this integration, please refer to
https://github.com/dpktjf/eto-irrigation
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.const import (
    CONF_NAME,
    Platform,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ETOSmartZoneClient
from .const import (
    CONF_ETO_ENTITY_ID,
    CONF_MAX_MINS,
    CONF_RAIN_ENTITY_ID,
    CONF_SCALE,
    CONF_THROUGHPUT_MM_H,
)
from .coordinator import ETOSmartZoneDataUpdateCoordinator
from .data import ETOSmartZoneData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import ETOSmartZoneConfigEntry

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
]

# https://homeassistantapi.readthedocs.io/en/latest/api.html

_LOGGER = logging.getLogger(__name__)

DEFAULT_SCAN_INTERVAL = timedelta(minutes=10)


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(
    hass: HomeAssistant,
    entry: ETOSmartZoneConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    _name = entry.data[CONF_NAME]

    eto_api = ETOSmartZoneClient(
        name=_name,
        eto_entity_id=entry.options[CONF_ETO_ENTITY_ID],
        rain_entity_id=entry.options[CONF_RAIN_ENTITY_ID],
        throughput=entry.options[CONF_THROUGHPUT_MM_H],
        scale=entry.options[CONF_SCALE],
        max_mins=entry.options[CONF_MAX_MINS],
        session=async_get_clientsession(hass),
        states=hass.states,
    )
    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    coordinator = ETOSmartZoneDataUpdateCoordinator(eto_api, hass)
    await coordinator.async_config_entry_first_refresh()

    entry.async_on_unload(entry.add_update_listener(async_update_options))

    entry.runtime_data = ETOSmartZoneData(_name, eto_api, coordinator)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_update_options(
    hass: HomeAssistant, entry: ETOSmartZoneConfigEntry
) -> None:
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ETOSmartZoneConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
