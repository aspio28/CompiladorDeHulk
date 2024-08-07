from utils.error_manager import UnexspectedSequenceTokens

class ShiftReduceParser:
    SHIFT = 'SHIFT'
    REDUCE = 'REDUCE'
    OK = 'OK'

    def __init__(self, G, verbose=False):
        self.G = G
        self.verbose = verbose
        self.action = {}
        self.goto = {}
        self._build_parsing_table()

    def _build_parsing_table(self):
        raise NotImplementedError()

    def __call__(self, tokens):
        w = [token.token_type for token in tokens]
        stack = [0]
        cursor = 0
        output = []
        operations = []
        while True:
            state = stack[-1]
            lookahead = tokens[cursor]
            if self.verbose: print(stack, '<---||--->', w[cursor:], output)

            if (state, lookahead.token_type) not in self.action:
                error = UnexspectedSequenceTokens(lookahead, tokens[cursor - 1])
                return None, error

            action, tag = self.action[state, lookahead.token_type]
            
            if action == ShiftReduceParser.SHIFT:
                operations.append(ShiftReduceParser.SHIFT)
                stack.append(tag)
                cursor += 1

            elif action == ShiftReduceParser.REDUCE:
                operations.append(ShiftReduceParser.REDUCE)
                for i in range(len(tag.Right)):
                    stack.pop()
                stack.append(self.goto[stack[-1], tag.Left])
                output.append(tag)

            elif action == ShiftReduceParser.OK:
                return output, operations

            else:
                raise ValueError
