import hashlib
import abc
from typing import Any

from tatsu.tool import gencode

from amino import Either, Try, Map, L, Path, _, Right
from amino.util.string import camelcaseify

from ribosome.record import Record, map_field

from tubbs.tatsu.parser_ext import ParserExt, DataSemantics
from tubbs.logging import Logging
from tubbs.tatsu.ast import AstElem


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

    @abc.abstractproperty
    def left_recursion(self) -> bool:
        ...

    @abc.abstractmethod
    def cons_parser(self, tpe: type) -> Either[str, ParserExt]:
        ...

    @property
    def camel_name(self) -> str:
        return camelcaseify(self.name)

    @property
    def parser_class(self) -> str:
        return '{}Parser'.format(self.camel_name)

    @property
    def base_dir(self) -> Path:
        return Path(__file__).parent.parent

    @property
    def chksums_path(self) -> Path:
        return self.base_dir / 'hashes'

    @property
    def chksum_path(self) -> Path:
        return self.chksums_path / self.name

    @property
    def parser_args(self) -> Map[str, Any]:
        return Map(
            left_recursion=self.left_recursion,
            # trace=True,
        )

    @property
    def grammar_chksum(self) -> bytes:
        return hashlib.sha384(self.grammar_file.read_bytes()).digest()

    @property
    def checksum_invalid(self) -> bool:
        return (not self.chksum_path.is_file() or
                self.chksum_path.read_bytes() != self.grammar_chksum)

    def gen(self) -> None:
        self.parser_path.parent.mkdir(parents=True, exist_ok=True)
        self.chksums_path.mkdir(parents=True, exist_ok=True)
        if not self.parser_path.is_file() or self.checksum_invalid:
            if self.parser_path.is_file():
                self.parser_path.unlink()
            grammar = self.grammar_file.read_text()
            model = gencode(self.camel_name, grammar)
            self.parser_path.write_text(model)
            self.chksum_path.write_bytes(self.grammar_chksum)

    @property
    def parser(self) -> Either[str, ParserExt]:
        return Either.import_path(self.module_path) // self.cons_parser

    @abc.abstractproperty
    def semantics(self) -> Any:
        ...

    def parse(self, text: str, rule: str) -> Either[str, AstElem]:
        def log_error(err: str) -> None:
            self.log.debug(f'failed to parse `{rule}`:\n{err}')
        return (
            self.parser //
            L(Try)(_.parse, text, rule, semantics=self.semantics)
        ).leffect(log_error)


class BuiltinParser(ParserBase):

    @property
    def module_base(self) -> str:
        return 'tubbs.parsers'

    @property
    def module_path(self) -> str:
        return '{}.{}.{}'.format(self.module_base, self.name, self.parser_class)

    @property
    def grammar_path(self) -> Path:
        return self.base_dir / 'grammar'

    @property
    def grammar_file(self) -> Path:
        return self.grammar_path / '{}.ebnf'.format(self.name)

    @property
    def parsers_path(self) -> Path:
        return self.base_dir / 'parsers'

    @property
    def parser_path(self) -> Path:
        return self.parsers_path / '{}.py'.format(self.name)


class LangParser(BuiltinParser):

    def cons_parser(self, tpe: type) -> Either[str, ParserExt]:
        cls = type(self.parser_class, (ParserExt, tpe), {})
        return Try(lambda *a, **kw: cls(*a, **kw), **self.parser_args)

    @property
    def semantics(self) -> Any:
        return DataSemantics()


class Parsers(Record):
    parsers = map_field()

    @property
    def _builtin_mod(self) -> str:
        return 'tubbs.tatsu'

    def load(self, name: str) -> Either[str, 'Parsers']:
        return Right(self) if name in self.parsers else self._load(name)

    def _load(self, name: str) -> Either[str, 'Parsers']:
        def update(parser_ctor: type) -> Parsers:
            parser = parser_ctor()
            parser.gen()
            return self.modder.parsers(_ + (name, parser))
        return (
            Either.import_name('{}.{}'.format(self._builtin_mod, name), 'Parser') /
            update
        )

    def parser(self, name: str) -> Either[str, ParserBase]:
        return (
            self.parsers
            .lift(name)
            .to_either('no parser for `{}`'.format(name))
        )

__all__ = ('ParserBase', 'BuiltinParser', 'Parsers')
