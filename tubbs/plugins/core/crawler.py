from typing import Tuple, Any

from ribosome.record import Record, field, str_field

from tubbs.tatsu.base import ParserBase
from tubbs.hints.base import HintsBase, HintMatch
from tubbs.logging import Logging
from tubbs.tatsu.ast import AstMap

from amino import Maybe, __, L, _, List, Map, Either
from amino.regex import Match


class StartMatch(Record):
    ast = field(AstMap)
    rule = str_field()
    ident = str_field()
    hint = field(HintMatch)

    @property
    def _str_extra(self) -> List[Any]:
        return List(self.ident, self.rule, self.ast)

    @property
    def info(self) -> Map:
        return Maybe.check(self.ast.info) / __._asdict() / Map | Map()

    @property
    def line(self) -> int:
        return self.hint.line

    @property
    def start(self) -> int:
        return self.ast.start_line.lnum + self.line

    @property
    def start1(self) -> int:
        ''' first line of the match in 1-based indexing for vim
        '''
        return self.start + 1

    @property
    def end(self) -> int:
        return self.ast.end_line.lnum + self.line

    @property
    def end1(self) -> int:
        ''' last line of the match in 1-based indexing for vim
        '''
        return self.end + 1

    @property
    def range(self) -> Tuple[int, int]:
        return self.start, self.end + 1

    @property
    def range1(self) -> Tuple[int, int]:
        return self.start1, self.end1

    @property
    def range_inclusive(self) -> Tuple[int, int]:
        return self.start, self.end


class Crawler(Logging):

    def __init__(self, content: List[str], line: int, parser: ParserBase, hints: Maybe[HintsBase]) -> None:
        self.content = content
        self.line = line
        self.parser = parser
        self.hints = hints.to_either('no hints specified')

    def find_and_parse(self, ident: str, linewise: bool=True) -> Either:
        line = self.find(ident, linewise)
        return self._parse(ident, line)

    def find(self, ident: str, linewise: bool=True) -> Either:
        self.log.debug('crawling for {}'.format(ident))
        return (
            (self.hints // __.find(self.content, self.line, ident)) |
            L(self._default_start)(ident)
        )

    @property
    def parsable_range(self) -> Either:
        err = 'could not find parsable range for {}'
        return (
            self.hints
            .map(_.hints.k)
            .flat_map(
                __.find_map(self.find_and_parse)
                .to_either(err.format(self.hints.value))
            )
        )

    def _default_start(self, ident: str) -> Either:
        return HintMatch(line=self.line, rules=List(ident))

    def _parse(self, ident: str, match: Match) -> Either:
        self.log.debug('parsing {} for {}'.format(match, ident))
        text = self.content[match.line:].join_lines
        def match_rule(rule: str) -> Either:
            return (
                self.parser.parse(text, rule) /
                L(StartMatch.from_attr('ast'))(_, rule=rule, ident=ident, hint=match)
            )
        return (
            match.rules
            .find_map(match_rule)
            .to_either('no rule matched for `{}` at {}'.format(ident, match))
        )

__all__ = ('Crawler',)
