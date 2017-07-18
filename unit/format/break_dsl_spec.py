from typing import Callable, Any

from tubbs.tatsu.break_dsl import Parser
from tubbs.formatter.breaker.dsl import parse_break_expr
from tubbs.formatter.breaker.state import BreakState
from tubbs.formatter.breaker.cond import (pred_cond_f, BreakCondSet, BreakCondPos, BreakCondOr, BreakCondPrio,
                                          PredCond)

from kallikrein import k, Expectation
from kallikrein.matchers.either import be_right
from kallikrein.matchers.typed import have_type
from kallikrein.matchers.maybe import be_just

from amino import Map, Boolean, _, __, List


@pred_cond_f('pred condition')
def condition(state: BreakState, par: str, attr: Callable[..., Any]) -> Callable[[BreakState], Boolean]:
    return attr(par)() == 'Param'


class BreakDslSpec:
    '''Break config DSL
    single priority $prio
    set of compound expressions $set
    '''

    def setup(self) -> None:
        self.parser = Parser()
        self.parser.gen()

    def prio(self) -> Expectation:
        num = 1.1
        res = self.parser.parse(str(num), 'expr')
        return k(res).must(be_right(num))

    def set(self) -> Expectation:
        expr = 'before:((1.1 @ condition(param, _.capitalize)) | 0.5 @ (boo & zoo)) + after:(0.2)'
        res = parse_break_expr(self.parser, expr, Map({'condition': condition}))
        state = BreakState(None, List())
        return (
            k(res).must(have_type(BreakCondSet)) &
            k(res.conds.head).must(be_just(have_type(BreakCondPos))) &
            k(res.conds.head / _.cond).must(be_just(have_type(BreakCondOr))) &
            k(res.conds.head / _.cond.left).must(be_just(have_type(BreakCondPrio))) &
            k(res.conds.head / _.cond.left.cond).must(be_just(have_type(PredCond))) &
            k(res.conds.head / __.cond.left.cond.f(state)).must(be_just(True))
        )

__all__ = ('BreakDslSpec',)
