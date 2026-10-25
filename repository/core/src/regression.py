"""Compare a score_tracker result with a bundled panel expectation (v0.1 self-test).

Integers, strings and identifiers are compared exactly. Crossing positions are
compared numerically only to report the effect of the MOTChallenge +1/-1
coordinate round trip; the bound is fixed in PROTOCOL.md. Import has no I/O.
"""
from __future__ import annotations

SEQS = ('MOT20-01', 'MOT20-02')
GATES = ('H_30', 'H_50', 'H_70', 'V_25', 'V_50', 'V_75')
BINS = ('low', 'mid_low', 'mid_high', 'high')
EVENT_KEYS = ('prediction_id', 'track_id', 'fragment_index', 'direction', 'source_frame', 'target_frame',
              'group_id', 'member_prediction_ids')


def compare(expected, report, units, events):
    agg = report['main']['aggregate']
    primary = expected['primary']
    observed_primary = dict(bins={b: [agg['bins'][b]['numerator'], agg['bins'][b]['denominator']] for b in BINS},
                            matched=agg['correct'], final_events=agg['final_events'])
    checks = dict(
        R1_primary_bins_and_precision=observed_primary == primary,
        R2_main_aggregate_equal=report['main']['aggregate'] == expected['main']['aggregate'],
        R2_by_sequence_equal=report['main']['by_sequence'] == expected['main']['by_sequence'],
        R2_gate_units_equal=units == expected['units'])
    mismatches = []
    if not checks['R2_gate_units_equal']:
        exp = {(u['sequence'], u['gate']): u for u in expected['units']}
        for u in units:
            if exp.get((u['sequence'], u['gate'])) != u:
                mismatches.append(dict(kind='unit', sequence=u['sequence'], gate=u['gate'],
                                       observed=u, expected=exp.get((u['sequence'], u['gate']))))
    tolerance = expected['position_tolerance_px']
    max_diff = 0.
    compared = 0
    counts_equal = lists_equal = True
    for seq in SEQS:
        for gate in GATES:
            o = events[seq][gate]
            e = expected['final_events'][seq][gate]
            for key in ('candidates', 'confirmed', 'final'):
                if o[key] != e[key]:
                    counts_equal = False
                    mismatches.append(dict(kind='count', sequence=seq, gate=gate, field=key, observed=o[key], expected=e[key]))
            if len(o['final_events']) != len(e['final_events']):
                lists_equal = False
                continue
            for i, (a, b) in enumerate(zip(o['final_events'], e['final_events'])):
                if any(a[k] != b[k] for k in EVENT_KEYS):
                    lists_equal = False
                    mismatches.append(dict(kind='event', sequence=seq, gate=gate, index=i,
                                           observed={k: a[k] for k in EVENT_KEYS}, expected={k: b[k] for k in EVENT_KEYS}))
                    continue
                pa, pb = a['crossing_position_native_px'], b['crossing_position_native_px']
                max_diff = max(max_diff, abs(pa[0] - pb[0]), abs(pa[1] - pb[1]))
                compared += 1
    checks['R3_event_counts_equal'] = counts_equal
    checks['R3_final_event_lists_equal'] = lists_equal
    checks['R3_position_difference_within_round_trip_bound'] = max_diff <= tolerance
    return dict(status='PASS' if all(checks.values()) else 'FAIL', checks=checks,
                observed_primary=observed_primary, expected_primary=primary,
                final_events_compared=compared, crossing_position_max_abs_diff_px=max_diff,
                position_bound_px=tolerance, mismatches=mismatches[:200], mismatch_count=len(mismatches))
