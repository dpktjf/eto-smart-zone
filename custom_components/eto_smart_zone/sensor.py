"""Sensor platform for eto_irrigation."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.components.sensor.const import SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo

from custom_components.eto_smart_zone.api import ETOApiSmartZoneError
from custom_components.eto_smart_zone.const import (
    ATTR_ETO,
    ATTR_RAIN,
    ATTRIBUTION,
    CALC_RAW_RUNTIME,
    CALC_RUNTIME,
    CONF_MAX_MINS,
    CONF_SCALE,
    CONF_THROUGHPUT_MM_H,
    DEFAULT_NAME,
    DOMAIN,
    MANUFACTURER,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import ETOSmartZoneDataUpdateCoordinator
    from .data import ETOSmartZoneConfigEntry

SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key=DOMAIN,
        name="ETO Smart Zone",
        icon="mdi:sprinkler",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    config_entry: ETOSmartZoneConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    domain_data = config_entry.runtime_data
    name = domain_data.name
    weather_coordinator = domain_data.coordinator

    entities: list[ETOSmartZoneSensor] = [
        ETOSmartZoneSensor(
            name,
            f"{description.key}-{name}",
            description,
            weather_coordinator,
        )
        for description in SENSOR_TYPES
    ]
    async_add_entities(entities)


class ETOSmartZoneSensor(SensorEntity):
    """ETO Smart Zone Sensor class."""

    _attr_should_poll = False
    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        name: str,
        unique_id: str,
        entity_description: SensorEntityDescription,
        coordinator: ETOSmartZoneDataUpdateCoordinator,
    ) -> None:
        """Initialize the sensor class."""
        self.entity_description = entity_description
        self._coordinator = coordinator
        self.states: dict[str, Any] = {}

        self._attr_name = f"{entity_description.name} {name}"
        self._attr_unique_id = unique_id
        split_unique_id = unique_id.split("-")
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, f"{split_unique_id[1]}.lower()")},
            manufacturer=MANUFACTURER,
            name=DEFAULT_NAME,
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._coordinator.last_update_success

    async def async_added_to_hass(self) -> None:
        """Connect to dispatcher listening for entity data notifications."""
        self.async_on_remove(
            self._coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self) -> None:
        """Get the latest data from OWM and updates the states."""
        await self._coordinator.async_request_refresh()

    @property
    def native_value(self) -> str | None:
        """Return the native value of the sensor."""
        return self._coordinator.data[CALC_RUNTIME]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the device specific state attributes."""
        attributes: dict[str, Any] = {}

        try:
            attributes[ATTR_ETO] = self._coordinator.data[ATTR_ETO]
            attributes[ATTR_RAIN] = self._coordinator.data[ATTR_RAIN]
            attributes[CONF_THROUGHPUT_MM_H] = self._coordinator.data[
                CONF_THROUGHPUT_MM_H
            ]
            attributes[CONF_SCALE] = self._coordinator.data[CONF_SCALE]
            attributes[CALC_RAW_RUNTIME] = self._coordinator.data[CALC_RAW_RUNTIME]
            attributes[CONF_MAX_MINS] = self._coordinator.data[CONF_MAX_MINS]
        except ETOApiSmartZoneError as ex:
            _LOGGER.exception(ex)  # noqa: TRY401

        return attributes
