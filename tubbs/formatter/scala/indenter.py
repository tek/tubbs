from ribosome.nvim import NvimFacade

from tubbs.formatter.indenter import Indenter as IndenterBase, Indent, after, from_here, IndentResult, keep, children
from tubbs.tatsu.ast import RoseData
from tubbs.formatter.indenter import IndentRules


class ScalaIndentRules(IndentRules):

    def assign_eol(self, node: RoseData) -> IndentResult:
        return after(node, 1)

    def block_body_bol(self, node: RoseData) -> Indent:
        return children(node, 1) if node.bol else keep(node)

    def case_clauses_bol(self, node: RoseData) -> IndentResult:
        return children(node, 1) if node.bol else keep(node)

    def apply_expr_chain_bol(self, node: RoseData) -> IndentResult:
        return from_here(node, 1)


class Indenter(IndenterBase):

    def __init__(self, shiftwidth: int) -> None:
        super().__init__(ScalaIndentRules(), shiftwidth)


class VimIndenter(Indenter):

    def __init__(self, vim: NvimFacade) -> None:
        sw = vim.buffer.options('shiftwidth') | 2
        super().__init__(sw)

__all__ = ('Indenter', 'VimIndenter')
