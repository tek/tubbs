from amino import Left, Map
from amino.util.string import snake_case

from ribosome.util.callback import VimCallback
from ribosome.nvim import NvimFacade

from tubbs.formatter import base
from tubbs.formatter.base import Formatter, BreakRules, IndentRules, BreakData
from tubbs.grako.ast import AstMap
from tubbs.formatter.tree import Tree, Node


class Formatter(Formatter):

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

    def map_case_clause(self, node: Node) -> BreakData:
        ''' TODO check parent; if more than one case is present, return
        1.0, else 0.9
        '''
        return 'casekw', 1.0, 0.0

    def map_param_clause(self, node: Node) -> BreakData:
        return 'lpar', 0.89, 0.1

    def map_implicit_param_clause(self, node: Node) -> BreakData:
        return 'lpar', 0.9, 0.1

    def map_block_body(self, node: Node) -> BreakData:
        return 'head', 0.9, 0.0

    def list_block_rest_stat(self, node: Node) -> BreakData:
        return 'stat', 0.9, 0.0

    def token_seminl_semi(self, node: Node) -> BreakData:
        return 'semi', 0.0, 1.1

    def token_lbrace(self, node: Node) -> BreakData:
        return 'lbrace', 0.0, 1.0

    def token_rbrace(self, node: Node) -> BreakData:
        return 'rbrace', 1.0, 0.0


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
