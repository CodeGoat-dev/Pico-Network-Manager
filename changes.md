# Goat - Pico Network Manager Version History

This document outlines the changes made between versions of the **Goat - Pico Network Manager** library.

## V1.1.6

### Changes

#### Time Synchronisation

The virtual RTC is now re-used when synchronising the time to improve resource usage.

## V1.1.5

### Bug Fixes

#### Time Synchronisation

Fixes an issue creating the time synchronisation task due to a missing class inheritance.

## V1.1.4

### Changes

#### Instantiation

The `time_sync_interval` class instantiation property can now be used to set the time synchronisation interval.

#### Time Synchronisation

Time synchronisation is now performed periodically. By default, the synchronisation interval is 360 minutes or 6 hours.

## V1.1.3

### Bug Fixes

#### Time Synchronisation

Fixed an issue where the system time would not be set after creating the virtual RTC.

## V1.1.2

### Changes

#### Execution

Improves execution by implementing CPU clock gating.

## V1.1.1

### Bug Fixes

#### Time Synchronisation

Fixes an issue where the time might not always be synchronised correctly. The internal RTC module is now used to set the date and time.

## V1.1.0

## New Features

#### Time Synchronisation API

The **Time Synchronisation API** is now included as a NodeJS application. This enables users to host their own local Time Synchronisation API.

### changes

#### Instantiation

The `time_server` class instantiation property can now be used to set the time synchronisation server. Only use this if you are self-hosting the **Time Synchronisation API**.

## V1.0.4

### Changes

#### Date And Time Synchronisation

Date and time synchronisation now uses a new internal API to improve reliability.

## V1.0.3

### New Features

#### Instantiation

When instantiating the `NetworkManager` class, you can now specify a `time_sync` Boolean property to enable/disable time synchronisation.

#### Date And Time Synchronisation

When connected to a wireless network, the system date and time can now be synchronised from a well known NTP time provider. The **World Time API** is used for date and time retrieval.

### Bug Fixes

#### Captive Portal

Fixes an issue re-initializing the station web server when reconnecting to a network via the captive portal.

## V1.0.2

### New Features

#### Instantiation

When instantiating the `NetworkManager` class, you can now specify an `ap_dns_server` Boolean property to enable/disable access point DNS redirection.

### Changes

#### Initialization

Network interfaces are now prepared by de-initializing during class initialization.

## V1.0.1

### Changes

#### Captive Portal

Added a link to the Pico Network Manager GitHub repository to the captive portal.

## V1.0.0

Initial release.
