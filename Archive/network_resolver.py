import socket
import logging

class NetworkResolver:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)

    def resolve_host(self):
        """Determine the appropriate Redis host based on local subnet information."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 1))  # Use an external server to determine local IP
            local_ip = s.getsockname()[0]
        except Exception as e:
            self.logger.error(f"Failed to determine local IP: {e}")
            local_ip = '127.0.0.1'  # Fallback to localhost if IP determination fails
        finally:
            s.close()

        self.logger.info(f"Local IP detected: {local_ip}")

        if local_ip.startswith('192.168.1.'):
            self.logger.info("Detected home network. Connecting to Redis at home.")
            redis_host = self.config['Redis']['host_home']
        elif local_ip.startswith('172.30.98.'):
            self.logger.info("Detected work network. Connecting to Redis at work.")
            redis_host = self.config['Redis']['host_work']
        else:
            raise Exception(f"Unknown subnet {local_ip}. Cannot determine correct Redis host.")

        return redis_host

    def resolve_ollama_endpoint(self, local_ip):
        """Resolve the correct Ollama API endpoint based on the network."""
        if local_ip.startswith('192.168.1.'):
            self.logger.info("Detected home network. Using Ollama API endpoint for home network.")
            return self.config['API']['endpoint_home']
        elif local_ip.startswith('172.30.98.'):
            self.logger.info("Detected work network. Using Ollama API endpoint for work network.")
            return self.config['API']['endpoint_work']
        else:
            raise Exception(f"Unknown subnet {local_ip}. Cannot determine correct Ollama API endpoint.")

    def resolve_all(self):
        """Resolve both Redis host and Ollama API endpoint."""
        local_ip = self.resolve_host()
        ollama_endpoint = self.resolve_ollama_endpoint(local_ip)
        return local_ip, ollama_endpoint
