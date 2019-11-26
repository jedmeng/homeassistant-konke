
修改原插件为新版本Home Assistant支持，目前测试支持0.103版本。

[Home Assistant](https://www.home-assistant.io/) component of [Konke](http://www.ikonke.com/) devices

# Supported Devices

- Mini K

![Mini K](https://p5.ssl.qhimg.com/dm/300_300_/t01763cbb0d461968a5.png)
- Mini Pro

![Mini Pro](https://p2.ssl.qhimg.com/dm/300_300_/t01da45d0484178dfab.jpg)
- Smart Plug K(untested)

![K](https://p1.ssl.qhimg.com/dm/300_300_/t016c9c239d8d71fb78.jpg)
- K2 Pro(untested)

![K2](https://p1.ssl.qhimg.com/dm/300_300_/t019a7103eb99573480.jpg)

- (cnct) intelliPLUG (Mini K us version, untested)

![intelliPLUG](https://p5.ssl.qhimg.com/dm/300_300_/t0166baaec86aa83a4b.jpg)

# Install
copy the `custom_components` to your home-assistant config directory.

# config
Add the following to your configuration.yaml file:
```yaml
switch:
  - platform: konke
    name: switch_1
    host: 192.168.0.101
  - platform: konke
    name: switch_2
    host: 192.168.0.102
```

CONFIGURATION VARIABLES:

- name
  (string)(Optional)The display name of the device

- host
  (string)(Required)The host/IP address of the device.
