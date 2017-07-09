from amino.tree import SubTree, SubTreeLeaf, SubTreeValid
from amino import Boolean

from kallikrein.matcher import Predicate, matcher, NestingUnavailable

from tubbs.tatsu.ast import AstElem, AstToken


class BeToken:
    pass


class PredBeToken(Predicate):
    pass


class PredBeTokenSubTree(PredBeToken, tpe=SubTree):

    def check(self, exp: SubTree, target: str) -> Boolean:
        return Boolean(isinstance(exp, SubTreeLeaf) and exp.data.raw == target)


class PredBeTokenAstElem(PredBeToken, tpe=AstElem):

    def check(self, exp: AstElem, target: str) -> Boolean:
        return Boolean(isinstance(exp, AstToken) and exp.raw == target)


success = '`{}` is token `{}`'
failure = '`{}` is not token `{}`'
be_token = matcher(BeToken, success, failure, PredBeToken, NestingUnavailable)


class HaveRule:
    pass


class PredHaveRule(Predicate):
    pass


class PredHaveRuleSubTree(PredHaveRule, tpe=SubTree):

    def check(self, exp: SubTree, target: str) -> Boolean:
        return Boolean(isinstance(exp, SubTreeValid) and exp.data.rule == target)


class PredHaveRuleAstElem(PredHaveRule, tpe=AstElem):

    def check(self, exp: AstElem, target: str) -> Boolean:
        return Boolean(exp.rule == target)


success = '`{}` has rule `{}`'
failure = '`{}` does not have rule `{}`'
have_rule = matcher(HaveRule, success, failure, PredHaveRule, NestingUnavailable)

__all__ = ('be_token', 'have_rule')
