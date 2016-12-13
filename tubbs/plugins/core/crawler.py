from ribosome.nvim import NvimFacade
from ribosome.record import Record, field, str_field

from tubbs.grako.base import ParserBase, AstMap
from tubbs.hints.base import HintsBase, HintMatch
from tubbs.logging import Logging

from amino import Maybe, __, L, _, List, Map


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
    def range(self):
        return self.start & self.end

    @property
    def range1(self):
        return self.start1 & self.end1


class Crawler(Logging):

    def __init__(self, vim: NvimFacade, parser: ParserBase,
                 hints: Maybe[HintsBase]) -> None:
        self.vim = vim
        self.parser = parser
        self.hints = hints

    def find(self, ident) -> Match:
        return (
            (self.hints // __.find(self.vim, ident))
            .o(lambda: self._default_start(ident)) //
            L(self._parse)(ident, _)
        )

    def _default_start(self, ident):
        return (self.vim.window.line /
                L(HintMatch.from_attr)('line')(_, rules=List(ident)))

    def _parse(self, ident, match):
        text = self.vim.buffer.content[match.line:].join_lines
        def match_rule(rule):
            return (
                self.parser.parse(text, rule) /
                L(Match.from_attr('ast'))(_, rule=rule, ident=ident,
                                          hint=match)
            )
        return match.rules.find_map(match_rule)

__all__ = ('Crawler',)
