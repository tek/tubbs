from tubbs.grako.base import BuiltinParser


class Parser(BuiltinParser):

    @property
    def name(self):
        return 'scala'


def parse(text: str, rule: str):
    return Parser().parse(text, rule)

__all__ = ('gen', 'parse')
