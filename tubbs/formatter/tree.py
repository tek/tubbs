import abc
from typing import Tuple, Generic, TypeVar, Any

from toolz import valfilter

from tatsu.infos import ParseInfo

from amino import List, L, _, __, Either, Right, Map, LazyList
from amino.lazy import lazy
from amino.list import flatten
from amino.func import is_not_none
from amino.tree import Node, LeafNode, ListNode, SubTree, SubTreeLeaf, SubTreeValid
from amino.tc.base import TypeClass, tc_prop

from tubbs.logging import Logging
from tubbs.tatsu.ast import AstList, AstElem, AstToken, AstMap


def flatten_list(data: AstElem) -> List:
    def flat(data: AstElem) -> List:
        l = data.sub if isinstance(data, AstList) else data
        return (
            flatten(map(flat, l))
            if isinstance(l, list) else
            [l]
        )
    return List.wrap(flat(data))


Sub = TypeVar('Sub')
Sub1 = TypeVar('Sub1')


class BiNode(Generic[Sub, Sub1], Node[AstElem[Sub1], Sub]):

    def __init__(self, key: str, data: AstElem[Sub1], parent: Node[AstElem, Any]) -> None:
        self._data = data
        self.parent = parent
        self.key = key

    @abc.abstractproperty
    def rule(self) -> str:
        ...

    @property
    def range(self) -> Tuple[int, int]:
        return self._data.range

    @property
    def pos(self) -> int:
        return self._data.pos

    @property
    def endpos(self) -> int:
        return self._data.endpos

    @property
    def line(self) -> int:
        return self._data.line

    def __str__(self) -> str:
        return '{}({}, {}, {} children)'.format(self.__class__.__name__, self.rule, self.key, len(self.sub))

    @property
    def text(self) -> str:
        return self._data.text

    @property
    def with_ws(self) -> str:
        return self._data.with_ws

    @property
    def indent(self) -> int:
        return self._data.indent

    @property
    def k(self) -> List[str]:
        return self._data.k


class BiInode(Generic[Sub1], ListNode[AstElem[Sub1]]):

    def sub_range(self, name: str) -> Either[str, Tuple[int, int]]:
        return self._data.sub_range(name)


class BiListNode(Generic[Sub1], BiInode[Sub1]):

    def __init__(self, key: str, data: AstElem[Sub], parent: Node[AstElem, Any]) -> None:
        super().__init__(key, data, parent)
        self._sub_l = None

    @property
    def sub(self) -> LazyList[AstElem[Sub1]]:
        if self._sub_l is None:
            sub = flatten_list(self._data)
            self._sub_l = List.wrap(sub) / L(bi_node)(self.key, _, self)
        return self._sub_l

    @property
    def _desc(self) -> str:
        return '[{}]'.format(self.key)

    @property
    def rule(self) -> str:
        return self.parent.rule


class BiMapNode(Generic[Sub1], BiInode[Sub1]):

    def __init__(self, key: str, data: AstElem[Sub1], parent: Node[AstElem, Any]) -> None:
        super().__init__(key, data, parent)
        self._sub_l = None

    @property
    def info(self) -> ParseInfo:
        return self._data.parseinfo

    @property
    def rule(self) -> str:
        return self._data.rule

    @property
    def lines(self) -> List[str]:
        return self._data.lines

    @property
    def _sub(self) -> List[Node[AstElem, Any]]:
        if self._sub_l is None:
            self._sub_l = (
                Map(valfilter(is_not_none, self._data.as_dict))
                .to_list
                .map2(L(bi_node)(_, _, self))
                .sort_by(_.pos)
            )
        return self._sub_l

    @property
    def sub(self) -> List[Node[AstElem, Any]]:
        return self._sub

    @property
    def _desc(self) -> str:
        return '{{{}}}'.format(self.key)


class BiTokenNode(BiNode, LeafNode):

    @property
    def _value(self) -> LeafNode:
        return self._data

    @property
    def rule(self) -> str:
        return self.parent.rule

    def __str__(self) -> str:
        return '{}({})'.format(self.__class__.__name__, self._data)


def bi_node(key: str, data: AstElem[Sub1], parent: BiNode) -> BiNode[Sub, Sub1]:
    def err() -> None:
        msg = 'cannot convert ast to tree: {} is not an AstElem'
        raise Exception(msg.format(data))
    return (
        BiMapNode(key, data, parent)
        if isinstance(data, AstMap) else
        BiListNode(key, data, parent)
        if isinstance(data, AstList) else
        BiTokenNode(key, data, parent)
        if isinstance(data, AstToken) else
        err()  # type: ignore
    )


class Tree(Logging):

    def __init__(self, ast: AstMap) -> None:
        self.ast = ast

    @lazy
    def root(self) -> BiNode:
        return bi_node('root', self.ast, self)

    def __str__(self) -> str:
        return 'Tree({})'.format(self.root)

    @property
    def lines(self) -> List[str]:
        return self.root.lines.map(__.rstrip())

    @property
    def flatten(self) -> List:
        return List.wrap(self.root.flatten)


class SubTreeExt(TypeClass):

    @tc_prop
    def raw(self, fa: SubTree) -> Either[str, str]:
        return (
            Right(fa._data.raw)
            if isinstance(fa, SubTreeLeaf) else
            fa._getattr('raw')
        )

    @tc_prop
    def line(self, fa: SubTree) -> Either[str, int]:
        return (
            Right(fa._data.line)
            if isinstance(fa, SubTreeValid) else
            fa
        )


class BiTreeExt(SubTreeExt, tpe=SubTree):
    pass

__all__ = ('Tree',)
