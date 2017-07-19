import abc
from typing import Union, TypeVar, Generic, Tuple, cast, Any, Callable

from tatsu.ast import AST
from tatsu.infos import LineInfo, ParseInfo

from hues import huestr

from toolz import dissoc, valfilter

from ribosome.record import Record, str_field, int_field, field

from amino import List, _, Maybe, Map, Boolean, LazyList, L, Just, Either
from amino.tree import Node, ListNode, MapNode, LeafNode, Inode, SubTree
from amino.list import Lists
from amino.bi_rose_tree import RoseTree, BiRoseTree
from amino.func import dispatch
from amino.lazy_list import LazyLists
from amino.boolean import true, false
from amino.lazy import lazy


def indent(strings: Union[str, List[str]]) -> List[str]:
    return (
        cast(List[str], strings).map(' {}'.format)
        if isinstance(strings, List) else
        [str(strings)]
    )


class Line(Record):
    text = str_field()
    lnum = int_field()
    start = int_field()
    end = int_field()
    length = int_field()
    indent = int_field()

    @staticmethod
    def from_line_info(info: LineInfo) -> 'Line':
        return Line(
            text=info.text,
            lnum=info.line,
            start=info.start,
            end=info.end,
            length=info.end - info.start - 1,
            indent=Lists.wrap(info.text).index_where(_ != ' ').get_or_else(0)
        )

    @property
    def show_text(self) -> str:
        chomped = self.text.replace('\n', '')
        return f'"{chomped}"'

    @property
    def _str_extra(self) -> List[Any]:
        return List(self.lnum, self.start, self.length, self.end, self.show_text)

    @property
    def trim(self) -> str:
        return self.text.strip()


Sub = TypeVar('Sub')


class AstElem(Generic[Sub], Node[str, Sub]):

    @property
    def tpe(self) -> type:
        return AstElem

    @abc.abstractproperty
    def rule(self) -> str:
        ...

    @abc.abstractproperty
    def pos(self) -> int:
        ...

    @abc.abstractproperty
    def endpos(self) -> int:
        ...

    @property
    def range(self) -> Tuple[int, int]:
        return self.pos, self.endpos

    @abc.abstractproperty
    def line(self) -> Line:
        ...

    @property
    def line_length(self) -> int:
        return self.line.length

    @property
    def lnum(self) -> int:
        return self.line.lnum

    @abc.abstractproperty
    def text(self) -> str:
        ...

    @abc.abstractproperty
    def with_ws(self) -> str:
        ...

    @abc.abstractproperty
    def pos_with_ws(self) -> int:
        ...

    @abc.abstractproperty
    def indent(self) -> int:
        ...

    @abc.abstractproperty
    def col(self) -> int:
        ...

    @property
    def endcol(self) -> int:
        return self.endpos - self.line.start

    @property
    def is_bol(self) -> Boolean:
        return Boolean(self.col == self.indent)

    @abc.abstractproperty
    def is_eol(self) -> Boolean:
        ...

    @abc.abstractproperty
    def k(self) -> List[str]:
        ...

    @property
    def is_newline(self) -> bool:
        return isinstance(self, AstToken) and self.text == '\n'

    @abc.abstractproperty
    def short(self) -> str:
        ...

    @abc.abstractproperty
    def is_rule_node(self) -> bool:
        ...


class AstInode(Generic[Sub], Inode[str, Sub], AstElem[Sub]):

    @property
    def with_ws(self) -> str:
        return self.text

    @lazy
    def _sub_ref(self) -> Maybe[AstElem]:
        return self.sub_l.find(lambda a: not a.is_newline)

    def _sub_ref_int(self, attr: Callable[[AstElem], Maybe[int]]) -> int:
        return self._sub_ref / attr | -1

    @property
    def pos_with_ws(self) -> int:
        return self._sub_ref_int(_.pos_with_ws)

    @property
    def pos(self) -> int:
        return self._sub_ref_int(_.pos)

    @property
    def col(self) -> int:
        return self._sub_ref_int(_.col)

    @property
    def indent(self) -> int:
        return self._sub_ref_int(_.indent)

    @abc.abstractproperty
    def start_line(self) -> Line:
        ...

    @property
    def end_line(self) -> Line:
        return self.sub_l.last / _.line | self.start_line

    @property
    def line(self) -> Line:
        return self.sub_l.head / _.line | self.start_line

    @property
    def line_count(self) -> int:
        return self.end_line.lnum - self.start_line.lnum

    @property
    def ws_count(self) -> int:
        return self._sub_ref_int(_.ws_count)

    @property
    def is_eol(self) -> Boolean:
        return self.sub_l.last / _.is_eol | false


class AstList(ListNode[str], AstInode[LazyList[Node[str, Any]]]):

    def __init__(self, sub: List[AstElem], rule: str, line: Line) -> None:
        super().__init__(sub)
        self._rule = rule
        self._line = line

    @property
    def rule(self) -> str:
        return self._rule

    @property
    def endpos(self) -> int:
        return self.last.e / _.endpos | -1

    @property
    def start_line(self) -> Line:
        return self._line

    def replace(self, data: LazyList[AstElem]) -> 'AstList':
        return type(self)(data, self._rule, self.line)

    def cat(self, elem: AstElem) -> 'AstList':
        return self.replace(self.data.cat(elem))

    def __str__(self) -> str:
        return '{}({}, {})'.format(self.__class__.__name__, self.rule, self.data.join_comma)

    def __repr__(self) -> str:
        return '{}({}, {})'.format(self.__class__.__name__, self.rule, (self.data / repr).join_comma)

    @property
    def k(self) -> List[Tuple[int, str]]:
        return (self.data / _.rule).with_index

    @property
    def _keytree(self) -> List[str]:
        return (
            indent(self.data // _._keytree)
            .cons('[{}]'.format(huestr(self.rule).red.colorized))
        )

    @property
    def text(self) -> str:
        return (self.sub / _.with_ws).mk_string()

    @property
    def _desc(self) -> str:
        return f'[{self.rule}]'

    @property
    def short(self) -> str:
        sub = self.sub.map(_.rule).join_comma
        return f'{self.__class__.__name__}({self.rule}, {sub})'

    @property
    def is_rule_node(self) -> bool:
        return Boolean(not isinstance(self, AstClosure))


class AstClosure(AstList):
    ''' Closures are sublists of rules and cannot be top level.
    '''
    pass


class AstInternal(Map):

    def __init__(self, ast: AST, info: ParseInfo) -> None:
        super().__init__(ast)
        self.ast = ast
        self.info = info


class AstMap(MapNode[str], AstInode[Map[str, AstElem]]):

    def __init__(self, ast: AstInternal) -> None:
        super().__init__(ast)
        self._text = None
        self._with_ws = None

    @staticmethod
    def from_ast(ast: AST) -> 'AstMap':
        def filt(a: Any) -> bool:
            return a is not None and not a.empty and not a.is_newline
        return AstMap(AstInternal(valfilter(filt, dissoc(ast, 'parseinfo')), ast.parseinfo))

    @lazy
    def sub_l(self) -> LazyList[Node[AstElem, Any]]:
        return LazyList(self.sub.v.sort_by(_.pos))

    @property
    def ast(self) -> AstInternal:
        return self.data

    @property
    def info(self) -> ParseInfo:
        return self.ast.info

    @property
    def rule(self) -> str:
        return self.info.rule

    @property
    def pos(self) -> int:
        return self.info.pos

    @property
    def endpos(self) -> int:
        return self.info.endpos

    @property
    def start_line(self) -> Line:
        return Line.from_line_info(self.info.buffer.line_info(self.pos))

    @property
    def end_line(self) -> Line:
        return Line.from_line_info(self.info.buffer.line_info(self.endpos))

    def get(self, key: str, default: AstElem=None) -> Union[None, AstElem]:
        return dict.get(self, key, default)

    def __str__(self) -> str:
        return 'AstMap({}, {})'.format(self.rule, self.ast)

    def __repr__(self) -> str:
        return 'AstMap(\'{}\', {})'.format(self.rule, dict.__repr__(self.ast))

    @property
    def _keytree(self) -> List[str]:
        def sub(key: str, ast: AstElem) -> List[str]:
            ckey = huestr(key).yellow.colorized
            return indent(indent(ast._keytree).cons(ckey))
        return (
            List.wrap(list(dict.items(self)))
            .flat_map2(sub)
            .cons('{{{}}}'.format(huestr(self.rule).red.colorized))
        )

    @property
    def keytree(self) -> str:
        return self._keytree.join_lines

    @property
    def _k(self) -> List[str]:
        return self.ast.keys()

    @property
    def text(self) -> str:
        if self._text is None:
            self._text = self.info.buffer.text[self.pos:self.endpos]
        return cast(str, self._text)

    @property
    def with_ws(self) -> str:
        if self._with_ws is None:
            self._with_ws = self.info.buffer.text[self.pos_with_ws:self.endpos]
        return cast(str, self._with_ws)

    @property
    def lines(self) -> List[str]:
        return List.lines(self.with_ws)

    @property
    def k(self) -> List[str]:
        return List.wrap(self.data.keys())

    @property
    def _desc(self) -> str:
        return f'{{{self.rule}}}'

    def replace(self, data: Map[str, AstElem]) -> 'AstMap':
        return AstMap(AstInternal(data, self.ast.info))

    @property
    def short(self) -> str:
        keys = self.ast.k.join_comma
        return f'AstMap({self.rule}: {keys})'

    @property
    def boundary_nodes(self) -> AstElem:
        def filt(node: Node) -> bool:
            return node.is_bol or node.is_eol
        return self.filter_not(_.is_newline).filter(filt)

    @property
    def eols(self) -> List[int]:
        folder = lambda z, a: z.cons((z.head | 0) + len(a) + 1)
        return self.lines.detach_head.map2(lambda h, t: t.fold_left(List(len(h)))(folder).reversed) | List()

    @property
    def bols(self) -> List[int]:
        ''' add 1 for the newline byte
        '''
        return self.lines.fold_left(List(0))(lambda z, a: z.cat((z.last | 0) + 1 + len(a)))

    @property
    def is_rule_node(self) -> Boolean:
        return true

    @property
    def empty(self) -> Boolean:
        return self.sub.empty


class AstToken(LeafNode[str], AstElem[None]):

    def __init__(self, raw: str, pos: int, line: Line, rule: str, ws_count: int) -> None:
        super().__init__(raw)
        self._rule = rule
        self._pos = pos
        self._line = line
        self.ws_count = ws_count  # whitespace between previous and this token

    @property
    def raw(self) -> str:
        return self.data

    @property
    def text(self) -> str:
        return self.raw

    @property
    def rule(self) -> str:
        return self._rule

    @property
    def pos(self) -> int:
        return self._pos

    @property
    def endpos(self) -> int:
        return self.pos + len(self.raw)

    @property
    def col(self) -> int:
        return self.pos - self.line.start

    @property
    def indent(self) -> int:
        return self.line.indent

    @property
    def line(self) -> Line:
        return self._line

    def __str__(self) -> str:
        return self.raw

    def __repr__(self) -> str:
        raw = '\\n' if self.raw == '\n' else self.raw
        return '{}({}, {}, {}, {}, {})'.format(
            self.__class__.__name__, self.rule, raw, self.pos, self.lnum, self.ws_count)

    @property
    def whitespace(self) -> str:
        return ' ' * self.ws_count

    @property
    def _keytree(self) -> List[str]:
        return List('{} -> {}'.format(huestr(self.rule).red.colorized, huestr(self.raw).green.colorized))

    @property
    def range(self) -> Tuple[int, int]:
        return self.pos, self.pos + len(self.text)

    @property
    def with_ws(self) -> str:
        return '{}{}'.format(self.whitespace, self.text)

    @property
    def pos_with_ws(self) -> int:
        return self.pos - self.indent

    @property
    def k(self) -> List[str]:
        return List(self.key)

    @property
    def short(self) -> str:
        return str(self)

    @property
    def is_rule_node(self) -> Boolean:
        return false

    @property
    def is_eol(self) -> Boolean:
        return Boolean(self.line_length == self.endcol)

A = TypeVar('A')


class RoseData(Record):
    key = str_field()
    ast = field(AstElem)
    parent = field(RoseTree)

    def cons(key: str, ast: AstElem, parent: RoseTree) -> 'RoseData':
        return RoseData(key=key, ast=ast, parent=parent)

    def __str__(self) -> str:
        bol = ' bol' if self.bol else ''
        eol = ' eol' if self.eol else ''
        return f'{self.key}: {self.ast.short}{bol}{eol}'

    def __repr__(self) -> str:
        return f'RoseData({str(self)})'

    @property
    def rule(self) -> str:
        return self.ast.rule

    @property
    def parent_rule(self) -> str:
        return self.parent.data.rule

    @property
    def desc(self) -> str:
        return f'{self.rule}_{self.key}'

    @property
    def is_token(self) -> bool:
        return isinstance(self.ast, AstToken)

    @property
    def line(self) -> int:
        return self.ast.line

    @property
    def bol(self) -> Boolean:
        return self.ast.is_bol

    @property
    def eol(self) -> Boolean:
        return self.ast.is_eol

    @property
    def indent(self) -> int:
        return self.ast.indent

    @property
    def with_ws(self) -> str:
        return self.ast.with_ws

    @property
    def ws_count(self) -> int:
        return self.ast.ws_count

    @property
    def pos(self) -> int:
        return self.ast.pos


class RoseAstTree(RoseTree[RoseData]):

    @property
    def ast(self) -> AstElem:
        return self.data.ast

    @property
    def rule(self) -> str:
        return self.data.rule

    @property
    def is_token(self) -> bool:
        return self.data.is_token

    @property
    def range(self) -> Tuple[int, int]:
        return self.ast.range

    @property
    def pos(self) -> int:
        return self.ast.pos

    @property
    def line(self) -> int:
        return self.ast.line

    @property
    def s(self) -> SubTree:
        return self.ast.s

    @property
    def startpos(self) -> int:
        return self.pos

    @property
    def endpos(self) -> int:
        return self.ast.endpos

    def parent_with_rule(self, rule: str) -> Either[str, 'RoseAstTree']:
        def loop(cur: RoseAstTree) -> Maybe[RoseAstTree]:
            return Just(cur) if cur.rule == rule else loop(cur.parent)
        return loop(self.parent).to_either(f'no parent with rule `{rule}` for {self}')


class RoseAstElem(BiRoseTree[RoseData], RoseAstTree):
    pass


class AstRoseTreeConverter:

    @staticmethod
    def convert() -> Callable:
        return dispatch(AstRoseTreeConverter(), List(AstMap, AstList, AstToken), 'convert_')

    def rec(self, ast: AstElem) -> Callable:
        return AstRoseTreeConverter.convert()(ast)

    def convert_ast_token(self, ast: AstToken) -> Callable:
        return lambda parent: LazyLists.empty()

    def convert_ast_list(self, ast: AstList) -> Callable:
        return lambda parent: ast.sub.map(
            lambda a: RoseAstElem(RoseData.cons(parent.data.key, a, parent), parent, self.rec(a)))

    def convert_ast_map(self, ast: AstMap) -> Callable:
        def cons(key: str, node: AstElem, parent: RoseTree) -> RoseTree:
            return RoseAstElem(RoseData.cons(key, node, parent), parent, self.rec(node))
        return lambda parent: LazyList(ast.sub.to_list.sort_by(lambda a: a[1].pos)).map2(L(cons)(_, _, parent))


def ast_rose_tree(ast: AstElem[Any]) -> RoseTree[AstElem[Any]]:
    convert = AstRoseTreeConverter.convert()
    return RoseAstTree(RoseData.cons('root', ast, RoseTree(ast, LazyLists.empty())), convert(ast))

__all__ = ('indent', 'Line', 'AstElem', 'AstInode', 'AstList', 'AstMap', 'AstToken', 'RoseData', 'RoseAstTree',
           'RoseAstElem', 'ast_rose_tree')
