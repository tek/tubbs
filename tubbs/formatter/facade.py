from typing import Tuple

from amino import List, Either, L, _, Just

from tubbs.logging import Logging
from tubbs.formatter.tree import Tree
from tubbs.formatter.base import Formatter
from tubbs.grako.base import ParserBase
from tubbs.hints.base import HintsBase
from tubbs.plugins.core.crawler import Crawler


class FormattingFacade(Logging):

    def __init__(self, parser: ParserBase, formatters: List[Formatter],
                 hints: HintsBase) -> None:
        self.parser = parser
        self.formatters = formatters
        self.hints = hints

    def parsable_range(self, context: List[str], rng: Tuple[int, int]
                       ) -> Either[str, Tuple[str, List[str]]]:
        start, end = rng
        crawler = Crawler(context, start, self.parser, Just(self.hints))
        result = crawler.parsable_range
        return (
            result.map(_.rule) &
            result.flat_map(_.range).map2(context.slice)
        )

    def format(self, context: List[str], rng: Tuple[int, int]) -> List[str]:
        return (
            self.parsable_range(context, rng)
            .map2(self.format_range)
        )

    def format_range(self, rule: str, lines: List[str]) -> List[str]:
        format_with = L(self.format_with)(rule, _, _)
        return self.formatters.fold_left(lines)(format_with)

    def format_with(self, rule: str, lines: List[str], formatter: Formatter
                    ) -> List[str]:
        return (
            self.parser.parse(lines.join_lines, rule) /
            Tree //
            formatter.format |
            lines
        )

__all__ = ('FormattingFacade',)
