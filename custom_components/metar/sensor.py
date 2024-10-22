import aiohttp
import async_timeout
import re  # Importing re for regex operations
from datetime import timedelta
from metar.Metar import Metar
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import ATTR_ATTRIBUTION
import homeassistant.util.dt as dt_util
from .const import BASE_URL, DEFAULT_UPDATE_INTERVAL

ATTRIBUTION = "Data provided by NOAA"

class MetarSensor(SensorEntity):
    """Representation of a METAR sensor."""

    def __init__(self, station_code, update_interval):
        """Initialize the sensor."""
        self._station_code = station_code
        self._update_interval = update_interval
        self._state = None
        self._attr_name = f"METAR Sensor - {station_code}"
        self._attr_unique_id = f"metar_sensor_{station_code}"
        self._attributes = {}
        self._next_update = None

    async def async_update(self):
        """Fetch and parse METAR data."""
        if self._next_update and dt_util.utcnow() < self._next_update:
            return  # Skip update if not time yet

        await self._fetch_metar_data()
        self._next_update = dt_util.utcnow() + timedelta(minutes=self._update_interval)

    async def _fetch_metar_data(self):
        """Helper method to fetch and parse METAR data."""
        url = BASE_URL.format(station=self._station_code)
        async with aiohttp.ClientSession() as session:
            try:
                with async_timeout.timeout(10):
                    response = await session.get(url)
                    raw_data = await response.text()
                    metar_string = self._extract_metar(raw_data)
                    report = Metar(metar_string)

                    self._attributes = {
                        "station": report.station_id,
                        "report_type": str(report.report_type()),
                        "time": report.time.strftime("%Y-%m-%d %H:%M:%S"),
                        "temperature": f"{report.temp.value('C')} °C" if report.temp else "N/A",
                        "dew_point": f"{report.dewpt.value('C')} °C" if report.dewpt else "N/A",
                        "wind": (
                            f"{report.wind_dir.compass()} at {report.wind_speed.value('KT')} knots"
                            if report.wind_speed else "Calm"
                        ),
                        "visibility": f"{report.vis.value('SM')} miles" if report.vis else "N/A",
                        "pressure": f"{report.press.value('MB')} mb" if report.press else "N/A",
                        "sky": self._format_sky_conditions(report.sky),
                        "remarks": " ".join(report.remarks()) if report.remarks() else "None",
                        "raw_metar": report.code,
                    }
                    self._state = report.temp.value('C') if report.temp else "N/A"
            except Exception as e:
                self._state = f"Error: {e}"
                self._attributes = {"error": str(e)}

    def _extract_metar(self, raw_data):
        """Extract the METAR string from the raw response."""
        lines = raw_data.splitlines()
        for line in reversed(lines):
            if re.match(r"^[A-Z]{4} \d{6}Z", line):
                return line.strip()
        raise ValueError("No valid METAR found in response.")

    def _format_sky_conditions(self, sky_conditions):
        """Format the sky conditions as a readable string."""
        if not sky_conditions:  # Handle cases with no detailed layers
            return "Clear"
    
        formatted_layers = []
        for layer in sky_conditions:
            condition = layer[0]
            altitude = layer[1].value('FT') if layer[1] else None
            if altitude:
                formatted_layers.append(f"{condition} at {altitude} ft")
            else:
                formatted_layers.append(condition)
    
        return ", ".join(formatted_layers)


    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return extra attributes."""
        return {**self._attributes, ATTR_ATTRIBUTION: ATTRIBUTION}

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the METAR sensor platform."""
    station_code = entry.data["station_code"]
    update_interval = entry.options.get("update_interval", DEFAULT_UPDATE_INTERVAL)

    async_add_entities([MetarSensor(station_code, update_interval)])