import abc
from typing import Callable, Any, Union, cast

from amino import List, L, Right, Map, Left, Either, __, _, Maybe, Eval, Boolean
from amino.list import Lists

from ribosome.record import Record, int_field, field, list_field, bool_field
from ribosome.nvim import NvimFacade
from ribosome.util.callback import VimCallback

from tubbs.formatter.base import Formatter, VimFormatterMeta
from tubbs.tatsu.ast import AstElem, ast_rose_tree, RoseAstTree, Line, RoseData


class Indent(Record):
    node = field(RoseData)
    indent = int_field()
    absolute = bool_field()

    @property
    def line(self) -> int:
        return self.node.line

    @property
    def _str_extra(self) -> List[Any]:
        return List(self.node.desc, self.indent)

    @property
    def sub(self) -> bool:
        return isinstance(self, IndentChildren)

    @property
    def after(self) -> bool:
        return isinstance(self, IndentAfter)

    def inc(self, i: int) -> 'Indent':
        return self.set(indent=self.indent + i)


class IndentAfter(Indent):
    pass


class IndentHere(Indent):
    pass


class IndentFromHere(Indent):
    pass


class IndentChildren(Indent):
    pass


def after(node: RoseData, amount: int) -> Indent:
    return IndentAfter(node=node, indent=amount)


def from_here(node: RoseData, amount: int) -> Indent:
    return IndentFromHere(node=node, indent=amount)


def children(node: RoseData, amount: int) -> Indent:
    return IndentChildren(node=node, indent=amount)


def keep(node: RoseData) -> Indent:
    return Indent(node=node, indent=0)


class IndentState(Record):
    current = int_field()
    indents = list_field(Indent)
    stack = list_field(Indent)

    def push_here(self, new: Indent) -> 'IndentState':
        add = new.inc(self.current)
        self.log.ddebug(lambda: f'indent for {add.node}: {add.indent}')
        return self.append1.indents(add)

    def update_current(self, update: Indent) -> 'IndentState':
        current = update.indent if update.absolute else self.current + update.indent
        self.log.ddebug(lambda: f'push current: {update} {current}')
        return self.set(current=current).append1.stack(update)

    def push_sub(self, new: Indent) -> 'IndentState':
        keep = Indent(node=new.node, indent=0)
        add_stack = cast(Indent, new) if isinstance(new, (IndentChildren, IndentFromHere)) else keep
        add_indents = new if isinstance(new, (IndentHere, IndentFromHere)) else keep
        return self.push_here(add_indents).update_current(add_stack)

    def push_after(self, new: Indent) -> 'IndentState':
        return self.update_current(new) if isinstance(new, (IndentAfter, IndentFromHere)) else self

    def pop(self, start: Indent) -> 'IndentState':
        index = self.stack.index_where(lambda a: a.node == start.node) | -1
        before = self.stack[:index]
        after = self.stack[index:]
        dec = sum(after.map(_.indent))
        self.log.ddebug(lambda: f'pop: {start} {dec}')
        return self.set(current=self.current - dec, stack=before)

    @property
    def _str_extra(self) -> List[Any]:
        return List(self.current, self.indents)


IndentResult = Union[Indent, int]
Handler = Callable[[RoseData], IndentResult]


class IndenterBase(Formatter):

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

    def collect_indents(self, ast: RoseAstTree) -> List[str]:
        def run(z: IndentState, n: RoseAstTree) -> Either[str, IndentState]:
            def descend(i: Indent) -> Either[str, IndentState]:
                z1 = z.push_sub(i)
                return n.sub.fold_m(Right(z1))(run).map(__.pop(i)).map(__.push_after(i))
            return self.node_indent(n.data) // descend
        return run(IndentState(current=0), ast)

    def apply_indents(self, ast: AstElem, indents: List[Indent]) -> List[str]:
        return (
            indents
            .group_by(_.line)
            .valmap(__.max_by(lambda a: abs(a.indent)))
            .map2(lambda l, i: (l.lnum, self.indent_line(ast.indent, l, i)))
            .sort_by(_[0])
            .map(_[1])
        )

    def indent_line(self, baseline: int, line: Line, indent: Maybe[Indent]) -> str:
        shifts = (indent / _.indent | 0)
        ws = ' ' * ((shifts * self.shiftwidth) + baseline)
        return f'{ws}{line.trim}'

    def _handler_names(self, node: RoseData, names: List[str]) -> List[str]:
        def boundary(cond: Boolean, suf: str) -> List[str]:
            return Lists.iff_l(cond)(lambda: names.map(lambda a: f'{a}_{suf}'))
        return boundary(node.bol, 'bol') + boundary(node.eol, 'eol')

    def node_indent(self, node: RoseData) -> Either[str, Indent]:
        result = self.lookup_handler(node)(node)
        return (
            Right(IndentHere(node=node, indent=result))
            if isinstance(result, int) else
            Right(result)
            if isinstance(result, Indent) else
            Left(f'invalid indent result {result} for {node}')
        )


class IndentRules:

    def default(self, node: RoseData) -> IndentResult:
        return 0


class Indenter(IndenterBase):

    def __init__(self, rules: IndentRules, shiftwidth: int) -> None:
        super().__init__(shiftwidth)
        self.rules = rules

    def handler(self, name: str) -> Maybe[Handler]:
        return Maybe.getattr(self.rules, name)

    @property
    def default_handler(self) -> Callable[[RoseData], IndentResult]:
        return self.rules.default


class DictIndenter(IndenterBase):

    def __init__(self, rules: Map, shiftwidth: int) -> None:
        super().__init__(shiftwidth)
        self.rules = rules

    def handler(self, name: str) -> Maybe[Handler]:
        return self.rules.lift(name) / (lambda a: lambda node: a)

    @property
    def default_handler(self) -> Handler:
        return lambda node: 0


class VimDictIndenter(DictIndenter, VimCallback, metaclass=VimFormatterMeta):

    def __init__(self, vim: NvimFacade, rules: Map) -> None:
        sw = vim.options('shiftwidth') | 2
        super().__init__(rules, sw)


__all__ = ('Indenter', 'DictIndenter', 'VimDictIndenter')
