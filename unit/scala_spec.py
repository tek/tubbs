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


class ScalaSpec(Spec):

    def setup(self):
        super().setup()
        self._parser = Parser()
        self._parser.gen()

    def _parse(self, text, rule):
        return self._parser.parse(text, rule)

    def fundef(self):
        ast = self._parse(fundef, 'Def')
        (ast // __.lift(1) // _.sig // _.id).should.contain(funname)

    def incomplete_fundef(self):
        ast = self._parse(incomplete_fundef, 'TemplateStat')
        (ast // _.dcl // _.dcl // _.sig // _.id).should.contain(funname)

    def fundecl(self):
        self._parse(fundecl, 'FunDef').should.be.left
        ast = self._parse(fundecl, 'TemplateStat')
        ast.should.be.right
        (ast // _.mod).should.contain(acc_mod)
        (ast // _.dcl // _.dcl // _.sig // _.id).should.contain(funname)

    def funsig(self):
        ast = self._parse(funsig, 'FunSig')
        (ast // _.id).should.contain(funname)

    def rettype(self):
        ast = self._parse(rettype, 'Type')
        (ast // _.head // _.simple // _.id).should.contain(rettypeid)

    def typeargs(self):
        ast = self._parse(typeargs, 'TypeArgs')
        (ast // _.types | List()).should.have.length_of(2)

__all__ = ('ScalaSpec',)
