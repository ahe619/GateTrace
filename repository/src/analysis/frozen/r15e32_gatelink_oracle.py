"""e32 GateLink oracle (protocol docs/e32_gatelink_oracle_protocol_v1.md, sha 5313edb1...).
Transforms MOTChallenge tracker outputs into O0 / O-bridge / O-link variants. Scoring is done separately with the
unchanged release v0.1 score_tracker.py. Development MOT20-01/02 only. Writes under data/r15/e32_gatelink_oracle/."""
import collections, gzip, hashlib, json, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_SHA = '5313edb10ebaddd0950fc3756dc4dd15b00fddec72401895141529c0c28d4afe'
PANEL = ROOT / 'release/mot20_crossing_events_v0_1/examples/panel'
IDENT = ROOT / 'data/r15/release_v0_1_build/runs/selftest_with_report_040428'
OUT = ROOT / 'data/r15/e32_gatelink_oracle'
SEQS = ('MOT20-01', 'MOT20-02'); TRACKERS = ('byte', 'oc', 'bot')
K = 25


def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def read_mot(p):
    rows = []
    for line in open(p, encoding='utf-8'):
        f = line.rstrip('\n').split(',')
        rows.append([int(f[0]), int(f[1]), float(f[2]), float(f[3]), float(f[4]), float(f[5]), float(f[6])])
    return rows


def write_mot(p, rows):
    rows = sorted(rows, key=lambda r: (r[0], r[1]))
    with open(p, 'x', encoding='utf-8') as fo:
        for r in rows:
            fo.write(f"{r[0]},{r[1]},{r[2]!r},{r[3]!r},{r[4]!r},{r[5]!r},{r[6]!r},-1,-1,-1\n")


def identities(tracker, seq):
    """(frame, track_id) -> gt_id for status=valid observations."""
    m = {}
    with gzip.open(IDENT / tracker / f'{seq}_frame_identity.jsonl.gz', 'rt', encoding='utf-8') as f:
        for line in f:
            d = json.loads(line)
            for o in d['observations']:
                if o.get('status') == 'valid' and o.get('gt_id') is not None:
                    m[(o['source_frame'], o['track_id'])] = o['gt_id']
    return m


def vote(ids):
    ids = [i for i in ids if i is not None]
    if len(ids) < 3: return None
    c = collections.Counter(ids).most_common()
    if len(c) > 1 and c[0][1] == c[1][1]: return None
    return c[0][0] if c[0][1] * 2 >= len(ids) else None


def bridge_same_id(rows, G):
    by = collections.defaultdict(list)
    for r in rows: by[r[1]].append(r)
    out = list(rows); added = 0
    for tid, rs in by.items():
        rs.sort(key=lambda r: r[0])
        for a, b in zip(rs, rs[1:]):
            gap = b[0] - a[0]
            if 1 < gap <= G:
                for f in range(a[0] + 1, b[0]):
                    w = (f - a[0]) / gap
                    out.append([f, tid] + [a[k] + w * (b[k] - a[k]) for k in (2, 3, 4, 5)] + [1.0]); added += 1
    return out, added


def oracle_link(rows, idmap, G):
    by = collections.defaultdict(list)
    for r in rows: by[r[1]].append(r)
    for rs in by.values(): rs.sort(key=lambda r: r[0])
    info = {}
    for tid, rs in by.items():
        valid = [idmap.get((r[0], tid)) for r in rs]
        vv = [(r[0], g) for r, g in zip(rs, valid) if g is not None]
        info[tid] = dict(start=rs[0][0], end=rs[-1][0], first=rs[0], last=rs[-1],
                         sid=vote([g for _, g in vv[:K]]), eid=vote([g for _, g in vv[-K:]]))
    cands = []
    for a, ia in info.items():
        if ia['eid'] is None: continue
        for b, ib in info.items():
            if a == b or ib['sid'] is None: continue
            gap = ib['start'] - ia['end']
            if 0 < gap <= G and ia['eid'] == ib['sid']:
                cands.append((gap, a, b))
    cands.sort()
    used_end, used_start, nxt = set(), set(), {}
    for gap, a, b in cands:
        if a in used_end or b in used_start: continue
        used_end.add(a); used_start.add(b); nxt[a] = b
    prev = {b: a for a, b in nxt.items()}
    root = {}
    for tid in info:
        r = tid
        while r in prev: r = prev[r]
        root[tid] = r
    out = [[r[0], root[r[1]]] + r[2:] for r in rows]; added = 0
    for a, b in nxt.items():
        la, fb = info[a]['last'], info[b]['first']; gap = fb[0] - la[0]
        for f in range(la[0] + 1, fb[0]):
            w = (f - la[0]) / gap
            out.append([f, root[a]] + [la[k] + w * (fb[k] - la[k]) for k in (2, 3, 4, 5)] + [1.0]); added += 1
    return out, len(nxt), added


def main():
    assert sha(ROOT / 'docs/e32_gatelink_oracle_protocol_v1.md') == PROTOCOL_SHA, 'protocol changed'
    log = {}
    for G in (50, 125):
        for tr in TRACKERS:
            for variant in (['O0'] if G == 50 else []) + ['O-bridge', 'O-link']:
                d = OUT / f'G{G}' / variant / tr; d.mkdir(parents=True, exist_ok=False)
                for seq in SEQS:
                    rows = read_mot(PANEL / tr / f'{seq}.txt')
                    stats = dict(input_rows=len(rows))
                    if variant == 'O0':
                        out = rows
                    elif variant == 'O-bridge':
                        out, stats['bridged_rows'] = bridge_same_id(rows, G)
                    else:
                        b, stats['bridged_rows'] = bridge_same_id(rows, G)
                        out, stats['links'], stats['link_rows'] = oracle_link(b, identities(tr, seq), G)
                    keys = collections.Counter((r[0], r[1]) for r in out)
                    assert max(keys.values()) == 1, 'duplicate (frame,id)'
                    write_mot(d / f'{seq}.txt', out); stats['output_rows'] = len(out)
                    stats['sha256'] = sha(d / f'{seq}.txt')
                    log[f'G{G}/{variant}/{tr}/{seq}'] = stats
                    print(f'G{G} {variant} {tr} {seq}', stats, flush=True)
    json.dump(log, open(OUT / 'transform_log.json', 'x'), indent=1)


if __name__ == '__main__':
    main()
