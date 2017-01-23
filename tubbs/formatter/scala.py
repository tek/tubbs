from amino import Left
from amino.util.string import snake_case

from ribosome.util.callback import VimCallback

from tubbs.formatter import base
from tubbs.formatter.base import BuiltinFormatter, BreakRules, IndentRules
from tubbs.grako.ast import AstMap
from tubbs.formatter.tree import Tree


class Formatter(BuiltinFormatter):

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

    def map_case_clause(self, node):
        return 'start', 0.9, 0.0

    def token_param_clause_lpar(self, node):
        return 'lpar', 0.89, 0.1

    def token_implicit_param_clause_lpar(self, node):
        return 'lpar', 0.9, 0.1

    def list_block_first(self, node):
        return 'first', 0.9, 0.0

    def list_block_rest_stat(self, node):
        return 'stat', 0.9, 0.0

    def token_eol(self, node):
        return 'eol', 0.0, 1.1

    def token_rbrace(self, node):
        return 'rbrace', 1.0, 0.0

class Breaker(base.Breaker):

    def __init__(self, textwidth) -> None:
        super().__init__(ScalaBreakRules(), textwidth)


class VimBreaker(Breaker, VimCallback):

    def __init__(self, vim) -> None:
        tw = vim.buffer.options('textwidth') | 80
        super().__init__(tw)


class ScalaIndentRules(IndentRules):

    def case_clause_first(self, node):
        return 1

    def block_first(self, node):
        return 1

    def rbrace(self, node):
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
