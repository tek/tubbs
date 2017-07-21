from typing import Callable, Tuple

from ribosome.machine import may_handle, handle, Message, Nop
from ribosome.machine.base import io, UnitTask
from ribosome.machine.transition import Fatal
from ribosome.request.base import parse_int

from amino import __, L, _, Task, Either, Maybe, Right, List, Map
from amino.util.string import snake_case
from amino.state import EvalState

from tubbs.state import TubbsComponent, TubbsTransitions

from tubbs.plugins.core.message import (StageI, AObj, Select, Format,
                                        FormatRange, FormatAt, FormatExpr)
from tubbs.plugins.core.crawler import Crawler, Match
from tubbs.tatsu.base import ParserBase
from tubbs.formatter.facade import FormattingFacade, Formatted, Range
from tubbs.formatter.base import Formatter, VimFormatterMeta
from tubbs.hints.base import HintsBase
from tubbs.env import Env


formatters_pkg = 'tubbs.formatter'


class CoreTransitions(TubbsTransitions):

    @may_handle(StageI)
    def stage_i(self) -> Message:
        return io(__.vars.set_p('started', True))

    @handle(AObj)
    def a_obj(self) -> Maybe[Message]:
        return (
            self.load_and_run(L(Select)(_, 'a', self.msg.ident) >> Right)
            .lmap(Fatal)
        )

    @handle(Select)
    def select(self) -> Maybe[Message]:
        self.log.debug('selecting {} {}'.format(self.msg.tpe, self.msg.ident))
        return self.with_match_msg(self.visual).lmap(Fatal)

    @handle(FormatRange)
    def format_range(self) -> Either[str, Message]:
        start = (
            self.msg.options.get('start')
            .o(lambda: self.vim.window.line) //
            parse_int /
            (_ - 1)
        )
        end = self.msg.options.get('end').o(start) // parse_int
        load = lambda s, e: self.load_and_run(L(Format)(_, (s, e)) >> Right)
        return (
            (start & end)
            .to_either('invalid range for formatting')
            .flat_map2(load)
            .lmap(Fatal)
        )

    @may_handle(FormatAt)
    def format_at(self) -> Message:
        return FormatRange(options=(Map(start=self.msg.line)))

    @may_handle(FormatExpr)
    def format_expr(self) -> Message:
        line = self.msg.line
        count = self.msg.count
        return FormatRange(options=(Map(start=line, end=line + count - 1)))

    @may_handle(Format)
    def format(self) -> EvalState[Env, Either[str, Message]]:
        name = self.msg.parser
        range = self.msg.range
        return (
            EvalState.modify(lambda a: a.load_parser(name) | a)
            .flat_map(lambda a: self.formatters(name))
            .eff(Either)
            .flat_map(L(self._format)(name, _, range))
            .map(L(self.update_range)(_, self.msg.range))
            .value
            .map(__.lmap(Fatal))
        )

    @property
    def parser_name(self) -> Either[str, str]:
        return (
            self.vim.vars.p('parser')
            .o(lambda: self.vim.buffer.options('filetype'))
        )

    def load_and_run(self, f: Callable[[str], Either[str, Message]]) -> Either[str, Tuple[ParserBase, Message]]:
        load = lambda name: (self.data.load_parser(name) & f(name))
        return self.parser_name // load

    def formatters(self, name: str) -> EvalState[Env, Either[str, List[Formatter]]]:
        custom = self._callbacks('formatters_{}'.format(name))
        return self.lang_formatters(name) if custom.empty else EvalState.pure(custom, Either)

    def lang_formatters(self, lang: str) -> EvalState[Env, Either[str, List[Formatter]]]:
        return (
            List(('Breaker', 'breaks'), ('Indenter', 'indents'))
            .map2(L(self.lang_formatter)(lang, _, _))
            .sequence(EvalState)
            .map(__.sequence(Either))
        )

    def lang_formatter(self, lang: str, name: str, tpe: str) -> EvalState[Env, Either[str, Formatter]]:
        return (
            EvalState.pure(self.vim.vars.pd('{}_{}'.format(lang, tpe))).eff(Either)
            .flat_map(L(self.dict_formatter)(lang, name, _))
            .value
            .map(__.o(lambda: self.builtin_formatter(lang, name)))
        )

    # import_pvar_name_typed(Map)
    def dict_formatter(self, lang: str, name: str, rules: dict) -> EvalState[Env, Either[str, Formatter]]:
        def cons(tpe: VimFormatterMeta, parser: ParserBase, conds: Map[str, str]) -> Formatter:
            return tpe(self.vim, parser, tpe.convert_data(Map(rules)), conds)
        snake_name = snake_case(name)
        pkg = f'{formatters_pkg}.{snake_name}'
        conds = (
            self.vim.import_pvar_path(f'{snake_name}_conds')
            .o(Either.import_name(f'{pkg}.conds', 'default_conds'))
        )
        parser_name = f'{snake_name}_dsl'
        def load_parser(env: Env) -> Env:
            return env.load_parser(parser_name) | env
        def create_formatter(env: Env) -> Either[str, Formatter]:
            formatter = Either.import_name(f'{pkg}.main', f'VimDict{name}')
            parser = env.parser(parser_name)
            return formatter.zip(parser, conds).map3(cons)
        return (
            EvalState.modify(load_parser).replace(Right(None)).eff(Either) //
            (lambda a: EvalState.inspect(create_formatter))
        ).value

    def builtin_formatter(self, lang: str, name: str) -> Either[str, Formatter]:
        return (
            Either.import_name('{}.{}'.format(formatters_pkg, lang), 'Vim{}'.format(name)) /
            __(self.vim)
        )

    def with_match_msg(self, f: Callable[[ParserBase], Message]) -> Either:
        return self.data.parser(self.msg.parser) / L(self.with_match)(_, self.msg.ident, f)

    def with_match(self, parser: str, ident: str, f: Callable[[ParserBase], Either]) -> Either:
        return self.crawler(parser) // __.find_and_parse(ident) // f

    def visual(self, match: Match) -> UnitTask:
        self.log.debug('attempting to select {}'.format(match))
        start, end = match.range1
        return UnitTask(Task.delay(self.vim.window.visual_line, start, end))

    def hints(self, name: str) -> Either[str, HintsBase]:
        return (
            self._callback('hints')
            .o(lambda: self.lang_hints(name)) /
            __()
        )

    def lang_hints(self, name: str) -> Either[str, HintsBase]:
        return Either.import_name('tubbs.hints.{}'.format(name), 'Hints')

    def crawler(self, parser: ParserBase) -> Either[str, Crawler]:
        hints = self.hints(parser.name)
        content = self.vim.buffer.content
        return self.vim.window.line0 / (L(Crawler)(content, _, parser, hints))

    def _format(self, name: str, formatters: List[Formatter], rng: Range) -> Formatted:
        content = self.vim.buffer.content
        return (
            EvalState.inspect(__.parser(name))
            .eff(Either)
            .map(L(self.formatting_facade)(_, formatters))
            .map(__.format(content, rng)._value())
            .value
        )

    def formatting_facade(self, parser: ParserBase, formatters: List[Formatter]) -> FormattingFacade:
        return FormattingFacade(parser, formatters, self.hints(parser.name))

    def update_range(self, formatted: Formatted, rng: Range) -> Message:
        return io(__.buffer.set_content(formatted.lines, rng=slice(*formatted.rng)))


class Plugin(TubbsComponent):
    Transitions = CoreTransitions

__all__ = ('Plugin',)
