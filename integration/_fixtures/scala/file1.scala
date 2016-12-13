package pack1
package pack2

object Ob1
{
  def fun1[TPar1 <: UB1: TC1](par1: Tpe1)(par2: Tpe2)(implicit par3: Tpe3, par4: Tpe4) = {
    val v1 = fun2(par1)
    fun3(v1)
  }

  def fun2(par5: Tpe1) = par5

  def fun3(par6: Tpe1 = null) = { par6 + 4 }
}

class Cls1[TPar2](par7: Tpe5)(implicit par8: Tpe6)
extends Base1
with Base2[TPar2]
{
  def fun4 = Ob1.fun2(null)

  def fun5[TPar3 <: UB2: TC2](par8: TPar3) = {
    def fun6 = par8 >> null
    fun6
  }
}
