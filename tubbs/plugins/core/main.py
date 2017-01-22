from typing import Callable

from ribosome.machine import may_handle, handle, Message
from ribosome.machine.base import io, UnitTask
from ribosome.machine.transition import Fatal

from amino import __, L, _, Task, Either, Maybe, Right, List

from tubbs.state import TubbsComponent, TubbsTransitions

from tubbs.plugins.core.message import (StageI, AObj, Select, Format,
                                        FormatRange)
from tubbs.plugins.core.crawler import Crawler
from tubbs.grako.base import ParserBase
from tubbs.formatter.tree import Tree


class CoreTransitions(TubbsTransitions):

    @may_handle(StageI)
    def stage_i(self):
        return io(__.vars.set_p('started', True))

    @handle(AObj)
    def a_obj(self):
        return self.load_and_run(L(Select)(_, 'a', self.msg.ident) >> Right)

    @handle(Select)
    def select(self):
        self.log.debug(f'selecting {self.msg.tpe} {self.msg.ident}')
        return self.with_match_msg(L(self.visual)(self.msg.tpe, _)).lmap(Fatal)

    @handle(FormatRange)
    def format_range(self):
        start = self.msg.options.get('start').o(lambda: self.vim.window.line)
        end = self.msg.options.get('end').o(start)
        load = lambda s, e: self.load_and_run(L(Format)(_, (s, e)) >> Right)
        return (
            (start & end)
            .to_either(Fatal('invalid range for formatting'))
            .flat_map2(load)
            .lmap(Fatal)
        )

    @handle(Format)
    def format(self):
        start, end = self.msg.range
        vim_range = start - 1, end
        return (
            (self.data.parser(self.msg.parser) &
             self.formatters(self.msg.parser))
            .map2(L(self._format)(_, _, self.msg.range)) /
            L(self.update_range)(_, vim_range)
        ).lmap(Fatal)

    @property
    def parser_name(self):
        return (
            self.vim.vars.p('parser')
            .o(lambda: self.vim.buffer.options('filetype'))
        )

    def load_and_run(self, f: Callable[[str], Either[str, Message]]):
        load = lambda name: (self.data.load_parser(name) & f(name))
        return (self.parser_name // load).lmap(Fatal)

    def formatters(self, name):
        custom = self._callbacks('formatters_{}'.format(name))
        return self.lang_formatters(name) if custom.empty else Right(custom)

    def lang_formatters(self, name):
        return (
            List('VimFormatter', 'VimBreaker', 'VimIndenter')
            .map(L(self.lang_formatter)(name, _))
            .sequence(Either)
        )

    def lang_formatter(self, lang, name):
        mod = 'tubbs.formatter'
        return (Either.import_name('{}.{}'.format(mod, lang), name) /
                __(self.vim))

    def with_match_msg(self, f: Callable[[ParserBase], Either]):
        return (self.data.parser(self.msg.parser) //
                L(self.with_match)(_, self.msg.ident, f))

    def with_match(self, parser: str, ident: str,
                   f: Callable[[ParserBase], Maybe]):
        return self.crawler(parser).find_and_parse(ident) // f

    def visual(self, tpe, match) -> Either:
        self.log.debug(f'attempting to select {match}')
        return (
            match.range1
            .map2(L(Task.delay)(self.vim.window.visual_line, _, _)) /
            UnitTask
        )

    def crawler(self, parser):
        hints = (self._callback('hints')
                 .o(lambda: self.lang_hints(parser.name))) / __()
        return Crawler(self.vim, parser, hints)

    def lang_hints(self, name):
        return Either.import_name('tubbs.hints.{}'.format(name), 'Hints')

    def _format(self, parser, formatters, rng):
        rule = 'templateStat'
        start, end = rng
        content = self.vim.buffer.content[start - 1:end]
        def run(lines: List[str], formatter):
            return (
                parser.parse(lines.join_lines, rule) /
                Tree //
                formatter.format |
                lines
            )
        return formatters.fold_left(content)(run)

    def update_range(self, lines, rng):
        return io(__.buffer.set_content(lines, rng=slice(*rng)))


class Plugin(TubbsComponent):
    Transitions = CoreTransitions

__all__ = ('Plugin',)
