from typing import Tuple

from amino import List, Either, L, _, Maybe, Eval

from tubbs.logging import Logging
from tubbs.formatter.base import Formatter
from tubbs.tatsu.base import ParserBase
from tubbs.hints.base import HintsBase
from tubbs.plugins.core.crawler import Crawler

Range = Tuple[int, int]


class Formatted:

    def __init__(self, lines: List[str], rng: Range) -> None:
        self.lines = lines
        self.rng = rng


class FormattingFacade(Logging):

    def __init__(self, parser: ParserBase, formatters: List[Formatter], hints: Maybe[HintsBase]) -> None:
        self.parser = parser
        self.formatters = formatters
        self.hints = hints

    def parsable_range(self, context: List[str], rng: Range) -> Either[str, Tuple[str, Range]]:
        start, end = rng
        crawler = Crawler(context, start, self.parser, self.hints)
        result = crawler.parsable_range
        return result.map(_.rule).zip(result.map(_.range))

    def format(self, context: List[str], rng: Range) -> Eval[Formatted]:
        return (
            self.parsable_range(context, rng)
            .flat_map2(L(self.format_range)(_, context, _))
        )

    def format_range(self, rule: str, context: List[str], rng: Range) -> Eval[Formatted]:
        lines = context.slice(*rng)
        format_with = L(self.format_with)(rule, _, _)
        return self.formatters.fold_m(Eval.now(lines))(format_with) / L(Formatted)(_, rng)

    def format_with(self, rule: str, lines: List[str], formatter: Formatter) -> Eval[List[str]]:
        return (
            self.parser.parse(lines.join_lines, rule) //
            formatter.format /
            (_ | lines)
        )

__all__ = ('FormattingFacade',)
