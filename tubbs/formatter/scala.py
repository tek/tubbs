from amino import Left, Either, List
from amino.util.string import snake_case

from stevedore.example.base import FormatterBase

from ribosome.util.callback import VimCallback
from ribosome.nvim import NvimFacade
from ribosome.nvim.components import NvimComponent

from tubbs.formatter.breaker import Breaker as BreakerBase
from tubbs.formatter.indenter import Indenter as IndenterBase
from tubbs.tatsu.ast import AstMap, AstElem, AstList
from tubbs.formatter.tree import Tree, BiNode
from tubbs.formatter.breaker import StrictBreakData, BreakRules, BreakData, BreakState
from tubbs.formatter.indenter import IndentRules


class Formatter(FormatterBase):

    def no_rule(self, tree: Tree) -> Either[str, List[str]]:
        return Left('cannot format rule `{}`'.format(tree.info.rule))

    def _format_rule(self, ast: AstMap) -> Either[str, List[str]]:
        handler = getattr(self, snake_case(ast.rule), self.no_rule)
        return handler(ast)

    def format(self, ast: Tree) -> Either[str, List[str]]:
        return self._format_rule(ast.root)

    def template_stat(self, ast: Tree) -> Either[str, List[str]]:
        return Left('NI')


class VimFormatter(Formatter):

    def __init__(self, vim: NvimComponent) -> None:
        self.vim = vim


def nel(ast: AstElem) -> bool:
    return isinstance(ast, AstList) and ast.data.length > 0


def in_multi_line_block(node: BiNode) -> bool:
    return node.parent.parent.data.body.tail.e.exists(nel)


class ScalaBreakRules(BreakRules):

    def map_case_clause(self, state: BreakState) -> BreakData:
        ''' TODO check parent; if more than one case is present, return
        1.0, else 0.9
        '''
        return 'casekw', 1.0, 0.0

    def map_param_clause(self, state: BreakState) -> BreakData:
        return 'lpar', 0.7, 0.1

    def map_implicit_param_clause(self, state: BreakState) -> BreakData:
        return 'lpar', 0.75, 0.1

    def map_block_body(self, state: BreakState) -> BreakData:
        return 'head', 0.9, 0.0

    def list_block_rest_stat(self, state: BreakState) -> BreakData:
        return 'stat', 0.9, 0.0

    def token_seminl_semi(self, state: BreakState) -> BreakData:
        return 'semi', 0.0, 1.1

    def token_lbrace(self, state: BreakState) -> BreakData:
        return 'lbrace', 0.0, (1.0 if in_multi_line_block(state.node) else 0.3)

    def token_rbrace(self, state: BreakState) -> BreakData:
        def decide(state: BreakState) -> StrictBreakData:
            opening_brace = state.node.parent.parent.data.lbrace.brace.e
            opening_break = state.parent_breaks.find(lambda a: opening_brace.contains(a.node.data))
            force_break = opening_break.present or in_multi_line_block(state.node)
            return 'rbrace', (1.0 if force_break else 0.3), 0.0
        return decide

    def map_assign(self, state: BreakState) -> BreakData:
        def decide(state: BreakState) -> StrictBreakData:
            rhs = state.node.parent.data.rhs
            lbrace = state.after('lbrace')
            after = (
                0.0
                if state.node.parent.rule == 'param' else
                0.3
                if rhs.rule == 'block' and rhs.valid and lbrace else
                0.8
            )
            return 'op', 0.0, after
        return decide


class Breaker(BreakerBase):

    def __init__(self, textwidth: int) -> None:
        super().__init__(ScalaBreakRules(), textwidth)


class VimBreaker(Breaker, VimCallback):

    def __init__(self, vim: NvimFacade) -> None:
        tw = vim.buffer.options('textwidth') | 80
        super().__init__(tw)


class ScalaIndentRules(IndentRules):

    def case_clauses(self, node: BiNode) -> int:
        return 1

    def block_body(self, node: BiNode) -> int:
        return 1

    def rbrace(self, node: BiNode) -> int:
        return -1

    def rhs(self, node: BiNode) -> int:
        return 1

    def dot(self, node: BiNode) -> int:
        return 0 if node.parent.rule == "applyExprChain" else 1


class Indenter(IndenterBase):

    def __init__(self, shiftwidth: int) -> None:
        super().__init__(ScalaIndentRules(), shiftwidth)


class VimIndenter(Indenter):

    def __init__(self, vim: NvimFacade) -> None:
        sw = vim.options('shiftwidth') | 2
        super().__init__(sw)

__all__ = ('Formatter', 'Breaker', 'Indenter', 'VimFormatter', 'VimBreaker', 'VimIndenter')
