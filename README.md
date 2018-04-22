[Home Assistant](https://www.home-assistant.io/) component of [Konke](http://www.ikonke.com/) devices

# Supported Devices

- Mini K

![Mini K](http://www.ikonke.com/pro/miniK/images/minik_img1.png)
- Mini Pro

![Mini Pro](https://img.alicdn.com/imgextra/i2/2259671767/TB2ZgLZi4rI8KJjy0FpXXb5hVXa_!!2259671767.jpg_430x430q90.jpg)
- Smart Plug K(untested)

![K](https://gd4.alicdn.com/imgextra/i4/322866315/TB2KOYpbgMPMeJjy1XcXXXpppXa_!!322866315.jpg_400x400.jpg_.webp)
- K2 Pro(untested)

![K2](https://img.alicdn.com/imgextra/i4/2259671767/TB2THHQtXXXXXcoXpXXXXXXXXXX_!!2259671767.jpg_430x430q90.jpg)

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