package pack

object Ob2 {
  def fun1[TPar1 <: UB1: TC1](par1a: Tpe1, par1b: Tpe1)
  (par2a: Tpe2, par2b: Tpe2)
  (implicit par3: Tpe3, par4: Tpe4) = {
    val a = par1a match {
      case _: Tpe1 => { println("Tpe1") } case Tpe2(f) => par1b map f
      case _ => { val v1 = fun2(par1); fun3(v1) }
    }
  }
}
