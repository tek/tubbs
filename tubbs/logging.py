import amino.logging
from ribosome.logging import trypnv_logger

from amino.lazy import lazy


log = tubbs_root_logger = trypnv_logger('tubbs')


def tubbs_logger(name: str):
    return tubbs_root_logger.getChild(name)


class Logging(amino.logging.Logging):

    @lazy
    def _log(self) -> amino.logging.Logger:
        return tubbs_logger(self.__class__.__name__)

__all__ = ('tubbs_logger', 'Logging')
