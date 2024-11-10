"""Adds config flow for ETO."""

from __future__ import annotations

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
from homeassistant.const import CONF_NAME, PERCENTAGE, UnitOfTime, UnitOfVolumetricFlux
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector

from .const import (
    _LOGGER,
    CONF_ETO_ENTITY_ID,
    CONF_MAX_MINS,
    CONF_RAIN_ENTITY_ID,
    CONF_SCALE,
    CONF_THROUGHPUT_MM_H,
    CONFIG_FLOW_VERSION,
    DOMAIN,
)

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): selector.TextSelector(),
    }
)

OPTIONS = vol.Schema(
    {
        vol.Required(
            CONF_ETO_ENTITY_ID, default=vol.UNDEFINED
        ): selector.EntitySelector(
            selector.EntityFilterSelectorConfig(domain=[SENSOR_DOMAIN])
        ),
        vol.Required(
            CONF_RAIN_ENTITY_ID, default=vol.UNDEFINED
        ): selector.EntitySelector(
            selector.EntityFilterSelectorConfig(domain=[SENSOR_DOMAIN])
        ),
        vol.Required(CONF_THROUGHPUT_MM_H, default=10): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=5,
                max=20,
                mode=selector.NumberSelectorMode.SLIDER,
                unit_of_measurement=UnitOfVolumetricFlux.MILLIMETERS_PER_HOUR,
            ),
        ),
        vol.Required(CONF_SCALE, default=100): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=1,
                max=100,
                mode=selector.NumberSelectorMode.SLIDER,
                unit_of_measurement=PERCENTAGE,
            ),
        ),
        vol.Required(CONF_MAX_MINS, default=30): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=1,
                max=60,
                mode=selector.NumberSelectorMode.SLIDER,
                unit_of_measurement=UnitOfTime.MINUTES,
            ),
        ),
    }
)


@callback
def configured_instances(hass: HomeAssistant) -> set[str | None]:
    """Return a set of configured instances."""
    entries = [
        entry.data.get(CONF_NAME) for entry in hass.config_entries.async_entries(DOMAIN)
    ]
    return set(entries)


class ConfigFlowHandler(ConfigFlow, domain=DOMAIN):
    """Config flow for ETO."""

    VERSION = CONFIG_FLOW_VERSION

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlowHandler:
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None
    ) -> ConfigFlowResult:
        """Handle initial step."""
        if user_input:
            self.config = user_input
            if user_input[CONF_NAME] in configured_instances(self.hass):
                errors = {}
                errors[CONF_NAME] = "already_configured"
                return self.async_show_form(
                    step_id="user", data_schema=CONFIG_SCHEMA, errors=errors
                )

            return await self.async_step_init()
        return self.async_show_form(step_id="user", data_schema=CONFIG_SCHEMA)

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show detailed config."""
        if user_input is not None:
            self.config.update(user_input)
            return await self.async_step_update()

        return self.async_show_form(
            step_id="init",
            data_schema=OPTIONS,
        )

    async def async_step_update(
        self,
        user_input: dict[str, Any] | None = None,  # noqa: ARG002
    ) -> ConfigFlowResult:
        """Create entry."""
        return self.async_create_entry(
            title=self.config[CONF_NAME],
            data={
                CONF_NAME: self.config[CONF_NAME],
            },
            options={
                CONF_ETO_ENTITY_ID: self.config.get(CONF_ETO_ENTITY_ID),
                CONF_RAIN_ENTITY_ID: self.config.get(CONF_RAIN_ENTITY_ID),
                CONF_THROUGHPUT_MM_H: self.config.get(CONF_THROUGHPUT_MM_H),
                CONF_SCALE: self.config.get(CONF_SCALE),
                CONF_MAX_MINS: self.config.get(CONF_MAX_MINS),
            },
        )

    async def old_async_step_user(
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


class OptionsFlowHandler(OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self.current_config: dict = dict(config_entry.data)
        self.options = dict(config_entry.options)
        _LOGGER.debug("options=%s", self.options)

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Manage the options."""
        schema = OPTIONS
        if user_input is not None:
            self.options.update(user_input)
            return await self._update_options()
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                schema, user_input or self.options
            ),
        )

    async def _update_options(self) -> ConfigFlowResult:
        """Update config entry options."""
        return self.async_create_entry(title="", data=self.options)


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
                    vol.Required(
                        CONF_ETO_ENTITY_ID,
                        default=self.config_entry.options[CONF_ETO_ENTITY_ID],
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain=[SENSOR_DOMAIN],
                            multiple=False,
                        ),
                    ),
                    vol.Required(
                        CONF_RAIN_ENTITY_ID,
                        default=self.config_entry.options[CONF_RAIN_ENTITY_ID],
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain=[SENSOR_DOMAIN],
                            multiple=False,
                        ),
                    ),
                    vol.Optional(
                        CONF_THROUGHPUT_MM_H,
                        default=self.config_entry.options[CONF_THROUGHPUT_MM_H],
                    ): vol.Coerce(int),
                    vol.Optional(
                        CONF_SCALE,
                        default=self.config_entry.options[CONF_SCALE],
                    ): vol.Coerce(int),
                    vol.Optional(
                        CONF_MAX_MINS,
                        default=self.config_entry.options[CONF_MAX_MINS],
                    ): vol.Coerce(int),
                }
            ),
        )
