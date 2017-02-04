from amino import List, _, Either
from amino.test.path import load_fixture

from kallikrein import k, unsafe_k
from kallikrein.matchers import contain, equal
from kallikrein.expectation import Expectation
from kallikrein.matchers.either import be_left, be_right
from kallikrein.matchers.length import have_length

from tubbs.grako.scala import Parser
from tubbs.grako.ast import AstMap

funname = List.random_alpha(5)

tpe3 = 'Tpe3'

funsig = ('{}[A <: B: TCL](par1: Tpe1, par2: Tpe2)(par3: {})' +
          '(implicit par4: Tpe4, par5: Tpe5)').format(funname, tpe3)

typeargs = '[A, Tpe6]'

rettypeid = 'ReturnType'

rettype = '{}{}'.format(rettypeid, typeargs)

acc_mod = 'protected'

fundecl = '{} def {}(a: Int): Ret'.format(acc_mod, funname)

fundef = '''def {}: {} = {{
    val a: Int = 1
    foo("asdf")
}}
'''.format(funsig, rettype)

incomplete_fundef = '''def {}: {} = {{
    val a: Int = 1
'''.format(funsig, rettype)

caseclause = 'case a: Type => 1'

caseclause_wildcard = 'case _ => 3'

caseclauses = '''{}
{}'''.format(caseclause, caseclause_wildcard)

patmat = '''a match {{
{}
}}'''.format(caseclauses)

patmat_assign = 'val b = {}'.format(patmat)

resulttype = '''def foo = {{
{}
new Cls(b)
}}'''.format(patmat_assign)

val_var_def = 'val a = 1'

block = '''{}
val b = 2'''.format(val_var_def)

blockExpr = '''{{
{}
}}'''.format(block)

broken_lines = '''  def fun1[TPar1 <: UB1: TC1]
(
par1: Tpe1
)
(
par2: Tpe2
)
(
implicit par3: Tpe3, par4: Tpe4
) = { val v1 = fun2(par1); fun3(v1) }'''

broken_lines_2 = '''  def fun1[TPar1 <: UB1: TC1]
(par1a: Tpe1, par1b: Tpe1)
(par2a: Tpe2, par2b: Tpe2)
(
implicit par3: Tpe3, par4: Tpe4) = {
val v1 = fun2(par1);
 fun3(v1)
}'''

argument_assign = '''{ def foo: Tpe = foo(a = true) }'''

argument_select = '''{ def foo: Tpe = foo(a.b) }'''

cls_inst_attr = 'new Cls(b).c'

cls_inst_attr_assign = '{{ val a = {} }}'.format(cls_inst_attr)

triple_bool = '''{a && b && c}'''

attr_assign = 'a.b = c'

attr_assign_template = '{{ {} }}'.format(attr_assign)

assign_ext = 'a.b = ((a.b ++ c.d) infix e.f.g.h).i'

complex_eta = '''c.d[A] _'''

chained_apply = 'b.c(d).e(f)'

apply_attr_type_args = '{b.c[C]()}'

case_unapply = '''{
case A(a, _) => b
}'''


class ScalaSpecBase:

    def setup(self) -> None:
        self.parser = Parser()
        self.parser.gen()

    def parse(self, text: str, rule: str) -> Either[str, AstMap]:
        return self.parser.parse(text, rule)

    def ast(self, text: str, rule: str, target: str=None) -> AstMap:
        res = self.parse(text, rule)
        unsafe_k(res).must(be_right)
        ast = res.value
        if target:
            unsafe_k(ast.rule).must(equal(target))
        return res.value

    def expr(self, text: str, target: str) -> AstMap:
        return self.ast(text, 'expr', target)

    def stat(self, text: str, target: str) -> AstMap:
        return self.ast(text, 'templateStat', target)


class ScalaSpec(ScalaSpecBase):
    '''scala ebnf
    keyword $keyword
    plain id should not eat whitespace $plainid_ws
    applyExpr $apply
    applyChain $apply_chain
    apply string literal $apply_string_literal
    function definition $fundef
    incomplete function definition $incomplete_fundef
    function declaration $fundecl
    function signature $funsig
    return type $rettype
    type arguments $typeargs
    simple pattern $pattern
    case clause $caseclause
    case clause with wildcard pattern $caseclause_wildcard
    case clause with guard $caseclause_guard
    multiple case clauses $caseclauses
    pattern matching expression $patmat
    pattern matching expression assigned to val $patmat_assign
    result type $result_type
    val definition $val_var_def
    block statement $block_stat
    block body $block_body
    block expression $block_expr
    infix expression $infix
    whitespace $whitespace
    function def with broken lines at parens $broken
    function def with broken lines at params $broken2
    trait definition $trait
    assignment in arguments $argument_assign
    select $select
    select in a function argument $argument_select
    import statement $import_
    attribute access on a string literal $literal_attr
    function apply on a string literal $literal_apply_args
    function apply on string literal as arg $literal_apply_args_as_arg
    attribute access on a class instantiation $cls_inst_attr
    assignment of class instantiation attribute $cls_inst_attr_assign
    three operand logical expression $triple_bool
    select in a template $select_template
    attribute assignment $attr_assign
    attribute assignment in a template $attr_assign_template
    whitespace is not an operator character $ws_op_char
    plus operator $plus
    symbolic infix operator $pluspluseq
    plus expression with literal operand $plus_literal
    assignment with complex rhs $assign_ext
    complex eta expansion expression $complex_eta
    chained function application $chained_apply
    private final val modifiers $modifiers
    apply on an attribute with type arg $apply_attr_type_args
    misc apply assignments $apply_assign
    unapply in a case pattern $case_unapply
    equals expression $equal
    prefix op in an infix expression $infix_prefix
    attribute apply in an infix expression $infix_attr_apply
    anonymous function without parameters $paramless_anonymous_fun
    '''

    def keyword(self) -> Expectation:
        return k(self.parse('case', 'plainidName')).must(be_left)

    def plainid_ws(self) -> Expectation:
        result = self.parse('case _', 'plainidName')
        return k(result).must(be_left)

    def apply(self) -> Expectation:
        ast = self.expr('f(a)', 'applyExpr')
        return k(ast.head_.args.head.args.head_.raw).must(contain('a'))

    def apply_chain(self) -> Expectation:
        ast = self.expr('f.g(a)', 'applyExpr')
        return (k(ast.head_.pre.rule).must(equal('attrExpr')) &
                k(ast.head_.args.head.args.head_.raw).must(contain('a')))

    def apply_string_literal(self) -> Expectation:
        word = List.random_alpha()
        ast = self.expr('foo("{}")'.format(word), 'applyExpr')
        return k(ast.head_.args.head.args.head_.data.raw).must(contain(word))

    def fundef(self) -> Expectation:
        ast = self.stat(fundef, 'templateStatDef')
        sig = ast.def_.def_.sig
        explicit = sig.paramss.explicit
        id = explicit.last.params.head.tpe.id
        return (
            k(sig.id.raw).must(contain(funname)) &
            k(explicit.e / _.rule).must(contain('paramClauses')) &
            k(id.raw).must(contain(tpe3)) &
            k(id.e / _.rule).must(contain('plainid'))
        )

    def incomplete_fundef(self) -> Expectation:
        ast = self.ast(incomplete_fundef, 'templateStat')
        return k(ast.dcl.dcl.sig.id.raw).must(contain(funname))

    def fundecl(self) -> Expectation:
        ast = self.ast(fundecl, 'templateStat')
        return (
            k(self.parse(fundecl, 'funDef')).must(be_left) &
            k(ast.mod.raw).must(contain(acc_mod)) &
            k(ast.dcl.dcl.sig.id.raw).must(contain(funname))
        )

    def funsig(self) -> Expectation:
        ast = self.ast(funsig, 'funSig')
        return k(ast.id.raw).must(contain(funname))

    def rettype(self) -> Expectation:
        ast = self.ast(rettype, 'type')
        return k(ast.simple.id.raw).must(contain(rettypeid))

    def typeargs(self) -> Expectation:
        ast = self.ast(typeargs, 'typeArgs')
        return k(ast.types.head.id.raw).must(contain('A'))
        return k(ast.types.last.last.id).must(contain('Tpe6'))

    def pattern(self) -> Expectation:
        ast = self.ast('a: Type', 'pattern')
        return k(ast.head_.last.last.raw).must(contain('Type'))

    def caseclause(self) -> Expectation:
        ast = self.ast(caseclause, 'caseClause')
        return k(ast.rhs.raw).must(contain('1'))

    def caseclause_wildcard(self) -> Expectation:
        ast = self.ast(caseclause_wildcard, 'caseClause')
        return k(ast.rhs.raw).must(contain('3'))

    def caseclause_guard(self) -> Expectation:
        ast = self.ast('case c if b => a', 'caseClause')
        return k(ast.guard.expr.raw).must(contain('b'))

    def caseclauses(self) -> Expectation:
        ast = self.ast(caseclauses, 'caseClauses')
        return (
            k(ast.head_.rhs.head_.raw).must(contain('1')) &
            k(ast.tail.head.case.rhs.raw).must(contain('3'))
        )

    def patmat(self) -> Expectation:
        ast = self.ast(patmat, 'patMat')
        return (
            k(ast.cases.tail.head.case.pat.head_.raw).must(contain('_')) &
            k(ast.cases.tail.head.case.rhs.head_.raw).must(contain('3'))
        )

    def patmat_assign(self) -> Expectation:
        ast = self.ast(patmat_assign, 'patVarDef')
        cases = ast.def_.rhs.cases
        case1 = cases.head_
        case2 = cases.tail.head.case
        return (
            k(case1.pat.head_.last.last.raw).must(contain('Type')) &
            k(case2.rhs.head_.raw).must(be_right(contain('3')))
        )

    def result_type(self) -> Expectation:
        ast = self.ast(resulttype, 'def')
        return (k(ast.def_.rhs.body.tail.head.stat.templ.head.head.id.raw)
                .must(contain('Cls')))

    def val_var_def(self) -> Expectation:
        ast = self.ast(val_var_def, 'valVarDef')
        return k(ast.def_.rhs.raw).must(contain('1'))

    def block_stat(self) -> Expectation:
        ast = self.ast(val_var_def, 'blockStat')
        return k(ast[1].def_.rhs.raw).must(contain('1'))

    def block_body(self) -> Expectation:
        ast = self.ast(block, 'blockBody')
        return k(ast.head_[1].def_.rhs.raw).must(contain('1'))

    def block_expr(self) -> Expectation:
        ast = self.ast(blockExpr, 'block')
        return k(ast.body.head_[1].def_.rhs.raw).must(contain('1'))

    def infix(self) -> Expectation:
        ast = self.ast('foo boo\n zoo', 'infixExpr')
        return k(ast.right.raw).must(contain('zoo'))

    def whitespace(self) -> Expectation:
        i = 3
        ast = self.ast('{}def foo = 1'.format(' ' * i), 'def')
        return k(ast.defkw._data.ws_count).must(equal(i))

    def broken(self) -> Expectation:
        ast = self.ast(broken_lines, 'def')
        return (k(ast.def_.rhs.body.head_[1].def_.rhs.head_.pre.raw)
                .must(contain('fun2')))

    def broken2(self) -> Expectation:
        ast = self.ast(broken_lines_2, 'def')
        return (k(ast.def_.rhs.body.head_[1].def_.rhs.head_.pre.raw)
                .must(contain('fun2')))

    def trait(self) -> Expectation:
        ast = self.ast('trait Foo {\n}', 'trait')
        return k(ast.data).must(have_length(2))

    def argument_assign(self) -> Expectation:
        ast = self.ast(argument_assign, 'templateBody')
        rhs = ast.stats.head_.body.head_[1].def_.rhs
        return k(rhs.head_.args.head.args.head_.rhs.raw).must(contain('true'))

    def select(self) -> Expectation:
        ast = self.ast('a.b.c', 'path')
        return k(ast.tail.last.id.raw).must(contain('c'))

    def argument_select(self) -> Expectation:
        ast = self.ast(argument_select, 'templateBody')
        rhs = ast.stats.head_.body.head_[1].def_.rhs
        return (k(rhs.head_.args.head.args.head_.tail.head.id.raw)
                .must(contain('b')))

    def import_(self) -> Expectation:
        ast = self.ast('one.two.three', 'importExpr')
        return k(ast.last.raw).must(contain('three'))

    def literal_attr(self) -> Expectation:
        ast = self.ast('"i".a', 'simpleOrCompoundExpr')
        return k(ast.tail.last.id.raw).must(contain('a'))

    def literal_apply_args(self) -> Expectation:
        ast = self.ast('"i".a(1)', 'simpleOrCompoundExpr')
        return k(ast.head_.args.head.args.head_.raw).must(contain('1'))

    def literal_apply_args_as_arg(self) -> Expectation:
        ast = self.ast('f("i".a(1))', 'applyExpr')
        args = ast.head_.args.head.args.head_.head_.args.head.args
        return k(args.head_.raw).must(contain('1'))

    def cls_inst_attr(self) -> Expectation:
        ast = self.ast(cls_inst_attr, 'expr')
        return k(ast.tail.head.id.raw).must(contain('c'))

    def cls_inst_attr_assign(self) -> Expectation:
        ast = self.ast(cls_inst_attr_assign, 'templateBody')
        rhs = ast.stats.head_.body.head_[1].def_.rhs
        return (
            k(rhs.head_.templ.head.head.id.raw).must(contain('Cls')) &
            k(rhs.tail.head.id.raw).must(contain('c'))
        )

    def triple_bool(self) -> Expectation:
        ast = self.ast(triple_bool, 'templateBody')
        return k(ast.stats.head_.body.head_.right.right.raw).must(contain('c'))

    def select_template(self) -> Expectation:
        ast = self.ast('{a.b.c}', 'template')
        expr = ast.stats.stats.head_
        return (
            k(expr.rule).must(equal('attrExpr')) &
            k(expr.tail.last.id.raw).must(contain('c'))
        )

    def attr_assign(self) -> Expectation:
        ast = self.expr(attr_assign, 'attrAssignExpr')
        return k(ast.rhs.raw).must(contain('c'))

    def attr_assign_template(self) -> Expectation:
        ast = self.ast(attr_assign_template, 'template')
        return k(ast.stats.stats.head_.rule).must(equal('attrAssignExpr'))

    def ws_op_char(self) -> Expectation:
        return k(self.parse(' ', 'OpChar')).must(be_left)

    def plus(self) -> Expectation:
        ast = self.ast('+', 'op')
        return k(ast.raw).must(equal('+'))

    def pluspluseq(self) -> Expectation:
        op = '++='
        ast = self.ast('a{} b'.format(op), 'infixExpr')
        return (
            k(ast.method.raw).must(contain(op)) &
            k(ast.right.raw).must(contain('b'))
        )

    def plus_literal(self) -> Expectation:
        ast = self.ast('a + "b"', 'infixExpr')
        return k(ast.right.rule).must(contain('singleLineStringLiteral'))

    def assign_ext(self) -> Expectation:
        ast = self.ast(assign_ext, 'attrAssignExpr')
        return (k(ast.rhs.head_.exprs.head_.left.exprs.head_.method.raw)
                .must(contain('++')))

    def complex_eta(self) -> Expectation:
        ast = self.ast(complex_eta, 'expr')
        return (
            k(ast.rule).must(equal('etaExpansion')) &
            k(ast.expr.typeargs.types.head.id.raw).must(contain('A'))
        )

    def chained_apply(self) -> Expectation:
        ast = self.ast(chained_apply, 'expr')
        return (k(ast.tail.head.args.head.args.head_.raw)
                .must(contain('f')))

    def modifiers(self) -> Expectation:
        ast = self.ast('{private final val a = 1}', 'template')
        return k(ast.stats.stats.head_.mod.last.raw).must(contain('final'))

    def apply_attr_type_args(self) -> Expectation:
        ast = self.ast(apply_attr_type_args, 'template')
        return (
            k(ast.stats.stats.head_.head_.pre.rule)
            .must(equal('attrExprTypeArgs')) &
            (k(ast.stats.stats.head_.head_.pre.typeargs.types.head.id.raw))
            .must(contain('C'))
        )

    def apply_assign(self) -> Expectation:
        def go(c: str, target: str=None) -> Expectation:
            a = self.ast(c, 'applyAssignExpr')
            return k(a.rhs.raw).must(contain('d'))
        ast = self.ast('super[A].a.b(c) = d', 'applyAssignExpr')
        return (
            go('a((b, c)) = d') &
            go('a.b(c) = d') &
            go('(a.b ++ a.b)(c) = d') &
            k(ast.rhs.raw).must(contain('d')) &
            k(ast.expr.head_.rule).must(equal('superAttr'))
        )

    def case_unapply(self) -> Expectation:
        ast = self.ast(case_unapply, 'block')
        return (k(ast.body.head_.pat.head_.pats.tail.pats.head_.head_.raw)
                .must(contain('_')))

    def equal(self) -> Expectation:
        ast = self.ast('a == b', 'infixExpr')
        return k(ast.method.raw).must(contain('=='))

    def infix_prefix(self) -> Expectation:
        ast = self.ast('!a && b', 'infixExpr')
        return (
            k(ast.left.rule).must(equal('prefixExpr')) &
            k(ast.right.raw).must(contain('b'))
        )

    def infix_attr_apply(self) -> Expectation:
        ast = self.ast('a.b(c) d e', 'infixExpr')
        return k(ast.right.raw).must(contain('e'))

    def paramless_anonymous_fun(self) -> Expectation:
        ast = self.ast('{() => 1}', 'block')
        return k(ast.body.head_.rhs.raw).must(contain('1'))

temp = '''\
a.b(c) d e
'''


class ScalaFileSpec(ScalaSpecBase):
    '''experiments
    whole file $file
    temp $temp
    temp in block $temp_block
    temp2 $temp2
    '''

    __unsafe__ = None

    def file(self) -> Expectation:
        content = load_fixture('parser', 'scala', 'file2.scala')
        ast = self.ast(content, 'template')
        print(ast)

    def temp(self) -> Expectation:
        ast = self.ast(temp, 'templateStat')
        print(ast)

    def temp_block(self) -> Expectation:
        ast = self.ast('{{\n{}\n}}'.format(temp), 'template')
        print(ast)

    def temp2(self) -> Expectation:
        ast = self.ast('ptarg weak_<:< tparg', 'infixExpr')
        print(ast)

__all__ = ('ScalaSpec',)
