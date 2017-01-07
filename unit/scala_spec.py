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

caseclause = 'case a: Type => b'

caseclauses = '''{}
case a => b
'''.format(caseclause)

patmat = '''a match {{
{}
}}'''.format(caseclauses)


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

    def fundef(self):
        ast = self._ast(fundef, 'def')
        (ast.lift(1) // _.sig // _.id).should.contain(funname)

    def incomplete_fundef(self):
        ast = self._ast(incomplete_fundef, 'templateStat')
        (ast.dcl // _.dcl // _.sig // _.id).should.contain(funname)

    def fundecl(self):
        self._parse(fundecl, 'funDef').should.be.left
        ast = self._ast(fundecl, 'templateStat')
        ast.mod.should.contain(acc_mod)
        (ast.dcl // _.dcl // _.sig // _.id).should.contain(funname)

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
        ast.block.should.contain(List('b'))

    def caseclauses(self):
        ast = self._ast(caseclauses, 'caseClauses')
        (ast.cases // _.last // _.block).should.contain(List('b'))

    def patmat(self):
        ast = self._ast(patmat, 'patMat')
        (ast.cases // _.cases // _.last // _.block).should.contain(List('b'))

__all__ = ('ScalaSpec',)
