"""Verbatim frozen scientific functions; pure and no import-time I/O.
Source: scripts/r15_c1star_t3_matching75.py; software notice in package LICENSE_CODE.
"""
from collections.abc import Mapping
from fractions import Fraction
from heapq import heappop,heappush
from math import lcm


def _exact(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, Fraction)):
        raise ValueError(name + " must be int or Fraction; convert floats explicitly")
    return Fraction(value)


def _key(value):
    if type(value) is int:
        return value
    if (isinstance(value, tuple) and value
            and all(type(part) is int for part in value)):
        return value
    raise ValueError("Stable keys must be integers or nonempty tuples of integers")


def _keys(values, side):
    values = [_key(value) for value in values]
    if len(values) != len(set(values)):
        raise ValueError("Duplicate " + side + " key")
    try:
        return sorted(values)
    except TypeError as exc:
        raise ValueError("Keys on one side must have mutually comparable numeric types") from exc


def _prepare(left_keys, right_keys, edges, secondary_weights):
    left = _keys(left_keys, "left")
    right = _keys(right_keys, "right")
    left_set, right_set = set(left), set(right)
    by_pair = {}
    for edge in edges:
        if not isinstance(edge, Mapping):
            raise ValueError("Every edge must be a mapping")
        if not all(name in edge for name in ("left", "right", "cost")):
            raise ValueError("Every edge needs left, right, and cost")
        pair = (_key(edge["left"]), _key(edge["right"]))
        if pair[0] not in left_set or pair[1] not in right_set:
            raise ValueError("Edge endpoint is absent from its declared side")
        if pair in by_pair:
            raise ValueError("Duplicate edge")
        by_pair[pair] = _exact(edge["cost"], "Edge cost")
    weights = {} if secondary_weights is None else secondary_weights
    if not isinstance(weights, Mapping):
        raise ValueError("secondary_weights must map (left, right) to exact weight")
    if not set(weights).issubset(by_pair):
        raise ValueError("Secondary weight names an undeclared edge")
    secondary = {pair: _exact(weights.get(pair, 0), "Secondary weight")
                 for pair in by_pair}
    return left, right, by_pair, secondary


def _components(left, right, costs):
    """Return edge-bearing components; side tagging keeps equal keys distinct."""
    adjacent = {}
    for lkey, rkey in costs:
        ln, rn = (0, lkey), (1, rkey)
        adjacent.setdefault(ln, []).append(rn)
        adjacent.setdefault(rn, []).append(ln)
    seen = set()
    for root in [(0, key) for key in left] + [(1, key) for key in right]:
        if root in seen or root not in adjacent:
            continue
        seen.add(root)
        pending = [root]
        ls, rs = [], []
        while pending:
            node = pending.pop()
            (ls if node[0] == 0 else rs).append(node[1])
            for neighbour in adjacent[node]:
                if neighbour not in seen:
                    seen.add(neighbour)
                    pending.append(neighbour)
        ls.sort()
        rs.sort()
        pair_keys = sorted((lk, rn[1]) for lk in ls for rn in adjacent[(0, lk)])
        yield ls, rs, pair_keys


def _integer_scale(values):
    denominator = 1
    for value in values:
        denominator = lcm(denominator, value.denominator)
    return denominator


def _solve_component(left, right, pair_keys, costs, secondary):
    primary_den = _integer_scale(costs[pair] for pair in pair_keys)
    secondary_den = _integer_scale(secondary[pair] for pair in pair_keys)
    primary_int = {pair: int(costs[pair] * primary_den) for pair in pair_keys}
    secondary_int = {pair: int(secondary[pair] * secondary_den) for pair in pair_keys}
    max_pairs = min(len(left), len(right))
    max_secondary_abs = max(abs(value) for value in secondary_int.values())
    # For any two fixed-cardinality matchings, secondary-sum difference is
    # <= 2*K*max_abs. The total pair-bit reward differs by < 2**edge_count.
    # Consequently a one-integer primary improvement dominates every possible
    # lower-objective difference; secondary dominates the full tie range.
    primary_base = 2 * max_pairs * max_secondary_abs + 1
    tie_base = 1 << len(pair_keys)
    combined = {
        pair: (primary_int[pair] * primary_base + secondary_int[pair]) * tie_base
        - (1 << (len(pair_keys) - rank - 1))
        for rank, pair in enumerate(pair_keys)
    }
    source = 0
    left_node = {key: index + 1 for index, key in enumerate(left)}
    right_node = {key: index + 1 + len(left) for index, key in enumerate(right)}
    sink = 1 + len(left) + len(right)
    graph = [[] for _ in range(sink + 1)]

    def add_edge(start, end, cost):
        forward = [end, len(graph[end]), 1, cost]
        reverse = [start, len(graph[start]), 0, -cost]
        graph[start].append(forward)
        graph[end].append(reverse)
        return forward

    for key in left:
        add_edge(source, left_node[key], 0)
    for key in right:
        add_edge(right_node[key], sink, 0)
    links = [(pair, add_edge(left_node[pair[0]], right_node[pair[1]], combined[pair]))
             for pair in pair_keys]

    # Initial shortest distances in source -> left -> right -> sink DAG.
    potential = [0] * len(graph)
    incoming_min = {}
    for (_, rkey), value in combined.items():
        if rkey not in incoming_min or value < incoming_min[rkey]:
            incoming_min[rkey] = value
    for key in right:
        potential[right_node[key]] = incoming_min[key]
    potential[sink] = min(potential[right_node[key]] for key in right)

    while True:
        distance = [None] * len(graph)
        previous = [None] * len(graph)
        distance[source] = 0
        heap = [(0, source)]
        while heap:
            dist, node = heappop(heap)
            if distance[node] != dist:
                continue
            for edge_index, edge in enumerate(graph[node]):
                target, _, capacity, cost = edge
                if not capacity:
                    continue
                reduced = cost + potential[node] - potential[target]
                if reduced < 0:
                    raise AssertionError("Negative reduced cost violates exact potential invariant")
                proposal = dist + reduced
                if distance[target] is None or proposal < distance[target]:
                    distance[target] = proposal
                    previous[target] = (node, edge_index)
                    heappush(heap, (proposal, target))
        if distance[sink] is None:
            break
        for node, delta in enumerate(distance):
            if delta is not None:
                potential[node] += delta
        node = sink
        while node != source:
            prior, edge_index = previous[node]
            edge = graph[prior][edge_index]
            edge[2] -= 1
            graph[node][edge[1]][2] += 1
            node = prior
    return [pair for pair, edge in links if edge[2] == 0]


def solve(left_keys, right_keys, edges, secondary_weights=None):
    """Solve an explicitly eligible bipartite graph without any input I/O.

    Keys: mutually comparable stable ints or int tuples on each side. Edge rows
    require ``left``, ``right``, ``cost``; cost must be int/Fraction, never an
    implicitly rounded float. A missing edge is ineligible, not a large penalty.
    ``secondary_weights`` maps existing (left,right) pairs to exact weights;
    omitted entries have weight zero. Both primary and secondary are minimized.

    Cardinality is ALWAYS maximized first, even for positive costs. Optional
    secondary weights optimize only among equal-cardinality/equal-primary-cost
    solutions; they cannot trade time distance or IoU for a preferred label.

    Returns pairs (sorted numeric tuples), cardinality, Fraction total_cost,
    Fraction secondary_total, and the number of non-isolated graph components.
    Inputs are not mutated. Equal keys on opposite sides remain different nodes.
    """
    left, right, costs, secondary = _prepare(left_keys, right_keys, edges, secondary_weights)
    pairs = []
    component_count = 0
    for ls, rs, pair_keys in _components(left, right, costs):
        component_count += 1
        pairs.extend(_solve_component(ls, rs, pair_keys, costs, secondary))
    pairs.sort()
    return {
        "pairs": pairs,
        "cardinality": len(pairs),
        "total_cost": sum((costs[pair] for pair in pairs), Fraction(0)),
        "secondary_total": sum((secondary[pair] for pair in pairs), Fraction(0)),
        "component_count": component_count,
    }


def optimal_secondary_range(left_keys, right_keys, edges, weights):
    """Min/max weighted counts over ALL equal first-two-objective optima.

    For an assigned-other/unknown count supply 0/1 per eligible edge. This does
    not constrain the original canonical tie solution, so equivalent pairings
    are genuinely explored. Negative weights are supported as exact arithmetic.
    """
    left_keys, right_keys, edges = list(left_keys), list(right_keys), list(edges)
    minimum = solve(left_keys, right_keys, edges, weights)
    negative = {pair: -_exact(value, "Range weight") for pair, value in weights.items()}
    maximum = solve(left_keys, right_keys, edges, negative)
    if (minimum["cardinality"], minimum["total_cost"]) != (maximum["cardinality"], maximum["total_cost"]):
        raise AssertionError("Secondary objective changed a primary optimum")
    return {
        "minimum": minimum["secondary_total"],
        "maximum": -maximum["secondary_total"],
        "min_solution": minimum,
        "max_solution": maximum,
    }


def can_match_right_optimally(left_keys, right_keys, edges, right_key, eligible_left_keys=None):
    """Can a right node have a specified-type partner in an exact optimum?

    This is an existence query at the UNCHANGED maximum cardinality and minimum
    primary cost, not a forced match that is allowed to worsen either objective.
    ``eligible_left_keys`` can restrict partners to identity-compatible outputs.
    Returns possible plus a witness solution (which may instead witness no such
    match). An undeclared node or partner is an input error.
    """
    left_keys, right_keys, edges = list(left_keys), list(right_keys), list(edges)
    if right_key not in right_keys:
        raise ValueError("Requested right key is undeclared")
    allowed_left = set(left_keys) if eligible_left_keys is None else set(eligible_left_keys)
    if not allowed_left.issubset(left_keys):
        raise ValueError("Requested left partner is undeclared")
    weights = {(edge["left"], edge["right"]): -1 for edge in edges
               if edge["right"] == right_key and edge["left"] in allowed_left}
    result = solve(left_keys, right_keys, edges, weights)
    return {"possible": result["secondary_total"] == -1, "solution": result}
