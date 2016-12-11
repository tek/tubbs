from pathlib import Path
import hashlib

from grako import gencode
from grako.ast import AST

from amino import Try, List, Map

base = Path(__file__).parent.parent.parent  # type: ignore

grammar_path = base / 'grammar'

scala_grammar_file = grammar_path / 'scala.ebnf'

parser_path = base / 'tubbs' / 'parsers' / 'scala.py'

chksum_path = base / 'hashes' / 'scala'


def flatten(ast):
    return ast if isinstance(ast, str) else ''.join(map(flatten, ast))


def to_list(a):
    return List.wrap(a) if isinstance(a, list) else a


def filter_empty(l):
    return [a for a in l if not (isinstance(a, list) and not a)]


class AstMap(AST, Map):

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
            AstMap(ast)
            if isinstance(ast, dict) else
            ast
        )


def grammar_chksum():
    return hashlib.sha384(scala_grammar_file.read_bytes()).digest()


def checksum_changed():
    return (not chksum_path.is_file() or
            chksum_path.read_bytes() != grammar_chksum())


def gen():
    if not parser_path.is_file() or checksum_changed():
        if parser_path.is_file():
            parser_path.unlink()
        grammar = scala_grammar_file.read_text()
        model = gencode('Scala', grammar)
        parser_path.write_text(model)
        chksum_path.write_bytes(grammar_chksum())


def parse(text: str, rule: str):
    from tubbs.parsers.scala import ScalaParser
    parser = ScalaParser()
    return Try(parser.parse, text, rule, semantics=DataSemantics()) / to_list

__all__ = ('gen', 'parse')
