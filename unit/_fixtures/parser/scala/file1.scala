/* NSC -- new Scala compiler
 * Copyright 2005-2013 LAMP/EPFL
 * @author  Martin Odersky
 */

//todo: rewrite or disallow new T where T is a mixin (currently: <init> not a member of T)
//todo: use inherited type info also for vars and values
//todo: disallow C#D in superclass
//todo: treat :::= correctly

package scala
package tools.nsc
package typechecker

import scala.annotation.tailrec
import scala.collection.{ mutable, immutable }
import mutable.{ LinkedHashMap, ListBuffer }
import scala.util.matching.Regex
import symtab.Flags._
import scala.reflect.internal.util.{TriState, Statistics}
import scala.language.implicitConversions

/** This trait provides methods to find various kinds of implicits.
 *
 *  @author  Martin Odersky
 *  @version 1.0
 */
trait Implicits {
  self: Analyzer =>

  import global._
  import definitions._
  import ImplicitsStats._
  import typingStack.{ printTyping }
  import typeDebug._

  def inferImplicit(tree: Tree, pt: Type, reportAmbiguous: Boolean, isView: Boolean, context: Context): SearchResult =
    inferImplicit(tree, pt, reportAmbiguous, isView, context, saveAmbiguousDivergent = true, tree.pos)

  def inferImplicit(tree: Tree, pt: Type, reportAmbiguous: Boolean, isView: Boolean, context: Context, saveAmbiguousDivergent: Boolean): SearchResult =
    inferImplicit(tree, pt, reportAmbiguous, isView, context, saveAmbiguousDivergent, tree.pos)

  /** Search for an implicit value. See the comment on `result` at the end of class `ImplicitSearch`
   *  for more info how the search is conducted.
   *  @param tree                    The tree for which the implicit needs to be inserted.
   *                                 (the inference might instantiate some of the undetermined
   *                                 type parameters of that tree.
   *  @param pt                      The expected type of the implicit.
   *  @param reportAmbiguous         Should ambiguous implicit errors be reported?
   *                                 False iff we search for a view to find out
   *                                 whether one type is coercible to another.
   *  @param isView                  We are looking for a view
   *  @param context                 The current context
   *  @param saveAmbiguousDivergent  False if any divergent/ambiguous errors should be ignored after
   *                                 implicits search,
   *                                 true if they should be reported (used in further typechecking).
   *  @param pos                     Position that is should be used for tracing and error reporting
   *                                 (useful when we infer synthetic stuff and pass EmptyTree in the `tree` argument)
   *                                 If it's set NoPosition, then position-based services will use `tree.pos`
   *  @return                        A search result
   */
  def inferImplicit(tree: Tree, pt: Type, reportAmbiguous: Boolean, isView: Boolean, context: Context, saveAmbiguousDivergent: Boolean, pos: Position): SearchResult = {
    // Note that the isInvalidConversionTarget seems to make a lot more sense right here, before all the
    // work is performed, than at the point where it presently exists.
    val shouldPrint     = printTypings && !context.undetparams.isEmpty
    val rawTypeStart    = if (Statistics.canEnable) Statistics.startCounter(rawTypeImpl) else null
    val findMemberStart = if (Statistics.canEnable) Statistics.startCounter(findMemberImpl) else null
    val subtypeStart    = if (Statistics.canEnable) Statistics.startCounter(subtypeImpl) else null
    val start           = if (Statistics.canEnable) Statistics.startTimer(implicitNanos) else null
    if (shouldPrint)
      typingStack.printTyping(tree, "typing implicit: %s %s".format(tree, context.undetparamsString))
  }
}
