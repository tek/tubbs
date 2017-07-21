import abc
from typing import Callable, Union

from amino import List, L, Right, Map, Either, __, _, Maybe, Eval, Boolean
from amino.list import Lists

from ribosome.nvim import NvimFacade
from ribosome.util.callback import VimCallback

from tubbs.formatter.base import Formatter, VimFormatterMeta
from tubbs.tatsu.ast import AstElem, ast_rose_tree, RoseAstTree, Line, RoseData
from tubbs.formatter.indenter.indent import Indent
from tubbs.formatter.indenter.state import IndentState
from tubbs.formatter.indenter.cond import IndentCond, NoIndent, mk_indent
from tubbs.tatsu.indenter_dsl import Parser
from tubbs.formatter.indenter.dsl import parse_indent_expr


IndentResult = Union[Indent, int]
Handler = Callable[[], IndentCond]


class IndenterBase(Formatter[IndentCond]):

    def __init__(self, shiftwidth: int) -> None:
        self.shiftwidth = shiftwidth

    @abc.abstractmethod
    def handler(self, name: str) -> Maybe[Handler]:
        ...

    @abc.abstractproperty
    def default_handler(self) -> Handler:
        ...

    def format(self, ast: AstElem) -> Eval[Either[str, List[str]]]:
        rt = ast_rose_tree(ast.boundary_nodes)
        return Eval.now(self.collect_indents(rt) / _.indents / L(self.apply_indents)(ast, _))

    def collect_indents(self, ast: RoseAstTree) -> Either[str, IndentState]:
        def run(z: IndentState, n: RoseAstTree) -> Either[str, IndentState]:
            def descend(i: Indent) -> Either[str, IndentState]:
                z1 = z.push_sub(i)
                return n.sub.fold_m(Right(z1))(run).map(__.pop(i)).map(__.push_after(i))
            return self.node_indent(z.set(node=n)) // descend
        return run(IndentState(node=ast, current=0), ast)

    def apply_indents(self, ast: AstElem, indents: List[Indent]) -> List[str]:
        return (
            indents
            .group_by(_.line)
            .valmap(__.max_by(lambda a: abs(a.amount)))
            .map2(lambda l, i: (l.lnum, self.indent_line(ast.indent, l, i)))
            .sort_by(_[0])
            .map(_[1])
        )

    def indent_line(self, baseline: int, line: Line, indent: Maybe[Indent]) -> str:
        shifts = (indent / _.amount | 0)
        ws = ' ' * ((shifts * self.shiftwidth) + baseline)
        return f'{ws}{line.trim}'

    def _handler_names(self, node: RoseData, names: List[str]) -> List[str]:
        def boundary(cond: Boolean, suf: str) -> List[str]:
            return Lists.iff_l(cond)(lambda: names.map(lambda a: f'{a}_{suf}'))
        return boundary(node.bol, 'bol') + boundary(node.eol, 'eol')

    def node_indent(self, state: IndentState) -> Either[str, Indent]:
        result = self.lookup_handler(state.data)()
        return result.info(state).info.map2(L(mk_indent)(state.node, _, _))


class IndentRules:

    def default(self) -> IndentCond:
        return NoIndent()


class Indenter(IndenterBase):

    def __init__(self, rules: IndentRules, shiftwidth: int) -> None:
        super().__init__(shiftwidth)
        self.rules = rules

    def handler(self, name: str) -> Maybe[Handler]:
        return Maybe.getattr(self.rules, name)

    @property
    def default_handler(self) -> Handler:
        return self.rules.default


class DictIndenter(IndenterBase):

    def __init__(self, parser: Parser, rules: Map, conds: Map[str, Callable], shiftwidth: int) -> None:
        super().__init__(shiftwidth)
        self.parser = parser
        self.rules = rules
        self.conds = conds

    def handler(self, attr: str) -> Maybe[Handler]:
        return self.rules.lift(attr) / L(parse_indent_expr)(self.parser, _, self.conds) / (lambda a: lambda: a)

    @property
    def default_handler(self) -> Handler:
        return lambda: NoIndent()


class VimDictIndenter(DictIndenter, VimCallback, metaclass=VimFormatterMeta):

    def __init__(self, vim: NvimFacade, parser: Parser, rules: Map, conds: Map[str, Callable]) -> None:
        sw = vim.buffer.options('shiftwidth') | 2
        super().__init__(parser, rules, conds, sw)


__all__ = ('Indenter', 'DictIndenter', 'VimDictIndenter')
