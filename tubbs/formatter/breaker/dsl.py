from typing import Callable, Any

from amino import Either, List, Map, _
from amino.lazy import lazy
from amino.func import dispatch

from tubbs.formatter.breaker.cond import BreakCond, BreakCondOr, BreakCondAnd, BreakCondSet
from tubbs.tatsu.breaker_dsl import (Parser, Expr, OrCond, AndCond, NotCond, Prio, Name, Cond, LambdaExpr, Top, Side,
                                   PrioCond, CondStrict)
from tubbs.formatter.breaker.conds import inv


class Builder:

    def __init__(self, conds: Map[str, Any]) -> None:
        self.conds = conds

    @lazy
    def build(self) -> Callable[[Expr], Any]:
        types = List(Name, Cond, OrCond, AndCond, NotCond, PrioCond, LambdaExpr, Top, Side, Prio, CondStrict)
        return dispatch(self, types, '')

    def name(self, expr: Name) -> str:
        return expr.data

    def lambda_expr(self, expr: LambdaExpr) -> Callable[[Any], Callable[..., bool]]:
        return expr.method_names.fold_left(_)(lambda z, a: getattr(z, a))

    def cond_strict(self, expr: CondStrict) -> BreakCond:
        name = expr.cond
        return self.conds.lift(name).get_or_fail(f'invalid condition: {name}')

    def cond(self, expr: Cond) -> BreakCond:
        name = expr.cond
        args = expr.arguments.map(self.build)
        f = self.conds.lift(name).get_or_fail(f'invalid condition: {name}')
        return f(*args)

    def or_cond(self, expr: OrCond) -> BreakCond:
        return BreakCondOr(self.build(expr.left), self.build(expr.right))

    def and_cond(self, expr: AndCond) -> BreakCond:
        return BreakCondAnd(self.build(expr.left), self.build(expr.right))

    def not_cond(self, expr: NotCond) -> BreakCond:
        raise Exception('condition negation is not implemented yet')

    def prio_cond(self, expr: PrioCond) -> BreakCond:
        return self.build(expr.expr).prio(expr.prio.value)

    def prio(self, expr: Prio) -> BreakCond:
        return inv(expr.value)

    def side(self, expr: Side) -> BreakCond:
        cond = self.build(expr.expr)
        return cond.before if expr.side == 'before' else cond.after

    def top(self, expr: Top) -> BreakCond:
        return BreakCondSet(expr.conds / self.build)


def parse_break_expr(parser: Parser, expr: str, conds: Map[str, Any]) -> Either[str, BreakCond]:
    ast = parser.parse(expr, 'top')
    return Builder(conds).build(ast.value)

__all__ = ('parse_break_expr',)
