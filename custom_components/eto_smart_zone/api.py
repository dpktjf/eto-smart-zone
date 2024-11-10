"""Sample API Client."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .const import (
    _LOGGER,
    ATTR_ETO,
    ATTR_RAIN,
    CALC_RAW_RUNTIME,
    CALC_RUNTIME,
    CONF_ETO_ENTITY_ID,
    CONF_MAX_MINS,
    CONF_RAIN_ENTITY_ID,
    CONF_SCALE,
    CONF_THROUGHPUT_MM_H,
)

if TYPE_CHECKING:
    from .data import ETOSmartZoneConfigEntry


class ETOApiSmartZoneError(Exception):
    """Exception to indicate a general API error."""


class ETOApiSmartZoneCommunicationError(
    ETOApiSmartZoneError,
):
    """Exception to indicate a communication error."""


class ETOApiSmartZoneAuthenticationError(
    ETOApiSmartZoneError,
):
    """Exception to indicate an authentication error."""


class ETOApiSmartZoneCalculationError(
    ETOApiSmartZoneError,
):
    """Exception to indicate a calculation error."""


class ETOApiSmartZoneCalculationStartupError(
    ETOApiSmartZoneError,
):
    """Exception to indicate a calculation error - probably due to start-up ."""


class ETOSmartZoneClient:
    """Smart Zone API Client."""

    def __init__(
        self,
        name: str,
        config: ETOSmartZoneConfigEntry,
    ) -> None:
        """Sample API Client."""
        self._name = name
        self._config = config
        self._entities = {}
        self._entities[config.options[CONF_ETO_ENTITY_ID]] = None
        self._entities[config.options[CONF_RAIN_ENTITY_ID]] = 0

        self._throughput = config.options[CONF_THROUGHPUT_MM_H]
        self._scale = config.options[CONF_SCALE]
        self._max_mins = config.options[CONF_MAX_MINS]
        self._calc_data = {}
        self._calc_data[CALC_RUNTIME] = None
        self._calc_data[CALC_RAW_RUNTIME] = None
        self._calc_data[ATTR_ETO] = None
        self._calc_data[ATTR_RAIN] = None
        self._calc_data[CONF_THROUGHPUT_MM_H] = self._throughput
        self._calc_data[CONF_SCALE] = self._scale
        self._calc_data[CONF_MAX_MINS] = self._max_mins

    async def entity_update(self, entity_id: str, new_state: float) -> None:
        """Update to an entity pushed."""
        self._entities[entity_id] = new_state

    async def collect_calculation_data(self) -> None:
        """
        Collect all the necessary weather and other calculation data.

        Convert into the correct units for calculation.
        """
        # https://developers.home-assistant.io/docs/core/entity/sensor
        try:
            self._calc_data[ATTR_ETO] = self._entities[
                self._config.options[CONF_ETO_ENTITY_ID]
            ]
            self._calc_data[ATTR_RAIN] = self._entities[
                self._config.options[CONF_RAIN_ENTITY_ID]
            ]

            await self.calc_smart_zone()
            """
                delta = precip - eto : < 0 means irrigation required
                precip_rate = throughput(LPH) / size(M2)
                duration = abs(delta) / precip_rate * 3600
            """

            _LOGGER.debug("collect_calculation_data: %s", self._calc_data)
        except ValueError as exception:
            msg = f"Value error fetching information - {exception}"
            _LOGGER.exception(msg)
            raise ETOApiSmartZoneCalculationError(
                msg,
            ) from exception
        except Exception as exception:  # pylint: disable=broad-except
            msg = f"Something really wrong happened! - {exception}"
            _LOGGER.exception(msg)
            raise ETOApiSmartZoneError(
                msg,
            ) from exception

    async def async_get_data(self) -> Any:
        """Get data from the API."""
        await self.collect_calculation_data()
        return self._calc_data

    async def calc_smart_zone(self) -> None:
        """Perform ETO calculation."""
        if (
            self._calc_data[ATTR_ETO] is not None
            and self._calc_data[ATTR_RAIN] is not None
        ):
            # was amount of rain enough to cover calculated ETo?
            delta: float = self._calc_data[ATTR_RAIN] - self._calc_data[ATTR_ETO]
            _LOGGER.debug("required %s", -delta)
            if delta < 0:
                # not enough rainfall for the day; work out scaled runtime duration
                reqd: float = abs(delta) / self._throughput * 60 * 60
                self._calc_data[CALC_RUNTIME] = round(reqd * self._scale / 100)
                _LOGGER.debug("raw runtime %s", self._calc_data[CALC_RUNTIME])
                self._calc_data[CALC_RAW_RUNTIME] = self._calc_data[CALC_RUNTIME]
                if self._calc_data[CALC_RUNTIME] > (self._max_mins * 60):
                    # make sure not longer than max run time
                    self._calc_data[CALC_RUNTIME] = self._max_mins * 60
                    _LOGGER.debug("adjusted runtime %s", self._calc_data[CALC_RUNTIME])
            else:
                self._calc_data[CALC_RAW_RUNTIME] = 0
                self._calc_data[CALC_RUNTIME] = 0
                _LOGGER.debug("no runtime %s", self._calc_data[CALC_RUNTIME])
