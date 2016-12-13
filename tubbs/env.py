from ribosome.data import Data
from ribosome.record import dfield

from amino import __

from tubbs.logging import Logging
from tubbs.grako.base import Parsers


class Env(Data, Logging):
    initialized = dfield(False)
    parsers = dfield(Parsers())

    def load_parser(self, name):
        return self.parsers.load(name) / self.setter.parsers

    def parser(self, name):
        return self.parsers.parser(name)

__all__ = ('Env',)
