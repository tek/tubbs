from amino.test import Spec
from amino import List, _, __

from tubbs.grako.scala import Parser

funname = List.random_alpha(5)

funsig = ('{}[A <: B: TCL](par1: Tpe1, par2: Tpe2)(par3: Tpe3)' +
          '(implicit par4: Tpe4, par5: Tpe5)').format(funname)

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

caseclauses = '''{}
case _ => 3'''.format(caseclause)

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

    def blockExprApplyStrLit(self):
        word = List.random_alpha()
        ast = self._ast('{{foo("{}")}}'.format(word), 'simpleBlockExpr')
        # print(ast)
        print(ast.block.first[1][0][1][0])
        # ast.block.first[1][0][1].data.raw_m.should.contain(word)

    def fundef(self):
        ast = self._ast(fundef, 'def')
        ast.def_.sig.id.id.id.raw_m.should.contain(funname)

    def incomplete_fundef(self):
        ast = self._ast(incomplete_fundef, 'templateStat')
        ast.dcl.dcl.sig.id.id.id.raw_m.should.contain(funname)

    def fundecl(self):
        self._parse(fundecl, 'funDef').should.be.left
        ast = self._ast(fundecl, 'templateStat')
        ast.mod.raw_m.should.contain(acc_mod)
        ast.dcl.dcl.sig.id.id.id.raw_m.should.contain(funname)

    def funsig(self):
        ast = self._ast(funsig, 'funSig')
        ast.id.should.contain(funname)

    def rettype(self):
        ast = self._ast(rettype, 'type')
        (ast.head // _.simple // _.id).should.contain(rettypeid)

    def typeargs(self):
        ast = self._ast(typeargs, 'typeArgs')
        (ast.types | List()).should.have.length_of(2)

    def pattern(self):
        ast = self._ast('a: Type', 'pattern')
        (ast.last // _.id).should.contain('Type')

    def caseclause(self):
        ast = self._ast(caseclause, 'caseClause')
        ast.block.should.contain(List('1'))

    def caseclauses(self):
        ast = self._ast(caseclauses, 'caseClauses')
        (ast.cases // _.last // _.block).should.contain(List('3'))

    def patmat(self):
        ast = self._ast(patmat, 'patMat')
        (ast.cases // _.cases // _.last // _.block).should.contain(List('3'))

    def patmat_assign(self):
        ast = self._ast(patmatAssign, 'patVarDef')
        block = ast.def_ // _.rhs // _.cases // _.cases // _.last // _.block
        (block // _.stats).should.contain(List(List('3')))

    def result_type(self):
        ast = self._ast(resulttype, 'def')

    def valVarDef(self):
        ast = self._ast(valVarDef, 'valVarDef')
        (ast.def_ // _.rhs // _.head).should.contain('1')

    def blockStat(self):
        ast = self._ast(valVarDef, 'blockStat')
        (ast.head // _.def_ // _.rhs // _.head).should.contain('1')

    def block(self):
        ast = self._ast(block, 'block')
        (ast.first // _.head // _.def_ // _.rhs // _.head).should.contain('1')

    def blockExpr(self):
        ast = self._ast(blockExpr, 'blockExpr')
        (ast.block // _.first // _.head // _.def_ // _.rhs // _.head
         ).should.contain('1')

__all__ = ('ScalaSpec',)
