import unittest
from http_parser import HTTPParser, HTTPMessage, IncompleteMessageError, InvalidMessageError

class TestHTTPParser(unittest.TestCase):

    def test_valid_get_request(self):
        request = (
            b"GET /index.html HTTP/1.1\r\n"
            b"Host: example.com\r\n"
            b"User-Agent: TestClient\r\n"
            b"\r\n"
        )
        msg, used = HTTPParser.parse_message(request)
        self.assertIsInstance(msg, HTTPMessage)
        self.assertEqual(msg.method, "GET")
        self.assertEqual(msg.url, "/index.html")
        self.assertEqual(msg.version, "HTTP/1.1")
        self.assertEqual(msg.headers["host"], "example.com")
        self.assertEqual(msg.headers["user-agent"], "TestClient")
        self.assertEqual(msg.body, b"")
        self.assertEqual(used, len(request))

    def test_valid_post_request_with_body(self):
        request = (
            b"POST /submit HTTP/1.1\r\n"
            b"Host: example.com\r\n"
            b"Content-Length: 11\r\n"
            b"\r\n"
            b"hello=world"
        )
        msg, used = HTTPParser.parse_message(request)
        self.assertEqual(msg.method, "POST")
        self.assertEqual(msg.url, "/submit")
        self.assertEqual(msg.version, "HTTP/1.1")
        self.assertEqual(msg.headers["content-length"], "11")
        self.assertEqual(msg.body, b"hello=world")
        self.assertEqual(used, len(request))

    def test_incomplete_headers(self):
        request = (
            b"GET / HTTP/1.1\r\n"
            b"Host: test"
        )
        with self.assertRaises(IncompleteMessageError):
            HTTPParser.parse_message(request)

    def test_incomplete_body(self):
        request = (
            b"POST / HTTP/1.1\r\n"
            b"Host: test\r\n"
            b"Content-Length: 20\r\n"
            b"\r\n"
            b"short"
        )
        with self.assertRaises(IncompleteMessageError):
            HTTPParser.parse_message(request)

    def test_invalid_start_line(self):
        request = b"BADREQUEST\r\nHost: x\r\n\r\n"
        with self.assertRaises(InvalidMessageError):
            HTTPParser.parse_message(request)

    def test_invalid_header_line(self):
        request = b"GET / HTTP/1.1\r\nInvalidHeader\r\n\r\n"
        with self.assertRaises(InvalidMessageError):
            HTTPParser.parse_message(request)

    def test_invalid_content_length(self):
        request = (
            b"POST / HTTP/1.1\r\n"
            b"Content-Length: abc\r\n"
            b"\r\n"
            b"hello"
        )
        with self.assertRaises(InvalidMessageError):
            HTTPParser.parse_message(request)

    def test_multiple_messages_in_one_buffer(self):
        request = (
            b"GET /first HTTP/1.1\r\n"
            b"Host: example.com\r\n"
            b"Content-Length: 0\r\n"
            b"\r\n"
            b"POST /submit HTTP/1.1\r\n"
            b"Host: example.com\r\n"
            b"Content-Length: 5\r\n"
            b"\r\n"
            b"hello"
        )
        msg1, used1 = HTTPParser.parse_message(request)
        msg2, used2 = HTTPParser.parse_message(request[used1:])

        self.assertEqual(msg1.method, "GET")
        self.assertEqual(msg1.url, "/first")
        self.assertEqual(msg1.headers["content-length"], "0")
        self.assertEqual(msg1.body, b"")

        self.assertEqual(msg2.method, "POST")
        self.assertEqual(msg2.url, "/submit")
        self.assertEqual(msg2.headers["content-length"], "5")
        self.assertEqual(msg2.body, b"hello")

    def test_full_and_partial_message(self):
        request = (
            b"GET /complete HTTP/1.1\r\n"
            b"Host: test\r\n"
            b"\r\n"
            b"POST /incomplete HTTP/1.1\r\n"
            b"Host: test\r\n"
            b"Content-Length: 10\r\n"
            b"\r\n"
            b"abc"
        )
        msg1, used1 = HTTPParser.parse_message(request)
        self.assertEqual(msg1.method, "GET")
        self.assertEqual(msg1.url, "/complete")
        with self.assertRaises(IncompleteMessageError):
            HTTPParser.parse_message(request[used1:])
        




if __name__ == "__main__":
    unittest.main()
