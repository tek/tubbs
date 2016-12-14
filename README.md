This *neovim* plugin provides code parsing functionality on the basis of EBNF
grammars in order to facilitate generalized text objects and code formatting.

# Setup

**tubbs** is based on [ribosome], so it requires the neovim plugin stub
[tubbs.nvim] as well as this python project:

```
pip install tubbs
```

# EBNF

**tubbs** uses [grako] to load grammars and parse code. Grammar files can be
specified with:

> TODO

Shipped grammars that work out of the box:
* scala

# Text objects

Individual grammar rules can be used as basis for operator mappings by using
the functions `TubA` and `TubI` with the rule name as argument.

```viml
omap ad :call TubA('def')<cr>
```

[ribosome]: https://github.com/tek/ribosome
[tubbs.nvim]: https://github.com/tek/tubbs.nvim
[grako]: https://bitbucket.org/apalala/grako
