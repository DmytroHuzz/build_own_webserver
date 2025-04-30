from typing import Dict, Optional, Tuple

# -----------------------------------------------------------------------------
# Custom exception classes for precise error handling in our HTTP parser.
# -----------------------------------------------------------------------------
class IncompleteMessageError(Exception):
    """
    Raised when the parser determines that the data buffer does not yet
    contain a full HTTP message. Signals to the server: “this input is
    valid so far, but you need to read more bytes before retrying parse.”
    """
    pass

class InvalidMessageError(Exception):
    """
    Raised when the parser finds a structural or syntactic problem in the
    data buffer that cannot be fixed by reading more bytes. Signals to the
    server: “this request is malformed—respond with an error (e.g. 400 Bad Request).”
    """
    pass


class HTTPMessage:
    """
    Represents a complete HTTP message (request or response).

    Attributes:
        method:  HTTP method (e.g. 'GET', 'POST') or response status code.
        url:     Request target (e.g. '/index.html') or response reason phrase.
        version: HTTP version (e.g. 'HTTP/1.1').
        headers: dict of header-name (lowercased) → header-value.
        body:    Raw bytes of the message body.
    """
    def __init__(
        self,
        method: str,
        url: str,
        version: str,
        headers: Dict[str, str],
        body: bytes
    ):
        self.method = method
        self.url = url
        self.version = version
        self.headers = headers
        self.body = body

    def __repr__(self):
        snippet = self.body[:100]  # preview first 100 bytes of body
        return (
            f"HTTPMessage(method={self.method!r}, url={self.url!r}, "
            f"version={self.version!r}, headers={self.headers!r}, "
            f"body={snippet!r}...)"
        )


class HTTPParser:
    """
    A simple HTTP message parser that can extract one message at a time
    from a byte buffer.

    Exceptions:
      - IncompleteMessageError: the buffer is valid so far but incomplete.
      - InvalidMessageError:   the buffer is malformed and cannot be parsed.
    """
    @staticmethod
    def parse_message(data: bytes) -> Tuple[Optional[HTTPMessage], int]:
        """
        Parse exactly one HTTP message from the start of `data`.

        :param data: Bytes that may contain zero, one, or multiple messages.
        :return: A tuple (message, bytes_consumed). If data is empty, (None, 0).
        :raises IncompleteMessageError: headers or body are incomplete.
        :raises InvalidMessageError:    data is syntactically invalid.
        """
        # --- A) Empty buffer: nothing to parse yet.
        if not data:
            return None, 0

        # --- B) Locate end of headers ("\r\n\r\n").
        sep = b"\r\n\r\n"
        idx = data.find(sep)
        if idx == -1:
            # Missing header terminator → need more data.
            raise IncompleteMessageError(
                "Incomplete headers: missing CRLF CRLF separator."
            )

        # Split header block from potential body.
        header_text = data[:idx].decode("iso-8859-1", errors="replace")
        rest = data[idx + len(sep):]

        # --- C) Break headers into lines.
        lines = header_text.split("\r\n")
        start_line = lines[0]
        header_lines = lines[1:]

        # --- D) Parse start line into method, URL/status, version.
        parts = start_line.split(" ", 2)
        if len(parts) != 3:
            # Syntax error cannot be fixed by more data → invalid.
            raise InvalidMessageError(f"Malformed start line: {start_line!r}")
        method, url, version = parts

        # --- E) Parse headers into dict.
        headers: Dict[str, str] = {}
        for line in header_lines:
            if not line:
                continue  # skip stray blank lines
            if ":" not in line:
                raise InvalidMessageError(f"Bad header line: {line!r}")
            name, value = line.split(":", 1)
            headers[name.strip().lower()] = value.strip()

        # --- F) Determine body length via Content-Length, if present.
        length_hdr = headers.get("content-length")
        if length_hdr is not None:
            try:
                length = int(length_hdr)
            except ValueError:
                # Non-integer length cannot be corrected → invalid.
                raise InvalidMessageError(
                    f"Invalid Content-Length value: {length_hdr!r}"
                )
            if len(rest) < length:
                # Not enough data for full body → incomplete.
                raise IncompleteMessageError(
                    f"Body incomplete: expected {length} bytes, got {len(rest)}."
                )
            body = rest[:length]
            consumed = idx + len(sep) + length
        else:
            # No Content-Length — assume no body (e.g. for GET, HEAD).
            body = b""
            consumed = idx + len(sep)

        message = HTTPMessage(method, url, version, headers, body)
        return message, consumed

# -----------------------------------------------------------------------------
# Usage in your server loop:
#
# try:
#     msg, used = HTTPParser.parse_message(buffer)
# except IncompleteMessageError:
#     # Buffer is valid but needs more data: wait for socket.read(), then retry.
#     continue
# except InvalidMessageError as err:
#     # Data is malformed: log error, send 400 Bad Request, close connection.
#     send_400_response(str(err))
#     break
# -----------------------------------------------------------------------------
