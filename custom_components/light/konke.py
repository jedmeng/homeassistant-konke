"""
Support for the Opple light.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/light.opple/
"""

import logging

import voluptuous as vol

from homeassistant.components.light import (
    ATTR_BRIGHTNESS, ATTR_COLOR_TEMP, ATTR_HS_COLOR, PLATFORM_SCHEMA, SUPPORT_BRIGHTNESS,
    SUPPORT_COLOR, SUPPORT_COLOR_TEMP, Light)
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_MODEL
import homeassistant.helpers.config_validation as cv
from homeassistant.util.color import \
    color_temperature_kelvin_to_mired as kelvin_to_mired
from homeassistant.util.color import \
    color_temperature_mired_to_kelvin as mired_to_kelvin
from homeassistant.util.color import \
    color_hs_to_RGB as hs_to_rgb

REQUIREMENTS = ['pykonkeio=2.0.1b0']

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Konke Light"

MODEL_KLIGHT = 'klight'
MODEL_KBULB = 'kblub'
MODEL_K2_LIGHT = 'k2_light'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONF_MODEL): vol.In([
        MODEL_KLIGHT,
        MODEL_KBULB,
        MODEL_K2_LIGHT]),
})

KBLUB_MIN_KELVIN = 2700
KBLUB_MAX_KELVIN = 6500


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up Konke light platform."""
    name = config[CONF_NAME]
    host = config[CONF_HOST]
    model = config[CONF_MODEL]

    if model == MODEL_KLIGHT:
        from pykonkeio import KLight
        device = KLight(host)
    elif model == MODEL_KBULB:
        from pykonkeio import KBlub
        device = KBlub(host)
    else:
        from pykonkeio import K2
        device = K2(host)

    entity = KonkeLight(name, device, model)
    add_entities([entity])

    _LOGGER.debug("Init %s %s %s", model, host, entity.unique_id)


class KonkeLight(Light):
    """Konke light device."""

    def __init__(self, name, device, model):
        """Initialize an Konke light."""
        self._name = name
        self._model = model
        self._device = device
        self._is_on = None
        self._brightness = None
        self._color_temp = None
        self._color = None

    @property
    def available(self) -> bool:
        """Return True if light is available."""
        return self._device.is_online

    @property
    def unique_id(self) -> str:
        """Return unique ID for light."""
        if self._model == MODEL_K2_LIGHT:
            return self._device.mac + ':light'
        else:
            return self._device.mac

    @property
    def name(self) -> str:
        """Return the display name of this light."""
        return self._name

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        return self._is_on

    @property
    def brightness(self) -> int:
        """Return the brightness of the light."""
        return self._brightness

    @property
    def color_temp(self):
        """Return the color temperature of this light."""
        return kelvin_to_mired(self._color_temp)

    @property
    def min_mireds(self):
        """Return minimum supported color temperature."""
        return kelvin_to_mired(KBLUB_MAX_KELVIN)

    @property
    def max_mireds(self):
        """Return maximum supported color temperature."""
        return kelvin_to_mired(KBLUB_MIN_KELVIN)

    @property
    def supported_features(self):
        """Flag supported features."""
        if self._model == MODEL_KBULB:
            return SUPPORT_BRIGHTNESS | SUPPORT_COLOR_TEMP
        elif self._model == MODEL_KLIGHT:
            return SUPPORT_BRIGHTNESS | SUPPORT_COLOR
        else:
            return 0

    def turn_on(self, **kwargs):
        """Instruct the light to turn on."""
        _LOGGER.debug("Turn on light %s %s", self._device.ip, kwargs)
        if not self.is_on:
            self._device.turn_on()

        if ATTR_BRIGHTNESS in kwargs and \
                self.brightness != kwargs[ATTR_BRIGHTNESS]:
            self._device.set_brightness(kwargs[ATTR_BRIGHTNESS])

        if ATTR_COLOR_TEMP in kwargs and \
                self.color_temp != kwargs[ATTR_COLOR_TEMP]:
            self._device.set_ct(mired_to_kelvin(kwargs[ATTR_COLOR_TEMP]))

        if ATTR_HS_COLOR in kwargs and \
                self._color != kwargs[ATTR_HS_COLOR]:
            hs_color = kwargs[ATTR_HS_COLOR]
            rgb_color = hs_to_rgb(*hs_color)
            self._device.set_color(*rgb_color)

    def turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        self._device.turn_off()
        _LOGGER.debug("Turn off light %s", self._device.ip)

    def update(self):
        """Synchronize state with light."""
        prev_available = self.available
        self._device.update()

        if prev_available == self.available and \
                self._is_on == self._device.power_on and \
                self._brightness == self._device.brightness and \
                self._color_temp == self._device.color_temperature and \
                self._color == self._device.color:
            return

        if not self.available:
            _LOGGER.debug("Light %s is offline", self._device.ip)
            return

        self._is_on = self._device.power_on
        self._brightness = self._device.brightness
        self._color_temp = self._device.color_temperature
        self._color = self._device.color

        if not self.is_on:
            _LOGGER.debug("Update light %s success: power off",
                          self._device.ip)
        elif self._model == MODEL_KLIGHT:
            _LOGGER.debug("Update light %s success: power on brightness %s "
                          "color %s,%s,%s",
                          self._device.ip, self._brightness, *self._color)
        elif self._model == MODEL_KBULB:
            _LOGGER.debug("Update light %s success: power on brightness %s "
                          "color temperature %s",
                          self._device.ip, self._brightness, self._color_temp)
