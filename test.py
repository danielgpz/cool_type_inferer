from cool import tokenizer, pprint_tokens
from cool import CoolParser
from cool.cmp import evaluate_reverse_parse
from cool import FormatVisitor, TypeCollector, TypeBuilder, TypeChecker, TypeInferer

def run_pipeline(text):
    print('=================== TEXT ======================')
    print(text)
    print('================== TOKENS =====================')
    tokens = tokenizer(text)
    pprint_tokens(tokens)
    print('=================== PARSE =====================')
    parse, operations = CoolParser([t.token_type for t in tokens])
    print('\n'.join(repr(x) for x in parse))
    print('==================== AST ======================')
    ast = evaluate_reverse_parse(parse, operations, tokens)
    formatter = FormatVisitor()
    tree = formatter.visit(ast)
    print(tree)
    print('============== COLLECTING TYPES ===============')
    errors = []
    collector = TypeCollector(errors)
    collector.visit(ast)
    context = collector.context
    print('Errors:', errors)
    print('Context:')
    print(context)
    print('=============== BUILDING TYPES ================')
    builder = TypeBuilder(context, errors)
    builder.visit(ast)
    print('Errors: [')
    for error in errors:
        print('\t', error)
    print(']')
    print('Context:')
    print(context)
    print('=============== CHECKING TYPES ================')
    checker = TypeChecker(context, errors)
    scope = checker.visit(ast)
    print('Errors: [')
    for error in errors:
        print('\t', error)
    print(']')
    print('============== INFERINING TYPES ===============')
    inferer = TypeInferer(context, errors)
    while inferer.visit(ast, scope): pass
    # tree = formatter.visit(ast)
    # print(tree)
    print('Context:')
    print(context)
    return ast, errors, context, scope

if __name__ == '__main__':
    f = open('test.cl')
    run_pipeline(f.read())