from typing import Callable, Any

from amino import Either, List, Map, _
from amino.lazy import lazy
from amino.func import dispatch

from tubbs.formatter.indenter.cond import IndentCond, IndentCondOr, IndentCondAnd, Invariant
from tubbs.tatsu.indenter_dsl import (Parser, Expr, OrCond, AndCond, NotCond, Amount, Name, Cond, LambdaExpr, Range,
                                    AmountCond, CondStrict, Top, RangeCond)
from tubbs.formatter.indenter import info
from tubbs.formatter.indenter.info import IndentAmountRange

ranges = Map(
    here=info.Here,
    after=info.After,
    from_here=info.FromHere,
    children=info.Children,
    skip=info.Skip,
)


class Builder:

    def __init__(self, conds: Map[str, Any]) -> None:
        self.conds = conds

    @lazy
    def build(self) -> Callable[[Expr], Any]:
        types = List(Name, Cond, OrCond, AndCond, NotCond, AmountCond, LambdaExpr, Range, Amount, CondStrict, Top,
                     RangeCond)
        return dispatch(self, types, '')

    def name(self, expr: Name) -> str:
        return expr.data

    def lambda_expr(self, expr: LambdaExpr) -> Callable[[Any], Callable[..., bool]]:
        return expr.method_names.fold_left(_)(lambda z, a: getattr(z, a))

    def cond_strict(self, expr: CondStrict) -> IndentCond:
        name = expr.cond
        return self.conds.lift(name).get_or_fail(f'invalid condition: {name}')

    def cond(self, expr: Cond) -> IndentCond:
        name = expr.cond
        args = expr.arguments.map(self.build)
        f = self.conds.lift(name).get_or_fail(f'invalid condition: {name}')
        return f(*args)

    def or_cond(self, expr: OrCond) -> IndentCond:
        return IndentCondOr(self.build(expr.left), self.build(expr.right))

    def and_cond(self, expr: AndCond) -> IndentCond:
        return IndentCondAnd(self.build(expr.left), self.build(expr.right))

    def not_cond(self, expr: NotCond) -> IndentCond:
        raise Exception('condition negation is not implemented yet')

    def amount_cond(self, expr: AmountCond) -> IndentCond:
        return self.build(expr.expr).amount(expr.amount.value)

    def amount(self, expr: Amount) -> IndentCond:
        return Invariant().amout(expr.value)

    def _range(self, expr: Range) -> info.Range:
        return ranges.lift(expr.value).get_or_fail(f'invalid range: {expr.value}')

    def range(self, expr: Range) -> IndentCond:
        return Invariant().range(self._range(expr))

    def range_cond(self, expr: RangeCond) -> IndentCond:
        return self.build(expr.expr).range(self._range(expr.range))

    def top(self, expr: Top) -> IndentCond:
        sub = self.build(expr.expr)
        return sub if isinstance(sub, IndentAmountRange) else sub.amount(1)


def parse_indent_expr(parser: Parser, expr: str, conds: Map[str, Any]) -> Either[str, IndentCond]:
    ast = parser.parse(expr, 'top')
    return Builder(conds).build(ast.value)

__all__ = ('parse_indent_expr',)
