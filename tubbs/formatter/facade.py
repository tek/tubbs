from amino import List

from tubbs.logging import Logging
from tubbs.formatter.tree import Tree


class FormattingFacade(Logging):

    def __init__(self, parser, formatters) -> None:
        self.parser = parser
        self.formatters = formatters

    def format(self, lines):
        rule = 'templateStat'
        def run(lines: List[str], formatter):
            return (
                self.parser.parse(lines.join_lines, rule) /
                Tree //
                formatter.format |
                lines
            )
        return self.formatters.fold_left(lines)(run)

__all__ = ('FormattingFacade',)
