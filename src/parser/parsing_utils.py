from  utils.pycompiler import Item, EOF
from  utils.automata import State, multiline_formatter
from  utils.utils import ContainerSet
from itertools import islice
from  parser.SRParser import ShiftReduceParser


def compute_local_first(firsts, alpha):
    first_alpha = ContainerSet()

    try:
        alpha_is_epsilon = alpha.IsEpsilon
    except:
        alpha_is_epsilon = False

    if alpha_is_epsilon:
        first_alpha.set_epsilon()

    else:
        for p in alpha:
            first_alpha.update(firsts[p])

            if not firsts[p].contains_epsilon:
                break
        else:
            first_alpha.set_epsilon()

    return first_alpha


def compute_firsts(G):
    firsts = {}
    change = True

    for terminal in G.terminals:
        firsts[terminal] = ContainerSet(terminal)

    for non_terminal in G.nonTerminals:
        firsts[non_terminal] = ContainerSet()

    while change:
        change = False

        for production in G.Productions:
            x = production.Left
            alpha = production.Right

            first_x = firsts[x]

            try:
                first_alpha = firsts[alpha]
            except KeyError:
                first_alpha = firsts[alpha] = ContainerSet()

            local_first = compute_local_first(firsts, alpha)

            change |= first_alpha.hard_update(local_first)
            change |= first_x.hard_update(local_first)

    return firsts


def compute_follows(G, firsts):
    follows = {}
    change = True

    local_firsts = {}

    for non_terminal in G.nonTerminals:
        follows[non_terminal] = ContainerSet()
    follows[G.startSymbol] = ContainerSet(G.EOF)

    while change:
        change = False

        for production in G.Productions:
            x = production.Left
            alpha = production.Right

            follow_x = follows[x]

            for i, Y in enumerate(alpha):
                if Y.IsNonTerminal:
                    try:
                        beta_f = local_firsts[alpha, i]
                    except KeyError:
                        beta_f = local_firsts[alpha, i] = compute_local_first(firsts, islice(alpha, i + 1, None))
                    change |= follows[Y].update(beta_f)
                    if beta_f.contains_epsilon:
                        change |= follows[Y].hard_update(follow_x)
    return follows


def expand(item, firsts):
    next_symbol = item.NextSymbol
    if next_symbol is None or not next_symbol.IsNonTerminal:
        return []

    lookaheads = ContainerSet()
    for symbol in item.Preview():
        lookaheads.update(compute_local_first(firsts, symbol))

    assert not lookaheads.contains_epsilon

    return [Item(production, 0, lookaheads) for production in next_symbol.productions]


def compress(items):
    centers = {}

    for item in items:
        center = item.Center()
        try:
            lookaheads = centers[center]
        except KeyError:
            centers[center] = lookaheads = set()
        lookaheads.update(item.lookaheads)

    return {Item(x.production, x.pos, set(lookahead)) for x, lookahead in centers.items()}


def closure_lr1(items, firsts):
    closure = ContainerSet(*items)

    changed = True
    while changed:
        changed = False

        new_items = ContainerSet()
        for item in closure:
            new_items.extend(expand(item, firsts))

        changed = closure.update(new_items)

    return compress(closure)


def goto_lr1(items, symbol, firsts=None, just_kernel=False):
    assert just_kernel or firsts is not None, '`firsts` must be provided if `just_kernel=False`'
    items = frozenset(item.NextItem() for item in items if item.NextSymbol == symbol)
    return items if just_kernel else closure_lr1(items, firsts)


def build_LR1_automaton(G):
    assert len(G.startSymbol.productions) == 1, 'Grammar must be augmented'

    firsts = compute_firsts(G)
    firsts[G.EOF] = ContainerSet(G.EOF)

    start_production = G.startSymbol.productions[0]
    start_item = Item(start_production, 0, lookaheads=(G.EOF,))
    start = frozenset([start_item])

    closure = closure_lr1(start, firsts)
    automaton = State(frozenset(closure), True)

    pending = [start]
    visited = {start: automaton}

    while pending:
        current = pending.pop()
        current_state = visited[current]

        for symbol in G.terminals + G.nonTerminals:
            next_items = goto_lr1(current_state.state, symbol, just_kernel=True)
            if not next_items:
                continue

            try:
                next_state = visited[next_items]
            except KeyError:
                pending.append(next_items)
                closure = closure_lr1(next_items, firsts)
                visited[next_items] = State(frozenset(closure), True)
                next_state = visited[next_items]

            current_state.add_transition(symbol.Name, next_state)

    automaton.set_formatter(multiline_formatter)
    return automaton


def build_LR0_automaton(G):
    assert len(G.startSymbol.productions) == 1, 'Grammar must be augmented'

    start_production = G.startSymbol.productions[0]
    start_item = Item(start_production, 0)

    automaton = State(start_item, True)

    pending = [start_item]
    visited = {start_item: automaton}

    while pending:
        current_item = pending.pop()
        if current_item.IsReduceItem:
            continue

        next_item = current_item.NextItem()
        if next_item not in visited.keys():
            visited[next_item] = State(next_item, True)
            pending.append(next_item)

        next_symbol = current_item.NextSymbol

        current_state = visited[current_item]
        current_state.add_transition(next_symbol.Name, visited[next_item])

        if next_symbol.IsNonTerminal:
            for production in G.Productions:
                if next_symbol == production.Left:
                    item = Item(production, 0)
                    if item not in visited.keys():
                        visited[item] = State(item, True)
                        pending.append(item)
                    current_state.add_epsilon_transition(visited[item])
    return automaton


def evaluate_reverse_parse(right_parse, operations, tokens, get_tokens=False):
    if not right_parse or not operations or not tokens:
        return

    right_parse = iter(right_parse)
    tokens = iter(tokens)
    stack = []
    for operation in operations:
        if operation == ShiftReduceParser.SHIFT:
            token = next(tokens)
            if get_tokens:
                stack.append(token)
            else:
                stack.append(token.lex)
        elif operation == ShiftReduceParser.REDUCE:
            production = next(right_parse)
            head, body = production
            attributes = production.attributes
            assert all(rule is None for rule in attributes[1:]), 'There must be only synteticed attributes.'
            rule = attributes[0]

            if len(body):
                synteticed = [None] + stack[-len(body):]
                value = rule(None, synteticed)
                stack[-len(body):] = [value]
            else:
                stack.append(rule(None, None))
        else:
            raise Exception('Invalid action!!!')

    assert len(stack) == 1
    assert isinstance(next(tokens).token_type, EOF)
    return stack[0]
