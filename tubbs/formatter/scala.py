from amino import Left, Either, List, _
from amino.util.string import snake_case

from stevedore.example.base import FormatterBase

from ribosome.util.callback import VimCallback
from ribosome.nvim import NvimFacade
from ribosome.nvim.components import NvimComponent

from tubbs.formatter.breaker import Breaker as BreakerBase
from tubbs.formatter.indenter import Indenter as IndenterBase, Indent, after, from_here, IndentResult, keep, children
from tubbs.tatsu.ast import AstMap, AstElem, AstList, RoseData
from tubbs.formatter.breaker import StrictBreakData, BreakRules, BreakData, BreakState
from tubbs.formatter.indenter import IndentRules


class Formatter(FormatterBase):

    def no_rule(self, ast: AstElem) -> Either[str, List[str]]:
        return Left('cannot format rule `{}`'.format(ast.info.rule))

    def _format_rule(self, ast: AstMap) -> Either[str, List[str]]:
        handler = getattr(self, snake_case(ast.rule), self.no_rule)
        return handler(ast)

    def format(self, ast: AstElem) -> Either[str, List[str]]:
        return self._format_rule(ast.root)

    def template_stat(self, ast: AstElem) -> Either[str, List[str]]:
        return Left('NI')


class VimFormatter(Formatter):

    def __init__(self, vim: NvimComponent) -> None:
        self.vim = vim


def nel(ast: AstElem) -> bool:
    return isinstance(ast, AstList) and ast.data.length > 0


def in_multi_line_block(node: RoseData) -> bool:
    return node.parent.parent.data.ast.s.body.tail.e.exists(nel)


class ScalaBreakRules(BreakRules):
    pass

    def case_clause(self, state: BreakState) -> BreakData:
        ''' TODO check parent; if more than one case is present, return
        1.0, else 0.9
        '''
        return 1.0, 0.0

    def param_clause(self, state: BreakState) -> BreakData:
        return 0.7, 0.1

    def implicit_param_clause(self, state: BreakState) -> BreakData:
        return 0.75, 0.1

    def block_body(self, state: BreakState) -> BreakData:
        return 0.9, 0.0

    def block_rest_stat(self, state: BreakState) -> BreakData:
        return 0.9, 0.0

    def seminl_semi(self, state: BreakState) -> BreakData:
        return 0.0, 1.1

    def lbrace(self, state: BreakState) -> BreakData:
        return 0.0, (1.0 if in_multi_line_block(state.node) else 0.3)

    def rbrace(self, state: BreakState) -> BreakData:
        def decide(state: BreakState) -> StrictBreakData:
            opening_brace = state.node.parent.data.ast.s.lbrace.e
            opening_break = state.parent_breaks.find(lambda a: opening_brace.contains(a.node.ast))
            force_break = opening_break.present or in_multi_line_block(state.node)
            return (1.0 if force_break else 0.3), 0.0
        return decide

    def assign(self, state: BreakState) -> BreakData:
        def decide(state: BreakState) -> StrictBreakData:
            rhs = state.node.parent.data.ast.s.rhs
            lbrace = state.after('lbrace')
            after = (
                0.0
                if state.node.parent.rule == 'param' else
                0.3
                if rhs.rule.contains('block') and rhs.valid and lbrace else
                0.8
            )
            return 0.0, after
        return decide


class Breaker(BreakerBase):

    def __init__(self, textwidth: int) -> None:
        super().__init__(ScalaBreakRules(), textwidth)


class VimBreaker(Breaker, VimCallback):

    def __init__(self, vim: NvimFacade) -> None:
        tw = vim.buffer.options('textwidth') | 80
        super().__init__(tw)


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
        sw = vim.options('shiftwidth') | 2
        super().__init__(sw)

__all__ = ('Formatter', 'Breaker', 'Indenter', 'VimFormatter', 'VimBreaker', 'VimIndenter')
