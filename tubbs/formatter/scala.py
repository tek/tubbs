from amino import Left, List
from amino.util.string import snake_case

from tubbs.formatter import base
from tubbs.formatter.base import BuiltinFormatter, BreakRules
from tubbs.grako.ast import AstMap


class Formatter(BuiltinFormatter):

    def no_rule(self, ast):
        return Left('cannot format rule `{}`'.format(ast.parseinfo.rule))

    def _format_rule(self, ast: AstMap):
        handler = getattr(self, snake_case(ast.rule), self.no_rule)
        return handler(ast)

    def format(self, ast: AstMap, lines):
        return self._format_rule(ast)

    def template_stat(self, ast):
        return Left('NI')


class ScalaBreakRules(BreakRules):

    def map_case_clause(self, node):
        return 'start', 0.9, 0.0

    def token_param_clause_lpar(self, leaf):
        return 'lpar', 0.89, 0.1

    def token_implicit_param_clause_lpar(self, leaf):
        return 'lpar', 0.9, 0.1


class Breaker(base.Breaker):

    def __init__(self, textwidth) -> None:
        super().__init__(ScalaBreakRules(), textwidth)


class Indenter(base.Indenter):
    pass

__all__ = ('Formatter', 'Breaker', 'Indenter')
