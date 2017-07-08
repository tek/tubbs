import abc

from amino import List, Map, Task

from tubbs.logging import Logging
from tubbs.tatsu.ast import AstElem


class Formatter(Logging, abc.ABC):

    @abc.abstractmethod
    def format(self, ast: AstElem) -> Task[List[str]]:
        ...

    def __call__(self, ast: AstElem) -> Task[List[str]]:
        return self.format(ast)


class VimFormatterMeta(abc.ABCMeta):

    def convert_data(self, data: Map) -> Map:
        return data

__all__ = ('Formatter', 'VimFormatterMeta')
