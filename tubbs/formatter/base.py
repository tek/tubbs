import abc

from amino import Either, List, Map

from tubbs.logging import Logging
from tubbs.formatter.tree import Tree


class Formatter(Logging, abc.ABC):

    @abc.abstractmethod
    def format(self, tree: Tree) -> Either[str, List[str]]:
        ...

    def __call__(self, tree: Tree) -> Either:
        return self.format(tree)


class VimFormatterMeta(abc.ABCMeta):

    def convert_data(self, data: Map) -> Map:
        return data

__all__ = ('Formatter', 'VimFormatterMeta')
