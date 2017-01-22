from amino.test import Spec
from amino import List, _

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
        self._ast.when.called_with('case', 'plainid').should.throw(Exception)

    def blockExprApplyStrLit(self):
        word = List.random_alpha()
        ast = self._ast('{{foo("{}")}}'.format(word), 'simpleBlockExpr')
        ast.block.first[2].data.raw.should.contain(word)

    def fundef(self):
        ast = self._ast(fundef, 'def')
        ast.def_.sig.id.raw.should.contain(funname)
        tpe = ast.def_.sig.paramss.explicit.last.params.head.tpe
        id = tpe.infixhead.compoundpre.head.id
        id.raw.should.contain(tpe3)
        (id.e / _.rule).should.contain('id')

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
        ast.infixhead.compoundpre.head.simple.id.raw.should.contain(rettypeid)

    def typeargs(self):
        ast = self._ast(typeargs, 'typeArgs')
        ast.types.head.infixhead.compoundpre.head.id.raw.should.contain('A')
        ast.types.last.infixhead.compoundpre.head.id.raw.should.contain('Tpe6')

    # FIXME ast is a list of lists
    # also filter empty lists
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
        case1.pat[2].infixhead.compoundpre.head.id.raw.should.contain('Type')
        case2.block.first.head.raw.should.contain('3')

    def result_type(self):
        ast = self._ast(resulttype, 'def')
        (ast.def_.rhs.block.rest.head.stat.templ.head.id.raw
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

__all__ = ('ScalaSpec',)
