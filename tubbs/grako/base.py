import hashlib
import abc

from grako import gencode
from grako.ast import AST

from amino import Either, Try, List, Map, L, Path, _, Right
from amino.util.string import camelcaseify

from ribosome.record import Record, map_field


def flatten(ast):
    return ast if isinstance(ast, str) else ''.join(map(flatten, ast))


def to_list(a):
    return List.wrap(a) if isinstance(a, list) else a


def filter_empty(l):
    return [a for a in l if not (isinstance(a, list) and not a)]


class AstMap(AST, Map):

    @staticmethod
    def from_ast(ast: AST):
        a = AstMap()
        a.update(**ast)
        a._order = ast._order
        a._parseinfo = ast._parseinfo
        a._closed = ast._closed
        return a

    def __getattr__(self, key):
        return self.lift(key) / to_list

    def get(self, key, default=None):
        return dict.get(self, key, default)


class DataSemantics:

    def id(self, ast):
        return flatten(ast)

    def _default(self, ast):
        return (
            ast
            if isinstance(ast, str) else
            filter_empty(ast)
            if isinstance(ast, list) else
            AstMap.from_ast(ast)
            if isinstance(ast, dict) else
            ast
        )


class ParserBase(metaclass=abc.ABCMeta):

    @abc.abstractproperty
    def name(self) -> str:
        ...

    @abc.abstractproperty
    def path(self) -> str:
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
        return Map()

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
        return Either.import_path(self.path) // L(Try)(_, **self.parser_args)

    @property
    def semantics(self):
        return DataSemantics()

    def parse(self, text: str, rule: str):
        return (
            self.parser //
            L(Try)(_.parse, text, rule, semantics=self.semantics) /
            to_list
        )


class BuiltinParser(ParserBase):

    @property
    def path(self):
        return 'tubbs.parsers.{}.{}Parser'.format(self.name, self.camel_name)

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
        return self.parsers.lift(name)

__all__ = ('ParserBase',)
