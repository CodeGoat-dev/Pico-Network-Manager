# Goat - Pico Network Manager Version History

This document outlines the changes made between versions of the **Goat - Pico Network Manager** library.

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
