from tubbs.tatsu.base import LangParser

from amino import Map


class Parser(LangParser):

    @property
    def name(self):
        return 'scala'

    @property
    def parser_args(self):
        return super().parser_args ** Map(comments_re='/\*.*?\*/')

    @property
    def left_recursion(self) -> bool:
        return False


def parse(text: str, rule: str):
    return Parser().parse(text, rule)

__all__ = ('parse',)
