import hashlib
import abc

from grako import gencode
from grako.exceptions import FailedToken
from grako.parsing import Parser as GrakoParser
from grako.ast import AST

from amino import Either, Try, Map, L, Path, _, Right, List
from amino.util.string import camelcaseify
from amino.lazy import lazy
from amino.func import dispatch

from ribosome.record import Record, map_field

from tubbs.grako.ast import to_list, AstMap, AstToken, AstList
from tubbs.logging import Logging


def flatten(ast):
    return ast if isinstance(ast, str) else ''.join(map(flatten, ast))


def filter_empty(l):
    return [a for a in l if not (isinstance(a, list) and not a)]


class PostProc:

    def __call__(self, ast, rule, pos):
        return self.wrap_data(ast, rule, pos)

    @lazy
    def wrap_data(self):
        return dispatch(self, [str, list, AstMap, AstToken], 'wrap_')

    def wrap_str(self, raw, rule, pos):
        return AstToken(raw=raw, rule=rule, pos=pos)

    def wrap_list(self, raw, rule, pos):
        return AstList(raw, rule, pos)

    def wrap_ast_map(self, ast, rule, pos):
        return ast

    def wrap_ast_token(self, token, rule, pos):
        return token


class DataSemantics(Logging):

    def _special(self, ast, name):
        handler = getattr(self, '_special_{}'.format(name),
                          L(self._no_special)(name, _))
        return handler(ast)

    def _special_token(self, ast):
        raw = (ast / _.raw).mk_string()
        return AstToken(raw=raw, rule=ast.rule, pos=ast.pos)

    def _no_special(self, name, ast):
        self.log.error('no handler for argument `{}` and {}'.format(name, ast))
        return ast

    def _default(self, ast, *a, **kw):
        ast1 = List.wrap(a).head / L(self._special)(ast, _) | ast
        return AstMap.from_ast(ast1) if isinstance(ast1, AST) else ast1


class ParserMixin(GrakoParser):

    @lazy
    def _wrap_data(self):
        return PostProc()

    @property
    def _last_rule(self):
        return self._rule_stack[-1]

    def _token(self, raw):
        self._next_token()
        pos = self._pos
        if self._buffer.match(raw) is None:
            self._trace_match(raw, failed=True)
            self._error(raw, etype=FailedToken)
        token = AstToken(raw=raw, pos=pos, rule=self._last_rule)
        self._trace_match(token)
        self._add_cst_node(token)
        self._last_node = token
        return token

    def name_last_node(self, name):
        self.ast[name] = self._wrap_data(self.last_node, name, self._last_pos)

    def _call(self, rule, name, params, kwparams):
        self._last_pos = pos = self._pos
        ret = GrakoParser._call(self, rule, name, params, kwparams)
        return self._wrap_data(ret, name, pos)

    def _wrap_str(self, raw, rule, pos):
        return AstToken(raw=raw, rule=rule, pos=pos)

    def _wrap_list(self, raw, rule, pos):
        return AstList(raw, rule, pos)

    def _wrap_dict(self, ast, rule, pos):
        if not isinstance(ast, AstMap):
            raise Exception('invalid ast map: {}'.format(ast))
        return ast

    def _wrap_ast_token(self, token, rule, pos):
        return token

    def _add_cst_node(self, node):
        wrapped = self._wrap_data(node, self._last_rule, self._last_pos)
        return super()._add_cst_node(wrapped)


class ParserBase(abc.ABC):

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
    def parser_class(self):
        return '{}Parser'.format(self.camel_name)

    @property
    def base_dir(self):
        return Path(__file__).parent.parent.parent  # type: ignore

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
            cls = type(self.parser_class, (ParserMixin, tpe), {})
            return Try(lambda *a, **kw: cls(*a, **kw), **self.parser_args)
        return Either.import_path(self.path) // cons

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
        return 'tubbs.parsers.{}.{}'.format(self.name, self.parser_class)

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

__all__ = ('ParserBase',)
