package pack

object Ob2 {
  val name =
    value.attr
      .map(fun1)
      .collect { case Extract(v1, v2) => fun2(v2, v1) }
      .flatMap {
        case (x, y) =>
          Option(x + y)
      }
      .zip
}
