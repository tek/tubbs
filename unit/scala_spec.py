from amino.test import Spec
from amino import List, _
from amino.test.path import load_fixture

from tubbs.grako.scala import Parser

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

patmatAssign = 'val b = {}'.format(patmat)

resulttype = '''def foo = {{
{}
new Cls(b)
}}'''.format(patmatAssign)

valVarDef = 'val a = 1'

block = '''{}
val b = 2'''.format(valVarDef)

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

class_instantiation = '''{ val a = new Cls(b).c }'''

triple_bool = '''{a && b && c}'''

attr_assign = 'a.b = c'

attr_assign_template = '{{ {} }}'.format(attr_assign)


class ScalaSpec(Spec):

    def setup(self):
        super().setup()
        self._parser = Parser()
        self._parser.gen()

    def _parse(self, text, rule):
        return self._parser.parse(text, rule)

    def _ast(self, text, rule):
        res = self._parse(text, rule)
        res.should.be.right
        return res.value

    def keyword(self):
        (self._ast.when.called_with('case', 'plainidName')
         .should.throw(Exception))

    def blockExprApplyStrLit(self):
        word = List.random_alpha()
        ast = self._ast('{{foo("{}")}}'.format(word), 'simpleBlockExpr')
        ast.block.first.args.head.args.first.data.raw.should.contain(word)

    def fundef(self):
        ast = self._ast(fundef, 'def')
        ast.def_.sig.id.raw.should.contain(funname)
        explicit = ast.def_.sig.paramss.explicit
        (explicit.e / _.rule).should.contain('paramClauses')
        id = explicit.last.params.head.tpe.infixhead.compoundpre.head.id.id
        id.raw.should.contain(tpe3)
        (id.e / _.rule).should.contain('plainid')

    def incomplete_fundef(self):
        ast = self._ast(incomplete_fundef, 'templateStat')
        ast.dcl.dcl.sig.id.raw.should.contain(funname)

    def fundecl(self):
        self._parse(fundecl, 'funDef').should.be.left
        ast = self._ast(fundecl, 'templateStat')
        ast.mod.raw.should.contain(acc_mod)
        ast.dcl.dcl.sig.id.raw.should.contain(funname)

    def funsig(self):
        ast = self._ast(funsig, 'funSig')
        ast.id.raw.should.contain(funname)

    def rettype(self):
        ast = self._ast(rettype, 'type')
        (ast.infixhead.compoundpre.head.simple.id.id.raw
         .should.contain(rettypeid))

    def typeargs(self):
        ast = self._ast(typeargs, 'typeArgs')
        ast.types.head.infixhead.compoundpre.head.id.id.raw.should.contain('A')
        (ast.types.last.infixhead.compoundpre.head.id.id.raw
         .should.contain('Tpe6'))

    def pattern(self):
        ast = self._ast('a: Type', 'pattern')
        ast[2].infixhead.compoundpre.head.id.raw.should.contain('Type')

    def caseclause(self):
        ast = self._ast(caseclause, 'caseClause')
        ast.block.first.head.raw.should.contain('1')

    def caseclause_wildcard(self):
        ast = self._ast(caseclause_wildcard, 'caseClause')
        ast.block.first.head.raw.should.contain('3')

    def caseclauses(self):
        ast = self._ast(caseclauses, 'caseClauses')
        ast.first.block.first.head.raw.should.contain('1')
        ast.rest.head.case.block.first.head.raw.should.contain('3')

    def patmat(self):
        ast = self._ast(patmat, 'patMat')
        ast.cases.rest.head.case.pat.head.raw.should.contain('_')
        ast.cases.rest.head.case.block.first.head.raw.should.contain('3')

    def patmat_assign(self):
        ast = self._ast(patmatAssign, 'patVarDef')
        cases = ast.def_.rhs.cases
        case1 = cases.first
        case2 = cases.rest.head.case
        (case1.pat[2].infixhead.compoundpre.head.id.id.raw
         .should.contain('Type'))
        case2.block.first.head.raw.should.contain('3')

    def result_type(self):
        ast = self._ast(resulttype, 'def')
        (ast.def_.rhs.block.rest.head.stat.templ.head.id.id.raw
         .should.contain('Cls'))

    def valVarDef(self):
        ast = self._ast(valVarDef, 'valVarDef')
        ast.def_.rhs.head.raw.should.contain('1')

    def blockStat(self):
        ast = self._ast(valVarDef, 'blockStat')
        ast.head.def_.rhs.head.raw.should.contain('1')

    def block(self):
        ast = self._ast(block, 'block')
        ast.first.head.def_.rhs.head.raw.should.contain('1')

    def blockExpr(self):
        ast = self._ast(blockExpr, 'blockExpr')
        ast.block.first.head.def_.rhs.head.raw.should.contain('1')

    def infix(self):
        ast = self._ast('foo boo\n zoo', 'infixExpr')
        ast.arg.raw.should.contain('zoo')

    def whitespace(self):
        i = 3
        ast = self._ast('{}def foo = 1'.format(' ' * i), 'def')
        ast.defkw._data.ws_count.should.equal(i)

    def broken(self):
        ast = self._ast(broken_lines, 'def')
        ast.def_.rhs.block.first.head.def_.rhs.pre.raw.should.contain('fun2')

    def broken2(self):
        ast = self._ast(broken_lines_2, 'def')
        ast.def_.rhs.block.first.head.def_.rhs.pre.raw.should.contain('fun2')

    def trait(self):
        ast = self._ast('trait Foo {\n}', 'trait')
        ast.data.should.have.length_of(5)

    def argument_assign(self):
        ast = self._ast(argument_assign, 'templateBody')
        (ast[1].def_.def_.rhs.args.head.args.first.rhs.raw
         .should.contain('true'))

    def select(self):
        ast = self._ast('a.b.c', 'path')
        ast.pre.last.selector.raw.should.contain('b')

    def argument_select(self):
        ast = self._ast(argument_select, 'templateBody')
        print(ast[1].def_.def_.rhs[1].args.first)

    def import_(self):
        ast = self._ast('one.two.three', 'importExpr')
        ast.last.raw.should.contain('three')

    def literal_attr(self):
        ast = self._ast('"i".a', 'simpleOrCompoundExpr')
        ast.last.raw.should.contain('a')

    def literal_apply_args(self):
        ast = self._ast('"i".a(1)', 'simpleOrCompoundExpr')
        ast.args.head.args.first.head.raw.should.contain('1')

    def literal_apply_args_as_arg(self):
        ast = self._ast('f("i".a(1))', 'simpleApplyExpr')
        (ast.args.head.args.first.args.head.args.first.head.raw
         .should.contain('1'))

    def class_instantiation(self):
        ast = self._ast(class_instantiation, 'templateBody')
        rhs = ast[1].head.def_.def_.rhs
        rhs.pre.templ.head.head.head.id.raw.should.contain('Cls')
        rhs.id.raw.should.contain('c')

    def triple_bool(self):
        ast = self._ast(triple_bool, 'templateBody')
        ast[1].head.right.right.raw.should.contain('c')

    def select(self):
        ast = self._ast('{a.b.c}', 'template')
        expr = ast.stats.stats.head_
        expr.rule.should.equal('attrExpr')
        expr.tail.last.id.raw.should.contain('c')

    def attr_assign(self):
        ast = self._ast(attr_assign, 'expr')
        ast.rule.should.equal('attrAssignExpr')
        ast.rhs.head_.raw.should.contain('c')

    def attr_assign_template(self):
        ast = self._ast(attr_assign_template, 'template')
        ast.stats.stats.head_.rule.should.equal('attrAssignExpr')

    def file(self):
        content = load_fixture('parser', 'scala', 'file1.scala')
        ast = self._ast(content, 'compilationUnit')
        print(ast)

__all__ = ('ScalaSpec',)
