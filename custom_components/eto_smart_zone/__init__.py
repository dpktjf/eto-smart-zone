"""
Custom integration to integrate eto_irrigation with Home Assistant.

For more details about this integration, please refer to
https://github.com/dpktjf/eto-irrigation
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.const import (
    CONF_NAME,
    Platform,
)
from homeassistant.helpers.event import async_track_state_change_event

from .api import ETOSmartZoneClient
from .const import (
    CONF_ETO_ENTITY_ID,
    CONF_RAIN_ENTITY_ID,
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


DEFAULT_SCAN_INTERVAL = timedelta(minutes=10)


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(
    hass: HomeAssistant,
    entry: ETOSmartZoneConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    _name = entry.data[CONF_NAME]

    eto_api = ETOSmartZoneClient(name=_name, config=entry)
    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    coordinator = ETOSmartZoneDataUpdateCoordinator(eto_api, hass)
    _eto = entry.options.get(CONF_ETO_ENTITY_ID)
    _rain = entry.options.get(CONF_RAIN_ENTITY_ID)
    _entities = []
    for entity in [_eto, _rain]:
        if entity is not None:
            _entities.append(entity)  # noqa: PERF401
    entry.async_on_unload(
        async_track_state_change_event(
            hass,
            _entities,
            coordinator.async_check_entity_state_change,
        )
    )
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
