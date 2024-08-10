"""Adds config flow for ETO."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.components.sensor.const import (
    DOMAIN as SENSOR_DOMAIN,
)
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)

# https://github.com/home-assistant/core/blob/master/homeassistant/const.py
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_ALBEDO,
    CONF_HUMIDITY_MAX,
    CONF_HUMIDITY_MIN,
    CONF_SOLAR_RAD,
    CONF_TEMP_MAX,
    CONF_TEMP_MIN,
    CONF_WIND,
    CONFIG_FLOW_VERSION,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class ETOConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for ETO."""

    VERSION = CONFIG_FLOW_VERSION

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> ETOOptionsFlow:
        """Get the options flow for this handler."""
        return ETOOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None
    ) -> ConfigFlowResult:
        """Handle initial step."""
        if user_input is None:
            entity_selector = selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain=[SENSOR_DOMAIN],
                    multiple=False,
                ),
            )

            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_NAME): str,
                        vol.Required(CONF_TEMP_MIN): entity_selector,
                        vol.Required(CONF_TEMP_MAX): entity_selector,
                        vol.Required(CONF_HUMIDITY_MIN): entity_selector,
                        vol.Required(CONF_HUMIDITY_MAX): entity_selector,
                        vol.Required(CONF_WIND): entity_selector,
                        vol.Required(CONF_SOLAR_RAD): entity_selector,
                        vol.Required(CONF_ALBEDO): entity_selector,
                    }
                ),
            )

        await self.async_set_unique_id(user_input[CONF_NAME].lower())
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=user_input[CONF_NAME],
            data={CONF_NAME: user_input[CONF_NAME]},
            options={**user_input},
        )


class ETOOptionsFlow(OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        entity_selector = selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain=[SENSOR_DOMAIN],
                multiple=False,
            ),
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_TEMP_MIN, default=self.config_entry.options[CONF_TEMP_MIN]
                    ): entity_selector,
                    vol.Required(
                        CONF_TEMP_MAX, default=self.config_entry.options[CONF_TEMP_MAX]
                    ): entity_selector,
                    vol.Required(
                        CONF_HUMIDITY_MIN,
                        default=self.config_entry.options[CONF_HUMIDITY_MIN],
                    ): entity_selector,
                    vol.Required(
                        CONF_HUMIDITY_MAX,
                        default=self.config_entry.options[CONF_HUMIDITY_MAX],
                    ): entity_selector,
                    vol.Required(
                        CONF_WIND, default=self.config_entry.options[CONF_WIND]
                    ): entity_selector,
                    vol.Required(
                        CONF_SOLAR_RAD,
                        default=self.config_entry.options[CONF_SOLAR_RAD],
                    ): entity_selector,
                    vol.Required(
                        CONF_ALBEDO, default=self.config_entry.options[CONF_ALBEDO]
                    ): entity_selector,
                }
            ),
        )
