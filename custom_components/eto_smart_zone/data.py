"""Custom types for eto_irrigation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

    from .api import ETOSmartZoneClient
    from .coordinator import ETOSmartZoneDataUpdateCoordinator


type ETOSmartZoneConfigEntry = ConfigEntry[ETOSmartZoneData]


@dataclass
class ETOSmartZoneData:
    """Data for the ETO Smart Zone Calculator."""

    name: str
    client: ETOSmartZoneClient
    coordinator: ETOSmartZoneDataUpdateCoordinator
