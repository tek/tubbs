import abc
from typing import Union, TypeVar, Generic, Tuple, cast, Any

from tatsu.ast import AST
from tatsu.infos import LineInfo, ParseInfo

from hues import huestr

from toolz import dissoc, valfilter

from ribosome.record import Record, str_field, int_field

from amino import List, Empty, _, Maybe, Either, Left, Right, Just, Map, Boolean, LazyList
from amino.tree import Node, ListNode, MapNode, LeafNode, SubTree, SubTreeValid, SubTreeLeaf, Inode
from amino.list import Lists


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
        return List(self.lnum, self.start, self.length, self.show_text)


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
    def line_num(self) -> int:
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

    @property
    def indent(self) -> int:
        return self.line.indent

    @property
    def col(self) -> int:
        return self.pos - self.line.start

    @property
    def endcol(self) -> int:
        return self.endpos - self.line.start

    @property
    def is_bol(self) -> Boolean:
        return Boolean(self.col == self.indent)

    @property
    def is_eol(self) -> Boolean:
        return Boolean(self.line_length == self.endcol)

    @abc.abstractproperty
    def k(self) -> List[str]:
        ...

    @property
    def is_newline(self) -> bool:
        return isinstance(self, AstToken) and self.text == '\n'


class AstInode(Generic[Sub], Inode[str, Sub], AstElem[Sub]):

    @abc.abstractmethod
    def sub_range(self, name: str) -> Either[str, Tuple[int, int]]:
        ...

    @property
    def with_ws(self) -> str:
        return self.text

    @property
    def pos_with_ws(self) -> int:
        return self.sub_l.head / _.pos_with_ws | self.pos


class AstList(ListNode[str], AstInode[LazyList[Node[str, Any]]]):

    def __init__(self, sub: List[AstElem], rule: str, line: Line) -> None:
        super().__init__(sub)
        self._rule = rule
        self._line = line

    @property
    def rule(self) -> str:
        return self._rule

    @property
    def pos(self) -> int:
        return self.head.e / _.pos | -1

    @property
    def endpos(self) -> int:
        return self.last.e / _.endpos | -1

    @property
    def line(self) -> Line:
        return self._line

    def replace(self, data: List[AstElem]) -> 'AstList':
        return AstList(data, self._rule, self.line)

    def cat(self, elem: AstElem) -> 'AstList':
        return self.replace(self.data.cat(elem))

    @property
    def ws_count(self) -> int:
        return self.head.e / _.ws_count | 0

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

    def sub_range(self, name: str) -> Either[str, Tuple[int, int]]:
        return (
            self.sub.find(_.key == name)
            .to_either('{} not in {}'.format(name, self)) /
            _.range
        )

    @property
    def text(self) -> str:
        return (self.sub / _.with_ws).mk_string()

    @property
    def _desc(self) -> str:
        return f'[{self.rule}]'


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
            return a is not None and not a.empty
        return AstMap(AstInternal(valfilter(filt, dissoc(ast, 'parseinfo')), ast.parseinfo))

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
    def line(self) -> Line:
        return Line.from_line_info(self.info.buffer.line_info(self.pos))

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

    def sub_range(self, name: str) -> Either[str, Tuple[int, int]]:
        return self.lift(name).e / _.range

    @property
    def k(self) -> List[str]:
        return List.wrap(self.data.keys())

    @property
    def _desc(self) -> str:
        return f'{{{self.rule}}}'

    def replace(self, data: Map[str, AstElem]) -> 'AstMap':
        return AstMap(AstInternal(data, self.ast.info))


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
    def line(self) -> Line:
        return self._line

    def __str__(self) -> str:
        return self.raw

    def __repr__(self) -> str:
        raw = '\\n' if self.raw == '\n' else self.raw
        return '{}({}, {}, {}, {}, {})'.format(
            self.__class__.__name__, self.rule, raw, self.pos, self.line_num, self.ws_count)

    @property
    def whitespace(self) -> str:
        return ' ' * self.ws_count

    @property
    def _keytree(self) -> List[str]:
        return List('{} -> {}'.format(huestr(self.rule).red.colorized, huestr(self.raw).green.colorized))

    def sub_range(self, name: str) -> Either[str, Tuple[int, int]]:
        return Right(self.range)

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

A = TypeVar('A')


class SubAst(SubTree):

    # @staticmethod
    # def cons(data, key: str, rule: str) -> 'SubAst':
    #     cons = dispatch_with({AstMap: SubAstMap, AstList: SubAstList, AstToken: SubAstToken})
    #     return cons(data)

    # @staticmethod
    # def from_maybe(data: Maybe[AstElem], key: str, rule: str, err: str):
    #     return data.cata(
    #         L(SubAstValid.cons)(_, key, rule),
    #         SubAstInvalid(key, rule, err)
    #     )

    # def cata(self, f: Callable[[AstElem], A], b: Union[A, Callable[[], A]]
    #          ) -> A:
    #     return (
    #         f(self._data)
    #         if isinstance(self, SubAstValid)
    #         else call_by_name(b)
    #     )

    @abc.abstractproperty
    def line(self) -> Maybe[int]:
        ...

    @property
    def _no_token(self) -> str:
        return 'ast is not a token'

    @property
    def raw(self) -> Either[str, str]:
        return (
            Right(self._data.raw)
            if isinstance(self, SubTreeLeaf) else
            Left(self._no_token)
        )


class SubAstValid(Generic[A], SubAst, SubTreeValid):

    @property
    def rule(self) -> str:
        return self._data.rule

    @property
    def line(self) -> Maybe[int]:
        return Just(self._data.line)


class SubAstInvalid(SubAst):

    def __init__(self, key: str, rule: str, reason: str) -> None:
        super().__init__(key, reason)
        self.rule = rule

    def __str__(self) -> str:
        s = 'SubAstInvalid({}, {}, {})'
        return s.format(self.key, self.rule, self.reason)

    @property
    def _error(self) -> str:
        return 'no sub ast `{}` in `{}`: {}'.format(self.key, self.rule, self.reason)

    @property
    def _no_token(self) -> str:
        return self._error

    @property
    def line(self) -> Maybe[int]:
        return Empty()


def boundary_nodes(tree: AstMap) -> List[AstElem]:
    def filt(node: Node) -> bool:
        return node.is_bol or node.is_eol
    return tree.filter_not(_.is_newline).filter(filt)

__all__ = ('SubAst', 'SubAstValid', 'SubAstInvalid', 'AstMap')
