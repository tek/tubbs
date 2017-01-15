import abc
from typing import Callable, Union, TypeVar

from grako.ast import AST

from amino import Map, List, Just, Empty, _, L, Maybe
from amino.func import call_by_name, dispatch_with

from ribosome.record import Record, str_field, int_field


def to_list(a):
    return List.wrap(a) if isinstance(a, list) else a


class AstElem:
    pass


class AstList(AstElem, List):

    def __init__(self, data, rule, pos) -> None:
        self.rule = rule
        self.pos = pos
        super().__init__(*data)


class AstToken(AstElem, Record):
    raw = str_field()
    pos = int_field()
    rule = str_field()

    @property
    def _str_extra(self):
        return List(self.raw, self.pos, self.rule)

    @property
    def range(self):
        return self.pos, self.pos + len(self.raw)


class AstMap(AstElem, AST, Map):

    @staticmethod
    def from_ast(ast: AST):
        a = AstMap()
        a.update(**ast)
        a._order = ast._order
        a._parseinfo = ast.parseinfo
        a._closed = ast._closed
        return a

    def lift(self, key):
        return super().lift(key).cata(
            L(SubAst.cons)(_, key, self.rule),
            lambda: SubAstInvalid(key, self.rule, 'not present in AstMap')
        )

    def __getattr__(self, key):
        return self.lift(key)  # / to_list

    def get(self, key, default=None):
        return dict.get(self, key, default)

    @property
    def rule(self):
        return self.parseinfo.rule

    def __str__(self):
        return 'AstMap({}, {})'.format(self.rule, dict(self))

    def __repr__(self):
        return 'AstMap(\'{}\', {})'.format(self.rule, dict.__repr__(self))

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

    def cata(self, f: Callable[[AstElem], A], b: Union[A, Callable[[], A]]
             ) -> A:
        return (
            f(self.data)
            if isinstance(self, SubAstValid)
            else call_by_name(b)
        )

    @property
    def m(self):
        return self.cata(Just, Empty())

    @property
    def raw_m(self):
        return (Just(self.data.raw)
                if isinstance(self, SubAstToken) else
                Empty())


class SubAstValid(SubAst):

    def __init__(self, data) -> None:
        self.data = data

    def __str__(self):
        return '{}({})'.format(self.__class__.__name__, self.data)

    def __getattr__(self, key):
        return self._getattr(key)

    @abc.abstractmethod
    def _getattr(self, key) -> SubAst:
        ...

    def __getitem__(self, key):
        return self._getitem(key)

    @abc.abstractmethod
    def _getitem(self, key) -> SubAst:
        ...

    @property
    def rule(self):
        return self.data.rule


class SubAstMap(SubAstValid):

    def _getattr(self, key):
        return self.data.lift(key)

    _getitem = _getattr


class SubAstList(SubAstValid):

    def _getattr(self, key):
        return SubAstInvalid(key, self.rule,
                             'cannot access attrs in SubAstList')

    def _getitem(self, key):
        err = 'SubAstList index invalid: {}'.format(key)
        m = self.data.lift(key) if isinstance(key, int) else Empty()
        return SubAst.from_maybe(m, key, self.rule, err)


class SubAstToken(SubAstValid):

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
        return 'SubAstInvalid({}, {})'.format(self.key, self.rule, self.reason)

    def _getattr(self, key):
        return self

    def _getitem(self, key):
        return self

__all__ = ('SubAst', 'SubAstValid', 'SubAstInvalid', 'AstMap')
