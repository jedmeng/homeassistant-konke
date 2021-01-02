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
from homeassistant.const import CONF_HOST, CONF_NAME
import homeassistant.helpers.config_validation as cv
from homeassistant.util.color import \
    color_temperature_kelvin_to_mired as kelvin_to_mired
from homeassistant.util.color import \
    color_temperature_mired_to_kelvin as mired_to_kelvin
from homeassistant.util.color import \
    color_hs_to_RGB as hs_to_RGB
from homeassistant.util.color import \
    color_RGB_to_hs as RGB_to_hs

REQUIREMENTS = ['pykonkeio>=2.1.7']

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Konke Light"

CONF_MODEL = 'model'
MODEL_KLIGHT = 'klight'
MODEL_KBULB = 'kbulb'
MODEL_K2_LIGHT = 'k2_light'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONF_MODEL): vol.In((
        MODEL_KLIGHT,
        MODEL_KBULB,
        MODEL_K2_LIGHT)),
})

KBLUB_MIN_KELVIN = 2700
KBLUB_MAX_KELVIN = 6493


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up Konke light platform."""
    name = config[CONF_NAME]
    host = config[CONF_HOST]
    model = config[CONF_MODEL].lower()

    if model == MODEL_KLIGHT:
        from pykonkeio.device import KLight
        device = KLight(host)
    elif model == MODEL_KBULB:
        from pykonkeio.device import KBulb
        device = KBulb(host)
    else:
        from pykonkeio.device import K2
        device = K2(host)

    entity = KonkeLight(device, name, model)
    async_add_entities([entity])

    _LOGGER.debug("Init %s %s %s", model, host, entity.unique_id)


class KonkeLight(Light):
    """Konke light device."""

    def __init__(self, device, name: str, model: str):
        """Initialize an Konke light."""
        self._name = name
        self._model = model
        self._device = device

    @property
    def available(self) -> bool:
        """Return True if light is available."""
        return self._device.is_online

    @property
    def unique_id(self) -> str:
        """Return unique ID for light."""
        if self._device.mac and self._model == MODEL_K2_LIGHT:
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
        if self._model == MODEL_K2_LIGHT:
            return self._device.light_status == 'open'
        else:
            return self._device.status == 'open'

    @property
    def brightness(self) -> int:
        """Return the brightness of the light."""
        return self._device.brightness / 100 * 255

    @property
    def hs_color(self):
        """Return the hs color value."""
        return RGB_to_hs(*self._device.color)

    @property
    def color_temp(self) -> float:
        """Return the color temperature of this light."""
        return kelvin_to_mired(self._device.ct)

    @property
    def min_mireds(self) -> float:
        """Return minimum supported color temperature."""
        return kelvin_to_mired(KBLUB_MAX_KELVIN)

    @property
    def max_mireds(self) -> float:
        """Return maximum supported color temperature."""
        return kelvin_to_mired(KBLUB_MIN_KELVIN)

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        if self._model == MODEL_KBULB:
            return SUPPORT_BRIGHTNESS | SUPPORT_COLOR_TEMP
        elif self._model == MODEL_KLIGHT:
            return SUPPORT_BRIGHTNESS | SUPPORT_COLOR
        else:
            return 0

    async def async_turn_on(self, **kwargs) -> None:
        """Instruct the light to turn on."""
        _LOGGER.debug("Turn on light %s %s", self._device.ip, kwargs)
        if not self.is_on:
            if self._model == MODEL_K2_LIGHT:
                await self._device.turn_on_light()
            else:
                await self._device.turn_on()

        if ATTR_BRIGHTNESS in kwargs and \
                self.brightness != kwargs[ATTR_BRIGHTNESS]:
            await self._device.set_brightness(int(round(kwargs[ATTR_BRIGHTNESS] * 100 / 255)))

        if ATTR_COLOR_TEMP in kwargs and \
                self.color_temp != kwargs[ATTR_COLOR_TEMP]:
            await self._device.set_ct(mired_to_kelvin(kwargs[ATTR_COLOR_TEMP]))

        if ATTR_HS_COLOR in kwargs and \
                self.hs_color != kwargs[ATTR_HS_COLOR]:
            hs_color = kwargs[ATTR_HS_COLOR]
            rgb_color = hs_to_RGB(*hs_color)
            await self._device.set_color(*rgb_color)

    async def async_turn_off(self, **kwargs) -> None:
        """Instruct the light to turn off."""

        if self._model == MODEL_K2_LIGHT:
            await self._device.turn_off_light()
        else:
            await self._device.turn_off()
        _LOGGER.debug("Turn off light %s", self._device.ip)

    async def async_update(self) -> None:
        """Synchronize state with light."""
        from pykonkeio.error import DeviceOffline
        prev_available = self.available
        try:
            await self._device.update(type='light')
        except DeviceOffline:
            if prev_available:
                _LOGGER.warning('Device is offline %s', self.entity_id)

