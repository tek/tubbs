from ribosome.nvim import NvimFacade

from tubbs.formatter.indenter.main import Indenter as IndenterBase, IndentResult, IndentRules
from tubbs.formatter.indenter.conds import inv, sibling_indent


class ScalaIndentRules(IndentRules):

    def assign_eol(self) -> IndentResult:
        return inv.after

    def block_body_bol(self) -> IndentResult:
        return inv.children

    def case_clauses_bol(self) -> IndentResult:
        return inv.children

    def apply_expr_chain_app_bol(self) -> IndentResult:
        return sibling_indent.keep | inv.from_here


class Indenter(IndenterBase):

    def __init__(self, shiftwidth: int) -> None:
        super().__init__(ScalaIndentRules(), shiftwidth)


class VimIndenter(Indenter):

    def __init__(self, vim: NvimFacade) -> None:
        sw = vim.buffer.options('shiftwidth') | 2
        super().__init__(sw)

__all__ = ('Indenter', 'VimIndenter')
