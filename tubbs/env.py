from tubbs.logging import Logging
from ribosome.data import Data
from trypnv.record import dfield


class Env(Data, Logging):
    initialized = dfield(False)
    parsers = map_file
