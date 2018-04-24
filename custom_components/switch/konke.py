import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.switch import SwitchDevice, PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME, CONF_HOST

platformVersion = "1.0.0"

REQUIREMENTS = ['pykonkeio']

DEFAULT_NAME = '__KONKE_SWITCH__'
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    name = config.get('name')
    host = config.get('host')
    add_devices([KonkeSwitch(name, host)])


class KonkeSwitch(SwitchDevice):

    def __init__(self, name, ip):
        from pykonkeio import Switch
        self._name = name if name != DEFAULT_NAME else 'kongke_switch_%s' % ip

        self.device = Switch(ip)

    @property
    def name(self):
        return self._name

    @property
    def available(self) -> bool:
        return self.device.online

    @property
    def should_poll(self):
        return True

    @property
    def is_on(self):
        return self.device.status == 'open'

    def update(self):
        self.device.update()

    def turn_on(self, **kwargs):
        result = self.device.turn_on()
        if result:
            self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        result = self.device.turn_off()
        if result:
            self.schedule_update_ha_state()

