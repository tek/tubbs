from amino import _

from ribosome.util.callback import VimCallback
from ribosome.nvim import NvimFacade

from tubbs.formatter.breaker.main import Breaker as BreakerBase
from tubbs.formatter.breaker.cond import BreakCond
from tubbs.formatter.breaker.rules import BreakRules
from tubbs.formatter.breaker.state import BreakState
from tubbs.formatter.breaker.conds import (multi_line_block, sibling, parent_rule, sibling_rule, sibling_valid, after,
                                           inv, multi_line_block_for)


class ScalaBreakRules(BreakRules):

    def case_block_body(self, state: BreakState) -> BreakCond:
        return (multi_line_block.prio(1.1) | inv(0.91)).before

    # TODO __.parent_with_rule('caseBlock')
    def case_clause(self, state: BreakState) -> BreakCond:
        return (multi_line_block_for(_.parent.parent.parent.parent).prio(1.0) | inv(0.9)).before

    def param_clause(self, state: BreakState) -> BreakCond:
        return inv(0.7).before

    def implicit_param_clause(self, state: BreakState) -> BreakCond:
        return inv(0.75).before

    def block_body(self, state: BreakState) -> BreakCond:
        return inv(0.8).before

    def block_rest_stat(self, state: BreakState) -> BreakCond:
        return inv(0.8).before

    def seminl_semi(self, state: BreakState) -> BreakCond:
        return inv(1.1).after

    def lbrace(self, state: BreakState) -> BreakCond:
        return (multi_line_block.prio(1.0) | inv(0.31)).after

    def rbrace(self, state: BreakState) -> BreakCond:
        return (multi_line_block.prio(1.0) | sibling(_.body).prio(1.0) | sibling(_.lbrace).prio(1.0) | inv(0.31)).before

    def assign(self, state: BreakState) -> BreakCond:
        return (
            parent_rule('param').prio(0.0) |
            (sibling_rule(_.rhs, 'block') & sibling_valid(_.rhs) & after('lbrace')).prio(0.3) |
            inv(0.8)
        )


class Breaker(BreakerBase):

    def __init__(self, textwidth: int) -> None:
        super().__init__(ScalaBreakRules(), textwidth)


class VimBreaker(Breaker, VimCallback):

    def __init__(self, vim: NvimFacade) -> None:
        tw = vim.buffer.options('textwidth') | 120
        super().__init__(tw)

__all__ = ('ScalaBreakRules', 'Breaker', 'VimBreaker')
