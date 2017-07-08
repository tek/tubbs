from amino import List, Either, _
from amino.test.path import load_fixture

from kallikrein import k, unsafe_k, pending
from kallikrein.expectation import Expectation
from kallikrein.matchers.either import be_left, be_right
from kallikrein.matchers.length import have_length

from tubbs.tatsu.scala import Parser
from tubbs.tatsu.ast import AstMap
from tubbs.logging import Logging

from unit._support.ast import be_token, have_rule

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

multiline_expr = '''b
  .map(fun)
  .map(fun2)
'''

multiline_val = '''val a =
  b
    .map(fun)
'''

caseclause_arg = '''val a = b
.map(fun)
.collect { case c => d }'''

boundary_apply_chain = '''val a =
  b
    .map(f1)
    .map(f2)
'''


class ScalaSpecBase(Logging):

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
            unsafe_k(ast.rule) == target
        return res.value

    def expr(self, text: str, target: str) -> AstMap:
        return self.ast(text, 'expr', target)

    def stat(self, text: str, target: str) -> AstMap:
        return self.ast(text, 'templateStat', target)

    def tpe(self, text: str, target: str) -> AstMap:
        return self.ast(text, 'type', target)

    def def_(self, text: str, target: str) -> AstMap:
        return self.ast(text, 'def', target)


class ScalaSpec(ScalaSpecBase):
    '''scala ebnf
    keyword $keyword
    special char id $special_char_id
    plain id should not eat whitespace $plainid_ws
    function application $apply
    chained function application $apply_chain
    function application with type args $apply_typeargs
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
    method with type args $id_type_args
    private final val modifiers $modifiers
    apply on an attribute with type arg $apply_attr_type_args
    misc apply assignments $apply_assign
    unapply in a case pattern $case_unapply
    equals expression $equal
    prefix op in an infix expression $infix_prefix
    attribute apply in an infix expression $infix_attr_apply
    anonymous function without parameters $paramless_anonymous_fun
    parenthesized infix with nl before op and eolcomment $paren_infix
    type attribute with type args $type_attr_args
    infix with class instantiation as left operand $infix_inst_oper
    def with variadic params $splat_param
    string context $string_context
    case clause start without newline $single_line_cases
    def with just implicit params $only_implicit_params
    type lambda $type_lambda
    symbolic infix type $symbolic_infix_type
    token position $token_position
    infix type operator position $infix_position
    position inside case clause $case_clause_position
    multiline expression with newline before method call $multiline_expr
    multiline valdef with newline before method call $multiline_val
    case clauses as argument to a method call $caseclause_arg
    boundary node status for apply chains $apply_chain_boundary
    '''

    def keyword(self) -> Expectation:
        return k(self.parse('case', 'plainidName')).must(be_left)

    def special_char_id(self) -> Expectation:
        lam = self.ast('λ', 'id')
        arr = self.ast('→', 'op')
        return (k(lam).must(be_token('λ'))) & (k(arr).must(be_token('→')))

    def plainid_ws(self) -> Expectation:
        result = self.parse('case _', 'plainidName')
        return k(result).must(be_left)

    def apply(self) -> Expectation:
        ast = self.expr('f(a)', 'applyExpr')
        return k(ast.s.app.head.argss.head.args.head).must(be_token('a'))

    def apply_chain(self) -> Expectation:
        ast = self.expr('f.g(a)', 'applyExpr')
        return k(ast.s.app.head.argss.head.args.head).must(be_token('a'))

    def apply_typeargs(self) -> Expectation:
        ast = self.expr('f.g.h[A, B](a)', 'applyExpr')
        return k(ast.s.app.head.meths.last.meth.targs.types.tail.head.tpe).must(be_token('B'))

    def apply_string_literal(self) -> Expectation:
        word = List.random_alpha()
        ast = self.expr('foo("{}")'.format(word), 'applyExpr')
        return k(ast.s.app.head.argss.head.args.head['data']).must(be_token(word))

    def fundef(self) -> Expectation:
        ast = self.stat(fundef, 'templateStatDef')
        sig = ast.s.def_.def_.sig
        explicit = sig.paramss.explicit
        id = explicit.last.params.last.tpe
        return (
            k(sig.id).must(be_token(funname)) &
            k(explicit).must(have_rule('paramClauses')) &
            k(id).must(be_token(tpe3)) &
            k(id).must(have_rule('plainid'))
        )

    def incomplete_fundef(self) -> Expectation:
        ast = self.ast(incomplete_fundef, 'templateStat')
        return k(ast.s.dcl.dcl.sig.id).must(be_token(funname))

    def fundecl(self) -> Expectation:
        ast = self.ast(fundecl, 'templateStat')
        return (
            k(self.parse(fundecl, 'funDef')).must(be_left) &
            k(ast.s.mod).must(be_token(acc_mod)) &
            k(ast.s.dcl.dcl.sig.id).must(be_token(funname))
        )

    def funsig(self) -> Expectation:
        ast = self.ast(funsig, 'funSig')
        return k(ast.s.id).must(be_token(funname))

    def rettype(self) -> Expectation:
        ast = self.ast(rettype, 'type')
        return k(ast.s.simple).must(be_token(rettypeid))

    def typeargs(self) -> Expectation:
        ast = self.ast(typeargs, 'typeArgs')
        return k(ast.s.types.head).must(be_token('A'))
        return k(ast.s.types.last.last.id).must(be_token('Tpe6'))

    def pattern(self) -> Expectation:
        ast = self.ast('a: Type', 'pattern')
        return k(ast.s.head.last.last).must(be_token('Type'))

    def caseclause(self) -> Expectation:
        ast = self.ast(caseclause, 'caseClause')
        return k(ast.s.rhs).must(be_token('1'))

    def caseclause_wildcard(self) -> Expectation:
        ast = self.ast(caseclause_wildcard, 'caseClause')
        return k(ast.s.rhs).must(be_token('3'))

    def caseclause_guard(self) -> Expectation:
        ast = self.ast('case c if b => a', 'caseClause')
        return k(ast.s.guard.expr).must(be_token('b'))

    def caseclauses(self) -> Expectation:
        ast = self.ast(caseclauses, 'caseClauses')
        return (
            k(ast.s.head.rhs.head).must(be_token('1')) &
            k(ast.s.tail.head.case.rhs).must(be_token('3'))
        )

    def patmat(self) -> Expectation:
        ast = self.ast(patmat, 'patMat')
        return (
            k(ast.s.cases.tail.head.case.pat.head).must(be_token('_')) &
            k(ast.s.cases.tail.head.case.rhs.head).must(be_token('3'))
        )

    def patmat_assign(self) -> Expectation:
        ast = self.ast(patmat_assign, 'patVarDef')
        cases = ast.s.def_.rhs.cases
        case1 = cases.head
        case2 = cases.tail.head.case
        return (
            k(case1.pat.head.last.last).must(be_token('Type')) &
            k(case2.rhs.head).must(be_token('3'))
        )

    def result_type(self) -> Expectation:
        ast = self.ast(resulttype, 'def')
        return (k(ast.s.def_.rhs.body.tail.head.stat.templ.head.head)
                .must(be_token('Cls')))

    def val_var_def(self) -> Expectation:
        ast = self.stat(val_var_def, 'templateStatDef')
        return k(ast.s.def_.def_.rhs).must(be_token('1'))

    def block_body(self) -> Expectation:
        ast = self.ast(block, 'blockBody')
        return k(ast.s.head.def_.def_.rhs).must(be_token('1'))

    def block_expr(self) -> Expectation:
        ast = self.ast(blockExpr, 'block')
        return k(ast.s.body.head.def_.def_.rhs).must(be_token('1'))

    def infix(self) -> Expectation:
        ast = self.ast('foo boo\n zoo', 'infixExpr')
        return k(ast.s.right).must(be_token('zoo'))

    def whitespace(self) -> Expectation:
        i = 3
        ast = self.ast('{}def foo = 1'.format(' ' * i), 'def')
        return k(ast.s.defkw.data.ws_count) == i

    def broken(self) -> Expectation:
        ast = self.ast(broken_lines, 'def')
        return k(ast.s.def_.rhs.body.head.def_.def_.rhs.pre).must(be_token('fun2'))

    def broken2(self) -> Expectation:
        ast = self.ast(broken_lines_2, 'def')
        return k(ast.s.def_.rhs.body.head.def_.def_.rhs.pre).must(be_token('fun2'))

    def trait(self) -> Expectation:
        ast = self.ast('trait Foo {\n}', 'trait')
        return k(ast.data).must(have_length(2))

    def argument_assign(self) -> Expectation:
        ast = self.ast(argument_assign, 'templateBody')
        rhs = ast.s.stats.head.body.head.def_.def_.rhs
        return k(rhs.app.head.argss.head.args.head.rhs).must(be_token('true'))

    def select(self) -> Expectation:
        ast = self.ast('a.b.c', 'path')
        return k(ast.s.tail.last.id).must(be_token('c'))

    def argument_select(self) -> Expectation:
        ast = self.ast(argument_select, 'templateBody')
        rhs = ast.s.stats.head.body.head.def_.def_.rhs
        return k(rhs.app.head.argss.head.args.head.tail.head.id).must(be_token('b'))

    def import_(self) -> Expectation:
        ast = self.ast('one.two.three', 'importExpr')
        return k(ast.s.last).must(be_token('three'))

    def literal_attr(self) -> Expectation:
        ast = self.ast('"i".a', 'simpleOrCompoundExpr')
        return k(ast.s.tail.last.id).must(be_token('a'))

    def literal_apply_args(self) -> Expectation:
        ast = self.ast('"i".a(1)', 'simpleOrCompoundExpr')
        return k(ast.s.app.head.argss.head.args.head).must(be_token('1'))

    def literal_apply_args_as_arg(self) -> Expectation:
        ast = self.ast('f("i".a(1))', 'applyExpr')
        args = ast.s.app.head.argss.head.args.head.app.head.argss.head.args
        return k(args.head).must(be_token('1'))

    def cls_inst_attr(self) -> Expectation:
        ast = self.ast(cls_inst_attr, 'expr')
        return k(ast.s.tail.head.id).must(be_token('c'))

    def cls_inst_attr_assign(self) -> Expectation:
        ast = self.ast(cls_inst_attr_assign, 'templateBody')
        rhs = ast.s.stats.head.body.head.def_.def_.rhs
        return (
            k(rhs.head.templ.head.head).must(be_token('Cls')) &
            k(rhs.tail.head.id).must(be_token('c'))
        )

    def triple_bool(self) -> Expectation:
        ast = self.ast(triple_bool, 'templateBody')
        return k(ast.s.stats.head.body.head.right.right).must(be_token('c'))

    def select_template(self) -> Expectation:
        ast = self.ast('{a.b.c}', 'template')
        expr = ast.s.stats.stats.head
        return (
            k(expr).must(have_rule('attrExpr')) &
            k(expr.tail.last.id).must(be_token('c'))
        )

    def attr_assign(self) -> Expectation:
        ast = self.expr(attr_assign, 'attrAssignExpr')
        return k(ast.s.rhs).must(be_token('c'))

    def attr_assign_template(self) -> Expectation:
        ast = self.ast(attr_assign_template, 'template')
        return k(ast.s.stats.stats.head).must(have_rule('attrAssignExpr'))

    def ws_op_char(self) -> Expectation:
        return k(self.parse(' ', 'OpChar')).must(be_left)

    def plus(self) -> Expectation:
        ast = self.ast('+', 'op')
        return k(ast).must(be_token('+'))

    def pluspluseq(self) -> Expectation:
        op = '++='
        ast = self.ast('a{} b'.format(op), 'infixExpr')
        return (
            k(ast.s.method).must(be_token(op)) &
            k(ast.s.right).must(be_token('b'))
        )

    def plus_literal(self) -> Expectation:
        ast = self.ast('a + "b"', 'infixExpr')
        return k(ast.s.right).must(have_rule('singleLineStringLiteral'))

    def assign_ext(self) -> Expectation:
        ast = self.ast(assign_ext, 'attrAssignExpr')
        return k(ast.s.rhs.head.exprs.head.left.exprs.head.method).must(be_token('++'))

    def complex_eta(self) -> Expectation:
        ast = self.expr(complex_eta, 'etaExpansion')
        return k(ast.s.expr.targs.types.head).must(be_token('A'))

    def chained_apply(self) -> Expectation:
        ast = self.ast(chained_apply, 'expr')
        return k(ast.s.app.last.argss.head.args.head).must(be_token('f'))

    def modifiers(self) -> Expectation:
        ast = self.ast('{private final val a = 1}', 'template')
        return k(ast.s.stats.stats.head.mod.last).must(be_token('final'))

    def id_type_args(self) -> Expectation:
        ast = self.ast('name[A, B]', 'idTypeArgs')
        return k(ast.s.targs.types.tail.head.tpe).must(be_token('B'))

    def apply_attr_type_args(self) -> Expectation:
        ast = self.ast(apply_attr_type_args, 'template')
        return (
            k(ast.s.stats.stats.head).must(have_rule('applyExpr')) &
            k(ast.s.stats.stats.head.app.head.meths.head.meth.targs.types.head).must(be_token('C'))
        )

    def apply_assign(self) -> Expectation:
        def go(c: str, target: str=None) -> Expectation:
            a = self.ast(c, 'applyAssignExpr')
            return k(a.s.rhs).must(be_token('d'))
        ast = self.ast('super[A].a.b(c) = d', 'applyAssignExpr')
        return (
            go('a((b, c)) = d') &
            go('a.b(c) = d') &
            go('(a.b ++ a.b)(c) = d') &
            k(ast.s.rhs).must(be_token('d')) &
            k(ast.s.expr.head).must(have_rule('superAttr'))
        )

    def case_unapply(self) -> Expectation:
        ast = self.ast(case_unapply, 'block')
        return k(ast.s.body.head.pat.head.pats.tail.pats.head.head).must(be_token('_'))

    def equal(self) -> Expectation:
        ast = self.ast('a == b', 'infixExpr')
        return k(ast.s.method).must(be_token('=='))

    def infix_prefix(self) -> Expectation:
        ast = self.ast('!a && b', 'infixExpr')
        return (
            k(ast.s.left).must(have_rule('prefixExpr')) &
            k(ast.s.right).must(be_token('b'))
        )

    def infix_attr_apply(self) -> Expectation:
        ast = self.ast('a.b(c) d e', 'infixExpr')
        return k(ast.s.right).must(be_token('e'))

    def paramless_anonymous_fun(self) -> Expectation:
        ast = self.ast('{() => 1}', 'block')
        return k(ast.s.body.head.rhs.head).must(be_token('1'))

    def paren_infix(self) -> Expectation:
        ast = self.expr('(a\n|| b // comm\n|| c)', 'parenthesizedExprsExpr')
        return k(ast.s.exprs.head.right.right).must(be_token('c'))

    def type_attr_args(self) -> Expectation:
        ast = self.tpe('a.B[A]', 'appliedType')
        return k(ast.s.args.types.head).must(be_token('A'))

    def infix_inst_oper(self) -> Expectation:
        ast = self.ast('new A a()', 'expr')
        return (
            k(ast.s.left).must(have_rule('classInstantiation')) &
            k(ast.s.right).must(have_rule('parenthesizedExprsExpr'))
        )

    def splat_param(self) -> Expectation:
        ast = self.ast('def a(b: A*) = 1', 'def')
        var = ast.s.def_.sig.paramss.explicit.head.params.last
        return (
            k(var).must(have_rule('variadicParam')) &
            k(var.aster).must(be_token('*'))
        )

    def string_context(self) -> Expectation:
        ast = self.ast('sm"""sdf\nasdf"""', 'templateStat')
        return k(ast.s.lquote.context).must(be_token('sm'))

    def single_line_cases(self) -> Expectation:
        ast = self.ast('{ case a => b c d case _ => 2 }', 'blockExprContent')
        return k(ast.s.head.body.tail.head.case.rhs).must(be_token('2'))

    def only_implicit_params(self) -> Expectation:
        ast = self.stat('def a(implicit b: A) = c', 'templateStatDef')
        id = ast.s.def_.def_.sig.paramss.implicit.params.last.id
        return k(id).must(be_token('b'))

    def type_lambda(self) -> Expectation:
        ast = self.tpe('A[B]#C', 'typeProjection')
        return k(ast.s.id).must(be_token('C'))

    def symbolic_infix_type(self) -> Expectation:
        ast = self.ast('A :: B', 'infixType')
        return k(ast.s.tail.head.infix).must(be_token('::'))

    def token_position(self) -> Expectation:
        ast = self.ast('def name[A]', 'dcl')
        return k(ast.s.dcl.sig.id.data.pos) == 4

    def infix_position(self) -> Expectation:
        ast = self.ast('A :: B', 'infixType')
        return k(ast.s.tail.head.infix.data.pos) == 2

    def case_clause_position(self) -> Expectation:
        ast = self.ast('val x = a match { case a: A => b case c => d }', 'templateStat')
        return k(ast.s.def_.def_.rhs.cases.head.rhs.data.pos) == 31

    def multiline_expr(self) -> Expectation:
        ast = self.expr(multiline_expr, 'applyExpr')
        return k(ast.s.app[1].argss.head.args.head).must(be_token('fun2'))

    def multiline_val(self) -> Expectation:
        ast = self.def_(multiline_val, 'valVarDef')
        return k(ast.s.def_.rhs.app.head.argss.head.args.head).must(be_token('fun'))

    def caseclause_arg(self) -> Expectation:
        ast = self.def_(caseclause_arg, 'valVarDef')
        return k(ast.s.def_.rhs.app.last.argss.head.body.head.rhs).must(be_token('d'))

    def apply_chain_boundary(self) -> Expectation:
        ast = self.def_(boundary_apply_chain, 'valVarDef')
        return k(ast.s.def_.rhs.app.e / _.is_bol).must(be_right(True))

stat = '''\
'''


class ScalaFileSpec(ScalaSpecBase):
    '''experiments
    whole file $file
    statement $statement
    stat in block $stat_block
    temp2 $temp2
    '''

    __unsafe__ = None

    @pending
    def file(self) -> Expectation:
        content = load_fixture('parser', 'scala', 'file1.scala')
        ast = self.ast(content, 'compilationUnit')
        self.log.info(ast)

    @pending
    def statement(self) -> Expectation:
        ast = self.ast(stat, 'templateStat')
        self.log.info(ast)

    @pending
    def stat_block(self) -> Expectation:
        ast = self.ast('{{\n{}\n}}'.format(stat), 'template')
        self.log.info(ast)

    @pending
    def temp2(self) -> Expectation:
        ast = self.ast('A :: B', 'infixType')
        self.log.info(ast)

__all__ = ('ScalaSpec',)
