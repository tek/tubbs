from amino import _

from ribosome.util.callback import VimCallback
from ribosome.nvim import NvimFacade

from tubbs.formatter.breaker.main import Breaker as BreakerBase
from tubbs.formatter.breaker.cond import BreakCond
from tubbs.formatter.breaker.rules import BreakRules
from tubbs.formatter.breaker.conds import (multi_line_block, sibling, parent_rule, sibling_rule, sibling_valid, after,
                                           inv, multi_line_block_parent, anon_func)


class ScalaBreakRules(BreakRules):

    def case_block_body(self) -> BreakCond:
        return (multi_line_block.prio(1.1) | inv(0.91)).before

    def case_clause(self) -> BreakCond:
        return (multi_line_block_parent('caseBlock').prio(1.0) | inv(0.9)).before

    def param_clause(self) -> BreakCond:
        return inv(0.7).before

    def implicit_param_clause(self) -> BreakCond:
        return inv(0.75).before

    def block_body_head(self) -> BreakCond:
        return (anon_func.prio(0.1) | multi_line_block_parent('statBlock', 'caseBlock').prio(1.0) | inv(0.8)).before

    def block_rest_stat(self) -> BreakCond:
        return (anon_func.prio(0.1) | inv(1.0)).before

    def seminl_semi(self) -> BreakCond:
        return inv(1.1).after

    def lbrace(self) -> BreakCond:
        return (sibling_rule(_.body.head, 'anonFuncExpr').prio(0.1) | multi_line_block.prio(1.0) | inv(0.31)).after

    def rbrace(self) -> BreakCond:
        return (
            multi_line_block.prio(1.0) |
            sibling(_.body).prio(1.0) |
            sibling(_.body.head).prio(1.0) |
            sibling(_.lbrace).prio(1.0) |
            inv(0.31)
        ).before

    def assign(self) -> BreakCond:
        return (
            parent_rule('param').prio(0.0) |
            (sibling_rule(_.rhs, 'block') & sibling_valid(_.rhs) & after('lbrace')).prio(0.3) |
            inv(0.65)
        ).after

    def extends(self) -> BreakCond:
        return inv(1.0).before

    def withkw(self) -> BreakCond:
        return inv(1.0).before


class Breaker(BreakerBase):

    def __init__(self, textwidth: int) -> None:
        super().__init__(ScalaBreakRules(), textwidth)


class VimBreaker(Breaker, VimCallback):

    def __init__(self, vim: NvimFacade) -> None:
        tw = vim.buffer.options('textwidth') | 120
        super().__init__(tw)

__all__ = ('ScalaBreakRules', 'Breaker', 'VimBreaker')
