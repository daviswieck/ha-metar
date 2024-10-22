import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN

class MetarConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the configuration flow for METAR Sensor."""

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title=user_input["station_code"], data=user_input
            )

        # Configuration form to input the station code
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("station_code"): str,
            }),
        )
