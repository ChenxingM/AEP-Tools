"""COS (Carousel Object System) parser for AEP text data chunks.

After Effects stores text document styling data in a PDF-like COS binary format
inside btdk chunks. This parser tokenizes and parses that format.
"""

from __future__ import annotations
from typing import Any

# Token types
TK_IDENTIFIER = 0
TK_NUMBER = 1
TK_STRING = 2
TK_HEX_STRING = 3
TK_BOOLEAN = 4
TK_DICT_START = 5
TK_DICT_END = 6
TK_ARRAY_START = 7
TK_ARRAY_END = 8
TK_NULL = 9
TK_EOF = 10


class Token:
    __slots__ = ("type", "value")

    def __init__(self, type_: int, value: Any = None):
        self.type = type_
        self.value = value


class CosParser:
    """Parses COS/PDF-like binary data into nested dicts and lists."""

    def __init__(self, data: bytes):
        self._data = data
        self._offset = 0
        self._lookahead = Token(TK_EOF)

    def _get_byte(self) -> int:
        if self._offset >= len(self._data):
            return -1
        b = self._data[self._offset]
        self._offset += 1
        return b

    def _get_char(self) -> str:
        b = self._get_byte()
        return "" if b == -1 else chr(b)

    def _unget(self) -> None:
        self._offset -= 1
        if self._offset < 0:
            raise RuntimeError("Buffer underflow")

    # -- Lexer --

    def _lex(self) -> None:
        self._lookahead = self._lex_token()

    def _lex_token(self) -> Token:
        while True:
            ch = self._get_char()
            if ch == "":
                return Token(TK_EOF)
            if ch == "%":
                self._lex_comment()
                continue
            if not ch.isspace():
                break

        if ch == "<":
            ch2 = self._get_char()
            if ch2 == "<":
                return Token(TK_DICT_START)
            if ch2 and ch2 in "0123456789abcdefABCDEF":
                return self._lex_hex_string(ch2)
            raise SyntaxError(f"Unexpected '<{ch2}'")

        if ch == ">":
            ch2 = self._get_char()
            if ch2 != ">":
                raise SyntaxError("Expected '>>'")
            return Token(TK_DICT_END)

        if ch == "[":
            return Token(TK_ARRAY_START)
        if ch == "]":
            return Token(TK_ARRAY_END)
        if ch == "/":
            return self._lex_identifier()
        if ch == "(":
            return self._lex_string()
        if ch.isalpha():
            return self._lex_keyword(ch)
        if ch in "-+." or ch.isdigit():
            return self._lex_number(ch)

        raise SyntaxError(f"Unknown COS token: {ch!r}")

    def _lex_comment(self) -> None:
        while True:
            ch = self._get_char()
            if ch == "" or ch == "\n":
                break

    def _lex_number(self, ch: str) -> Token:
        if ch == ".":
            return self._lex_number_fract(self._get_char(), ch)
        if ch in "+-":
            return self._lex_number_int(self._get_char(), ch)
        return self._lex_number_int(ch, "")

    def _lex_number_int(self, ch: str, acc: str) -> Token:
        while True:
            if ch == ".":
                return self._lex_number_fract(self._get_char(), acc + ch)
            if ch == "":
                break
            if ch.isdigit():
                acc += ch
                ch = self._get_char()
            else:
                self._unget()
                break
        return Token(TK_NUMBER, float(acc) if "." in acc else int(acc))

    def _lex_number_fract(self, ch: str, acc: str) -> Token:
        while ch != "":
            if ch.isdigit():
                acc += ch
                ch = self._get_char()
            else:
                self._unget()
                break
        return Token(TK_NUMBER, float(acc))

    def _lex_keyword(self, ch: str) -> Token:
        kw = ch
        while True:
            c = self._get_char()
            if c == "" or not c.isalpha():
                if c:
                    self._unget()
                break
            kw += c
        if kw == "true":
            return Token(TK_BOOLEAN, True)
        if kw == "false":
            return Token(TK_BOOLEAN, False)
        if kw == "null":
            return Token(TK_NULL, None)
        raise SyntaxError(f"Unknown keyword: {kw}")

    def _lex_string(self) -> Token:
        encoding = "utf-8"
        raw: list[int] = []
        bom_checked = False

        while True:
            b = self._lex_string_char()
            if b == -1:
                break
            raw.append(b)
            if not bom_checked and len(raw) == 2:
                if raw[0] == 0xFE and raw[1] == 0xFF:
                    encoding = "utf-16-be"
                    raw.clear()
                elif raw[0] == 0xFF and raw[1] == 0xFE:
                    encoding = "utf-16-le"
                    raw.clear()
                bom_checked = True

        return Token(TK_STRING, bytes(raw).decode(encoding, errors="replace"))

    def _lex_string_char(self) -> int:
        b = self._get_byte()
        if b == -1:
            raise SyntaxError("Unterminated string")
        ch = chr(b)
        if ch == ")":
            return -1
        if ch == "\\":
            return self._lex_string_escape()
        if ch == "\r":
            nxt = self._get_char()
            if nxt != "\n" and nxt:
                self._unget()
            return 10
        if ch == "\n":
            nxt = self._get_char()
            if nxt != "\r" and nxt:
                self._unget()
            return 10
        return b

    def _lex_string_escape(self) -> int:
        ch = self._get_char()
        if ch == "":
            raise SyntaxError("Unterminated string escape")
        esc = {"b": 8, "n": 10, "f": 12, "r": 13}
        if ch in esc:
            return esc[ch]
        if ch in "()\\":
            return ord(ch)
        if ch in "01234567":
            octal = ch
            for _ in range(2):
                c = self._get_char()
                if c == "" or c not in "01234567":
                    if c:
                        self._unget()
                    break
                octal += c
            return int(octal, 8)
        raise SyntaxError(f"Invalid escape: \\{ch}")

    def _lex_hex_string(self, first_char: str) -> Token:
        count = 0
        result: list[int] = []
        prev = first_char

        while True:
            ch = self._get_char()
            if ch == "":
                raise SyntaxError("Unterminated hex string")
            if ch in "0123456789abcdefABCDEF":
                count += 1
                if count % 2 == 0:
                    result.append(int(prev + ch, 16))
                else:
                    prev = ch
            elif ch == ">":
                if count % 2 == 1:
                    result.append(int(prev + "0", 16))
                break
            elif not ch.isspace():
                raise SyntaxError(f"Invalid char in hex string: {ch!r}")

        return Token(TK_HEX_STRING, bytes(result))

    def _lex_identifier(self) -> Token:
        name = ""
        special = "()[]<>/%"
        while True:
            b = self._get_byte()
            if b == -1:
                break
            if b < 33 or b > 126:
                self._unget()
                break
            ch = chr(b)
            if ch == "#":
                hex_str = ""
                for _ in range(2):
                    c = self._get_char()
                    if c == "" or c not in "0123456789abcdefABCDEF":
                        raise SyntaxError("Invalid identifier escape")
                    hex_str += c
                name += chr(int(hex_str, 16))
            elif ch in special:
                self._unget()
                break
            else:
                name += ch
        return Token(TK_IDENTIFIER, name)

    # -- Parser --

    def parse(self) -> Any:
        self._lex()
        if self._lookahead.type == TK_IDENTIFIER:
            return self._parse_object_content()
        val = self._parse_value()
        if self._lookahead.type == TK_EOF:
            return val
        return [val] + self._parse_array_content()

    def _parse_object_content(self) -> dict:
        result: dict = {}
        while self._lookahead.type not in (TK_EOF, TK_DICT_END):
            if self._lookahead.type != TK_IDENTIFIER:
                raise SyntaxError(f"Expected identifier, got {self._lookahead.type}")
            key = self._lookahead.value
            self._lex()
            value = self._parse_value()
            result[key] = value
        return result

    def _parse_array_content(self) -> list:
        result = []
        while self._lookahead.type not in (TK_EOF, TK_ARRAY_END):
            result.append(self._parse_value())
        return result

    def _parse_value(self) -> Any:
        t = self._lookahead.type
        if t in (TK_STRING, TK_HEX_STRING, TK_NULL, TK_BOOLEAN,
                 TK_IDENTIFIER, TK_NUMBER):
            val = self._lookahead.value
            self._lex()
            return val
        if t == TK_DICT_START:
            self._lex()
            obj = self._parse_object_content()
            if self._lookahead.type != TK_DICT_END:
                raise SyntaxError("Expected '>>'")
            self._lex()
            return obj
        if t == TK_ARRAY_START:
            self._lex()
            arr = self._parse_array_content()
            if self._lookahead.type != TK_ARRAY_END:
                raise SyntaxError("Expected ']'")
            self._lex()
            return arr
        raise SyntaxError(f"Unexpected token type: {t}")
