import abc
from typing import Tuple, Callable

from amino import List, L, _, __, Boolean
from amino.lazy import lazy
from amino.list import flatten
from amino.func import is_not_none

from tubbs.logging import Logging
from tubbs.grako.ast import AstList, AstElem, AstToken, AstMap


def indent(strings):
    return strings.map('-' + _)


def flatten_list(data):
    def flat(data):
        l = data.data if isinstance(data, AstList) else data
        return (
            flatten(map(flat, l))
            if isinstance(l, list) else
            [l]
        )
    return List.wrap(flat(data))


class Node(Logging, abc.ABC):

    def __init__(self, key: str, data: AstElem, parent: 'Node') -> None:
        self.key = key
        self.data = data
        self.parent = parent

    @abc.abstractproperty
    def sub(self) -> List['Node']:
        ...

    @abc.abstractproperty
    def strings(self) -> List[str]:
        ...

    @abc.abstractproperty
    def rule(self) -> str:
        ...

    @property
    def range(self) -> Tuple[int, int]:
        return self.data.range

    @property
    def pos(self):
        return self.data.pos

    @property
    def endpos(self):
        return self.data.endpos

    @abc.abstractproperty
    def pos_with_ws(self) -> int:
        ...

    @property
    def show(self):
        return self.strings.mk_string('\n')

    def __str__(self):
        return '{}({}, {}, {} children)'.format(
            self.__class__.__name__, self.rule, self.key, len(self.sub))

    @abc.abstractmethod
    def foreach(self, f: Callable[['Node'], None]):
        ...

    @abc.abstractproperty
    def text(self) -> str:
        ...

    @abc.abstractproperty
    def with_ws(self) -> str:
        ...

    @abc.abstractmethod
    def filter(self, pred: Callable[['Node'], bool]) -> 'List[Node]':
        ...

    def _filter(self, pred):
        return Boolean(pred(self)).maybe(self).to_list

    @abc.abstractproperty
    def indent(self) -> int:
        ...

    @abc.abstractproperty
    def flatten(self) -> 'List[Node]':
        ...


class Inode(Node):

    def foreach(self, f):
        f(self)
        self.sub.foreach(__.foreach(f))

    @abc.abstractproperty
    def sub(self) -> List[Node]:
        ...

    @abc.abstractmethod
    def sub_range(self, name) -> Tuple[int, int]:
        ...

    @property
    def with_ws(self):
        return self.text

    def filter(self, pred):
        return self._filter(pred) + self.sub.flat_map(__.filter(pred))

    @property
    def indent(self):
        return self.sub.head / _.indent | 0

    @property
    def pos_with_ws(self):
        return self.sub.head / _.pos_with_ws | self.pos

    @property
    def flatten(self):
        yield self
        for a in self.sub:
            yield from a.flatten


class MapNode(Inode):

    @property
    def info(self):
        return self.data.parseinfo

    @property
    def rule(self):
        return self.data.rule

    @lazy
    def text(self):
        return self.info.buffer.text[self.pos:self.endpos]

    @lazy
    def with_ws(self):
        return self.info.buffer.text[self.pos_with_ws:self.endpos]

    @property
    def lines(self):
        return List.lines(self.with_ws)

    @lazy
    def sub(self):
        return (
            self.data
            .valfilter(is_not_none)
            .to_list
            .map2(L(node)(_, _, self))
            .sort_by(_.pos)
        )

    @property
    def _desc(self):
        return '{{{}}}'.format(self.key)

    @property
    def strings(self):
        return indent(self.sub // _.strings).cons(self._desc)

    def sub_range(self, name):
        return self.data.lift(name).e / _.range | (0, 0)


class ListNode(Inode):

    @lazy
    def sub(self):
        sub = flatten_list(self.data)
        return List.wrap(sub) / L(node)(self.key, _, self)

    @property
    def _desc(self):
        return '[{}]'.format(self.key)

    @property
    def strings(self):
        return indent(self.sub // _.strings).cons(self._desc)

    @property
    def rule(self):
        return self.parent.rule

    @property
    def text(self):
        return (self.sub / _.with_ws).mk_string()

    def sub_range(self, name):
        raise Exception('not implemented')


class TokenNode(Node):

    @lazy
    def sub(self):
        return List()

    @property
    def text(self):
        return self.data.raw

    @property
    def _desc(self):
        return self.text

    @property
    def strings(self):
        return List(self._desc)

    @property
    def rule(self):
        return self.parent.rule

    def sub_range(self, name):
        return (self.data.range
                if isinstance(self.data, AstToken) else
                self.parent.sub_range(self.key))

    @property
    def range(self):
        return self.data.pos, self.data.pos + len(self.text)

    def foreach(self, f):
        f(self)

    def __str__(self):
        return '{}({})'.format(self.__class__.__name__, self.data)

    @property
    def with_ws(self):
        return '{}{}'.format(self.data.whitespace, self.text)

    def filter(self, pred):
        return self._filter(pred)

    @property
    def indent(self):
        return len(self.data.whitespace)

    @property
    def pos_with_ws(self):
        return self.pos - self.indent

    @property
    def flatten(self):
        yield self


def node(key: str, data: AstElem, parent: Node):
    def err():
        msg = 'cannot convert ast to tree: {} is not an AstElem'
        raise Exception(msg.format(data))
    return (
        MapNode(key, data, parent)
        if isinstance(data, AstMap) else
        ListNode(key, data, parent)
        if isinstance(data, AstList) else
        TokenNode(key, data, parent)
        if isinstance(data, AstToken) else
        err()
    )


class Tree(Logging):

    def __init__(self, ast: AstMap) -> None:
        self.ast = ast

    @lazy
    def root(self):
        return node('root', self.ast, self)

    def __str__(self):
        return 'Tree({})'.format(self.root)

    @property
    def lines(self):
        return self.root.lines

    @property
    def flatten(self):
        return List.wrap(self.root.flatten)

    def line_nodes(self, eols):
        def index(node):
            return (eols.find(_ > node.pos) | 0) - 1
        return (
            self.flatten
            .group_by(index)
            .filter(lambda a: a[0] >= 0)
            .map2(lambda a, b: (a, b.filter(lambda a: a.pos >= 0)))
            .sort_by(_[0]) /
            _[1]
        )

__all__ = ('Tree',)
