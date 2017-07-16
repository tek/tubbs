from amino import Left, Either, List
from amino.util.string import snake_case

from ribosome.nvim.components import NvimComponent

from tubbs.tatsu.ast import AstMap, AstElem
from tubbs.formatter.base import Formatter as FormatterBase


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


__all__ = ('Formatter', 'VimFormatter')
