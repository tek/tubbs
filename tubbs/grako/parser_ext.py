from grako.exceptions import FailedToken, FailedKeywordSemantics, FailedPattern
from grako.parsing import Parser as GrakoParser
from grako.ast import AST

from amino import L, _, List
from amino.lazy import lazy
from amino.func import dispatch

from tubbs.logging import Logging
from tubbs.formatter.tree import flatten_list
from tubbs.grako.ast import AstMap, AstToken, AstList, AstElem


class PostProc:

    def __call__(self, ast, rule, pos, last_ws):
        return self.wrap_data(ast, rule, pos, last_ws)

    @lazy
    def wrap_data(self):
        return dispatch(self, [str, list, AstMap, AstToken], 'wrap_')

    def wrap_str(self, raw, rule, pos, last_ws):
        return AstToken(raw, pos, rule, last_ws)

    def wrap_list(self, raw, rule, pos, last_ws):
        return AstList(flatten_list(raw), rule)

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
        return (
            AstMap.from_ast(ast1)
            if isinstance(ast1, AST) else
            # flatten_list(ast1)
            # if isinstance(ast1, list) else
            ast1
        )


class ParserExt(GrakoParser):

    def __init__(self, **kw) -> None:
        super().__init__(**kw)
        self._poss = []  # type: list

    @lazy
    def post_proc(self):
        return PostProc()

    def _wrap_data(self, node, name, pos):
        return self.post_proc(node, name, self._last_pos, self._last_ws)

    @property
    def _last_rule(self):
        return self._rule_stack[-1]

    def _pattern(self, pattern):
        self._last_pos = pos = self._pos
        raw = self._buffer.matchre(pattern)
        if raw is None:
            self._trace_match('', pattern, failed=True)
            self._error(pattern, etype=FailedPattern)
            token = None
        else:
            token = AstToken(raw, pos, self._last_rule, self._last_ws)
        self._trace_match(token, pattern)
        self._add_cst_node(token)
        self._last_node = token
        return token

    def _token(self, raw):
        pre_pos = self._pos
        self._next_token()
        pos = self._pos
        self._last_ws = pos - pre_pos
        if self._buffer.match(raw) is None:
            self._trace_match(raw, failed=True)
            self._error(raw, etype=FailedToken)
        token = AstToken(raw, pos, self._last_rule, self._last_ws)
        self._trace_match(token)
        self._add_cst_node(token)
        self._last_node = token
        return token

    def name_last_node(self, name):
        node = (self.last_node
                if isinstance(self.last_node, AstElem) else
                self._wrap_data(self.last_node, name, self._last_pos))
        self.ast[name] = node

    def _call(self, rule, name, params, kwparams):
        self._last_pos = pos = self._pos
        self._poss.append(self._pos)
        result = GrakoParser._call(self, rule, name, params, kwparams)
        wrapped = self._wrap_data(result, name, pos)
        self._poss.pop()
        self._last_result = wrapped
        return wrapped

    def _check_name(self):
        name = str(self._last_result)
        if self.ignorecase or self._buffer.ignorecase:
            name = name.upper()
        if name in self.keywords:
            raise FailedKeywordSemantics('"%s" is a reserved word' % name)

__all__ = ('ParserExt', 'DataSemantics')
