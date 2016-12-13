from typing import Callable

from ribosome.machine import may_handle, handle
from ribosome.machine.base import io, UnitTask
from ribosome.machine.transition import Fatal

from amino import __, L, _, Right, Task, Either, Maybe

from tubbs.state import TubbsComponent, TubbsTransitions

from tubbs.plugins.core.message import StageI, AObj, Select
from tubbs.plugins.core.crawler import Crawler
from tubbs.grako.base import ParserBase


class CoreTransitions(TubbsTransitions):

    @may_handle(StageI)
    def stage_i(self):
        return io(__.vars.set_p('started', True))

    def _load_and_run(self, tpe, ident):
        def load(name):
            return (self.data.load_parser(name) &
                    Right(Select(name, tpe, ident)))
        return (
            self.vim.vars.p('parser')
            .o(lambda: self.vim.opts('filetype')) //
            load
        ).lmap(Fatal)

    @handle(AObj)
    def a_obj(self):
        return self._load_and_run('a', self.msg.ident)

    @handle(Select)
    def select(self):
        return self._with_match_msg(L(self._visual)(self.msg.tpe, _))

    def _with_match_msg(self, f: Callable[[ParserBase], Maybe]):
        return (self.data.parser(self.msg.parser) //
                L(self._with_match)(_, self.msg.ident, f))

    def _with_match(self, parser: str, ident: str,
                    f: Callable[[ParserBase], Maybe]):
        return self.crawler(parser).find(ident) // f

    def _visual(self, tpe, match):
        return (
            match.range1
            .map2(L(Task.delay)(self.vim.window.visual_line, _, _)) /
            UnitTask
        )

    def crawler(self, parser):
        hints = (self._callback('hints')
                 .o(lambda: self._lang_hints(parser.name))) / __()
        return Crawler(self.vim, parser, hints)

    def _lang_hints(self, name):
        return Either.import_name('tubbs.hints.{}'.format(name), 'Hints')


class Plugin(TubbsComponent):
    Transitions = CoreTransitions

__all__ = ('Plugin',)
