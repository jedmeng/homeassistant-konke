[Home Assistant](https://www.home-assistant.io/) component of [Konke](http://www.ikonke.com/) devices

# Supported Devices

## switch
- K1(Smart Plug K) [k1]
- K2 [k2]
- K2 Pro [k2]
- Mini K [minik]
- Mini Pro [minik]

## light
- RGB Light [klight]
- CCT Light [kbulb]

## power strip
- power strip with 4 socket and 3 usb [micmul]
- power strip with 3 socket and 4 usb [mul]

## remote
- K2 with IR module or RF module [k2]
- MiniK Pro [minik]

# Install
copy the `custom_components` to your home-assistant config directory.

# config

## switch and poer strip
Add the following to your configuration.yaml file:
```yaml
switch:
  - platform: konke
    name: switch_1
    model: k2
    host: 192.168.0.101
  - platform: konke
    name: switch_2
    model: minik
    host: 192.168.0.102
  - platform: konke
    name: power strip
    model: mic
    host: 192.168.0.111
```

CONFIGURATION VARIABLES:

- name
  (string)(Optional)The display name of the device.

- host
  (string)(Required)The host/IP address of the device.

- device
  (string)(Required)Model String(string in square brackets) of equipment.

## light
Add the following to your configuration.yaml file:
```yaml
light:
  - platform: konke
    name: bedroom light
    model: klight
    host: 192.168.0.121
  - platform: konke
    name: kitchen light
    model: kbulb
    host: 192.168.0.122
```

CONFIGURATION VARIABLES:

- name
  (string)(Optional)The display name of the device.

- host
  (string)(Required)The host/IP address of the device.

- device
  (string)(Required)Model String(string in square brackets) of equipment.


## remote
Add the following to your configuration.yaml file:
```yaml
remote:
  - platform: konke
    name: rf remote
    model: k2
    host: 192.168.0.101
    hidden: true
    type: rf
  - platform: konke
    name: ir remote 
    model: minik
    host: 192.168.0.102
    hidden: false
    type: ir
```

CONFIGURATION VARIABLES:

- name
  (string)(Optional)The display name of the device

- host
  (string)(Required)The host/IP address of the device.

- device
  (string)(Required)Model String(string in square brackets) of equipment.

- hidden
  (bool)(Optional, default true)Whether to hide the equipment in the dashboard.

- type
  (string)(Required)Remote control type: ir or rf