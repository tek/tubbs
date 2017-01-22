from grako.exceptions import FailedKeywordSemantics
from grako.parsing import Parser as GrakoParser
from grako.ast import AST
from grako.contexts import Closure

import amino
from amino import L, _, List
from amino.lazy import lazy
from amino.func import dispatch

from tubbs.logging import Logging
from tubbs.formatter.tree import flatten_list
from tubbs.grako.ast import AstMap, AstToken, AstList, AstElem


def check_list(l, rule):
    for e in l:
        if type(e) is list:
            raise Exception('list {!r} in {!r} for `{}`'.format(e, l, rule))
        elif isinstance(e, list):
            check_list(e, rule)
        elif isinstance(e, AstMap):
            check_list(e.v, rule)


class PostProc:

    def __call__(self, ast, rule, pos, last_ws):
        return self.wrap_data(ast, rule, pos, last_ws)

    @lazy
    def wrap_data(self):
        return dispatch(self, [str, list, AstList, AstMap, AstToken, Closure],
                        'wrap_')

    def wrap_str(self, raw, rule, pos, last_ws):
        return AstToken(raw, pos, rule, last_ws)

    def wrap_list(self, raw, rule, pos, last_ws):
        return AstList(flatten_list(raw), rule)

    def wrap_ast_list(self, ast, rule, pos, last_ws):
        return ast

    def wrap_closure(self, raw, rule, pos, last_ws):
        return self.wrap_list(raw, rule, pos, last_ws)

    def wrap_ast_map(self, ast, rule, pos, last_ws):
        return ast

    def wrap_ast_token(self, token, rule, pos, last_ws):
        return token


class DataSemantics(Logging):

    def _special(self, ast, name):
        handler = getattr(self, '_special_{}'.format(name),
                          L(self._no_special)(name, _))
        return handler(ast)

    def _special_token(self, ast):
        raw = (flatten_list(ast) / _.raw).mk_string()
        ref = ast if isinstance(ast, AstElem) else ast[0]
        ws_count = (ast[0].ws_count
                    if isinstance(ast, list) else
                    ast.ws_count)
        return AstToken(raw, ref.pos, ref.rule, ws_count)

    def _no_special(self, name, ast):
        self.log.error('no handler for argument `{}` and {}'.format(name, ast))
        return ast

    def _default(self, ast, *a, **kw):
        ast1 = List.wrap(a).head / L(self._special)(ast, _) | ast
        return AstMap.from_ast(ast1) if isinstance(ast1, AST) else ast1


class ParserExt(GrakoParser):

    def __init__(self, **kw) -> None:
        super().__init__(**kw)
        self._pos_stack = [0]  # type: list
        self._last_ws = 0

    @lazy
    def post_proc(self):
        return PostProc()

    def _wrap_data(self, node, name):
        return self.post_proc(node, name, self._last_pos, self._last_ws)

    @property
    def _last_rule(self):
        return self._rule_stack[-1]

    @property
    def _last_pos(self):
        return self._pos_stack[-1]

    def _next_token(self):
        pre_pos = self._pos
        super()._next_token()
        pos = self._pos
        self._pos_stack.pop()
        self._pos_stack.append(pos)
        self._last_ws = pos - pre_pos

    def _call(self, rule, name, params, kwparams):
        self._pos_stack.append(self._pos)
        result = GrakoParser._call(self, rule, name, params, kwparams)
        wrapped = self._wrap_data(result, name)
        if amino.development and isinstance(wrapped, list):
            check_list(wrapped, name)
        self._pos_stack.pop()
        self._last_result = wrapped
        return wrapped

    def _add_cst_node(self, node):
        wrapped = self._wrap_data(node, self._last_rule)
        return super()._add_cst_node(wrapped)

    def name_last_node(self, name):
        node = (self.last_node
                if isinstance(self.last_node, AstElem) else
                self._wrap_data(self.last_node, self._last_rule))
        if name in self.ast:
            cur = self.ast[name]
            new = (
                cur.cat(node)
                if isinstance(cur, AstList) else
                self._wrap_data([cur, node], self._rule_stack[-2])
            )
            dict.__setitem__(self.ast, name, new)
        else:
            self.ast[name] = node

    def _check_name(self):
        name = str(self._last_result)
        if self.ignorecase or self._buffer.ignorecase:
            name = name.upper()
        if name in self.keywords:
            raise FailedKeywordSemantics('"%s" is a reserved word' % name)

__all__ = ('ParserExt', 'DataSemantics')
