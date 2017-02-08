This *neovim* plugin provides code parsing functionality on the basis of EBNF
grammars in order to facilitate generalized text objects and code formatting.

# Setup

**tubbs** is based on [ribosome], so it requires the neovim plugin stub
[tubbs.nvim] as well as this python project:

```
pip install tubbs
```

# Text objects

Individual grammar rules can be used as basis for operator mappings by using
the functions `TubA` and `TubI` with the rule name as argument.

```viml
onoremap ad :call TubA('def')<cr>
```

# Formatting
**tubbs** provides low- and high-level tools for formatting code based on a
grammar.
An arbitrary sequence of formatting routines can be chained to process the
abstract syntax tree that's annotated with the labels of each sub-AST and the
names of the rules that produce them.

The simple way requires a dictionary that maps the names of rules and/or sub
ASTs to values indicating what action to perform. There are two major
formatters, for breaking lines and setting their indent.

## Breaking lines

## Indenting lines

## formatexpr
To use **tubbs** with regular vim formatting via the `gq` operator:
```viml
set formatexpr=TubFormat(v:lnum,\ v:count)
```

# EBNF

**tubbs** uses [grako] to load grammars and parse code. Grammar files can be
specified with:

> TODO

Shipped grammars that work out of the box:
* scala

# Hinting

To simplify the association of the requested expression with the cursor
position, a simple initial search can be performed by specifying **hints**.
This can be any [vim callback][callback], read from the variable
`g:tubbs_hints`, generally a backwards regex search.

As an example, when selecting a `def`, a backwards search for `^\s*def\b` will
yield a start location for the parsing process.
If no hints were specified, the parser iterates backwards through the lines
until a match is found.

A hint can defer to a different grammar rule, so different styles can be
specified for a given rule name. The name given as argument does not need to be
an existing rule if the hints contain an entry for it, the rule is then
obtained from the hinting match.

[ribosome]: https://github.com/tek/ribosome
[tubbs.nvim]: https://github.com/tek/tubbs.nvim
[grako]: https://bitbucket.org/apalala/grako
[callback]: https://github.com/tek/ribosome#callbacks
