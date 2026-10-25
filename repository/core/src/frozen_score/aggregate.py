"""Verbatim frozen scientific functions; pure and no import-time I/O.
Source: scripts/r15_offshelf82e_score.py; software notice in package LICENSE_CODE.
"""
from fractions import Fraction
import collections
BINS=('low','mid_low','mid_high','high')
UNKNOWN={'insufficient_observations','unidentified','ambiguous','mixed_unknown'}


def aggregate(rows):
    num = sum(r['correct'] for r in rows)
    den = sum(r['N_final'] for r in rows)
    states = collections.Counter()
    for r in rows:
        states.update(r['identity_statuses'])
    if sum(states.values()) != den:
        raise ValueError('Identity states do not partition ALL-final denominator')
    ans = dict(correct=num, GT=sum(r['N_GT'] for r in rows), final_events=den,
               identity_precision=dict(numerator=num, denominator=den,
                   exact=Fraction(num, den) if den else None, value=num / den if den else None),
               identity_statuses=dict(states),
               unknown_or_ambiguous=sum(states[k] for k in UNKNOWN),
               bins={b: dict(numerator=sum(r['bins'][b]['correct'] for r in rows),
                             denominator=sum(r['bins'][b]['GT'] for r in rows)) for b in BINS})
    for row in ans['bins'].values():
        n, d = row['numerator'], row['denominator']
        row.update(exact=Fraction(n, d) if d else None, value=n / d if d else None)
    if rows and 'N_clean' in rows[0]:
        clean = sum(r['N_clean'] for r in rows)
        ans['legacy_T3_clean_precision_only'] = dict(numerator=num, denominator=clean,
            exact=Fraction(num, clean) if clean else None)
        ans['removed_from_legacy_clean_only'] = dict(
            ignore=sum(r['ignore'] for r in rows), neutral=sum(r['neutral'] for r in rows))
    return ans
