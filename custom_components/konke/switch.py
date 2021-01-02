"""
Support for the Konke outlet.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/light.opple/
"""

import logging
import time

import voluptuous as vol

from homeassistant.components.switch import SwitchDevice, PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME, CONF_HOST
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['pykonkeio>=2.1.7']

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'Konke Outlet'

CONF_MODEL = 'model'
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


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    from pykonkeio.manager import get_device
    from pykonkeio.error import DeviceNotSupport
    name = config[CONF_NAME]
    host = config[CONF_HOST]
    model = config[CONF_MODEL].lower()
    entities = []

    try:
        device = get_device(host, model)
    except DeviceNotSupport:
        _LOGGER.error(
            'Unsupported device found! Please create an issue at '
            'https://github.com/jedmeng/python-konkeio/issues '
            'and provide the following data: %s', model)
        return False

    if hasattr(device, 'socket_count'):
        powerstrip = KonkePowerStrip(device, name)
        for i in range(device.socket_count):
            entities.append(KonkePowerStripOutlet(powerstrip, name, i))

        for i in range(device.usb_count or 0):
            entities.append(KonkePowerStripUSB(powerstrip, name, i))
    else:
        entities.append(KonkeOutlet(name, device, model))
        if hasattr(device, 'usb_status'):
            entities.append(KonkeUsbSwitch(name, device))

    async_add_entities(entities)


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
        return self._device.is_online

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

    @property
    def current_power_w(self):
        """Return the current power usage in W."""
        return self._current_power_w

    async def async_turn_on(self, **kwargs):
        """Instruct the outlet to turn on."""
        await self._device.turn_on()
        _LOGGER.debug("Turn on outlet %s", self.unique_id)

    async def async_turn_off(self, **kwargs):
        """Instruct the outlet to turn off."""
        await self._device.turn_off()
        _LOGGER.debug("Turn off outlet %s", self.unique_id)

    async def async_update(self):
        """Synchronize state with outlet."""
        from pykonkeio.error import DeviceOffline
        prev_available = self.available
        try:
            await self._device.update(type='relay')

            if self._model in MODEL_K2:
                self._current_power_w = await self._device.get_power()
        except DeviceOffline:
            if prev_available:
                _LOGGER.warning('Device is offline %s', self.entity_id)


class KonkeUsbSwitch(SwitchDevice):
    def __init__(self, name, device):
        self._name = name
        self._device = device

    @property
    def should_poll(self) -> bool:
        """Poll the plug."""
        return True

    @property
    def available(self) -> bool:
        """Return True if outlet is available."""
        return self._device.is_online

    @property
    def unique_id(self):
        """Return unique ID for light."""
        return '%s:usb' % self._device.mac

    @property
    def name(self):
        """Return the display name of this outlet."""
        return '%s_usb' % self._name

    @property
    def is_on(self):
        """Instruct the outlet to turn on."""
        return self._device.usb_status == 'open'

    async def async_turn_on(self, **kwargs):
        """Instruct the outlet to turn on."""
        await self._device.turn_on_usb()
        _LOGGER.debug("Turn on usb %s", self.unique_id)

    async def async_turn_off(self, **kwargs):
        """Instruct the outlet to turn off."""
        await self._device.turn_off_usb()
        _LOGGER.debug("Turn off usb %s", self.unique_id)

    async def async_update(self):
        """Synchronize state with outlet."""
        from pykonkeio.error import DeviceOffline
        prev_available = self.available
        try:
            await self._device.update(type='usb')
        except DeviceOffline:
            if prev_available:
                _LOGGER.warning('Device is offline %s', self.entity_id)



class KonkePowerStrip(object):

    def __init__(self, device, name: str):
        """Initialize the power strip."""
        self._name = name
        self._device = device
        self._last_update = 0

    @property
    def available(self) -> bool:
        """Return True if outlet is available."""
        return self._device.is_online

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
        return self._device.status[index] == 'open'

    def get_usb_status(self, index):
        """Return true if usb is on."""
        return self._device.usb_status[index] == 'open'

    async def async_turn_on(self, index):
        """Instruct the outlet to turn on."""
        await self._device.turn_on(index)

    async def async_turn_off(self, index):
        """Instruct the outlet to turn off."""
        await self._device.turn_off(index)

    async def async_turn_on_usb(self, index):
        """Instruct the usb to turn on."""
        await self._device.turn_on_usb(index)

    async def async_turn_off_usb(self, index):
        """Instruct the outlet to turn off."""
        await self._device.turn_off_usb(index)

    async def async_update(self):
        """Synchronize state with power strip."""
        from pykonkeio.error import DeviceOffline
        prev_available = self.available
        if time.time() - self._last_update >= UPDATE_DEBONCE:
            self._last_update = time.time()
            try:
                await self._device.update()
            except DeviceOffline:
                if prev_available:
                    _LOGGER.warning('Device is offline %s', self.unique_id)


class KonkePowerStripOutlet(SwitchDevice):
    """Outlet in Konke Power Strip."""

    def __init__(self, powerstrip: KonkePowerStrip, name: str, index: int):
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
        return self._powerstrip.available

    @property
    def unique_id(self):
        """Return unique ID for outlet."""
        return "%s:%s" % (self._powerstrip.unique_id, self._index + 1)

    @property
    def name(self):
        """Return the display name of this outlet."""
        return '%s_%s' % (self._name, self._index + 1)

    @property
    def is_on(self):
        """Return true if outlet is on."""
        return self._powerstrip.get_status(self._index)

    async def async_turn_on(self, **kwargs):
        """Instruct the outlet to turn on."""
        await self._powerstrip.async_turn_on(self._index)
        _LOGGER.debug("Turn on outlet %s", self.unique_id)

    async def async_turn_off(self, **kwargs):
        """Instruct the outlet to turn off."""
        await self._powerstrip.async_turn_off(self._index)
        _LOGGER.debug("Turn off outlet %s", self.unique_id)

    async def async_update(self):
        """Synchronize state with power strip."""
        await self._powerstrip.async_update()


class KonkePowerStripUSB(SwitchDevice):
    """Outlet in Konke Power Strip."""

    def __init__(self, powerstrip: KonkePowerStrip, name: str, index: int):
        """Initialize the outlet."""
        self._powerstrip = powerstrip
        self._index = index
        self._name = name

    @property
    def should_poll(self) -> bool:
        """Poll the plug."""
        return True

    @property
    def available(self) -> bool:
        """Return True if outlet is available."""
        return self._powerstrip.available

    @property
    def unique_id(self):
        """Return unique ID for outlet."""
        return "%s:usb_%s" % (self._powerstrip.unique_id, self._index + 1)

    @property
    def name(self):
        """Return the display name of this outlet."""
        return '%s_usb%s' % (self._name, self._index + 1)

    @property
    def is_on(self):
        """Return true if outlet is on."""
        return self._powerstrip.get_usb_status(self._index)

    async def async_turn_on(self, **kwargs):
        """Instruct the outlet to turn on."""
        await self._powerstrip.async_turn_on_usb(self._index)
        _LOGGER.debug("Turn on outlet %s", self.unique_id)

    async def async_turn_off(self, **kwargs):
        """Instruct the outlet to turn off."""
        await self._powerstrip.async_turn_off_usb(self._index)
        _LOGGER.debug("Turn off outlet %s", self.unique_id)

    async def async_update(self):
        """Synchronize state with power strip."""
        await self._powerstrip.async_update()
