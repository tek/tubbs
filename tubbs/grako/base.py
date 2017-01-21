import hashlib
import abc

from grako import gencode

from amino import Either, Try, Map, L, Path, _, Right
from amino.util.string import camelcaseify

from ribosome.record import Record, map_field

from tubbs.grako.parser_ext import ParserExt, DataSemantics
from tubbs.logging import Logging


class ParserBase(Logging, abc.ABC):

    @abc.abstractproperty
    def name(self) -> str:
        ...

    @abc.abstractproperty
    def module_path(self) -> str:
        ...

    @abc.abstractproperty
    def grammar_file(self) -> Path:
        ...

    @abc.abstractproperty
    def parser_path(self) -> Path:
        ...

    @property
    def camel_name(self):
        return camelcaseify(self.name)

    @property
    def parser_class(self):
        return '{}Parser'.format(self.camel_name)

    @property
    def base_dir(self):
        return Path(__file__).parent.parent.parent

    @property
    def chksums_path(self):
        return self.base_dir / 'hashes'

    @property
    def chksum_path(self):
        return self.chksums_path / self.name

    @property
    def parser_args(self):
        return Map(
            # trace=True
        )

    @property
    def grammar_chksum(self):
        return hashlib.sha384(self.grammar_file.read_bytes()).digest()

    @property
    def checksum_invalid(self):
        return (not self.chksum_path.is_file() or
                self.chksum_path.read_bytes() != self.grammar_chksum)

    def gen(self):
        if not self.parser_path.is_file() or self.checksum_invalid:
            if self.parser_path.is_file():
                self.parser_path.unlink()
            grammar = self.grammar_file.read_text()
            model = gencode(self.camel_name, grammar)
            self.parser_path.write_text(model)
            self.chksum_path.write_bytes(self.grammar_chksum)

    @property
    def parser(self):
        def cons(tpe):
            cls = type(self.parser_class, (ParserExt, tpe), {})
            return Try(lambda *a, **kw: cls(*a, **kw), **self.parser_args)
        return Either.import_path(self.module_path) // cons

    @property
    def semantics(self):
        return DataSemantics()

    def parse(self, text: str, rule: str):
        def log_error(err):
            self.log.debug(f'failed to parse `{rule}`:\n{err}')
        return (
            self.parser //
            L(Try)(_.parse, text, rule, semantics=self.semantics)
        ).leffect(log_error)


class BuiltinParser(ParserBase):

    @property
    def module_base(self):
        return 'tubbs.parsers'

    @property
    def module_path(self):
        return '{}.{}.{}'.format(self.module_base, self.name,
                                 self.parser_class)

    @property
    def grammar_path(self):
        return self.base_dir / 'grammar'

    @property
    def grammar_file(self):
        return self.grammar_path / '{}.ebnf'.format(self.name)

    @property
    def parsers_path(self):
        return self.base_dir / 'tubbs' / 'parsers'

    @property
    def parser_path(self):
        return self.parsers_path / '{}.py'.format(self.name)


class Parsers(Record):
    parsers = map_field()

    @property
    def _builtin_mod(self):
        return 'tubbs.grako'

    def load(self, name):
        return Right(self) if name in self.parsers else self._load(name)

    def _load(self, name):
        def update(parser):
            return self.modder.parsers(_ + (name, parser()))
        return (
            Either.import_name('{}.{}'.format(
                self._builtin_mod, name), 'Parser') /
            update
        )

    def parser(self, name):
        return (self.parsers.lift(name)
                .to_either('no parser for `{}`'.format(name)))

__all__ = ('ParserBase', 'BuiltinParser', 'Parsers')
