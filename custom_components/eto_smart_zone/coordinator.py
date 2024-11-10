"""DataUpdateCoordinator for eto_irrigation."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.const import (
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    ETOApiSmartZoneAuthenticationError,
    ETOApiSmartZoneError,
    ETOSmartZoneClient,
)
from .const import _LOGGER, DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import Event, EventStateChangedData, HomeAssistant

    from .data import ETOSmartZoneConfigEntry


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class ETOSmartZoneDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: ETOSmartZoneConfigEntry

    def __init__(
        self,
        eto_client: ETOSmartZoneClient,
        hass: HomeAssistant,
    ) -> None:
        """Initialize."""
        self._eto_client = eto_client

        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=10),
        )

    async def _async_update_data(self) -> Any:
        """Update data via library."""
        try:
            return await self._eto_client.async_get_data()
        except ETOApiSmartZoneAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except ETOApiSmartZoneError as exception:
            raise UpdateFailed(exception) from exception

    @property
    def eto_client(self) -> ETOSmartZoneClient:
        """Getter."""
        return self._eto_client

    async def async_check_entity_state_change(
        self, event: Event[EventStateChangedData]
    ) -> None:
        """Fetch and process state change event."""
        _LOGGER.debug("Entity state change: %s", event)
        if (
            (entity_id := event.data["entity_id"]) is None
            or (new_state := event.data["new_state"]) is None
            or new_state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE)
        ):
            _LOGGER.debug("skipping entity update for some reason")
            return
        _LOGGER.debug("new state = %s", float(new_state.state))
        await self._eto_client.entity_update(entity_id, float(new_state.state))
        """self.state_change = True"""
        await self.async_refresh()
