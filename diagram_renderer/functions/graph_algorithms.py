"""Pure graph algorithms operating on plain (source, target) pairs."""

from __future__ import annotations

from collections import defaultdict


def transitive_reduction_indices(pairs: list[tuple[str, str]]) -> list[int]:
    """Return indices of *pairs* that survive transitive reduction.

    A pair `(u, v)` at index `i` is dropped when `v` is still reachable from
    `u` via a path of length >= 2 built only from the *other* pairs. Pairs
    are expected to represent edges of a single relation (e.g. one link
    filter) — mixing unrelated relations would treat them as interchangeable
    hops, which is not generally correct.

    Cycles are tolerated: reachability search tracks visited nodes, so it
    always terminates.
    """
    successors: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for index, (source, target) in enumerate(pairs):
        successors[source].append((target, index))

    def has_indirect_path(index: int, source: str, target: str) -> bool:
        visited = {source}
        stack = [node for node, i in successors[source] if i != index]
        while stack:
            node = stack.pop()
            if node == target:
                return True
            if node in visited:
                continue
            visited.add(node)
            stack.extend(n for n, _ in successors.get(node, ()))
        return False

    return [
        index
        for index, (source, target) in enumerate(pairs)
        if not has_indirect_path(index, source, target)
    ]
