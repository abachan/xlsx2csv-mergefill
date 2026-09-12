"""ブック名だけに依存する限定的な数式を安全に評価する内部処理。"""

from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET
from typing import Sequence

from openpyxl.formula.tokenizer import Token, Tokenizer, TokenizerError


_SPREADSHEETML_NAMESPACE = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_CELL_TAG = f"{{{_SPREADSHEETML_NAMESPACE}}}c"
_FORMULA_TAG = f"{{{_SPREADSHEETML_NAMESPACE}}}f"
_VALUE_TAG = f"{{{_SPREADSHEETML_NAMESPACE}}}v"
_INLINE_STRING_TAG = f"{{{_SPREADSHEETML_NAMESPACE}}}is"
_MAX_FORMULA_LENGTH = 8192
_MAX_TOKEN_COUNT = 2048
_MAX_PARSE_DEPTH = 64
_MAX_CELL_TEXT_LENGTH = 32767
_FILENAME_CELL_PATTERN = re.compile(
    rb'@?CELL\s*\(\s*"filename"',
    flags=re.IGNORECASE,
)
_LOCAL_CELL_REFERENCE_PATTERN = re.compile(
    r"\$?[A-Z]{1,3}\$?[1-9][0-9]*(?::\$?[A-Z]{1,3}\$?[1-9][0-9]*)?",
    flags=re.IGNORECASE,
)
_LOCAL_CELL_REFERENCE = object()


class _UnsupportedFormula(ValueError):
    """安全な限定評価の対象外であることを表す内部例外。"""


class _FormulaParser:
    """外部参照や任意コード実行を持たない限定的な数式パーサー。"""

    def __init__(self, formula: str, filename_context: str) -> None:
        try:
            tokens = Tokenizer(formula).items
        except (TokenizerError, IndexError, TypeError, ValueError) as error:
            raise _UnsupportedFormula from error

        self._tokens = [token for token in tokens if token.type != Token.WSPACE]
        if len(self._tokens) > _MAX_TOKEN_COUNT:
            raise _UnsupportedFormula
        self._position = 0
        self._depth = 0
        self._filename_context = filename_context
        self.used_filename_context = False

    def parse(self) -> object:
        result = self._parse_concatenation()
        if self._position != len(self._tokens):
            raise _UnsupportedFormula
        return result

    def _parse_concatenation(self) -> object:
        value = self._parse_additive()
        while self._accept_infix("&"):
            value = _as_text(value) + _as_text(self._parse_additive())
        return value

    def _parse_additive(self) -> object:
        value = self._parse_multiplicative()
        while True:
            if self._accept_infix("+"):
                value = _as_number(value) + _as_number(self._parse_multiplicative())
            elif self._accept_infix("-"):
                value = _as_number(value) - _as_number(self._parse_multiplicative())
            else:
                return value

    def _parse_multiplicative(self) -> object:
        value = self._parse_unary()
        while True:
            if self._accept_infix("*"):
                value = _as_number(value) * _as_number(self._parse_unary())
            elif self._accept_infix("/"):
                divisor = _as_number(self._parse_unary())
                if divisor == 0:
                    raise _UnsupportedFormula
                value = _as_number(value) / divisor
            else:
                return value

    def _parse_unary(self) -> object:
        token = self._peek()
        if token is not None and token.type == Token.OP_PRE:
            self._position += 1
            value = _as_number(self._parse_unary())
            if token.value == "+":
                return value
            if token.value == "-":
                return -value
            raise _UnsupportedFormula
        return self._parse_primary()

    def _parse_primary(self) -> object:
        token = self._peek()
        if token is None:
            raise _UnsupportedFormula

        if token.type == Token.OPERAND:
            self._position += 1
            return _parse_operand(token)

        if token.type == Token.PAREN and token.subtype == Token.OPEN:
            self._position += 1
            value = self._parse_concatenation()
            self._expect(Token.PAREN, Token.CLOSE)
            return value

        if token.type == Token.FUNC and token.subtype == Token.OPEN:
            return self._parse_function()

        raise _UnsupportedFormula

    def _parse_function(self) -> object:
        if self._depth >= _MAX_PARSE_DEPTH:
            raise _UnsupportedFormula

        opening = self._tokens[self._position]
        self._position += 1
        self._depth += 1
        try:
            arguments: list[object] = []
            closing = self._peek()
            if closing is None:
                raise _UnsupportedFormula
            if not (closing.type == Token.FUNC and closing.subtype == Token.CLOSE):
                while True:
                    arguments.append(self._parse_concatenation())
                    separator = self._peek()
                    if separator is None:
                        raise _UnsupportedFormula
                    if separator.type == Token.SEP and separator.subtype == Token.ARG:
                        self._position += 1
                        continue
                    break
            self._expect(Token.FUNC, Token.CLOSE)
            function_name = opening.value[:-1].lstrip("@").upper()
            return self._call_function(function_name, arguments)
        finally:
            self._depth -= 1

    def _call_function(self, name: str, arguments: Sequence[object]) -> object:
        if name == "CELL":
            if len(arguments) not in {1, 2}:
                raise _UnsupportedFormula
            if _as_text(arguments[0]).casefold() != "filename":
                raise _UnsupportedFormula
            if len(arguments) == 2 and arguments[1] is not _LOCAL_CELL_REFERENCE:
                raise _UnsupportedFormula
            self.used_filename_context = True
            return self._filename_context

        if name in {"_XLFN.SINGLE", "_XLWS.SINGLE"}:
            _require_argument_count(arguments, 1)
            return arguments[0]

        if name == "MID":
            _require_argument_count(arguments, 3)
            text = _as_text(arguments[0])
            start = _as_integer(arguments[1])
            length = _as_integer(arguments[2])
            if start < 1 or length < 0:
                raise _UnsupportedFormula
            return text[start - 1 : start - 1 + length]

        if name in {"SEARCH", "FIND"}:
            if len(arguments) not in {2, 3}:
                raise _UnsupportedFormula
            needle = _as_text(arguments[0])
            haystack = _as_text(arguments[1])
            start = _as_integer(arguments[2]) if len(arguments) == 3 else 1
            return _find_text(needle, haystack, start, case_sensitive=name == "FIND")

        if name == "LEN":
            _require_argument_count(arguments, 1)
            return len(_as_text(arguments[0]))

        if name in {"LEFT", "RIGHT"}:
            if len(arguments) not in {1, 2}:
                raise _UnsupportedFormula
            text = _as_text(arguments[0])
            length = _as_integer(arguments[1]) if len(arguments) == 2 else 1
            if length < 0:
                raise _UnsupportedFormula
            return text[:length] if name == "LEFT" else text[len(text) - length :]

        if name == "SUBSTITUTE":
            if len(arguments) not in {3, 4}:
                raise _UnsupportedFormula
            text = _as_text(arguments[0])
            old = _as_text(arguments[1])
            new = _as_text(arguments[2])
            if not old:
                return text
            if len(arguments) == 3:
                return text.replace(old, new)
            instance = _as_integer(arguments[3])
            if instance < 1:
                raise _UnsupportedFormula
            return _replace_instance(text, old, new, instance)

        raise _UnsupportedFormula

    def _accept_infix(self, value: str) -> bool:
        token = self._peek()
        if token is None or token.type != Token.OP_IN or token.value != value:
            return False
        self._position += 1
        return True

    def _expect(self, token_type: str, subtype: str) -> None:
        token = self._peek()
        if token is None or token.type != token_type or token.subtype != subtype:
            raise _UnsupportedFormula
        self._position += 1

    def _peek(self) -> Token | None:
        if self._position >= len(self._tokens):
            return None
        return self._tokens[self._position]


def _parse_operand(token: Token) -> object:
    if token.subtype == Token.TEXT:
        if len(token.value) < 2:
            raise _UnsupportedFormula
        return token.value[1:-1].replace('""', '"')
    if token.subtype == Token.NUMBER:
        try:
            number = float(token.value)
        except ValueError as error:
            raise _UnsupportedFormula from error
        if not math.isfinite(number):
            raise _UnsupportedFormula
        return int(number) if number.is_integer() else number
    if token.subtype == Token.LOGICAL:
        return token.value.upper() == "TRUE"
    if token.subtype == Token.RANGE and _LOCAL_CELL_REFERENCE_PATTERN.fullmatch(
        token.value
    ):
        return _LOCAL_CELL_REFERENCE
    raise _UnsupportedFormula


def _as_text(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float) and math.isfinite(value):
        return format(value, ".15g")
    raise _UnsupportedFormula


def _as_number(value: object) -> int | float:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)) and math.isfinite(value):
        return value
    raise _UnsupportedFormula


def _as_integer(value: object) -> int:
    return int(_as_number(value))


def _require_argument_count(arguments: Sequence[object], expected: int) -> None:
    if len(arguments) != expected:
        raise _UnsupportedFormula


def _find_text(needle: str, haystack: str, start: int, case_sensitive: bool) -> int:
    if start < 1 or start > len(haystack) + 1:
        raise _UnsupportedFormula
    remainder = haystack[start - 1 :]
    if case_sensitive:
        position = remainder.find(needle)
    else:
        pattern = _search_pattern(needle)
        match = re.search(pattern, remainder, flags=re.IGNORECASE | re.DOTALL)
        position = -1 if match is None else match.start()
    if position < 0:
        raise _UnsupportedFormula
    return start + position


def _search_pattern(text: str) -> str:
    """Excel SEARCH のワイルドカードを正規表現へ変換する。"""
    parts: list[str] = []
    escaped = False
    for character in text:
        if escaped:
            parts.append(re.escape(character))
            escaped = False
        elif character == "~":
            escaped = True
        elif character == "?":
            parts.append(".")
        elif character == "*":
            parts.append(".*?")
        else:
            parts.append(re.escape(character))
    if escaped:
        parts.append(re.escape("~"))
    return "".join(parts)


def _replace_instance(text: str, old: str, new: str, instance: int) -> str:
    start = 0
    for _ in range(instance):
        position = text.find(old, start)
        if position < 0:
            return text
        start = position + len(old)
    return text[:position] + new + text[start:]


def _evaluate_filename_only_formula(formula: str, workbook_filename: str) -> str | None:
    """パスやシート名には依存せず、ブック名だけで決まる式の結果を返す。"""
    if not formula.startswith("="):
        formula = f"={formula}"
    if len(formula) > _MAX_FORMULA_LENGTH:
        return None

    contexts = (
        rf"C:\xlsx2csv-a\[{workbook_filename}]SheetA",
        rf"Z:\a-much-longer\異なるパス\[{workbook_filename}]DifferentSheetName",
    )
    results: list[object] = []
    try:
        for context in contexts:
            parser = _FormulaParser(formula, context)
            result = parser.parse()
            if not parser.used_filename_context:
                return None
            results.append(result)
    except (ArithmeticError, OverflowError, RecursionError, _UnsupportedFormula):
        return None

    first, second = results
    if not isinstance(first, str) or first != second:
        return None
    if len(first) > _MAX_CELL_TEXT_LENGTH:
        return None
    return first


def _refresh_filename_formula_caches(content: bytes, workbook_filename: str) -> bytes:
    """安全に評価できるブック名依存式の保存済み値だけをメモリ上で更新する。"""
    if b'"filename"' not in content and b'"FILENAME"' not in content:
        return content
    if _FILENAME_CELL_PATTERN.search(content) is None:
        return content

    root = ET.fromstring(content)
    changed = False
    for cell in root.iter(_CELL_TAG):
        formula_element = cell.find(_FORMULA_TAG)
        if formula_element is None or not formula_element.text:
            continue
        result = _evaluate_filename_only_formula(
            formula_element.text,
            workbook_filename,
        )
        if result is None:
            continue
        changed = _set_cached_string(cell, result) or changed

    if not changed:
        return content
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _set_cached_string(cell: ET.Element, value: str) -> bool:
    cached_value = cell.find(_VALUE_TAG)
    if (
        cell.get("t") == "str"
        and cached_value is not None
        and cached_value.text == value
    ):
        return False

    cell.set("t", "str")
    inline_string = cell.find(_INLINE_STRING_TAG)
    if inline_string is not None:
        cell.remove(inline_string)
    if cached_value is None:
        cached_value = ET.Element(_VALUE_TAG)
        formula_element = cell.find(_FORMULA_TAG)
        insertion_index = list(cell).index(formula_element) + 1
        cell.insert(insertion_index, cached_value)
    cached_value.text = value
    return True
