# Goat - Pico Network Manager library
# Version 1.1.6
# © (c) 2024-2025 Goat Technologies
# Description:
# Provides network management for your device firmware.
# Designed for the Raspberry Pi Pico W microcontroller.
# Responsible for maintaining network state and managing connection lifetime.
# Includes access point mode with a captive portal as well as station mode.
# Includes automatic network reconnection and access point fallback.
# Includes DNS redirection for captive portal compliance.

# Imports
import machine
import network
import socket
import time
import uasyncio as asyncio
import uos
import urequests
import utime
from ConfigManager import ConfigManager

# NetworkManager class
class NetworkManager:
    """Provides network management for device firmware.
    Responsible for maintaining network state and managing connection lifetime.
    """
    # Class constructor
    def __init__(self, ap_ssid="Goat - Captive Portal", ap_password="password", ap_dns_server=True, hostname="PicoW", time_sync=True, time_server="https://goatbot.org", time_sync_interval=360, sta_web_server=None):
        """Constructs the class and exposes properties."""
        # Network configuration
        self.config_directory = "/config"
        self.config_file = "network_config.conf"

        # Constants
        self.VERSION = "1.1.6"
        self.repo_url = "https://github.com/CodeGoat-dev/Pico-Network-Manager"

        # Interface configuration
        self.sta_if = network.WLAN(network.STA_IF)
        self.ap_if = network.WLAN(network.AP_IF)
        self.ip_address = None
        self.server = None

        # Access point settings
        self.ap_ssid = ap_ssid
        self.ap_password = ap_password
        self.ap_dns_server = ap_dns_server
        self.captive_portal_http_port = 80
        self.network_connection_timeout = 10

        # Access point IP settings
        self.ap_ip_address = "192.168.4.1"
        self.ap_subnet = "255.255.255.0"
        self.ap_gateway = "192.168.4.1"
        self.ap_dns = "192.168.4.1"

        # DHCP settings
        self.hostname = hostname

        # Captive portal DNS server
        self.dns_server = NetworkManagerDNS(portal_ip=self.ap_ip_address)

        # Time synchronisation settings
        self.time_sync = time_sync
        self.time_server = time_server
        self.time_sync_interval = time_sync_interval

        # STA web server configuration
        self.sta_web_server = sta_web_server

        # RTC clock
        self.rtc = None

    async def load_config(self):
        """Loads saved network configuration and connects to a saved network."""
        try:
            if self.config_file in uos.listdir(self.config_directory):
                config = ConfigManager(self.config_directory, self.config_file)
                await config.read_async()

                ssid = config.get_entry("network", "ssid")
                password = config.get_entry("network", "password")

                if not ssid:
                    print("No SSID provided in configuration. Cannot connect to a network.")
                    return

                attempts = 0

                while attempts < 3:
                    self.sta_if.active(True)
                    self.sta_if.connect(ssid, password)
                    print(f"Attempting to connect to {ssid}...")

                    timeout = utime.time() + self.network_connection_timeout
                    while not self.sta_if.isconnected() and utime.time() < timeout:
                        utime.sleep(0.5)

                    if self.sta_if.isconnected():
                        self.ip_address = self.sta_if.ifconfig()[0]
                        print(f"Connected to {ssid}. IP: {self.ip_address}")
                        # Set system date/time
                        try:
                            if self.time_sync:
                                asyncio.create_task(self.start_time_sync())
                        except Exception as e:
                            print(f"Unable to set the system date and time: {e}")
                        if self.sta_web_server:
                            try:
                                self.server = await self.sta_web_server.run()
                            except Exception as e:
                                print(f"Error starting web server: {e}")
                        break
                    else:
                        print(f"Attempt {attempts + 1}: Failed to connect to Wi-Fi.")
                        attempts += 1

                if not self.sta_if.isconnected():
                    self.sta_if.active(False)
                    print("All connection attempts failed.")
            else:
                print("No saved network configuration found.")
        except Exception as e:
            self.sta_if.active(False)
            print(f"Error loading network configuration: {e}")

    async def save_config(self, ssid, password):
        """Saves network connection configuration to a file."""
        try:
            config = ConfigManager(self.config_directory, self.config_file)
            await config.read_async()

            config.set_entry("network", "ssid", ssid)
            config.set_entry("network", "password", password)

            await config.write_async()

            print("Network configuration saved.")
        except Exception as e:
            print(f"Error saving configuration: {e}")

    async def start_ap(self):
        """Starts the access point with WPA2 security and optional custom IP configuration."""
        ip_address = self.ap_ip_address
        subnet = self.ap_subnet
        gateway = self.ap_gateway
        dns = self.ap_dns

        if len(self.ap_password) < 8:
            print("Password must be at least 8 characters long.")
            return

        try:
            self.ap_if.config(essid=self.ap_ssid, password=self.ap_password)
            self.ap_if.active(True)

            # Configure access point IP settings
            self.ap_if.ifconfig((ip_address, subnet, gateway, dns))

            self.ip_address = self.ap_if.ifconfig()[0]

            print(f"Access point started. SSID: {self.ap_ssid}, IP: {self.ip_address}")
        except Exception as e:
            print(f"Error starting Access point: {e}")

    async def stop_ap(self):
        """Stops the access point."""
        if not self.ap_if.isconnected():
            print("The access point is not currently enabled.")
            return

        try:
            self.ap_if.config(essid="", password="")
            self.ap_if.active(False)
            self.ap_if.deinit()

            self.ip_address = None

            print("Access point stopped.")
        except Exception as e:
            print(f"Error stopping Access point: {e}")

    async def start_captive_portal_server(self):
        """Starts the captive portal HTTP server asynchronously."""
        if not self.ip_address:
            print("AP IP address not assigned. Cannot start server.")
            return

        try:
            self.server = await asyncio.start_server(self.handle_request, self.ip_address, self.captive_portal_http_port)
            print(f"Serving on {self.ip_address}:{self.captive_portal_http_port}")

            while True:
                machine.idle()
                await asyncio.sleep(1)  # Keep the server running
        except Exception as e:
            print(f"Error starting the captive portal server: {e}")

    async def stop_captive_portal_server(self):
        """Stops the captive portal HTTP server."""
        try:
            if self.server:
                self.server.close()
                await self.server.wait_closed()
                print("Server stopped.")
            else:
                print("Server already stopped.")
        except Exception as e:
            print(f"Error stopping server: {e}")

    async def handle_request(self, reader, writer):
        """Handles incoming HTTP requests for the captive portal."""
        try:
            request = await reader.read(1024)
            request = request.decode()
            print("Request:", request)

            # Handle captive portal detection endpoints
            if "GET /generate_204" in request:  # Android detection
                response = "HTTP/1.1 204 No Content\r\n\r\n"
            elif "GET /connectivity-check" in request:  # Chrome OS/Chromium-based browsers
                response = "HTTP/1.1 204 No Content\r\n\r\n"
            elif "GET /hotspot-detect.html" in request:  # macOS/iOS detection
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"
                response += "<HTML><BODY><H1>Success</H1></BODY></HTML>"
            elif "GET /success.conf" in request:  # Windows detection
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n"
                response += "Microsoft Connect Test"
            elif "GET /ncsi.conf" in request:  # Windows NCSI detection
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n"
                response += "Microsoft NCSI"
            elif "GET /scan" in request:  # Wireless network scan
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + await self.scan_networks()
            elif "POST /connect" in request:  # Wireless network connection
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + await self.connect_to_wifi(request)
            elif "POST /reconnect" in request:  # Saved wireless network reconnection
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + await self.reconnect_to_wifi()
            else:
                # Default response or index page
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + self.serve_index()

            # Write the response
            writer.write(response.encode())
            await writer.drain()
        except Exception as e:
            print(f"Error handling request: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

    def html_template(self, title, body):
        """Generates an HTML page template."""
        return f"""
        <html>
        <head><title>{title}</title></head>
        <body>
            <h1>{title}</h1>
            <p>Welcome to the Goat - Captive Portal.</p>
            <p><a href="/">Home</a></p>
            {body}
            <h1>Information</h1>
            <p>Check out other Goat Technologies offerings at <a href="https://goatbot.org/">Goatbot.org</a></p>
            <p>Contribute to <b>Pico Network Manager</b> on <a href="{self.REPO_URL}">GitHub</a></p>
            <p><b>Version {self.VERSION}</b><br>
            <b>© (c) 2024-2025 Goat Technologies</b></p>
        </body>
        </html>
        """

    async def scan_networks(self):
        """Scans for available wireless networks and returns HTML."""
        self.sta_if.active(True)
        html = "<h2>Network Scan</h2><p>Network scan complete.</p><h3>Available Wi-Fi Networks</h3><p>The following wi-fi networks were detected:"
        try:
            networks = self.sta_if.scan()
            for net in networks:
                ssid = net[0].decode()
                html += f"""
                    <form action='/connect' method='POST'>
                        <label>{ssid} - Signal Strength: {net[3]}</label><br>
                        <input type='hidden' name='ssid' value='{ssid}'>
                        <input type='password' name='password' placeholder='Password'><br>
                        <button type='submit'>Connect</button>
                    </form><br>
                """
        except Exception as e:
            html += f"<h2>Scan Error</h2><p>An error occurred while scanning Wi-Fi networks.<br>Error: {e}</p>"
        finally:
            self.sta_if.active(False)
        html += """<h3>Information</h3>
        <p>If the network you want is not listed, click <a href="/scan">Rescan</a> to scan again.</p>
        <p><a href='/'>Go Back</a></p>
        """
        return self.html_template("Goat - Captive Portal", html)

    async def connect_to_wifi(self, request):
        """Parses request for Wi-Fi credentials and connects to the network."""
        try:
            body_start = request.find("\r\n\r\n") + 4
            body = request[body_start:]
            params = {}
            for kv in body.split("&"):
                if "=" in kv:
                    key, value = kv.split("=", 1)
                    params[key] = value.replace("+", " ").replace("%20", " ")

            ssid = params.get("ssid", "")
            password = params.get("password", "")

            if ssid and password:
                self.sta_if.active(True)
                self.sta_if.connect(ssid, password)

                timeout = utime.time() + self.network_connection_timeout
                while not self.sta_if.isconnected() and utime.time() < timeout:
                    await asyncio.sleep(0.5)

                if self.sta_if.isconnected():
                    self.ip_address = self.sta_if.ifconfig()[0]
                    body = f"""<h2>Connected</h2>
                    <p>You successfully connected to {ssid}.</p>
                    <h2>Information</h2>
                    <p>The access point has been shut down and you can now close this page.</p>"""
                    return self.html_template("Goat - Captive Portal", body)
                else:
                    self.sta_if.active(False)
                    body = f"""<h2>Connection Failed</h2>
                    <p>Failed to connect to {ssid}.</p>"""
                    return self.html_template("Goat - Captive Portal", body)
            else:
                self.sta_if.active(False)
                body = """<h2>Connection Error</h2>
                <p>The SSID or password for the wi-fi network was not provided.</p>"""
                return self.html_template("Goat - Captive Portal", body)
        except Exception as e:
            self.sta_if.active(False)
            body = f"""<h2>Error</h2>
            <p>An error occurred: {e}</p>"""
            return self.html_template("Goat - Captive Portal", body)
        finally:
            if self.sta_if.isconnected():
                try:
                    await self.save_config(ssid, password)
                except Exception as e:
                    print(f"Error saving network configuration: {e}")

                try:
                    await self.stop_captive_portal_server()
                    if self.ap_dns_server:
                        await self.dns_server.stop_dns()
                    await self.stop_ap()
                except Exception as e:
                    print(f"Error stopping access point services: {e}")

                # Set system date/time
                try:
                    if self.time_sync:
                        asyncio.create_task(self.start_time_sync())
                except Exception as e:
                    print(f"Unable to set the system date and time: {e}")

                # Start STA web server
                if self.sta_web_server:
                    try:
                        self.server = await self.sta_web_server.run()
                    except Exception as e:
                        print(f"Error starting station web server: {e}")

    async def reconnect_to_wifi(self, request):
        """Reconnects to a saved Wi-Fi network."""
        try:
            if self.config_file in uos.listdir(self.config_directory):
                await self.load_config()

                if self.sta_if.isconnected():
                    body = """<h2>Reconnected</h2>
                    <p>You successfully reconnected to your saved network.</p>
                    <h2>Information</h2>
                    <p>The access point has been shut down and you can now close this page.</p>"""
                    return self.html_template("Goat - Captive Portal", body)
                else:
                    body = """<h2>Reconnection Failed</h2>
                    <p>Failed to reconnect to your saved network.</p>"""
                    return self.html_template("Goat - Captive Portal", body)
            else:
                body = """<h2>Configuration Error</h2>
                <p>There was an error locating your network configuration.<br>
                Please try manually reconnecting to the network.</p>"""
                return self.html_template("Goat - Captive Portal", body)
        except Exception as e:
            body = f"""<h2>Error</h2>
            <p>An error occurred: {e}</p>"""
            return self.html_template("Goat - Captive Portal", body)
        finally:
            if self.sta_if.isconnected():
                try:
                    await self.stop_captive_portal_server()
                    if self.ap_dns_server:
                        await self.dns_server.stop_dns()
                    await self.stop_ap()
                except Exception as e:
                    print(f"Error stopping access point services: {e}")

                # Set system date/time
                try:
                    if self.time_sync:
                        asyncio.create_task(self.start_time_sync())
                except Exception as e:
                    print(f"Unable to set the system date and time: {e}")

                # Start STA web server
                if self.sta_web_server:
                    try:
                        self.server = await self.sta_web_server.run()
                    except Exception as e:
                        print(f"Error starting station web server: {e}")

    async def disconnect_from_wifi(self):
        """Disconnects from the currently connected wireless network."""
        if not self.sta_if.isconnected():
            print("The network is not connected.")
            return;

        try:
            self.sta_if.active(False)
            self.sta_if.deinit()
            self.ip_address = None
        except Exception as e:
            print(f"Error disconnecting from wi-fi: {e}")

    def serve_index(self):
        """Serves the captive portal index page."""
        body = """<p>Welcome to the Goat - Captive Portal.<br>
        Use the portal to connect your Goat device to your wireless network.</p>"""

        if self.config_file in uos.listdir(self.config_directory):
            body += """<h2>Reconnect To Saved Network</h2>
            <p>An existing saved wireless network connection is configured for this system.<br>
            Click the 'Reconnect' button below to attempt to reconnect to your saved network.</p>
            <p><form action="/reconnect" method="post">
            <button type="submit">Reconnect</button>
            </form></p>"""

        body += """<h2>Connect To A Network</h2>
        <p>Click the link below to scan for networks:</p>
        <p><a href='/scan'>Start Scan</a></p>"""
        return self.html_template("Goat - Captive Portal", body)

    def strptime(self, date_string, format="%Y-%m-%d %H:%M:%S"):
        """Manually parse a datetime string to a tuple like strptime"""
        parts = date_string.split(" ")
        date_part = parts[0].split("-")
        time_part = parts[1].split(":")

        # Convert to integers
        year, month, day = map(int, date_part)
        hour, minute, second = map(int, time_part)

        # Return a struct_time tuple (year, month, day, hour, min, sec, weekday, yearday, isdst)
        return (year, month, day, hour, minute, second, 0, 0, 0)

    async def get_ntp_time(self):
        """Fetches the current date and time from an NTP server or time API and sets the system time."""
        url = f"{self.time_server}/api/time"
    
        try:
            print("Fetching time from API...")
            response = urequests.get(url, timeout=5)

            if response.status_code == 200:
                data = response.json()

                # Extract datetime string from response
                datetime_str = data['currentTime']

                if not datetime_str:
                    raise ValueError("Missing 'currentTime' in API response.")

                # Convert to struct_time
                parsed_time = self.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")

                # Convert to RTC-compatible tuple
                rtc_time = (parsed_time[0], parsed_time[1], parsed_time[2], 
            parsed_time[6], parsed_time[3], parsed_time[4], 
            parsed_time[5], 0)  # Subseconds set to 0

                # Create RTC object
                if not isinstance(self.rtc, object):
                    self.rtc = machine.RTC()

                # Set RTC time
                self.rtc.datetime(rtc_time)

                # Get the time from the RTC
                rtc_now = self.rtc.datetime()

                # Update the system time
                utime.mktime((rtc_now[0], rtc_now[1], rtc_now[2], rtc_now[4], rtc_now[5], rtc_now[6], 0, 0))
            
                print("Date and time set to:", rtc_now)
            else:
                print(f"Failed to fetch time. Status code: {response.status_code}")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            if 'response' in locals():
                response.close()

    async def start_time_sync(self):
        """Periodically synchronises the system date and time."""
        if not self.time_sync:
            return

        try:
            print("Starting automatic time synchronisation...")

            while True:
                if not self.sta_if.isconnected():
                    print("Stopping automatic time synchronisation...")
                    break

                asyncio.create_task(self.get_ntp_time())

                await asyncio.sleep(self.time_sync_interval*60)
        except Exception as e:
            print(f"Unable to start time synchronisation: {e}")

    async def run(self):
        """Runs the network manager initialization process and maintains connectivity."""
        print(f"Goat - Pico Network Manager Version {self.VERSION}")

        try:
            print("Preparing network interfaces...")

            try:
                self.ap_if.deinit()
                self.ap_if.config(essid="", password="")
                self.ap_if.active(False)
                self.sta_if.deinit()
                self.sta_if.active(False)
            except Exception as e:
                print(f"Unable to prepare network interfaces: {e}")

            # Set the hostname for the device
            network.hostname(self.hostname)

            await self.load_config()  # Load and attempt to connect to saved configuration

            while True:
                if not self.sta_if.isconnected():
                    print("Station disconnected, attempting reconnection...")
                    await self.load_config()  # Reload saved configuration and reconnect
                    if not self.sta_if.isconnected():
                        # Start AP if STA fails to reconnect
                        print("Switching to AP mode...")
                        await self.start_ap()
                        await self.start_captive_portal_server()
                        if self.ap_dns_server:
                            await self.dns_server.start_dns()

                # Check if both STA and AP are disconnected
                if not self.sta_if.isconnected() and not self.ap_if.isconnected():
                    print("No active connections. Rescanning...")
                    await asyncio.sleep(3)  # Pause before rescanning
                    continue

                machine.idle()

                await asyncio.sleep(0.1)
        except Exception as e:
            print(f"Error in network manager: {e}")
        finally:
            print("Cleaning up resources...")
            try:
                if self.sta_web_server:
                    print("Stopping STA web server...")
                    await self.sta_web_server.stop_server()
                if self.sta_if.isconnected():
                    print("Disconnecting from WiFi...")
                    await self.disconnect_from_wifi()
                if self.ap_if.isconnected():
                    print("Stopping access point services...")
                    if self.ap_dns_server:
                        await self.dns_server.stop_dns()
                    await self.stop_captive_portal_server()
                    await self.stop_ap()
            except Exception as cleanup_error:
                print(f"Error during cleanup: {cleanup_error}")
            await asyncio.sleep(0)  # Yield control after cleanup


# NetworkManagerDNS class
class NetworkManagerDNS:
    """Provides DNS services for the captive portal provided by the Goat - Network Manager."""
    # Class constructor
    def __init__(self, portal_ip="192.168.4.1", dns_port=53):
        """Constructs the class and exposes properties."""
        self.dns_ip = portal_ip
        self.dns_port = dns_port

        self.udp_server = None
        self.buffer_size = 512  # Default DNS packet size

    async def start_dns(self):
        """Starts a simple DNS server to redirect all requests to the captive portal."""
        try:
            self.udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_server.setblocking(False)  # Non-blocking mode
            self.udp_server.bind((self.dns_ip, self.dns_port))
            print(f"DNS server started listening on IP address {self.dns_ip} port {self.dns_port}.")

            while True:
                try:
                    data, addr = await self._receive_from()
                    if data:
                        print(f"DNS query received from {addr}")
                        response = self.handle_dns_query(data)
                        await self._send_to(response, addr)
                except Exception as e:
                    print(f"Error handling DNS query: {e}")
        except Exception as e:
            print(f"Error starting DNS server: {e}")
        finally:
            if self.udp_server:
                self.udp_server.close()
                print("DNS server socket closed.")

    async def _receive_from(self):
        """Non-blocking wrapper for receiving data."""
        while True:
            try:
                data, addr = self.udp_server.recvfrom(self.buffer_size)
                return data, addr
            except OSError as e:
                if e.errno != 11:  # EAGAIN or EWOULDBLOCK
                    raise
                await asyncio.sleep(0)  # Yield to the event loop

    async def _send_to(self, data, addr):
        """Non-blocking wrapper for sending data."""
        while True:
            try:
                self.udp_server.sendto(data, addr)
                return
            except OSError as e:
                if e.errno != 11:  # EAGAIN or EWOULDBLOCK
                    raise
                await asyncio.sleep(0)  # Yield to the event loop

    def handle_dns_query(self, data):
        """Parses a DNS query and constructs a response to redirect to the portal."""
        try:
            transaction_id = data[:2]  # Transaction ID
            flags = b'\x81\x80'  # Standard DNS response, no error
            question_count = data[4:6]
            answer_count = b'\x00\x01'
            authority_rrs = b'\x00\x00'
            additional_rrs = b'\x00\x00'

            # Extract query section and domain name
            query_section = data[12:]
            domain_name = self._decode_domain_name(query_section)
            print(f"Handling DNS query for domain: {domain_name}")

            # Answer section
            answer_name = b'\xc0\x0c'  # Pointer to domain name in query
            answer_type = b'\x00\x01'  # Type A
            answer_class = b'\x00\x01'  # Class IN
            ttl = b'\x00\x00\x00\x3c'  # Time-to-live: 60 seconds
            data_length = b'\x00\x04'  # IPv4 address size
            answer_ip = socket.inet_aton(self.dns_ip)

            # Build the response
            dns_response = (
                transaction_id + flags + question_count + answer_count +
                authority_rrs + additional_rrs + query_section +
                answer_name + answer_type + answer_class + ttl +
                data_length + answer_ip
            )
            return dns_response
        except Exception as e:
            print(f"Error handling DNS query: {e}")
            return b''

    def _decode_domain_name(self, query_section):
        """Decodes the domain name from the query section."""
        domain_parts = []
        i = 0
        while query_section[i] != 0:
            length = query_section[i]
            i += 1
            domain_parts.append(query_section[i:i+length].decode())
            i += length
        return '.'.join(domain_parts)

    async def stop_dns(self):
        """Stops the DNS server."""
        if self.udp_server:
            self.udp_server.close()
            self.udp_server = None
            print("DNS server stopped.")
