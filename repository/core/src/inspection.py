"""Evidence presentation over frozen labels and frozen scorer audits; no I/O on import.

This module never creates a matching edge, changes an identity, or interpolates
a point. Statuses are projections of the frozen E1 v2 matching audit.
"""
from collections import defaultdict
import gzip
import hashlib
import json
import math
from pathlib import Path

from . import frozen_labels_census as census
from . import frozen_labels_regions as regions
from .frozen_events.point import point_for
from .motchallenge import parse_results
from .audit_integrity import validate_frame_identity
from .evidence_seal import load_evidence_bindings, safe_evidence_path
from .image_paths import resolve_image_inputs

SEQS = ('MOT20-01', 'MOT20-02')
BINS = ('low', 'mid_low', 'mid_high', 'high')


def visibility_bin(value):
    if value is None:
        return None
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError('Visibility outside [0,1]')
    return BINS[min(3, int(value * 4))]


def canonical_rows(transitions, audits):
    """Read, do not solve, the complete global-per-gate canonical assignment."""
    expected = {r['event_id']: r for r in transitions if r['confirmed']}
    if len(expected) != sum(bool(r['confirmed']) for r in transitions):
        raise ValueError('Duplicate confirmed event ID')
    rows = {}
    for seq, gates in audits.items():
        for gate in gates:
            pred = {tuple(p['matching_key']): p for p in gate['predictions']}
            if len(pred) != len(gate['predictions']):
                raise ValueError('Duplicate prediction key')
            pairing = {}
            used_predictions = set()
            for pk, gk in gate['solution']['pairs']:
                if tuple(gk) in pairing or tuple(pk) not in pred or tuple(pk) in used_predictions:
                    raise ValueError('Invalid canonical pairs')
                used_predictions.add(tuple(pk))
                pairing[tuple(gk)] = pred[tuple(pk)]
            if len(pairing) != gate['solution']['cardinality']:
                raise ValueError('Canonical cardinality mismatch')
            for m in gate['gt_membership_checks']:
                eid = m['gt_event_id']
                if eid in rows or eid not in expected:
                    raise ValueError('Duplicate/unrecognized GT membership')
                truth = expected[eid]
                if truth['sequence'] != seq or truth['line_id'] != gate['gate']:
                    raise ValueError('Membership scope differs')
                p = pairing.get(tuple(m['gt_key']))
                found = p is not None
                if found != m['canonical_matched']:
                    raise ValueError('Pair and membership disagree')
                if list(m['gt_key'][:2]) != [truth['gt_frame_1based'], truth['track_id']]:
                    raise ValueError('GT matching key differs from label')
                rows[eid] = dict(event_id=eid, sequence=seq, gate_id=gate['gate'],
                    gt_id=truth['track_id'], direction=truth['direction'],
                    source_frame_1based=truth['gt_frame_1based'],
                    event_visibility_mean=truth['attributes']['mean_visibility'],
                    event_visibility_bin=truth['attributes']['visibility_bin'],
                    found=found, system_event=p, membership=m)
    if set(rows) != set(expected):
        raise ValueError('Audit is incomplete for confirmed label population')
    return [rows[k] for k in sorted(rows)]


def region_of(point, polygons):
    if point is None:
        return 'invalid_point'
    distances = {z: regions.signed_distance(point, poly) for z, poly in polygons.items()}
    return regions.zone_from_distances(distances, 0)


def valid_support(observations, event, polygons, width, height):
    """Display identity-valid output observations in a fixed +/-25-frame window.

Spatial zones and temporal pre/post are separate; neither is a visibility claim.
"""
    anchor, gid = event['gt_frame_1based'], event['track_id']
    qualified = []
    for o in observations:
        if not anchor - 25 <= o['source_frame'] <= anchor + 25:
            continue
        if o['status'] != 'valid' or o['gt_id'] != gid:
            continue
        p, reason, outside = point_for(o['box'], width, height)
        qualified.append(dict(o, point_native_px=p, point_invalid_reason=reason,
                              region=region_of(p, polygons), point_outside_image=outside))
    source = event['frozen_transition']['source_zone']
    target = event['frozen_transition']['target_zone']
    def summary(obs):
        frames = sorted({o['source_frame'] for o in obs})
        return dict(observation_count=len(obs), frame_count=len(frames), source_frames_1based=frames)
    zones = {z: summary([o for o in qualified if o['region'] == z])
             for z in ('tunnel', 'plaza', 'gap', 'invalid_point')}
    missing = [side for side, zone in (('source', source), ('target', target))
               if zones[zone]['frame_count'] == 0]
    return dict(window_gt_frames_inclusive=[anchor-25, anchor+25],
        identity_valid_definition='Frozen E1 v2 frame status=valid and gt_id equals target GT person',
        spatial_source_zone=source, spatial_target_zone=target, spatial_regions=zones,
        temporal_before=summary([o for o in qualified if o['source_frame'] < anchor]),
        temporal_at_or_after=summary([o for o in qualified if o['source_frame'] >= anchor]),
        missing_spatial_sides=missing, observations=qualified,
        interpretation='Missing means no identity-valid output point in that spatial region inside this window; it is not visual invisibility or a causal diagnosis.')


class Inspector:
    """A read-only view of verified local data and a freshly frozen-scored run.

The caller verifies the package manifest. Supplied score_dir must come from
src.tracker_score.score_tracks; all source and scientific-code bindings are
rechecked. Audits are recorded in the read ledger, never imported as code.
"""
    def __init__(self, package, gt_files, track_files=None, score_dir=None,
                 read_ledger=None, evidence_manifest_sha256=None):
        # Keep the caller's list even when construction fails partway through.
        self.reads = [] if read_ledger is None else read_ledger
        if not isinstance(self.reads, list):
            raise TypeError('read_ledger must be a list')
        self.package = Path(package).resolve()
        if set(gt_files) != set(SEQS):
            raise ValueError('Exactly development GT maps required')
        if (track_files is None) != (score_dir is None):
            raise ValueError('Tracks and frozen scoring evidence must be supplied together')
        self.summary = self.jread(self.package/'labels/summary.json', 'labels:summary')
        self.transitions = self.gzread(self.package/'labels/transitions.jsonl.gz', 'labels:transitions')
        self.labels = {r['event_id']: r for r in self.transitions}
        if len(self.labels) != len(self.transitions) or any(r['sequence'] not in SEQS for r in self.transitions):
            raise ValueError('Duplicate or out-of-scope label')
        self.geometry = {(r['sequence'], r['line_id']): r for r in
            self.jread(self.package/'labels/geometry.json', 'labels:geometry')['lines']}
        self.gt = {}
        self.frames = {}
        self.frame_identity = {}
        self.audits = {}
        self.frame_integrity = {}
        self.evidence_manifest_sha256 = evidence_manifest_sha256
        self.score_dir = None if score_dir is None else Path(score_dir).resolve()
        if score_dir is not None:
            if set(track_files) != set(SEQS):
                raise ValueError('Exactly development tracks required')
            package_manifest = self.read(self.package/'MANIFEST.json', 'package:manifest')
            evidence_bindings = load_evidence_bindings(
                self.score_dir, evidence_manifest_sha256, self.read,
                hashlib.sha256(package_manifest).hexdigest())
            receipt = self.jread(safe_evidence_path(self.score_dir, 'complete.json'),
                                 'score:complete', evidence_bindings['complete.json'])
            if receipt['status'] != 'COMPLETE':
                raise ValueError('Frozen scoring evidence is not complete')
            bindings = self.jread(safe_evidence_path(self.score_dir, 'read_ledger.json'),
                                  'score:read_ledger', evidence_bindings['read_ledger.json'])
            byalias = {b['path']:b for b in bindings}
            if len(byalias) != len(bindings):
                raise ValueError('Duplicate frozen scoring input binding')
            for b in bindings:
                if b['path'].startswith('code:'):
                    rel = b['path'][5:]
                    if not rel.startswith('src/'):
                        rel = 'src/' + rel
                    p = (self.package/rel).resolve()
                    if not p.is_relative_to(self.package):
                        raise ValueError('Escaping scientific code binding')
                    self.read(p, b['path'], b)
        for seq in SEQS:
            meta = self.summary['sequences'][seq]['metadata']
            gt_binding = dict(sha256=census.EXPECTED_INPUTS[seq]['gt'])
            if score_dir is not None:
                b = byalias['gt:'+seq]
                if b['sha256'] != gt_binding['sha256']:
                    raise ValueError('Scoring GT binding differs from fixed development source')
                gt_binding['bytes'] = b['bytes']
            raw = self.read(gt_files[seq], 'gt:'+seq, gt_binding)
            rows, _, _ = census.parse_gt(raw, meta)
            self.gt[seq] = defaultdict(list)
            for r in rows:
                self.gt[seq][r.track_id].append(r)
            if score_dir is not None:
                traw = self.read(track_files[seq], 'tracks:'+seq, byalias['tracks:'+seq])
                self.frames[seq], _ = parse_results(traw.decode('utf-8-sig'), meta['seqLength'])
                match_name = seq+'_event_matching.json'
                frame_name = seq+'_frame_identity.jsonl.gz'
                self.audits[seq] = self.jread(safe_evidence_path(self.score_dir, match_name),
                    'score:'+seq+':matching', evidence_bindings[match_name])
                self.frame_identity[seq] = self.gzread(safe_evidence_path(self.score_dir, frame_name),
                    'score:'+seq+':frame_identity', evidence_bindings[frame_name])
                self.frame_integrity[seq] = validate_frame_identity(
                    self.frame_identity[seq], self.frames[seq], meta['seqLength'])
        self.statuses = {} if score_dir is None else {
            r['event_id']:r for r in canonical_rows(self.transitions, self.audits)}

    def read(self, path, alias, binding=None):
        try:
            raw = Path(path).read_bytes()
        except BaseException as exc:
            self.reads.append(dict(asset=alias, read_status='READ_ERROR', error=repr(exc)))
            raise
        row = dict(asset=alias, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(),
                   read_status='READ')
        if binding:
            for key in ('bytes', 'sha256'):
                if key in binding:
                    row['expected_'+key] = binding[key]
            row['binding_status'] = ('MISMATCH' if any(row[k] != binding[k]
                for k in ('bytes', 'sha256') if k in binding) else 'MATCH')
        self.reads.append(row)
        if row.get('binding_status') == 'MISMATCH':
            raise ValueError('Bound input changed: '+alias)
        return raw

    def jread(self, path, alias, binding=None):
        return json.loads(self.read(path, alias, binding).decode('utf-8'))

    def gzread(self, path, alias, binding=None):
        return [json.loads(x) for x in gzip.decompress(self.read(path, alias, binding)).splitlines() if x.strip()]

    def list_events(self, bin_name='all', misses_only=True):
        if not self.statuses:
            raise ValueError('List mode requires tracker scoring evidence')
        if bin_name not in ('all',)+BINS:
            raise ValueError('Unknown visibility bin')
        return [dict(event_id=r['event_id'], sequence=r['sequence'], gate_id=r['gate_id'],
                     gt_id=r['gt_id'], source_frame_1based=r['source_frame_1based'],
                     direction=r['direction'], event_visibility_bin=r['event_visibility_bin'], found=r['found'],
                     system_prediction_id=None if r['system_event'] is None else r['system_event']['prediction_id'],
                     membership_tie=r['membership']['membership_tie'])
                for _,r in sorted(self.statuses.items())
                if (bin_name=='all' or r['event_visibility_bin']==bin_name) and (not misses_only or not r['found'])]

    def detail(self, event_id):
        if event_id not in self.labels:
            raise ValueError('Unknown derived event ID')
        e = self.labels[event_id]
        seq, anchor = e['sequence'], e['gt_frame_1based']
        meta = self.summary['sequences'][seq]['metadata']
        geo = self.geometry[seq,e['line_id']]
        byframe = {r.frame:r for r in self.gt[seq][e['track_id']]}
        vis = []
        for f in range(max(1,anchor-25), min(meta['seqLength'],anchor+25)+1):
            r = byframe.get(f)
            vis.append(dict(source_frame_1based=f, present=r is not None,
                visibility=None if r is None else r.visibility,
                instantaneous_visibility_bin=None if r is None else visibility_bin(r.visibility),
                gt_physical_line=None if r is None else r.source_line))
        api = dict(signed_distance=regions.signed_distance, zone_from_distances=regions.zone_from_distances)
        runs = []
        for f, r in sorted(byframe.items()):
            obs = census.observation(r,meta,geo['polygons'],api)
            zone = region_of(obs['point'], geo['polygons'])
            if runs and runs[-1]['region']==zone and runs[-1]['last_observed_frame_1based']==f-1:
                runs[-1].update(last_observed_frame_1based=f, last_point=obs['point'], last_gt_line=r.source_line)
                runs[-1]['observed_frames'] += 1
            else:
                runs.append(dict(region=zone, first_observed_frame_1based=f,last_observed_frame_1based=f,
                    first_point=obs['point'],last_point=obs['point'],first_gt_line=r.source_line,
                    last_gt_line=r.source_line,observed_frames=1))
        conf = e['confirmation']
        reason = ('A valid observed target-region point reaches the frozen 0.2 own-GT-height depth within 2 s.'
                  if e['confirmed'] else 'No qualifying observed target-depth point in the frozen confirmation window; not a human judgment.')
        out = dict(schema='crossing_event_inspection_v0_2', event_id=event_id,
            reference_label=e, geometry=geo, source_manifest=e['audit']['source_gt_asset'],
            crossing_frame_semantics=e['audit']['event_time_semantics'],
            source_target_support=e['frozen_transition']['endpoints'],
            observed_region_runs=runs,
            region_runs_semantics='First/last observed frames in consecutive same-zone runs; no interpolated physical entry/exit time.',
            visibility_window=vis,event_visibility_mean=e['attributes']['mean_visibility'],
            event_visibility_bin=e['attributes']['visibility_bin'],
            confirmation_status=e['confirmed'],confirmation_reason=reason,confirmation_evidence=conf,
            human_qc='not_reviewed', system_evidence=None)
        if not self.statuses:
            return out
        if not e['confirmed']:
            out['system_evidence'] = dict(status='NOT_IN_CONFIRMED_DENOMINATOR', found=None)
            return out
        status = self.statuses[event_id]
        gate = next(g for g in self.audits[seq] if g['gate']==e['line_id'])
        nearby = [p for p in gate['predictions'] if abs(p['source_frame']-anchor)<=50]
        relevant = [o for frame in self.frame_identity[seq] if abs(frame['source_frame']-anchor)<=25
                    for o in frame['observations']]
        evidence = dict(found=status['found'], membership=status['membership'],
            same_gate_events_within_two_seconds=nearby,
            same_gate_events_scope='All final events, every identity status and direction, inclusive +/-50 frames.',
            anonymous_legal_edges=[x for x in gate['anonymous_legal_edges'] if x['gt_event_id']==event_id],
            identity_valid_output_support=valid_support(relevant,e,geo['polygons'],meta['width'],meta['height']),
            matched_system_event=status['system_event'])
        p = status['system_event']
        if p is not None:
            pf = p['source_frame']
            evidence.update(time_difference_s=(pf-anchor)/25,
                absolute_time_difference_s=abs(pf-anchor)/25,
                position_distance_px=math.dist(p['position_native_px'],e['position_native_px']),
                identity_vote_observations=[o for fr in self.frame_identity[seq] if abs(fr['source_frame']-pf)<=25
                    for o in fr['observations'] if o['track_id']==p['track_id']])
        out['system_evidence'] = evidence
        return out


def render_event(inspector, detail, image_dir, output_dir):
    """Optional existing Pillow backend; images never enter the package."""
    from PIL import Image, ImageDraw, ImageFont
    seq = detail['reference_label']['sequence']
    e=detail['reference_label']; anchor=e['gt_frame_1based']
    meta=inspector.summary['sequences'][seq]['metadata']
    frames=sorted({max(1,min(meta['seqLength'],anchor+d)) for d in (-25,-12,0,12,25)})
    image_dir, candidates = resolve_image_inputs(image_dir, seq, frames)
    out = Path(output_dir).resolve()
    if out.exists() or out.is_relative_to(inspector.package) or out.is_relative_to(image_dir):
        raise ValueError('Render output must be a new directory outside package/source images')
    out.mkdir(parents=True,exist_ok=False)
    gt={r.frame:r for r in inspector.gt[seq][e['track_id']]}
    receipt=[]
    for f,p in zip(frames,candidates):
        raw=inspector.read(p,f'image:{seq}:{f}')
        import io
        with Image.open(io.BytesIO(raw)) as source:
            im=source.convert('RGB')
        if im.size!=(meta['width'],meta['height']):
            raise ValueError('Image dimensions differ from sequence metadata')
        draw=ImageDraw.Draw(im); font=ImageFont.load_default(size=18)
        for zone,poly in detail['geometry']['polygons'].items():
            color=(255,190,30) if zone=='plaza' else (200,60,255)
            xy=[tuple(x) for x in poly]
            draw.line(xy+[xy[0]],fill=color,width=3)
            draw.line(xy[:2],fill=color,width=5)
        geo=detail['geometry'];c=geo['line_coordinate_px'];lo,hi=geo['line_extent_px']
        center=[(lo,c),(hi,c)] if geo['orientation']=='H' else [(c,lo),(c,hi)]
        draw.line(center,fill=(255,255,255),width=3)
        for r in inspector.frames.get(seq,{}).get(f,[]):
            draw.rectangle(tuple(r['box']),outline=(40,150,255),width=2)
        if f in gt:
            r=gt[f]; draw.rectangle((r.x0,r.y0,r.x1,r.y1),outline=(0,255,100),width=4)
            draw.text((max(0,r.x0),max(42,r.y0-24)),f'GT {r.track_id}',font=font,fill=(0,255,100),stroke_width=2,stroke_fill=(0,0,0))
        text=f'{seq} | {e["event_id"]} | frame {f} | GT green, system blue, gate white | entry {anchor}'
        draw.rectangle((0,0,im.width,36),fill=(0,0,0));draw.text((8,8),text,font=font,fill=(255,255,255))
        target=out/f'frame_{f:06d}.png';im.save(target)
        receipt.append(dict(source_frame_1based=f,input_sha256=hashlib.sha256(raw).hexdigest(),
            output_file=target.name,output_sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
    (out/'render_manifest.json').write_text(json.dumps(dict(sequence=seq,event_id=e['event_id'],frames=receipt,
        no_matching_outcome_drawn=True,original_media_not_redistributed=True),indent=2)+'\n',encoding='utf-8')
    return receipt
