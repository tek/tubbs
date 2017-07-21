from ribosome.data import Data
from ribosome.record import dfield

from amino import Either

from tubbs.logging import Logging
from tubbs.tatsu.base import Parsers, ParserBase


class Env(Data, Logging):
    initialized = dfield(False)
    parsers = dfield(Parsers())

    def load_parser(self, name: str) -> Either[str, 'Env']:
        return self.parsers.load(name) / self.setter.parsers

    def parser(self, name: str) -> Either[str, ParserBase]:
        return self.parsers.parser(name)

__all__ = ('Env',)
