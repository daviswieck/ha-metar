import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DEFAULT_UPDATE_INTERVAL

class MetarSensorConfigFlow(config_entries.ConfigFlow, domain="metar"):
    """Config flow for METAR sensor."""

    async def async_step_user(self, user_input=None):
        """Handle the initial setup step."""
        if user_input is not None:
            return self.async_create_entry(
                title=user_input["station_code"],
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("station_code"): str,
            })
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow."""
        return MetarSensorOptionsFlowHandler(config_entry)


class MetarSensorOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle the options flow for the METAR sensor."""

    def __init__(self, config_entry):
        """Initialize the options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options for the integration."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    "update_interval",
                    default=self.config_entry.options.get(
                        "update_interval", DEFAULT_UPDATE_INTERVAL
                    ),
                ): int,
            })
        )
