"""
Support for the Konke Remote Device(K2 with IR/RF module or MiniK Pro).

For more details about this platform, please refer to the documentation
https://home-assistant.io/components/remote.xiaomi_miio/
"""
import asyncio
import logging

import voluptuous as vol

from homeassistant.components.remote import (
    PLATFORM_SCHEMA, DOMAIN, ATTR_NUM_REPEATS, ATTR_DELAY_SECS,
    DEFAULT_DELAY_SECS, RemoteDevice)
from homeassistant.const import (
    CONF_NAME, CONF_HOST, CONF_TIMEOUT, CONF_TYPE,
    ATTR_ENTITY_ID, CONF_COMMAND)
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['pykonkeio>=2.1.7']

_LOGGER = logging.getLogger(__name__)

SERVICE_IR_LEARN = 'koneke_ir_learn'
SERVICE_RF_LEARN = 'koneke_rf_learn'
DATA_KEY = 'remote.konke_remote'
SOLT_RANGE = {"min": 1000, "max": 999999}

CONF_HIDDEN = 'hidden'
CONF_MODEL = 'model'
CONF_SLOT = 'slot'
MODEL_K2 = ['k2', 'k2 pro']
MODEL_MINIK = ['minik', 'minik pro']
TYPE_IR = 'ir'
TYPE_RF = 'rf'

DEFAULT_NAME = 'konke_remote'
DEFAULT_TIMEOUT = 10
DEFAULT_SLOT = 1001

ENTITIES = []

LEARN_COMMAND_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): vol.All(str),
    vol.Required(CONF_SLOT): vol.All(int, vol.Range(**SOLT_RANGE)),
    vol.Optional(CONF_TIMEOUT, default=10): vol.All(int, vol.Range(min=0)),
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_TYPE, default=TYPE_IR): vol.In((TYPE_IR, TYPE_RF)),
    vol.Optional(CONF_HIDDEN, default=True): cv.boolean,
    vol.Required(CONF_MODEL): vol.In(MODEL_K2 + MODEL_MINIK),
}, extra=vol.ALLOW_EXTRA)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Konke Remote platform."""
    from pykonkeio.manager import get_device

    name = config[CONF_NAME]
    host = config[CONF_HOST]
    model = config[CONF_MODEL]
    hidden = config[CONF_HIDDEN]
    remote_type = config[CONF_TYPE]

    entity = KonkeRemote(get_device(host, model), name, remote_type, hidden)
    async_add_entities([entity])

    ENTITIES.append(entity)

    async def async_service_handler(service):
        """Handle a learn command."""
        if service.service not in (SERVICE_IR_LEARN, SERVICE_RF_LEARN):
            _LOGGER.error("We should not handle service: %s", service.service)
            return

        entity_id = service.data[ATTR_ENTITY_ID]

        entities = [_entity for _entity in ENTITIES if _entity.entity_id in entity_id]

        if len(entities) == 0:
            _LOGGER.error("Entity_id: '%s' not found", entity_id)
            return

        slot = service.data.get(CONF_SLOT)
        timeout = service.data.get(CONF_TIMEOUT)

        log_title = 'Konke %s Remote' % entity.type
        log_message = 'Start learning %s remote, please press any key you want to learn on the remote.' % entity.type
        hass.components.persistent_notification.async_create(log_message, log_title, notification_id=entity_id)

        _LOGGER.debug('Start learning %s remote on slot %s: %s', entity.type, slot, entity_id)

        result = await hass.async_add_job(entity.async_learn, slot, timeout)

        if result:
            log_message = 'Learn %s remote success on slot %s' % (entity.type, slot)
            hass.components.persistent_notification.async_create(log_message, log_title, notification_id=entity_id)
            _LOGGER.debug('Learn %s remote success on slot %s: %s', entity.type, slot, entity_id)
        else:
            log_message = 'Learn %s remote failed on slot %s' % (entity.type, slot)
            hass.components.persistent_notification.async_create(log_message, log_title, notification_id=entity_id)
            _LOGGER.debug('Learn %s remote failed on slot %s: %s', entity.type, slot, entity_id)

    if remote_type == TYPE_IR:
        hass.services.async_register(DOMAIN, SERVICE_IR_LEARN, async_service_handler, schema=LEARN_COMMAND_SCHEMA)
    elif remote_type == TYPE_RF:
        hass.services.async_register(DOMAIN, SERVICE_RF_LEARN, async_service_handler, schema=LEARN_COMMAND_SCHEMA)


class KonkeRemote(RemoteDevice):
    """Representation of a Xiaomi Miio Remote device."""

    def __init__(self, device, name, remote_type, hidden):
        """Initialize the remote."""
        self._name = name
        self._device = device
        self._is_hidden = hidden
        self._type = remote_type
        self._state = False

    @property
    def unique_id(self) -> str:
        """Return an unique ID."""
        return '%s:%s' % (self._device.mac, self.type)

    @property
    def name(self) -> str:
        """Return the name of the remote."""
        return self._name

    @property
    def type(self) -> str:
        """Return the name of the remote."""
        return self._type.upper()

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not self._device.is_online:
            return False
        if self._type == TYPE_IR:
            return self._device.is_support_ir
        elif self._type == TYPE_RF:
            return self._device.is_support_rf
        else:
            return False

    @property
    def is_on(self) -> bool:
        """Return False if device is unreachable, else True."""
        return self._device.is_online

    @property
    def hidden(self) -> bool:
        """Return if we should hide entity."""
        return self._is_hidden

    @asyncio.coroutine
    def async_turn_on(self, **kwargs) -> None:
        """Turn the device on."""
        _LOGGER.error("Device does not support turn_on, "
                      "please use 'remote.send_command' to send commands.")

    @asyncio.coroutine
    def async_turn_off(self, **kwargs) -> None:
        """Turn the device off."""
        _LOGGER.error("Device does not support turn_off, "
                      "please use 'remote.send_command' to send commands.")

    async def async_update(self):
        from pykonkeio.error import DeviceOffline
        prev_available = self.available
        try:
            await self._device.update()
        except DeviceOffline:
            if prev_available:
                _LOGGER.warning('Device is offline %s', self.unique_id)

    async def _do_send_command(self, command):
        """Send a command."""
        try:
            command_type, slot = command.split('_')
        except ValueError:
            _LOGGER.warning("Illegal command format: %s", command)
            return False

        if self._type != command_type:
            _LOGGER.warning("Illegal command type: %s", command)
            return False
        if self._type == TYPE_IR:
            return await self._device.ir_emit(slot)
        elif self._type == TYPE_RF:
            return await self._device.rf_emit(slot)

    async def async_send_command(self, command, **kwargs) -> None:
        """Send a command."""
        num_repeats = kwargs.get(ATTR_NUM_REPEATS)
        delay = kwargs.get(ATTR_DELAY_SECS, DEFAULT_DELAY_SECS)

        for _ in range(num_repeats):
            for item in command:
                await self._do_send_command(item)
                await asyncio.sleep(delay)

    async def async_learn(self, command, timeout=DEFAULT_TIMEOUT) -> bool:
        """Learn a command."""
        if self._type == TYPE_IR:
            return await self._device.ir_learn(command, timeout=timeout)
        elif self._type == TYPE_RF:
            return await self._device.rf_learn(command, timeout=timeout)
