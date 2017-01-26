from tubbs.grako.base import BuiltinParser

from amino import Map


class Parser(BuiltinParser):

    @property
    def name(self):
        return 'scala'

    @property
    def parser_args(self):
        return super().parser_args ** Map(comments_re='/\*.*?\*/')


def parse(text: str, rule: str):
    return Parser().parse(text, rule)

__all__ = ('parse',)
