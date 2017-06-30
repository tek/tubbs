import abc
from typing import Callable, Tuple, Any

from amino import List, L, Right, Map, Left
from amino.util.string import snake_case

from ribosome.record import Record, int_field, field
from ribosome.nvim import NvimFacade
from ribosome.util.callback import VimCallback

from tubbs.formatter.tree import Tree, BiNode
from tubbs.formatter.base import Formatter, VimFormatterMeta


class IndentRules:

    def default(self, node: BiNode) -> int:
        return 0


class Indent(Record):
    node = field(BiNode)
    indent = int_field()

    @property
    def pos(self) -> int:
        return self.node.pos

    @property
    def _str_extra(self) -> List[Any]:
        return List(self.node.key, self.indent)


class IndentData:
    pass


class StrictIndentData(IndentData):
    pass


class LazyIndentData(IndentData):
    pass


class IndenterBase(Formatter):

    def __init__(self, shiftwidth: int) -> None:
        self.shiftwidth = shiftwidth

    @abc.abstractmethod
    def handler(self, name: str) -> Callable[[BiNode], int]:
        ...

    @abc.abstractproperty
    def default_handler(self) -> Callable[[BiNode], int]:
        ...

    # change the algorithm to operate node-wise
    # keep a stack of the indent levels, descend into a node, seek the next bol (or eol?), then recurse
    # after processing a node, convert its content to lines
    # apply the node's indent to all contained lines
    # find the next eol node and determine the container. maybe special case for braces and parens etc
    # filter tree to include only bol and eol, then map to create indent and keep the node
    def format(self, tree: Tree) -> List[str]:
        ...
        # def folder(z: List[Indent], a: BiNode) -> List[int]:
        #     # print('------')
        #     # print(a)
        #     # print(a)
        #     return z
        # # indents = tree.bol_nodes.fold_left(List())(folder)
        # indents = (
        #     bol_nodes(tree) /
        #     __.map(self.indents) //
        #     __.max_by(lambda a: abs(a.indent)) /
        #     _.indent
        # )
        # return self.indent(tree.root.indent, tree.lines, indents)

    def lookup_handler(self, node: BiNode) -> Callable[[BiNode], int]:
        def handler(name: str, or_else: Callable=lambda: None) -> Callable[[BiNode], int]:
            self.log.ddebug('trying ident handler {}'.format(name))
            h = self.handler(name)
            return h or or_else() or self.default_handler
        rule = snake_case(node.rule)
        return handler(
            '{}_{}'.format(rule, node.key),
            L(handler)(rule, L(handler)(node.key))
        )

    def indents(self, node: BiNode) -> Indent:
        indent = self.lookup_handler(node)(node)
        return Indent(node=node, indent=indent)

    def indent(self, baseline: int, lines: List[str], indents: List[int]) -> List[str]:
        if len(lines) != len(indents):
            return Left('got {} indents for {} lines'.format(len(indents), len(lines)))
        else:
            root_indent = baseline / self.shiftwidth
            data = lines.zip(indents)
            return Right(self._indent1(data, root_indent))

    def _indent1(self, data: List[Tuple[str, int]], root_indent: float) -> List[str]:
        def shift(z: Tuple[float, List[str]], a: Tuple[str, int]) -> Tuple[float, List[str]]:
            current_indent, result = z
            line, indent = a
            new_indent = current_indent + indent
            line_indent = int(self.shiftwidth * new_indent)
            new_line = '{}{}'.format(' ' * line_indent, line.strip())
            return new_indent, result.cat(new_line)
        return data.fold_left((root_indent, List()))(shift)[1]


class Indenter(IndenterBase):

    def __init__(self, rules: IndentRules, shiftwidth: int) -> None:
        super().__init__(shiftwidth)
        self.rules = rules

    def handler(self, name: str) -> Callable[[BiNode], int]:
        return getattr(self.rules, name, None)

    @property
    def default_handler(self) -> Callable[[BiNode], int]:
        return self.rules.default


class DictIndenter(IndenterBase):

    def __init__(self, rules: Map, shiftwidth: int) -> None:
        super().__init__(shiftwidth)
        self.rules = rules

    def handler(self, name: str) -> Callable[[BiNode], int]:
        return self.rules.lift(name) / (lambda a: lambda node: a) | None

    @property
    def default_handler(self) -> Callable[[BiNode], int]:
        return lambda node: 0


class VimDictIndenter(DictIndenter, VimCallback, metaclass=VimFormatterMeta):

    def __init__(self, vim: NvimFacade, rules: Map) -> None:
        sw = vim.options('shiftwidth') | 2
        super().__init__(rules, sw)


__all__ = ('Indenter', 'DictIndenter', 'VimDictIndenter')
