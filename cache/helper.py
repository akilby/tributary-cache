def single_item(elements):
    assert len(set(elements)) == 1
    return list(elements)[0]


def listr(item):
    return [item] if isinstance(item, str) else item
