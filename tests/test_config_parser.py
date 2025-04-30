import unittest
from config_parser import SimpleConfigLexer, SimpleConfigParser, ServerConfig

class TestSimpleConfigLexer(unittest.TestCase):

    def tokenize(self, text):
        lexer = SimpleConfigLexer(text)
        return lexer.tokens

    def test_simple_directive(self):
        tokens = self.tokenize("listen 8080;")
        expected = [
            ("WORD", "listen"),
            ("WORD", "8080"),
            ("SEMICOLON", ";")
        ]
        self.assertEqual(tokens, expected)

    def test_nested_block(self):
        tokens = self.tokenize("server { listen 8080; }")
        expected = [
            ("WORD", "server"),
            ("LBRACE", "{"),
            ("WORD", "listen"),
            ("WORD", "8080"),
            ("SEMICOLON", ";"),
            ("RBRACE", "}")
        ]
        self.assertEqual(tokens, expected)

    def test_block_with_argument(self):
        tokens = self.tokenize("location / { root /html; }")
        expected = [
            ("WORD", "location"),
            ("WORD", "/"),
            ("LBRACE", "{"),
            ("WORD", "root"),
            ("WORD", "/html"),
            ("SEMICOLON", ";"),
            ("RBRACE", "}")
        ]
        self.assertEqual(tokens, expected)

    def test_multiple_directives(self):
        tokens = self.tokenize("listen 80; server_name localhost;")
        expected = [
            ("WORD", "listen"),
            ("WORD", "80"),
            ("SEMICOLON", ";"),
            ("WORD", "server_name"),
            ("WORD", "localhost"),
            ("SEMICOLON", ";")
        ]
        self.assertEqual(tokens, expected)

    def test_ignores_comments(self):
        tokens = self.tokenize("listen 80; # this is a comment")
        expected = [
            ("WORD", "listen"),
            ("WORD", "80"),
            ("SEMICOLON", ";")
        ]
        self.assertEqual(tokens, expected)

    def test_whitespace_and_newlines(self):
        tokens = self.tokenize("""
        http {
            server {
                listen 8080;
            }
        }
        """)
        expected = [
            ("WORD", "http"),
            ("LBRACE", "{"),
            ("WORD", "server"),
            ("LBRACE", "{"),
            ("WORD", "listen"),
            ("WORD", "8080"),
            ("SEMICOLON", ";"),
            ("RBRACE", "}"),
            ("RBRACE", "}")
        ]
        self.assertEqual(tokens, expected)

class TestConfigParser(unittest.TestCase):

    def parse_config(self, config_text: str):
        lexer = SimpleConfigLexer(config_text)
        parser = SimpleConfigParser(lexer.tokens)
        return parser.parse()

    def test_single_directive(self):
        config = self.parse_config("listen 8080;")
        self.assertEqual(config, {"listen": "8080"})

    def test_directive_with_multiple_args(self):
        config = self.parse_config("access_log /var/log/access.log main;")
        self.assertEqual(config, {"access_log": ["/var/log/access.log", "main"]})

    def test_nested_blocks(self):
        config = self.parse_config("""
        http {
            server {
                listen 8080;
                location / {
                    root /var/www;
                }
            }
        }
        """)
        expected = {
            "http": {
                "server": {
                    "listen": "8080",
                    "location": {
                        "/": {
                            "root": "/var/www"
                        }
                    }
                }
            }
        }
        self.assertEqual(config, expected)

    def test_multiple_location_blocks(self):
        config = self.parse_config("""
        server {
            listen 8080;
            location / {
                root /www;
            }
            location /api {
                root /api;
            }
        }
        """)
        expected = {
            "server": {
                "listen": "8080",
                "location": {
                    "/": {"root": "/www"},
                    "/api": {"root": "/api"}
                }
            }
        }
        self.assertEqual(config, expected)

    def test_multiple_server_blocks(self):
        config = self.parse_config("""
        http {
            server {
                listen 80;
            }
            server {
                listen 81;
            }
        }
        """)
        expected = {
            "http": {
                "server": [
                    {"listen": "80"},
                    {"listen": "81"}
                ]
            }
        }
        self.assertEqual(config, expected)

    def test_empty_block(self):
        config = self.parse_config("events { }")
        self.assertEqual(config, {"events": {}})

    def test_invalid_missing_semicolon(self):
        with self.assertRaises(SyntaxError):
            self.parse_config("listen 8080")  # missing semicolon

    def test_invalid_block_with_multiple_arguments(self):
        with self.assertRaises(SyntaxError):
            self.parse_config("location / api { root /foo; }")  # invalid: too many args

class TestServerConfig(unittest.TestCase):

    def test_listen_ports_single(self):
        config_dict = {
            "http": {
                "server": {
                    "listen": "8080",
                    "location": {
                        "/": {"root": "/data/www"}
                    }
                }
            }
        }
        config = ServerConfig(config_dict)
        self.assertEqual(config.listen_ports, [8080])

    def test_listen_ports_multiple(self):
        config_dict = {
            "http": {
                "server": [
                    {"listen": "8080"},
                    {"listen": "8081"}
                ]
            }
        }
        config = ServerConfig(config_dict)
        self.assertEqual(config.listen_ports, [8080, 8081])

    def test_routes_single(self):
        config_dict = {
            "http": {
                "server": {
                    "listen": "8080",
                    "location": {
                        "/": {"root": "/data/www"},
                        "/images": {"root": "/data/img"}
                    }
                }
            }
        }
        config = ServerConfig(config_dict)
        expected = {
            8080: {
                "/": "/data/www",
                "/images": "/data/img"
            }
        }
        self.assertEqual(config.routes, expected)

    def test_routes_multiple_servers(self):
        config_dict = {
            "http": {
                "server": [
                    {
                        "listen": "8080",
                        "location": {"/": {"root": "/data/www"}}
                    },
                    {
                        "listen": "8081",
                        "location": {"/": {"root": "/data/alt"}}
                    }
                ]
            }
        }
        config = ServerConfig(config_dict)
        expected = {
            8080: {"/": "/data/www"},
            8081: {"/": "/data/alt"}
        }
        self.assertEqual(config.routes, expected)

    def test_invalid_port_raises(self):
        config_dict = {
            "http": {
                "server": {"listen": "not-a-number"}
            }
        }
        config = ServerConfig(config_dict)
        with self.assertRaises(ValueError):
            _ = config.listen_ports