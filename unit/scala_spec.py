from amino.test import Spec
from amino import List, _, __

from tubbs.grako.scala import parse, gen

funname = List.random_alpha(5)

funsig = ('{}[A <: B: TCL](par1: Tpe1, par2: Tpe2)(par3: Tpe3)' +
          '(implicit par4: Tpe4, par5: Tpe5)').format(funname)

typeargs = '[A, Tpe6]'

rettypeid = 'ReturnType'

rettype = '{}{}'.format(rettypeid, typeargs)

fundecl = 'def {}(a: Int): Ret'.format(funname)

fundef = '''def {}: {} = {{
    val a: Int = 1
    foo("asdf")
}}
'''.format(funsig, rettype)


class ScalaSpec(Spec):

    def setup(self):
        super().setup()
        gen()

    def fundef(self):
        res = parse(fundef, 'Def')
        (res // __.lift(1) // _.sig // _.id).should.contain(funname)

    def fundecl(self):
        parse(fundecl, 'FunDef').should.be.left
        res = parse(fundef, 'Dcl')
        (res // __.lift(1) // _.sig // _.id).should.contain(funname)

    def funsig(self):
        res = parse(funsig, 'FunSig')
        (res // _.id).should.contain(funname)

    def rettype(self):
        res = parse(rettype, 'Type')
        (res // _.head // _.simple // _.id).should.contain(rettypeid)

    def typeargs(self):
        res = parse(typeargs, 'TypeArgs')
        (res // _.types | List()).should.have.length_of(2)

__all__ = ('ScalaSpec',)
