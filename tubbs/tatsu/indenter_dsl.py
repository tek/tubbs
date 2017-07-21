from tatsu.parsing import Parser as TatsuParser
from tatsu.semantics import ModelBuilderSemantics
from tatsu.objectmodel import Node

from tubbs.tatsu.base import BuiltinParser
from tubbs.tatsu.ast import AstElem

from amino import Either, Try, _, List
from amino.list import Lists


class Expr(Node):
    pass


class Arg(Expr):
    pass


class Name(Arg):
    pass


class Method(Expr):
    pass


class LambdaExpr(Arg):

    @property
    def method_names(self) -> List[str]:
        return Lists.wrap(self.methods) / _.name.data


class Cond(Expr):

    @property
    def cond(self) -> str:
        return self.name.data

    @property
    def arguments(self) -> List[Arg]:
        return Lists.wrap(self.args) if isinstance(self.args, list) else List(self.args)


class CondStrict(Expr):

    @property
    def cond(self) -> str:
        return self.name.data


class OrCond(Expr):
    pass


class AndCond(Expr):
    pass


class NotCond(Expr):
    pass


class Parenthesized(Expr):
    pass


class Amount(Expr):
    pass


class AmountCond(Expr):
    pass


class Range(Expr):
    pass


class RangeCond(Expr):
    pass


class Top(Expr):
    pass


class Parser(BuiltinParser):

    @property
    def name(self) -> str:
        return 'indenter_dsl'

    @property
    def left_recursion(self) -> bool:
        return True

    def cons_parser(self, tpe: type) -> Either[str, TatsuParser]:
        return Try(lambda *a, **kw: tpe(*a, **kw), **self.parser_args)

    @property
    def semantics(self) -> bool:
        types = [Expr, Name, Cond, OrCond, AndCond, NotCond, Parenthesized, AmountCond, LambdaExpr, Method, Range,
                 Amount, CondStrict, Top, RangeCond]
        return ModelBuilderSemantics(types=types)


def parse(text: str, rule: str) -> Either[str, AstElem]:
    return Parser().parse(text, rule)

__all__ = ('parse',)
