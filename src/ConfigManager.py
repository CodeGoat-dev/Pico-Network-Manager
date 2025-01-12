# Goat - Configuration Manager
# Version 1.0.0
# © (c) 2024-2025 Goat Technologies
# Description:
# A lightweight configuration manager library for MicroPython.
# Provides INI-style configuration file support for Goat firmware.

# Imports
import re
import uos
import uasyncio as asyncio

# ConfigManager class
class ConfigManager:
    """Provides configuration file management support for Goat firmware."""

    def __init__(self, directory, filename, auto_read=False, auto_save=False):
        """Initialize the configuration manager."""
        if directory is None:
            directory = '/config'

        try:
            uos.mkdir(directory)
        except OSError:
            pass  # Ignore if the directory already exists

        self.directory = directory
        self.filename = "/".join([directory.rstrip('/'), filename])
        self.auto_read = auto_read
        self.auto_save = auto_save

        self.sections = []
        self.config = {}

        if auto_read:
            asyncio.run(self.read_async())

    async def read_async(self):
        """Read and parse the configuration file."""
        try:
            with open(self.filename, 'r') as configfile:
                section_re = re.compile(r'\[(.*)\]')
                entry_re = re.compile(r'(.*?)=(.*)')
                string_re = re.compile(r'^"(.*)"$')
                int_re = re.compile(r'^\d+$')
                bool_re = re.compile(r'^(true|false)$')
                comment_re = re.compile(r'^#.*')

                current_section = None
                for line in configfile:
                    line = line.strip()
                    if not line or comment_re.match(line):
                        continue
                    if section_re.match(line):
                        current_section = section_re.match(line).group(1)
                        if current_section not in self.sections:
                            self.sections.append(current_section)
                        self.config[current_section] = {}
                    elif current_section and entry_re.match(line):
                        entry = entry_re.match(line)
                        key = entry.group(1).strip()
                        value = entry.group(2).strip()
                        if string_re.match(value):
                            value = string_re.match(value).group(1)
                        elif bool_re.match(value.lower()):
                            value = value.lower() == "true"
                        elif int_re.match(value):
                            value = int(value)
                        elif value.startswith('!'):
                            value = [v.strip() for v in value[1:].split(',')]
                        self.config[current_section][key] = value
                    else:
                        raise ValueError(f"Invalid format in line: {line}")
        except OSError as e:
            print(f"Error reading configuration file: {e}")

    async def reload_async(self):
        """Reload the configuration file."""
        await self.read_async()

    async def write_async(self, config=None, filename=None):
        """Write the configuration to the file."""
        if config is None:
            config = self.config
        if filename is None:
            filename = self.filename

        temp_file = f"{filename}.tmp"
        try:
            with open(temp_file, 'w') as configfile:
                for section, entries in config.items():
                    await asyncio.sleep(0)  # Yield control to the event loop
                    configfile.write(f'[{section}]\n')
                    for key, value in entries.items():
                        if isinstance(value, str):
                            value = f'"{value}"'
                        elif isinstance(value, list):
                            value = f"!{','.join(map(str, value))}"
                        elif isinstance(value, bool):
                            value = "true" if value else "false"
                        configfile.write(f'{key}={value}\n')
                    configfile.write('\n')

            # Safely replace the original file
            uos.rename(temp_file, filename)
        except OSError as e:
            print(f"Error writing configuration file: {e}")
            try:
                uos.remove(temp_file)
            except OSError:
                pass

    def read(self):
        """Read and parse the configuration file (sync version)."""
        asyncio.run(self.read_async())

    def reload(self):
        """Reload the configuration file (sync version)."""
        asyncio.run(self.reload_async())

    def write(self, config=None, filename=None):
        """Write the configuration to the file (sync version)."""
        asyncio.run(self.write_async(config, filename))

    def get_section(self, section):
        """Get all key-value pairs in a section."""
        if not section:
            raise ValueError("Section name cannot be empty.")
        
        return self.config.get(section, {})

    def get_entry(self, section, key):
        """Get a specific value by section and key."""
        if not section or not key:
            raise ValueError("Section and key names cannot be empty.")
        
        return self.config.get(section, {}).get(key, None)

    def set_section(self, section):
        """Add a new section."""
        if not section:
            raise ValueError("Section name cannot be empty.")

        if section not in self.sections:
            self.sections.append(section)
            self.config[section] = {}

            if self.auto_save:
                self.write()

    def set_entry(self, section, key, value):
        """Set a key-value pair in a section."""
        if not section:
            raise ValueError("Section name cannot be empty.")

        if section not in self.sections:
            self.set_section(section)
        self.config[section][key] = value

        if self.auto_save:
            self.write()

    def remove_section(self, section):
        """Remove a section."""
        if not section:
            raise ValueError("Section name cannot be empty.")

        if section in self.sections:
            self.sections.remove(section)
            self.config.pop(section, None)

            if self.auto_save:
                self.write()

    def remove_entry(self, section, key):
        """Remove a key from a section."""
        if not section:
            raise ValueError("Section name cannot be empty.")

        if section in self.config and key in self.config[section]:
            self.config[section].pop(key, None)

            if self.auto_save:
                self.write()

    def __repr__(self):
        return f"ConfigFile Object: {self.filename}"

    def __len__(self):
        return len(self.sections)

    def __getitem__(self, conf):
        """Access configuration values."""
        try:
            if isinstance(conf, tuple) and len(conf) == 2:
                section, key = conf
                return self.config[section][key]
            elif isinstance(conf, str):
                return self.config[conf]
            else:
                raise KeyError("Invalid key format. Use 'section' or ('section', 'key').")
        except KeyError as e:
            print(f"Error accessing configuration: {e}")
            raise

    def __setitem__(self, sec_key, entry_val):
        """Set configuration values."""
        try:
            section, key = sec_key
            self.set_entry(section, key, entry_val)

            if self.auto_save:
                self.write()
        except ValueError:
            print("Error setting value. Provide a tuple ('section', 'key') for the configuration key.")
            raise

    async def start_watching(self, check_interval=3):
        """
        Start watching the configuration file for changes.

        Args:
            check_interval (int): Time in seconds between checks.
        """
        last_modified = self.get_last_modified_time()

        while True:
            await asyncio.sleep(check_interval)  # Yield control to other tasks
            current_modified = self.get_last_modified_time()

            if current_modified and current_modified != last_modified:
                print(f"Configuration file {self.filename} has changed. Reloading...")
                last_modified = current_modified
                await self.reload_async()

    def get_last_modified_time(self):
        """Get the last modified time of the configuration file."""
        try:
            return uos.stat(self.filename)[8]  # Index 8 is the modification time
        except OSError:
            # Log file not found but do not crash
            return None
