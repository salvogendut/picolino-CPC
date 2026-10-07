"""Minimal S-expression helpers for the KiCad hardware build scripts."""
import json
import re


class Atom(str):
    pass


def loads(text):
    tokens = iter(re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', text))
    def read(token):
        if token == '(':
            result = []
            for token in tokens:
                if token == ')': return result
                result.append(read(token))
            raise ValueError('Unclosed expression')
        return json.loads(token) if token.startswith('"') else Atom(token)
    result = read(next(tokens))
    if next(tokens, None) is not None: raise ValueError('Trailing expression')
    return result


def dumps(node, level=0):
    if isinstance(node, Atom): return str(node)
    if isinstance(node, str): return json.dumps(node, ensure_ascii=False)
    return '(' + ''.join(('\n' + '  '*(level+1) if isinstance(x, list) else ' ') + dumps(x, level+1)
                         for x in node).lstrip() + ')'


def children(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]


def child(node, key):
    return next(iter(children(node, key)), None)
