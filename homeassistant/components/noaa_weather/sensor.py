"""Support for the NOAAWeather service."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Any, cast

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfLength,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfTime,
    UnitOfVolumetricFlux,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import NOAAWeatherDataUpdateCoordinator
from .const import (
    ATTR_CATEGORY,
    ATTR_DIRECTION,
    ATTR_ENGLISH,
    ATTR_FORECAST,
    ATTR_SPEED,
    ATTR_VALUE,
    ATTRIBUTION,
    DOMAIN,
    MAX_FORECAST_DAYS,
)

PARALLEL_UPDATES = 1

_LOGGER = logging.getLogger(__name__)


@dataclass
class NOAAWeatherSensorDescriptionMixin:
    """Mixin for NOAA Weather sensor."""

    value_fn: Callable[[dict[str, Any]], StateType]


@dataclass
class NOAAWeatherSensorDescription(
    SensorEntityDescription, NOAAWeatherSensorDescriptionMixin
):
    """Class describing NOAAWeather sensor entities."""

    attr_fn: Callable[[dict[str, Any]], dict[str, StateType]] = lambda _: {}


FORECAST_SENSOR_TYPES: tuple[NOAAWeatherSensorDescription, ...] = (
    NOAAWeatherSensorDescription(
        key="AirQuality",
        icon="mdi:air-filter",
        name="Air quality",
        value_fn=lambda data: cast(str, data[ATTR_CATEGORY]),
        device_class=SensorDeviceClass.ENUM,
        options=["good", "hazardous", "high", "low", "moderate", "unhealthy"],
        translation_key="air_quality",
    ),
    NOAAWeatherSensorDescription(
        key="CloudCoverDay",
        icon="mdi:weather-cloudy",
        name="Cloud cover day",
        entity_registry_enabled_default=False,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data: cast(int, data),
    ),
    NOAAWeatherSensorDescription(
        key="CloudCoverNight",
        icon="mdi:weather-cloudy",
        name="Cloud cover night",
        entity_registry_enabled_default=False,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data: cast(int, data),
    ),
    NOAAWeatherSensorDescription(
        key="HoursOfSun",
        icon="mdi:weather-partly-cloudy",
        name="Hours of sun",
        native_unit_of_measurement=UnitOfTime.HOURS,
        value_fn=lambda data: cast(float, data),
    ),
    NOAAWeatherSensorDescription(
        key="LongPhraseDay",
        name="Condition day",
        value_fn=lambda data: cast(str, data),
    ),
    NOAAWeatherSensorDescription(
        key="LongPhraseNight",
        name="Condition night",
        value_fn=lambda data: cast(str, data),
    ),
    NOAAWeatherSensorDescription(
        key="RealFeelTemperatureMax",
        device_class=SensorDeviceClass.TEMPERATURE,
        name="RealFeel temperature max",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda data: cast(float, data[ATTR_VALUE]),
    ),
    NOAAWeatherSensorDescription(
        key="RealFeelTemperatureMin",
        device_class=SensorDeviceClass.TEMPERATURE,
        name="RealFeel temperature min",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda data: cast(float, data[ATTR_VALUE]),
    ),
    NOAAWeatherSensorDescription(
        key="ThunderstormProbabilityDay",
        icon="mdi:weather-lightning",
        name="Thunderstorm probability day",
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data: cast(int, data),
    ),
    NOAAWeatherSensorDescription(
        key="ThunderstormProbabilityNight",
        icon="mdi:weather-lightning",
        name="Thunderstorm probability night",
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data: cast(int, data),
    ),
    NOAAWeatherSensorDescription(
        key="WindGustDay",
        device_class=SensorDeviceClass.WIND_SPEED,
        name="Wind gust day",
        entity_registry_enabled_default=False,
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        value_fn=lambda data: cast(float, data[ATTR_SPEED][ATTR_VALUE]),
        attr_fn=lambda data: {"direction": data[ATTR_DIRECTION][ATTR_ENGLISH]},
    ),
    NOAAWeatherSensorDescription(
        key="WindGustNight",
        device_class=SensorDeviceClass.WIND_SPEED,
        name="Wind gust night",
        entity_registry_enabled_default=False,
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        value_fn=lambda data: cast(float, data[ATTR_SPEED][ATTR_VALUE]),
        attr_fn=lambda data: {"direction": data[ATTR_DIRECTION][ATTR_ENGLISH]},
    ),
    NOAAWeatherSensorDescription(
        key="WindDay",
        device_class=SensorDeviceClass.WIND_SPEED,
        name="Wind day",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        value_fn=lambda data: cast(float, data[ATTR_SPEED][ATTR_VALUE]),
        attr_fn=lambda data: {"direction": data[ATTR_DIRECTION][ATTR_ENGLISH]},
    ),
    NOAAWeatherSensorDescription(
        key="WindNight",
        device_class=SensorDeviceClass.WIND_SPEED,
        name="Wind night",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        value_fn=lambda data: cast(float, data[ATTR_SPEED][ATTR_VALUE]),
        attr_fn=lambda data: {"direction": data[ATTR_DIRECTION][ATTR_ENGLISH]},
    ),
)

SENSOR_TYPES: tuple[NOAAWeatherSensorDescription, ...] = (
    NOAAWeatherSensorDescription(
        key="ApparentTemperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        name="Apparent temperature",
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda data: cast(float, data[ATTR_VALUE]),
    ),
    NOAAWeatherSensorDescription(
        key="Ceiling",
        device_class=SensorDeviceClass.DISTANCE,
        icon="mdi:weather-fog",
        name="Cloud ceiling",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfLength.METERS,
        value_fn=lambda data: cast(float, data[ATTR_VALUE]),
        suggested_display_precision=0,
    ),
    NOAAWeatherSensorDescription(
        key="CloudCover",
        icon="mdi:weather-cloudy",
        name="Cloud cover",
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data: cast(int, data),
    ),
    NOAAWeatherSensorDescription(
        key="DewPoint",
        device_class=SensorDeviceClass.TEMPERATURE,
        name="Dew point",
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda data: cast(float, data[ATTR_VALUE]),
    ),
    NOAAWeatherSensorDescription(
        key="RealFeelTemperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        name="RealFeel temperature",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda data: cast(float, data[ATTR_VALUE]),
    ),
    NOAAWeatherSensorDescription(
        key="RealFeelTemperatureShade",
        device_class=SensorDeviceClass.TEMPERATURE,
        name="RealFeel temperature shade",
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda data: cast(float, data[ATTR_VALUE]),
    ),
    NOAAWeatherSensorDescription(
        key="Precipitation",
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
        name="Precipitation",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfVolumetricFlux.MILLIMETERS_PER_HOUR,
        value_fn=lambda data: cast(float, data[ATTR_VALUE]),
        attr_fn=lambda data: {"type": data["PrecipitationType"]},
    ),
    NOAAWeatherSensorDescription(
        key="PressureTendency",
        device_class=SensorDeviceClass.ENUM,
        icon="mdi:gauge",
        name="Pressure tendency",
        options=["falling", "rising", "steady"],
        translation_key="pressure_tendency",
        value_fn=lambda data: cast(str, data["LocalizedText"]).lower(),
    ),
    NOAAWeatherSensorDescription(
        key="WindChillTemperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        name="Wind chill temperature",
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda data: cast(float, data[ATTR_VALUE]),
    ),
    NOAAWeatherSensorDescription(
        key="Wind",
        device_class=SensorDeviceClass.WIND_SPEED,
        name="Wind",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        value_fn=lambda data: cast(float, data[ATTR_SPEED][ATTR_VALUE]),
    ),
    NOAAWeatherSensorDescription(
        key="WindGust",
        device_class=SensorDeviceClass.WIND_SPEED,
        name="Wind gust",
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        value_fn=lambda data: cast(float, data[ATTR_SPEED][ATTR_VALUE]),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Add NOAAWeather entities from a config_entry."""
    _LOGGER.info("async_setup_entry() START")
    coordinator: NOAAWeatherDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    sensors = [
        NOAAWeatherSensor(coordinator, description) for description in SENSOR_TYPES
    ]

    if coordinator.forecast:
        # Some air quality/allergy sensors are only available for certain
        # locations.
        # sensors.extend(
        #     NOAAWeatherSensor(coordinator, description, forecast_day=day)
        #     for day in range(MAX_FORECAST_DAYS + 1)
        #     for description in FORECAST_SENSOR_TYPES
        #     if description.key in coordinator.data[ATTR_FORECAST][0]
        # )
        for day in range(MAX_FORECAST_DAYS + 1):
            for description in FORECAST_SENSOR_TYPES:
                _LOGGER.info("Day %d, sensor:%s", day, description)
                if (
                    coordinator.data[ATTR_FORECAST]
                    and description.key in coordinator.data[ATTR_FORECAST][0]
                ):
                    sensors.append(
                        NOAAWeatherSensor(coordinator, description, forecast_day=day)
                    )

    async_add_entities(sensors)
    _LOGGER.info("async_setup_entry() END")


class NOAAWeatherSensor(
    CoordinatorEntity[NOAAWeatherDataUpdateCoordinator], SensorEntity
):
    """Define an NOAAWeather entity."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True
    entity_description: NOAAWeatherSensorDescription

    def __init__(
        self,
        coordinator: NOAAWeatherDataUpdateCoordinator,
        description: NOAAWeatherSensorDescription,
        forecast_day: int | None = None,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self.entity_description = description
        self._sensor_data = _get_sensor_data(
            coordinator.data, description.key, forecast_day
        )
        _LOGGER.info("NOAAWeatherSensor:%s, %s", description, coordinator)
        if forecast_day is not None:
            self._attr_name = f"{description.name} {forecast_day}d"
            self._attr_unique_id = (
                f"{coordinator.location_key}-{description.key}-{forecast_day}".lower()
            )
        else:
            self._attr_unique_id = (
                f"{coordinator.location_key}-{description.key}".lower()
            )
        self._attr_device_info = coordinator.device_info
        self.forecast_day = forecast_day

    @property
    def native_value(self) -> StateType:
        """Return the state."""
        return self.entity_description.value_fn(self._sensor_data)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if self.forecast_day is not None:
            return self.entity_description.attr_fn(self._sensor_data)

        return self.entity_description.attr_fn(self.coordinator.data)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle data update."""
        self._sensor_data = _get_sensor_data(
            self.coordinator.data, self.entity_description.key, self.forecast_day
        )
        self.async_write_ha_state()


def _get_sensor_data(
    sensors: dict[str, Any],
    kind: str,
    forecast_day: int | None = None,
) -> Any:
    """Get sensor data."""
    _LOGGER.info("_get_sensor_data(%s, %s)", kind, forecast_day)
    if forecast_day is not None:
        return sensors[ATTR_FORECAST][forecast_day][kind]

    # if kind == "Precipitation":
    #     return sensors["PrecipitationSummary"]["PastHour"]

    return sensors.get(kind)
