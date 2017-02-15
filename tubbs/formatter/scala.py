from amino import Left
from amino.util.string import snake_case

from ribosome.util.callback import VimCallback
from ribosome.nvim import NvimFacade

from tubbs.formatter import base
from tubbs.formatter.base import Formatter as FormatterBase, StrictBreakData
from tubbs.formatter.base import BreakRules, IndentRules, BreakData, BreakState
from tubbs.grako.ast import AstMap, AstElem, AstList
from tubbs.formatter.tree import Tree, Node


class Formatter(FormatterBase):

    def no_rule(self, tree):
        return Left('cannot format rule `{}`'.format(tree.info.rule))

    def _format_rule(self, ast: AstMap):
        handler = getattr(self, snake_case(ast.rule), self.no_rule)
        return handler(ast)

    def format(self, ast: Tree):
        return self._format_rule(ast.root)

    def template_stat(self, ast):
        return Left('NI')


class VimFormatter(Formatter):

    def __init__(self, vim) -> None:
        pass


class ScalaBreakRules(BreakRules):

    def map_case_clause(self, state: BreakState) -> BreakData:
        ''' TODO check parent; if more than one case is present, return
        1.0, else 0.9
        '''
        return 'casekw', 1.0, 0.0

    def map_param_clause(self, state: BreakState) -> BreakData:
        return 'lpar', 0.89, 0.1

    def map_implicit_param_clause(self, state: BreakState) -> BreakData:
        return 'lpar', 0.9, 0.1

    def map_block_body(self, state: BreakState) -> BreakData:
        return 'head', 0.9, 0.0

    def list_block_rest_stat(self, state: BreakState) -> BreakData:
        return 'stat', 0.9, 0.0

    def token_seminl_semi(self, state: BreakState) -> BreakData:
        return 'semi', 0.0, 1.1

    def token_lbrace(self, state: BreakState) -> BreakData:
        def nonempty(ast: AstElem) -> bool:
            return isinstance(ast, AstList) and ast.data.length > 0
        multi = state.node.parent.parent.data.body.tail.e.exists(nonempty)
        return 'lbrace', 0.0, (0.6 if multi else 0.3)

    def token_rbrace(self, state: BreakState) -> BreakData:
        return 'rbrace', 1.0, 0.0

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


class Breaker(base.Breaker):

    def __init__(self, textwidth: int) -> None:
        super().__init__(ScalaBreakRules(), textwidth)


class VimBreaker(Breaker, VimCallback):

    def __init__(self, vim: NvimFacade) -> None:
        tw = vim.buffer.options('textwidth') | 80
        super().__init__(tw)


class ScalaIndentRules(IndentRules):

    def case_clauses(self, node: Node) -> int:
        return 1

    def block_body(self, node: Node) -> int:
        return 1

    def rbrace(self, node: Node) -> int:
        return -1


class Indenter(base.Indenter):

    def __init__(self, shiftwidth) -> None:
        super().__init__(ScalaIndentRules(), shiftwidth)


class VimIndenter(Indenter):

    def __init__(self, vim) -> None:
        sw = vim.options('shiftwidth') | 2
        super().__init__(sw)

__all__ = ('Formatter', 'Breaker', 'Indenter', 'VimFormatter', 'VimBreaker',
           'VimIndenter')
