"""
Support for the Konke outlet.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/light.opple/
"""

import logging
import time

import voluptuous as vol

from homeassistant.components.switch import SwitchDevice, PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME, CONF_HOST, CONF_MODEL
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['pykonkeio=2.0.1b0']

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'Konke Outlet'

MODEL_K1 = ['smart plugin', 'k1']
MODEL_K2 = ['k2', 'k2 pro']
MODEL_MINIK = ['minik', 'minik pro']
MODEL_MUL = ['mul']
MODEL_MICMUL = ['micmul']

MODEL_SWITCH = MODEL_K1 + MODEL_K2 + MODEL_MINIK
MODEL_POWER_STRIP = MODEL_MUL + MODEL_MICMUL

UPDATE_DEBONCE = 0.3

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_MODEL): vol.In(MODEL_SWITCH + MODEL_POWER_STRIP)
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    name = config[CONF_NAME]
    host = config[CONF_HOST]
    model = config[CONF_MODEL]
    entities = []

    if model in MODEL_POWER_STRIP:
        if model in MODEL_MUL:
            from pykonkeio.device import Mul
            device = Mul(host)
        elif model.lower() in MODEL_MICMUL:
            from pykonkeio.device import MicMul
            device = MicMul(host)
        else:
            return False

        for i in range(device.socket_count):
            entities.append(KonkePowerStripOutlet(device, name, i))  # @fixme
    else:
        if model is None:
            from pykonkeio.device import BaseToggle
            device = BaseToggle(host)
        elif model.lower() in MODEL_K1:
            from pykonkeio.device import K1
            device = K1(host)
        elif model in MODEL_K2:
            from pykonkeio.device import K2
            device = K2(host)
        elif model in MODEL_MINIK:
            from pykonkeio.device import MiniK
            device = MiniK(host)
        else:
            _LOGGER.error(
                'Unsupported device found! Please create an issue at '
                'https://github.com/jedmeng/python-konkeio/issues '
                'and provide the following data: %s', model)
            return False
        entities.append(KonkeOutlet(name, device, model))
    add_devices(entities)


class KonkeOutlet(SwitchDevice):

    def __init__(self, name, device, model=None):
        self._name = name
        self._device = device
        self._model = model
        self._current_power_w = None

    @property
    def should_poll(self) -> bool:
        """Poll the plug."""
        return True

    @property
    def available(self) -> bool:
        """Return True if outlet is available."""
        return self._device.online

    @property
    def unique_id(self):
        """Return unique ID for light."""
        return self._device.mac

    @property
    def name(self):
        """Return the display name of this outlet."""
        return self._name

    @property
    def is_on(self):
        """Instruct the outlet to turn on."""
        return self._device.status == 'open'

    def turn_on(self, **kwargs):
        """Instruct the outlet to turn on."""
        self._device.turn_on()
        _LOGGER.debug("Turn on outlet %s", self.unique_id)

    def turn_off(self, **kwargs):
        """Instruct the outlet to turn off."""
        self._device.turn_off()
        _LOGGER.debug("Turn off outlet %s", self.unique_id)

    def update(self):
        """Synchronize state with outlet."""
        self._device.update()

        if self._model in MODEL_K2:
            self._current_power_w = self._device.get_power()


class KonkePowerStrip(object):

    def __init__(self, name, device):
        """Initialize the power strip."""
        self._name = name
        self._device = device
        self._last_update = 0

    @property
    def available(self) -> bool:
        """Return True if outlet is available."""
        return self._device.available

    @property
    def unique_id(self):
        """Return unique ID for outlet."""
        return self._device.mac

    @property
    def name(self):
        """Return the display name of this outlet."""
        return self._name

    def get_status(self, index):
        """Return true if outlet is on."""
        return self._device.status[index]

    def turn_on(self, index):
        """Instruct the outlet to turn on."""
        self._device.turn_on(index)

    def turn_off(self, index):
        """Instruct the outlet to turn off."""
        self._device.turn_off(index)

    def update(self):
        """Synchronize state with power strip."""
        if time.time() - self._last_update >= UPDATE_DEBONCE:
            self._device.update()
            self._last_update = time.time()


class KonkePowerStripOutlet(SwitchDevice):
    """Outlet in Konke Power Strip."""

    def __init__(self, powerstrip, name, index):
        """Initialize the outlet."""
        self._powerstrip = powerstrip
        self._index = index
        self._name = name
        self._is_on = False

    @property
    def should_poll(self) -> bool:
        """Poll the plug."""
        return True

    @property
    def available(self) -> bool:
        """Return True if outlet is available."""
        return self._powerstrip.online

    @property
    def unique_id(self):
        """Return unique ID for outlet."""
        return "%s:%s" % (self._powerstrip.unique_id, self._index)

    @property
    def name(self):
        """Return the display name of this outlet."""
        return self._name

    @property
    def is_on(self):
        """Return true if outlet is on."""
        return self._powerstrip.get_status(self._index)

    def turn_on(self, **kwargs):
        """Instruct the outlet to turn on."""
        self._powerstrip.turn_on(self._index)
        _LOGGER.debug("Turn on outlet %s", self.unique_id)

    def turn_off(self, **kwargs):
        """Instruct the outlet to turn off."""
        self._powerstrip.turn_off(self._index)
        _LOGGER.debug("Turn off outlet %s", self.unique_id)

    def update(self):
        """Synchronize state with power strip."""
        self._powerstrip.update()


