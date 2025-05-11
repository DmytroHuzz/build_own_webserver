import socket
import selectors
from typing import Tuple, Optional
from config_parser import load_config, ServerConfig
from http_parser import HTTPParser, HTTPMessage

# -------------------------
# Route Matching Logic
# -------------------------

class RouteMatcher:
    @staticmethod
    def match_location(locations, uri: str):
        # Find the longest prefix-matching location block
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
    def __init__(self):
        self._data = b""

    @property
    def data(self) -> bytes:
        return self._data

    @data.setter
    def data(self, chunk: bytes):
        # Append new data to the buffer
        self._data += chunk

    def reduce_data(self, size: int):
        # Remove processed data from the buffer
        self._data = self._data[size:]

# -------------------------
# Message Processor
# -------------------------

class HTTPProcessor:
    def __init__(self, data_provider: DataProvider):
        self.data_provider = data_provider

    def get_one_http_message(self) -> Optional[HTTPMessage]:
        try:
            # Attempt to parse a single HTTP message from the buffer
            message, consumed = HTTPParser.parse_message(self.data_provider.data)
            if message:
                # Remove the parsed message from the buffer
                self.data_provider.reduce_data(consumed)
            return message
        except Exception:
            return None

# -------------------------
# Server Entrypoint
# -------------------------

class Server:
    """
    Main server class. Reads config, binds to the correct port, and handles requests.
    """

    # ===================================================
    # Main epoll-based server loop:
    # 1. Create a non-blocking server socket.
    # 2. Register it with a selector to watch for incoming connections.
    # 3. Enter the event loop:
    #     a. Wait for events using selector.select().
    #     b. If the event is on the server socket, accept a new client.
    #     c. If the event is on a client socket, read data and respond.
    # 4. Parse requests and route them using our config and HTTP parser.
    # 5. Serve files or respond with a 404.
    # ===================================================

    def __init__(self, config_path: str):
        self.config = load_config(config_path)
        self.selector = selectors.DefaultSelector()

    def start(self):
        port = self.config.listen_ports[0]
        server_sock = socket.socket()
        server_sock.bind(("", port))
        server_sock.listen()
        server_sock.setblocking(False)
        # Register the server socket to accept new connections
        self.selector.register(server_sock, selectors.EVENT_READ, data=None)
        print(f"[Server] Listening on port {port}")

        try:
            while True:
                # Wait for events on registered sockets
                events = self.selector.select(timeout=1)
                # Iterate over the events returned by the selector
                # Each event corresponds to a socket ready for I/O
                for key, mask in events:
                    if key.data is None:
                        # Accept a new incoming connection from a client.
                        self._accept_connection(key.fileobj)
                    else:
                        # Handle incoming data from a client socket.
                        self._service_connection(key, mask)
        except KeyboardInterrupt:
            print("[Server] Shutting down")
        finally:
            # Clean up resources on shutdown
            self.selector.close()
            server_sock.close()

    def _accept_connection(self, sock):
        # Accept a new incoming connection from a client.
        # Set it to non-blocking and register it with the selector.
        conn, addr = sock.accept()
        print(f"[Server] Accepted connection from {addr}")
        conn.setblocking(False)
        # Create a new data provider for the connection
        data_provider = DataProvider()
        # Register the connection for reading
        self.selector.register(conn, selectors.EVENT_READ, data=data_provider)

    def _service_connection(self, key, mask):
        # Handle incoming data from a client socket.
        # Read data and trigger request processing if data is received.
        sock = key.fileobj
        data_provider = key.data
        addr = sock.getpeername()
        if mask & selectors.EVENT_READ:
            try:
                # Read data from the socket
                data = sock.recv(1024)
            except ConnectionResetError:
                data = None
            if data:
                # Add received data to the buffer
                data_provider.data = data
                self._handle_request(sock, data_provider)
            else:
                # Close the connection if no data is received
                print(f"[Server] Closing connection to {addr}")
                self.selector.unregister(sock)
                sock.close()

    def _handle_request(self, sock, data_provider):
        # Parse the buffered data into an HTTP request message.
        http_processor = HTTPProcessor(data_provider)
        while request := http_processor.get_one_http_message():
            # Determine the correct file path based on requested URL.
            url = request.url
            root = 'html'  # Default root directory
            if url == "/":
                url = "/index.html"
            else:
                # Match the location block for the requested URL
                root = RouteMatcher.match_location(self.config.routes[self.config.listen_ports[0]], url)

            file_path = f"{root}{url}"
            print(f"[Request] {url} => {file_path}")

            # Try to read and serve the requested file.
            try:
                with open(file_path, "rb") as f:
                    body = f.read()
                headers = (
                    "HTTP/1.1 200 OK\r\n"
                    f"Content-Length: {len(body)}\r\n"
                    "Content-Type: text/plain\r\n"
                )
                # Check if connection should be kept alive or closed.
                if "keep-alive" in request.headers.get("connection", "").lower():
                    headers += "Connection: keep-alive\r\n"
                else:
                    # Close the connection if not keep-alive
                    self.selector.unregister(sock)
                    sock.close()
                    return
                headers += "\r\n"
                sock.sendall(headers.encode() + body)
            # If something goes wrong (e.g., file not found), send a 404.
            except Exception as e:
                print(f"[Error] {e}")
                self._send_404(sock)
                self.selector.unregister(sock)
                sock.close()
                return

    def _send_404(self, sock):
        # Helper method to respond with a 404 Not Found status.
        msg = b"404 Not Found"
        headers = (
            "HTTP/1.1 404 Not Found\r\n"
            f"Content-Length: {len(msg)}\r\n"
            "Content-Type: text/plain\r\n\r\n"
        )
        sock.sendall(headers.encode() + msg)

# -------------------------
# Start Server
# -------------------------

if __name__ == "__main__":
    # Load the server configuration and start the server
    server = Server("config.conf")
    server.start()