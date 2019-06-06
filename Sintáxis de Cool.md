# Classes
```
class <type> [ inherits <type> ] {
	<feature_list>
};
```

# Attributes
```
<id> : <type> [ <- <expr> ];
```

# Methods
```
<id>(<id> : <type>,...,<id> : <type>): <type> { <expr> };
```

# Expressions
*Expressions are the largest syntactic category in Cool.*

# Constants
```
true
false
0
123
007
"This is a string."
```

# Assignment
```
<id> <- <expr>
```

# Dispatch
```
<expr>.<id>(<expr>,...,<expr>)
<id>(<expr>,...,<expr>)
<expr>@<type>.id(<expr>,...,<expr>)
```

# Conditionals
```
if <expr> then <expr> else <expr> fi
```

# Loops
```
while <expr> loop <expr> pool
```

# Blocks
```
{ <expr>; ... <expr>; }
```

# Let
```
let <id1> : <type1> [ <- <expr1> ], ..., <idn> : <typen> [ <- <exprn> ] in <expr>
```

# Case
```
case <expr0> of
	<id1> : <type1> => <expr1>;
	. . .
	<idn> : <typen> => <exprn>;
esac
```

# New
```
new <type>
```

# Isvoid
```
isvoid expr
```

# Arithmetic and Comparison Operations
```
expr1 <op> expr2
~<expr>
not <expr>
```

# Basic Classes
* Object
	```
	abort() : Object
	type_name() : String
	copy() : SELF_TYPE
	```

* IO
	```
	out_string(x : String) : SELF_TYPE
	out_int(x : Int) : SELF_TYPE
	in_string() : String
	in_int() : Int
	```

* Int

* String
	```
	length() : Int
	concat(s : String) : String
	substr(i : Int, l : Int) : String
	```

* Bool

# Keywords
`class`, `else`, `false`, `fi`, `if`, `in`, `inherits`, `isvoid`, `let`, `loop`, `pool`, `then`, `while`,
`case`, `esac`, `new`, `of`, `not`, `true`

# COOL Syntax
*program*  ***--->*** [[*class*; ]]+

*class*    ***--->*** `class` *TYPE* [`inherits` *TYPE*] `{` [[*feature*`;` ]]*`}`

*feature*  ***--->*** *ID*`(` [ *formal* [[`,` *formal*]]* ] `)` `:` *TYPE* `{` *expr* `}`

*feature*  ***--->*** *ID* `:` *TYPE* [ `<-` *expr* ]

*formal*   ***--->*** *ID* `:` *TYPE*

*expr*     ***--->*** *ID* `<-` *expr*

*expr*     ***--->*** *expr*[@*TYPE*]`.`*ID*`(` [ *expr* [[`,` *expr*]]* ] `)`

*expr*     ***--->*** *ID*`(` [ *expr* [[`,` *expr*]]* ] `)`

*expr*     ***--->*** `if` *expr* `then` *expr* `else` *expr* `fi`

*expr*     ***--->*** `while` *expr* `loop` *expr* `pool`

*expr*     ***--->*** `{` [[*expr*`;` ]]+ `}`

*expr*     ***--->*** `let` *ID* `:` *TYPE* [ `<-` *expr* ] [[`,` *ID* `:` *TYPE* [ `<-` *expr* ]]]* `in` *expr*

*expr*     ***--->*** `case` *expr* `of` [[*ID* : *TYPE* `=>` *expr*`;` ]]+ `esac`

*expr*     ***--->*** `new` *TYPE*

*expr*     ***--->*** `isvoid` *expr*

*expr*     ***--->*** *expr* `+` *expr*

*expr*     ***--->*** *expr* `−` *expr*

*expr*     ***--->*** *expr* `*` *expr*

*expr*     ***--->*** *expr* `/` *expr*

*expr*     ***--->*** `˜`*expr*

*expr*     ***--->*** *expr* `<` *expr*

*expr*     ***--->*** *expr* `<=` *expr*

*expr*     ***--->*** *expr* `=` *expr*

*expr*     ***--->*** `not` *expr*

*expr*     ***--->*** `(`*expr*`)`

*expr*     ***--->*** *ID*

*expr*     ***--->*** *integer*

*expr*     ***--->*** *string*

*expr*     ***--->*** *true*

*expr*     ***--->*** *false*

*TYPE*     ***--->*** [`A` - `Z`] [`_` `0` - `9` `a` - `z` `A` - `Z`]*

*ID*       ***--->*** [`a` - `z`] [`_` `0` - `9` `a` - `z` `A` - `Z`]*

*integer*  ***--->*** [`0` - `9`]+

*true*     ***--->*** `t` [ `rR` ] [ `uU` ] [ `eE` ]

*false*    ***--->*** `f` [ `aA` ] [ `lL` ] [ `sS` ] [ `eE` ]