import abc
from typing import TypeVar, Callable, Generic, GenericMeta

from amino import List, Map, Eval, Maybe, curried, Either
from amino.list import Lists
from amino.util.string import snake_case

from tubbs.logging import Logging
from tubbs.tatsu.ast import AstElem, RoseData


A = TypeVar('A')


class Formatter(Generic[A], Logging):

    @abc.abstractmethod
    def format(self, ast: AstElem) -> Eval[Either[str, List[str]]]:
        ...

    def __call__(self, ast: AstElem) -> Eval[Either[str, List[str]]]:
        return self.format(ast)

    @abc.abstractmethod
    def handler(self, name: str) -> Maybe[Callable[[], A]]:
        ...

    def lookup_handler(self, node: RoseData) -> Callable[[], A]:
        parent_rule = snake_case(node.parent_rule)
        key_handler = f'{parent_rule}_{node.key}'
        names = Lists.iff(node.ast.is_rule_node)(snake_case(node.rule)).cons(key_handler)
        return self._handler_names(node, names).find_map(self._try_handler(node)) | (lambda: self.default_handler)

    @curried
    def _try_handler(self, node: RoseData, name: str) -> Maybe[Callable[[], A]]:
        self.log.ddebug(f'trying ident handler {name}')
        return self.handler(name).foreach(lambda a: self.log.ddebug('success'))

    @abc.abstractmethod
    def _handler_names(self, node: RoseData, names: List[str]) -> List[str]:
        ...


class VimFormatterMeta(GenericMeta):

    def convert_data(self, data: Map) -> Map:
        return data

__all__ = ('Formatter', 'VimFormatterMeta')
