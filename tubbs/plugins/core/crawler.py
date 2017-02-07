from ribosome.record import Record, field, str_field

from tubbs.grako.base import ParserBase
from tubbs.hints.base import HintsBase, HintMatch
from tubbs.logging import Logging
from tubbs.grako.ast import AstMap

from amino import Maybe, __, L, _, List, Map, Either


class Match(Record):
    ast = field(AstMap)
    rule = str_field()
    ident = str_field()
    hint = field(HintMatch)

    @property
    def _str_extra(self):
        return List(self.ident, self.rule, self.ast)

    @property
    def parseinfo(self):
        return Maybe.check(self.ast.parseinfo) / __._asdict() / Map | Map()

    @property
    def line(self):
        return self.hint.line

    @property
    def start(self):
        return self.parseinfo.lift('line') / (_ + self.line)

    @property
    def start1(self):
        ''' first line of the match in 1-based indexing for vim
        '''
        return self.start / (_ + 1)

    @property
    def end(self):
        return self.parseinfo.lift('endline') / (_ + self.line)

    @property
    def end1(self):
        ''' last line of the match in 1-based indexing for vim
        '''
        return self.end / (_ + 1)

    @property
    def range(self) -> Either:
        return (
            (self.start & (self.end / (_ + 1)))
            .to_either('{} has no range'.format(self))
        )

    @property
    def range1(self) -> Either:
        return (
            (self.start1 & self.end1)
            .to_either('{} has no range1'.format(self))
        )

    @property
    def range_inclusive(self) -> Either:
        return (
            (self.start & self.end)
            .to_either('{} has no range'.format(self))
        )


class Crawler(Logging):

    def __init__(self, content: List[str], line: int, parser: ParserBase,
                 hints: Maybe[HintsBase]) -> None:
        self.content = content
        self.line = line
        self.parser = parser
        self.hints = hints

    def find_and_parse(self, ident: str, linewise: bool=True) -> Either:
        return self.find(ident, linewise) // L(self._parse)(ident, _)

    def find(self, ident: str, linewise: bool=True) -> Either:
        self.log.debug('crawling for {}'.format(ident))
        return (
            (self.hints // __.find(self.content, self.line, ident))
            .to_either('no hint matched for {}'.format(ident))
            .o(L(self._default_start)(ident))
        )

    @property
    def parsable_range(self) -> Either:
        return (self.hints / _.hints.k | List()).find_map(self.find_and_parse)

    def _default_start(self, ident: str) -> Either:
        return self.line / L(HintMatch.from_attr)('line')(_, rules=List(ident))

    def _parse(self, ident: str, match: Match) -> Either:
        self.log.debug('parsing {} for {}'.format(match, ident))
        text = self.content[match.line:].join_lines
        def match_rule(rule: str) -> Either:
            return (
                self.parser.parse(text, rule) /
                L(Match.from_attr('ast'))(_, rule=rule, ident=ident,
                                          hint=match)
            )
        return (
            match.rules
            .find_map(match_rule)
            .to_either('no rule matched for `{}` at {}'.format(ident, match))
        )

__all__ = ('Crawler',)
