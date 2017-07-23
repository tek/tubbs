from typing import Callable, Any

from hues import huestr

from amino import _


def simple_col(msg: Any, col: Callable[[huestr], huestr]) -> str:
    return col(huestr(str(msg))).colorized


def yellow(msg: Any) -> str:
    return simple_col(msg, _.yellow)


def blue(msg: Any) -> str:
    return simple_col(msg, _.blue)

__all__ = ('yellow', 'blue')
