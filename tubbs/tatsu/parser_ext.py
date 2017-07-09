from functools import namedtuple
from typing import Any, Callable, Union, cast

from tatsu.exceptions import FailedKeywordSemantics, FailedPattern
from tatsu.parsing import Parser as TatsuParser
from tatsu.ast import AST
from tatsu.contexts import closure, tatsumasu

import regex

import amino
from amino import L, _, List, LazyList
from amino.lazy import lazy
from amino.func import dispatch
from amino.list import flatten

from tubbs.logging import Logging
from tubbs.tatsu.ast import AstMap, AstToken, AstList, AstElem, Line, AstClosure


AstData = Union[str, list, AstList, AstMap, AstToken, closure, None]


def flatten_list(data: AstElem) -> List:
    def flat(data: AstElem) -> List:
        l = data.sub.drain if isinstance(data, AstList) else data
        return (
            flatten(map(flat, l))
            if isinstance(l, list) else
            [l]
        )
    return List.wrap(flat(data))


def check_list(l: Any, rule: str) -> None:
    for e in l:
        if type(e) is list:
            raise Exception('list {!r} in {!r} for `{}`'.format(e, l, rule))
        elif isinstance(e, list):
            check_list(e, rule)
        elif isinstance(e, AstMap):
            check_list(e.v, rule)


def process_list(data: Any) -> List:
    def loop(data: Any) -> list:
        return (
            flatten(map(loop, data))
            if isinstance(data, list) else
            [data]
        )
    return List.wrap(loop(data)).filter_not(_.empty)


class PostProc:

    def __call__(self, ast: AstData, parser: 'ParserExt', rule: str) -> Union[AstElem, None]:
        return self.wrap_data(ast, parser, rule)

    @lazy
    def wrap_data(self) -> Callable:
        return dispatch(self, [str, list, AstList, AstMap, AstToken, closure, type(None)], 'wrap_')

    def wrap_str(self, raw: str, parser: 'ParserExt', rule: str) -> AstElem:
        return AstToken(raw, parser._last_pos, parser._line, rule, parser._take_ws())

    def wrap_list(self, raw: list, parser: 'ParserExt', rule: str) -> AstElem:
        return AstList(LazyList(process_list(raw)), rule, parser._line)

    def wrap_ast_list(self, ast: AstList, parser: 'ParserExt', rule: str) -> AstElem:
        return ast

    def wrap_closure(self, raw: closure, parser: 'ParserExt', rule: str) -> AstElem:
        return AstClosure(LazyList(process_list(raw)), rule, parser._line)

    def wrap_ast_map(self, ast: AstMap, parser: 'ParserExt', rule: str) -> AstElem:
        return ast

    def wrap_ast_token(self, token: AstToken, parser: 'ParserExt', rule: str) -> AstElem:
        return token

    def wrap_none_type(self, n: None, parser: 'ParserExt', rule: str) -> None:
        pass


FlattenToken = namedtuple('FlattenToken', 'data')


class DataSemantics(Logging):

    def __init__(self) -> None:
        self.made_token = False

    def special(self, ast: AstData, name: str) -> AstData:
        handler = getattr(self, 'special_{}'.format(name), L(self._nospecial)(name, _))
        return handler(ast)

    def special_token(self, ast: AstData) -> AstToken:
        self.made_token = True
        return ast if isinstance(ast, AstToken) else self.flatten_token(ast)

    def flatten_token(self, ast: AstData) -> AstToken:
        raw = (flatten_list(ast) / _.raw).mk_string()
        pos = (
            ast[0].pos
            if isinstance(ast, list) else
            cast(AstList, ast).head.e / _.pos | -1
            if isinstance(ast, AstList) else
            cast(AstToken, ast).pos
            if isinstance(ast, AstToken) else
            (-1)
        )
        ws_count = (ast[0].ws_count
                    if isinstance(ast, list) else
                    cast(AstElem, ast).ws_count)
        line = (ast[0].line
                if isinstance(ast, list) else
                cast(AstElem, ast).line)
        return AstToken(raw, pos, line, '', ws_count)

    def _nospecial(self, name: str, ast: AstData) -> AstData:
        self.log.error('no handler for argument `{}` and {}'.format(name, ast))
        return ast

    def _default(self, ast: AstData, *a: Any, **kw: Any) -> AstData:
        ast1 = List.wrap(a).head / L(self.special)(ast, _) | ast
        return AstMap.from_ast(ast1) if isinstance(ast1, AST) else ast1

    def _postproc(self, parser: 'ParserExt', data: AstElem) -> None:
        if self.made_token:
            data._rule = parser._last_rule
            if data._pos == -1:
                data._pos = parser._last_pos
            self.made_token = False


class ParserExt(TatsuParser):

    def __init__(self, **kw: Any) -> None:
        super().__init__(**kw)
        self._pos_stack = [0]  # type: list
        self._last_ws = 0

    @lazy
    def post_proc(self) -> PostProc:
        return PostProc()

    def _wrap_data(self, node: AstData, name: str) -> AstData:
        return self.post_proc(node, self, name)

    @property
    def _last_rule(self) -> str:
        return self._rule_stack[-1] if len(self._rule_stack) >= 1 else 'none'

    @property
    def _penultimate_rule(self) -> str:
        return self._rule_stack[-2] if len(self._rule_stack) >= 2 else 'none'

    @property
    def _last_pos(self) -> int:
        return self._pos_stack[-1] if len(self._rule_stack) >= 1 else -1

    @property
    def _line(self) -> Line:
        return Line.from_line_info(self._buffer.line_info(self._last_pos))

    def _take_ws(self) -> int:
        ws = self._last_ws
        self._last_ws = 0
        return ws

    def _next_token(self, ruleinfo: Any=None) -> None:
        pre_pos = self._pos
        super()._next_token(ruleinfo)
        pos = self._pos
        self._pos_stack.pop()
        self._pos_stack.append(pos)
        ws = pos - pre_pos
        if ws > 0:
            self._last_ws = ws

    def _call(self, info: Any) -> Any:
        try:
            self._pos_stack.append(self._pos)
            result = TatsuParser._call(self, info)
            wrapped = self._wrap_data(result, info.name)
            if amino.development and isinstance(wrapped, list):
                check_list(wrapped, info.name)
            self._last_result = wrapped
            return wrapped
        finally:
            self._pos_stack.pop()

    def _add_cst_node(self, node: AstData) -> Any:
        wrapped = self._wrap_data(node, self._last_rule)
        return super()._add_cst_node(wrapped)

    def name_last_node(self, name: str) -> None:
        def after_cst() -> bool:
            return isinstance(self.cst, AstToken) and self.cst.raw == self.last_node
        node = (self.last_node
                if isinstance(self.last_node, AstElem) else
                self.cst
                if after_cst() else
                self._wrap_data(self.last_node, self._last_rule))
        if name in self.ast:
            cur = self.ast[name]
            new = (
                cur.cat(node)
                if isinstance(cur, AstList) else
                self._wrap_data([cur, node], self._penultimate_rule)
            )
            dict.__setitem__(self.ast, name, new)
        else:
            self.ast[name] = node

    def _check_name(self) -> None:
        name = str(self._last_result)
        if self.ignorecase or self._buffer.ignorecase:
            name = name.upper()
        if name in self.keywords:
            raise FailedKeywordSemantics('"%s" is a reserved word' % name)

    def _unicode_category(self, pat: str) -> str:
        def err(p: str) -> None:
            self._trace_match('', p, failed=True)
            self._error(p, exclass=FailedPattern)
        token = self._buffer.matchre('.')
        if token is None:
            err('.')
            return ''
        else:
            m = regex.match(pat, token)
            if m is None:
                err(pat)
                return ''
            else:
                self._trace_match(token, pat)
                self._add_cst_node(token)
                self._last_node = token
                return token

    @tatsumasu()
    def _UnicodeUpper_(self) -> str:
        return self._unicode_category('\p{Lu}')

    @tatsumasu()
    def _UnicodeLower_(self) -> str:
        return self._unicode_category('\p{Ll}')

    @tatsumasu()
    def _UnicodeLetterMisc_(self) -> str:
        return self._unicode_category('\p{Lo}|\p{Lt}|\p{Nl}')

    @tatsumasu()
    def _UnicodeOpchar_(self) -> str:
        return self._unicode_category('\p{Sm}|\p{So}')

__all__ = ('ParserExt', 'DataSemantics')
