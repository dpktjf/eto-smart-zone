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
from homeassistant.const import (
    CONF_NAME,
    CONF_UNIQUE_ID,
)
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import selector

from .const import (
    CONF_ETO_ENTITY_ID,
    CONF_MAX_MINS,
    CONF_RAIN_ENTITY_ID,
    CONF_SCALE,
    CONF_THROUGHPUT_MM_H,
    CONFIG_FLOW_VERSION,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class ETOSmartZoneConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for ETO."""

    VERSION = CONFIG_FLOW_VERSION

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> ETOSmartZoneOptionsFlow:
        """Get the options flow for this handler."""
        return ETOSmartZoneOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None
    ) -> ConfigFlowResult:
        """Handle initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_NAME): str,
                        vol.Required(CONF_ETO_ENTITY_ID): selector.EntitySelector(
                            selector.EntitySelectorConfig(
                                domain=[SENSOR_DOMAIN],
                                multiple=False,
                            ),
                        ),
                        vol.Required(CONF_RAIN_ENTITY_ID): selector.EntitySelector(
                            selector.EntitySelectorConfig(
                                domain=[SENSOR_DOMAIN],
                                multiple=False,
                            ),
                        ),
                        vol.Optional(CONF_THROUGHPUT_MM_H): selector.NumberSelector(
                            selector.NumberSelectorConfig(
                                min=5, max=20, mode=selector.NumberSelectorMode.BOX
                            ),
                        ),
                        vol.Optional(CONF_SCALE): selector.NumberSelector(
                            selector.NumberSelectorConfig(
                                min=1, max=100, mode=selector.NumberSelectorMode.BOX
                            ),
                        ),
                        vol.Optional(CONF_MAX_MINS): selector.NumberSelector(
                            selector.NumberSelectorConfig(
                                min=1, max=60, mode=selector.NumberSelectorMode.BOX
                            ),
                        ),
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


class ETOSmartZoneOptionsFlow(OptionsFlow):
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

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME): cv.string,
                    vol.Required(CONF_ETO_ENTITY_ID): cv.entity_id,
                    vol.Required(CONF_RAIN_ENTITY_ID): cv.entity_id,
                    vol.Optional(CONF_THROUGHPUT_MM_H): vol.Coerce(int),
                    vol.Optional(CONF_SCALE): vol.Coerce(int),
                    vol.Optional(CONF_MAX_MINS): vol.Coerce(int),
                    vol.Optional(CONF_UNIQUE_ID): cv.string,
                }
            ),
        )
