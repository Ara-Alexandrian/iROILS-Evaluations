# network_resolver.py

import socket
import logging

class NetworkResolver:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)

    def get_local_ip(self):
        """Get the local IP address of the machine."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Use an external server to determine local IP
            s.connect(('8.8.8.8', 1))
            local_ip = s.getsockname()[0]
            self.logger.info(f"Local IP detected: {local_ip}")
            return local_ip
        except Exception as e:
            self.logger.error(f"Failed to determine local IP: {e}")
            raise Exception("Unable to determine local IP address.")
        finally:
            s.close()

    def resolve_environment(self, local_ip):
        """Determine the environment based on the local IP address."""
        if local_ip.startswith('192.168.1.'):
            self.logger.info("Detected home network.")
            return 'home'
        elif local_ip.startswith('172.30.98.'):
            self.logger.info("Detected work network.")
            return 'work'
        else:
            self.logger.warning(f"Unknown subnet {local_ip}. Defaulting to 'home' environment.")
            return 'home'  # Default to 'home' if subnet is unknown