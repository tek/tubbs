from ribosome.nvim import NvimFacade

from tubbs.formatter.indenter.main import Indenter as IndenterBase, IndentResult, IndentRules
from tubbs.formatter.indenter.state import IndentState
from tubbs.formatter.indenter.indent import keep, after, from_here, children


class ScalaIndentRules(IndentRules):

    def assign_eol(self, state: IndentState) -> IndentResult:
        return after(state.data, 1)

    def block_body_bol(self, state: IndentState) -> IndentResult:
        return children(state.data, 1)

    def case_clauses_bol(self, state: IndentState) -> IndentResult:
        return children(state.data, 1)

    def apply_expr_chain_app_bol(self, state: IndentState) -> IndentResult:
        return keep(state.data) if state.sibling_indent else from_here(state.data, 1)


class Indenter(IndenterBase):

    def __init__(self, shiftwidth: int) -> None:
        super().__init__(ScalaIndentRules(), shiftwidth)


class VimIndenter(Indenter):

    def __init__(self, vim: NvimFacade) -> None:
        sw = vim.buffer.options('shiftwidth') | 2
        super().__init__(sw)

__all__ = ('Indenter', 'VimIndenter')
