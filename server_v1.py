import socket
from typing import Tuple, Optional, Dict
from config_parser import load_config, ServerConfig  # Your config parser from previous part
from http_parser import HTTPParser, HTTPMessage  # Your existing HTTP parser

# -------------------------
# Route Matching Logic
# -------------------------

class RouteMatcher:
    """
    Selects the server block based on port and matches location blocks using longest URI prefix.
    """
    @staticmethod
    def match_location(locations, uri: str):
        """
        Finds the location block with the longest prefix match.
        """
        matched_location = None
        longest_prefix = -1
        for path, root_dir in locations.items():
            if uri.startswith(path) and len(path) > longest_prefix:
                matched_location = root_dir
                longest_prefix = len(path)
        return matched_location


# -------------------------
# Data Buffer
# -------------------------

class DataProvider:
    """
    A simple buffer that accumulates received data and lets us consume it safely.
    """
    def __init__(self):
        self._data = b""

    @property
    def data(self) -> bytes:
        return self._data

    @data.setter
    def data(self, chunk: bytes):
        self._data += chunk

    def reduce_data(self, size: int):
        self._data = self._data[size:]


# -------------------------
# Message Processor
# -------------------------

class HTTPProcessor:
    """
    Handles parsing of buffered data into HTTPMessage objects.
    """
    def __init__(self, data_provider: DataProvider):
        self.data_provider = data_provider

    def get_one_http_message(self) -> Optional[HTTPMessage]:
        try:
            message, consumed = HTTPParser.parse_message(self.data_provider.data)
            if message:
                self.data_provider.reduce_data(consumed)
            return message
        except Exception:
            return None


# -------------------------
# Client Connection Session
# -------------------------

class HTTPSession:
    """
    Handles the lifecycle of a single HTTP connection.
    """
    def __init__(
        self,
        connection: socket.socket,
        client_address: Tuple[str, int],
        port: int,
        server_config: ServerConfig,
    ):
        self.connection = connection
        self.addr = client_address
        self.data_provider = DataProvider()
        self.http_processor = HTTPProcessor(self.data_provider)
        self.port = port
        self.server_config = server_config
        self.active = True

    def handle(self):
        print(f"[Session] Connected from {self.addr}")
        while self.active:
            data = self.connection.recv(1024)
            if not data:
                break

            self.data_provider.data = data

            while request := self.http_processor.get_one_http_message():
                url = request.url
                root = 'html'  # Default root directory
                if url == "/":
                    url = "/index.html"
                else:
                    # Get root path
                    root = RouteMatcher.match_location(self.server_config.routes[self.port], url)

                file_path = f"{root}{url}"
                print(f"[Request] {url} => {file_path}")

                try:
                    with open(file_path, "rb") as f:
                        body = f.read()
                    headers = (
                        "HTTP/1.1 200 OK\r\n"
                        f"Content-Length: {len(body)}\r\n"
                        "Content-Type: text/plain\r\n"
                    )
                    if "keep-alive" in request.headers.get("connection", "").lower():
                        headers += "Connection: keep-alive\r\n"
                    else:
                        self.active = False
                    headers += "\r\n"
                    self.connection.sendall(headers.encode() + body)
                except Exception as e:
                    print(f"[Error] {e}")
                    self._send_404()

        self.connection.close()

    def _send_404(self):
        msg = b"404 Not Found"
        headers = (
            "HTTP/1.1 404 Not Found\r\n"
            f"Content-Length: {len(msg)}\r\n"
            "Content-Type: text/plain\r\n\r\n"
        )
        self.connection.sendall(headers.encode() + msg)


# -------------------------
# Server Entrypoint
# -------------------------

class Server:
    """
    Main server class. Reads config, binds to the correct port, and handles requests.
    """
    def __init__(self, config_path: str):
        self.config = load_config(config_path)

    def start(self):
        port = self.config.listen_ports[0]
        with socket.socket() as s:
            s.bind(("", port))
            s.listen()
            print(f"[Server] Listening on port {port}")
            while True:
                conn, addr = s.accept()
                session = HTTPSession(conn, addr, port, self.config)
                session.handle()


# -------------------------
# Start Server
# -------------------------

if __name__ == "__main__":
    server = Server("config.conf")
    server.start()