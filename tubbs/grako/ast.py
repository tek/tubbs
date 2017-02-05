import abc
from typing import Callable, Union, TypeVar, Generic, Dict

from grako.ast import AST

from hues import huestr

from amino import List, Empty, _, L, Maybe, Either, Left, Right
from amino.func import call_by_name, dispatch_with


def indent(strings):
    return (
        strings.map(' {}'.format)
        if isinstance(strings, List) else
        [str(strings)]
    )


class AstElem(abc.ABC):

    @abc.abstractproperty
    def rule(self) -> str:
        ...

    @abc.abstractproperty
    def pos(self) -> int:
        ...

    @abc.abstractproperty
    def endpos(self) -> int:
        ...

    @property
    def range(self):
        return self.pos, self.endpos


class AstList(AstElem):

    def __init__(self, data: List, rule: str) -> None:
        self.data = data
        self._rule = rule

    @property
    def rule(self):
        return self._rule

    @property
    def head(self):
        return self.lift(0)

    @property
    def last(self):
        return self.lift(-1)

    @property
    def pos(self):
        return self.head.e / _.pos | -1

    @property
    def endpos(self):
        return self.last.e / _.endpos | -1

    def lift(self, key):
        return self.data.lift(key).cata(
            L(SubAst.cons)(_, key, self.rule),
            lambda: SubAstInvalid(key, self.rule, 'AstList index oob')
        )

    __getitem__ = lift

    def copy(self, data):
        return AstList(data, self._rule)

    def cat(self, elem):
        return self.copy(self.data.cat(elem))

    @property
    def ws_count(self):
        return self.head / _.ws_count | 0

    def __str__(self):
        return '{}({})'.format(self.__class__.__name__, self.data.join_comma)

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__,
                               (self.data / repr).join_comma)

    @property
    def k(self):
        return (self.data / _.rule).with_index

    @property
    def _keytree(self):
        return (
            indent(self.data // _._keytree)
            .cons('[{}]'.format(huestr(self.rule).red.colorized))
        )


class AstToken(AstElem):

    def __init__(self, raw, pos, rule, ws_count) -> None:
        self.raw = raw
        self._rule = rule
        self._pos = pos
        self.ws_count = ws_count

    @property
    def rule(self):
        return self._rule

    @property
    def pos(self):
        return self._pos

    @property
    def endpos(self):
        return self.pos + len(self.raw)

    def __str__(self):
        return self.raw

    def __repr__(self):
        raw = '\\n' if self.raw == '\n' else self.raw
        return '{}({}, {}, {}, {})'.format(
            self.__class__.__name__, self.rule, raw, self.pos,
            self.ws_count)

    @property
    def whitespace(self):
        return ' ' * self.ws_count

    @property
    def _keytree(self):
        return List('{} -> {}'.format(huestr(self.rule).red.colorized,
                                      huestr(self.raw).green.colorized))


class AstMap(AstElem, AST):

    @staticmethod
    def from_ast(ast: AST):
        a = AstMap()
        a.update(**ast)
        a._order = ast._order
        a._parseinfo = ast.parseinfo
        a._closed = ast._closed
        return a

    @property
    def rule(self):
        return self.parseinfo.rule

    @property
    def pos(self):
        return self.parseinfo.pos

    @property
    def endpos(self):
        return self.parseinfo.endpos

    def lift(self, key):
        msg = 'not present in AstMap({})'
        return Maybe(Dict.get(self, key)).cata(
            L(SubAst.cons)(_, key, self.rule),
            lambda: SubAstInvalid(key, self.rule,
                                  msg.format(' '.join(self.keys())))
        )

    def __getattr__(self, key):
        return self.lift(key)

    def get(self, key, default=None):
        return dict.get(self, key, default)

    def __str__(self):
        return 'AstMap({}, {})'.format(self.rule, dict(self))

    def __repr__(self):
        return 'AstMap(\'{}\', {})'.format(self.rule, dict.__repr__(self))

    @property
    def _keytree(self):
        def sub(key, ast):
            ckey = huestr(key).yellow.colorized
            return indent(indent(ast._keytree).cons(ckey))
        return (
            List.wrap(list(dict.items(self)))
            .flat_map2(sub)
            .cons('{{{}}}'.format(huestr(self.rule).red.colorized))
        )

    @property
    def keytree(self):
        return self._keytree.join_lines

A = TypeVar('A')


class SubAst(abc.ABC):

    @staticmethod
    def cons(data, key: str, rule: str) -> 'SubAst':
        cons = dispatch_with({AstMap: SubAstMap, AstList: SubAstList,
                              AstToken: SubAstToken})
        return cons(data)

    @staticmethod
    def from_maybe(data: Maybe[AstElem], key: str, rule: str, err: str):
        return data.cata(
            L(SubAstValid.cons)(_, key, rule),
            SubAstInvalid(key, rule, err)
        )

    def __getattr__(self, key):
        return self._getattr(key)

    @abc.abstractmethod
    def _getattr(self, key) -> 'SubAst':
        ...

    def __getitem__(self, key):
        return self._getitem(key)

    @abc.abstractmethod
    def _getitem(self, key) -> 'SubAst':
        ...

    def cata(self, f: Callable[[AstElem], A], b: Union[A, Callable[[], A]]
             ) -> A:
        return (
            f(self._data)
            if isinstance(self, SubAstValid)
            else call_by_name(b)
        )

    @abc.abstractproperty
    def e(self) -> Either[str, AstElem]:
        ...

    @property
    def _no_token(self):
        return 'ast is not a token'

    @property
    def raw(self):
        return (Right(self._data.raw)
                if isinstance(self, SubAstToken) else
                Left(self._no_token))


class SubAstValid(Generic[A], SubAst):

    def __init__(self, data: A) -> None:
        self._data = data

    def __str__(self):
        return '{}({})'.format(self.__class__.__name__, self._data)

    @property
    def rule(self):
        return self._data.rule

    @property
    def e(self):
        return Right(self._data)


class SubAstMap(SubAstValid[AstMap]):

    def _getattr(self, key):
        return self._data.lift(key)

    _getitem = _getattr

    @property
    def _keys(self):
        return self._data.k


class SubAstList(SubAstValid[AstList]):

    @property
    def head(self):
        return self[0]

    @property
    def last(self):
        return self[-1]

    def _getattr(self, key):
        return SubAstInvalid(key, self.rule,
                             'cannot access attrs in SubAstList')

    def _getitem(self, key):
        err = 'SubAstList index invalid: {}'.format(key)
        m = self._data.lift(key) if isinstance(key, int) else Empty()
        return SubAst.from_maybe(m, key, self.rule, err)

    def __str__(self):
        return '{}({})'.format(self.__class__.__name__,
                               self._data.data.join_comma)

    @property
    def _keys(self):
        return self._data.k


class SubAstToken(SubAstValid[AstToken]):

    def _getattr(self, key):
        return SubAstInvalid(key, self.rule,
                             'cannot access attrs in SubAstToken')

    def _getitem(self, key):
        return SubAstInvalid(key, self.rule,
                             'cannot access items in SubAstToken')


class SubAstInvalid(SubAst):

    def __init__(self, key: str, rule: str, reason: str) -> None:
        self.reason = reason
        self.key = key
        self.rule = rule

    def __str__(self):
        s = 'SubAstInvalid({}, {}, {})'
        return s.format(self.key, self.rule, self.reason)

    @property
    def _error(self):
        return 'no sub ast `{}` in `{}`: {}'.format(self.key, self.rule,
                                                    self.reason)

    def _getattr(self, key):
        return self

    def _getitem(self, key):
        return self

    @property
    def e(self):
        return Left(self._error)

    @property
    def _no_token(self):
        return self._error

__all__ = ('SubAst', 'SubAstValid', 'SubAstInvalid', 'AstMap')
