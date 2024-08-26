"""Sample API Client."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.const import STATE_UNKNOWN

from custom_components.eto_smart_zone.const import (
    ATTR_ETO,
    ATTR_RAIN,
    ATTR_RAW_RUNTIME,
    CALC_RUNTIME,
    CONF_MAX_MINS,
    CONF_SCALE,
    CONF_THROUGHPUT_MM_H,
)

if TYPE_CHECKING:
    import aiohttp
    from homeassistant.core import StateMachine

_LOGGER = logging.getLogger(__name__)


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

    def __init__(  # noqa: PLR0913
        self,
        name: str,
        eto_entity_id: str,
        rain_entity_id: str,
        throughput: int,
        scale: int,
        max_mins: int,
        session: aiohttp.ClientSession,
        states: StateMachine,
    ) -> None:
        """Sample API Client."""
        self._name = name
        self._eto_entity_id = eto_entity_id
        self._rain_entity_id = rain_entity_id
        self._eto: float | str = STATE_UNKNOWN
        self._rain = STATE_UNKNOWN
        self._throughput = throughput
        self._scale = scale
        self._max_mins = max_mins
        self._session = session
        self._states = states
        self._calc_data = {}
        self._calc_data[CALC_RUNTIME] = 0
        self._calc_data[ATTR_ETO] = STATE_UNKNOWN
        self._calc_data[ATTR_RAIN] = STATE_UNKNOWN
        self._calc_data[CONF_THROUGHPUT_MM_H] = self._throughput
        self._calc_data[CONF_SCALE] = self._scale
        self._calc_data[CONF_MAX_MINS] = self._max_mins

    def __str__(self) -> str:
        """Pretty print."""
        return f"eto/rain = {self._eto_entity_id}/{self._rain_entity_id}"

    async def _get(self, ent: str) -> float:
        st = self._states.get(ent)
        #        if st is not None and isinstance(st.state, float):
        if st is not None:
            if st.state == "unknown":
                msg = "State unknown; probably starting up???"
                raise ETOApiSmartZoneCalculationStartupError(
                    msg,
                )
            return float(st.state)
        msg = "States not yet available; probably starting up???"
        raise ETOApiSmartZoneCalculationError(
            msg,
        )

    async def collect_calculation_data(self) -> None:
        """
        Collect all the necessary weather and other calculation data.

        Convert into the correct units for calculation.
        """
        # https://developers.home-assistant.io/docs/core/entity/sensor
        try:
            self._calc_data[ATTR_ETO] = await self._get(self._eto_entity_id)
            self._calc_data[ATTR_RAIN] = await self._get(self._rain_entity_id)

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
            self._calc_data[ATTR_ETO] is not STATE_UNKNOWN
            and self._calc_data[ATTR_RAIN] is not STATE_UNKNOWN
        ):
            # was amount of rain enough to cover calculated ETo?
            delta: float = self._calc_data[ATTR_RAIN] - self._calc_data[ATTR_ETO]
            _LOGGER.debug("required %s", -delta)
            if delta < 0:
                # not enough rainfall for the day; work out scaled runtime duration
                reqd: float = abs(delta) / self._throughput * 60 * 60
                self._calc_data[CALC_RUNTIME] = round(reqd * self._scale / 100)
                _LOGGER.debug("raw runtime %s", self._calc_data[CALC_RUNTIME])
                self._calc_data[ATTR_RAW_RUNTIME] = self._calc_data[CALC_RUNTIME]
                if self._calc_data[CALC_RUNTIME] > (self._max_mins * 60):
                    # make sure not longer than max run time
                    self._calc_data[CALC_RUNTIME] = self._max_mins * 60
                    _LOGGER.debug("adjusted runtime %s", self._calc_data[CALC_RUNTIME])
            else:
                self._calc_data[CALC_RUNTIME] = 0
                _LOGGER.debug("no runtime %s", self._calc_data[CALC_RUNTIME])
