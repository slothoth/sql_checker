def to_number(x):
    if isinstance(x, (int, float)):
        return x
    if isinstance(x, str):
        s = x.strip()
        try:
            i = int(s)
            return i
        except ValueError:
            try:
                return float(s)
            except ValueError:
                return 'failed'


def flatten(xss):
    return [x for xs in xss for x in xs]


def flatten_avoid_string(items):
    out = []
    if isinstance(items, str):
        return items
    for x in items:
        if isinstance(x, (list, tuple)):
            out.extend(flatten(x))
        else:
            out.append(x)
    return out
