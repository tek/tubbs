from typing import Tuple

from amino import List, Either, L, _, Maybe

from tubbs.logging import Logging
from tubbs.formatter.tree import Tree
from tubbs.formatter.base import Formatter
from tubbs.grako.base import ParserBase
from tubbs.hints.base import HintsBase
from tubbs.plugins.core.crawler import Crawler

Range = Tuple[int, int]


class Formatted:

    def __init__(self, lines: List[str], rng: Range) -> None:
        self.lines = lines
        self.rng = rng


class FormattingFacade(Logging):

    def __init__(self, parser: ParserBase, formatters: List[Formatter],
                 hints: Maybe[HintsBase]) -> None:
        self.parser = parser
        self.formatters = formatters
        self.hints = hints

    def parsable_range(self, context: List[str], rng: Range
                       ) -> Either[str, Tuple[str, Range]]:
        start, end = rng
        crawler = Crawler(context, start, self.parser, self.hints)
        result = crawler.parsable_range
        return result.map(_.rule).zip(result.flat_map(_.range))

    def format(self, context: List[str], rng: Range) -> Either[str, Formatted]:
        return (
            self.parsable_range(context, rng)
            .map2(L(self.format_range)(_, context, _))
        )

    def format_range(self, rule: str, context: List[str], rng: Range
                     ) -> Formatted:
        lines = context.slice(*rng)
        format_with = L(self.format_with)(rule, _, _)
        return Formatted(self.formatters.fold_left(lines)(format_with), rng)

    def format_with(self, rule: str, lines: List[str], formatter: Formatter
                    ) -> List[str]:
        return (
            self.parser.parse(lines.join_lines, rule) /
            Tree //
            formatter.format |
            lines
        )

__all__ = ('FormattingFacade',)
