"""Sensor platform for eto_irrigation."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.components.sensor.const import SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfLength
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo

from custom_components.eto_irrigation.api import ETOApiClientError
from custom_components.eto_irrigation.const import (
    ATTR_API_RUNTIME,
    ATTRIBUTION,
    CALC_FSETO_35,
    CONF_ALBEDO,
    CONF_DOY,
    CONF_HUMIDITY_MAX,
    CONF_HUMIDITY_MIN,
    CONF_SOLAR_RAD,
    CONF_TEMP_MAX,
    CONF_TEMP_MIN,
    CONF_WIND,
    DEFAULT_NAME,
    DOMAIN,
    MANUFACTURER,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

    from .coordinator import ETODataUpdateCoordinator
    from .data import ETOConfigEntry

SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key=ATTR_API_RUNTIME,
        name="ETO",
        icon="mdi:weather-pouring",
        native_unit_of_measurement=UnitOfLength.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    config_entry: ETOConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    domain_data = config_entry.runtime_data
    name = domain_data.name
    weather_coordinator = domain_data.coordinator

    entities: list[AbstractETOSensor] = [
        ETOSensor(
            name,
            f"{name}-{description.key}",
            description,
            weather_coordinator,
        )
        for description in SENSOR_TYPES
    ]
    async_add_entities(entities)


class AbstractETOSensor(SensorEntity):
    """Abstract class for an OpenWeatherMap sensor."""

    _attr_should_poll = False
    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        name: str,
        unique_id: str,
        description: SensorEntityDescription,
        coordinator: DataUpdateCoordinator,
    ) -> None:
        """Initialize the sensor."""
        self.entity_description = description
        self._coordinator = coordinator

        self._attr_name = f"{name} {description.name}"
        self._attr_unique_id = unique_id
        split_unique_id = unique_id.split("-")
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, f"{split_unique_id[0]}.lower()")},
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


class ETOSensor(AbstractETOSensor):
    """eto_irrigation Sensor class."""

    def __init__(
        self,
        name: str,
        unique_id: str,
        entity_description: SensorEntityDescription,
        coordinator: ETODataUpdateCoordinator,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(name, unique_id, entity_description, coordinator)
        self.coordinator = coordinator

    @property
    def native_value(self) -> str | None:
        """Return the native value of the sensor."""
        return self.coordinator.data[CALC_FSETO_35]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the device specific state attributes."""
        attributes: dict[str, Any] = {}

        try:
            attributes[CONF_TEMP_MIN] = self.coordinator.data[CONF_TEMP_MIN]
            attributes[CONF_TEMP_MAX] = self.coordinator.data[CONF_TEMP_MAX]
            attributes[CONF_HUMIDITY_MIN] = self.coordinator.data[CONF_HUMIDITY_MIN]
            attributes[CONF_HUMIDITY_MAX] = self.coordinator.data[CONF_HUMIDITY_MAX]
            attributes[CONF_WIND] = round(self.coordinator.data[CONF_WIND], 1)
            attributes[CONF_ALBEDO] = self.coordinator.data[CONF_ALBEDO]
            attributes[CONF_SOLAR_RAD] = self.coordinator.data[CONF_SOLAR_RAD]
            attributes[CONF_DOY] = self.coordinator.data[CONF_DOY]
        except ETOApiClientError as ex:
            _LOGGER.exception(ex)  # noqa: TRY401

        return attributes
