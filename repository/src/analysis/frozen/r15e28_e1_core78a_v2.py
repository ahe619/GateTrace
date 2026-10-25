"""Pure E1 diagnostics. No file access, detector, tracker or application import.

Geometry reproduces the frozen r15e3 pure routines. Exact bipartite solver and
identity aggregation are supplied by the caller after code-hash verification.
"""
from collections import defaultdict
from fractions import Fraction
import math

UNKNOWN = {'insufficient_observations', 'unidentified', 'ambiguous', 'mixed_unknown'}


def valid_box(b):
    if len(b) != 4 or not all(math.isfinite(float(v)) for v in b) or b[2] <= b[0] or b[3] <= b[1]:
        raise ValueError('Invalid box')
    return tuple(float(v) for v in b)


def overlap(a, b):
    inter = max(0., min(a[2], b[2])-max(a[0], b[0])) * max(0., min(a[3], b[3])-max(a[1], b[1]))
    ad = (a[2]-a[0])*(a[3]-a[1]); ag = (b[2]-b[0])*(b[3]-b[1])
    return inter/(ad+ag-inter), inter/ad


def assign(pool, gt, solve, numpy):
    """Exact one-to-one max-cardinality/max-sum-IoU plus row margin."""
    if len({d['key'] for d in pool}) != len(pool):
        raise ValueError('Duplicate pool key')
    if len({g['gid'] for g in gt}) != len(gt):
        raise ValueError('Duplicate GT key')
    a = numpy.array([valid_box(d['box']) for d in pool], dtype='float64').reshape(-1, 4)
    b = numpy.array([valid_box(g['box']) for g in gt], dtype='float64').reshape(-1, 4)
    inter = numpy.maximum(0., numpy.minimum(a[:,None,2:],b[None,:,2:])-numpy.maximum(a[:,None,:2],b[None,:,:2])).prod(axis=2)
    ad = (a[:,2]-a[:,0])*(a[:,3]-a[:,1]); ag = (b[:,2]-b[:,0])*(b[:,3]-b[:,1])
    ious = inter / (ad[:,None]+ag[None,:]-inter)
    ioas = inter / ad[:,None]
    edges = [dict(left=pool[i]['key'], right=gt[j]['gid'], cost=-Fraction.from_float(float(ious[i,j])))
             for i,j in zip(*numpy.where(ious >= .5))]
    solution = solve([d['key'] for d in pool], [g['gid'] for g in gt], edges)
    pairs = dict(solution['pairs']); gi = {g['gid']:i for i,g in enumerate(gt)}
    records=[]; bygt={g['gid']:dict(any_iou=False, any_ioa=False, max_iou=0.,max_ioa=0.,strong=[],
                                  ambiguous=[],competition=[],containment=[]) for g in gt}
    assigned_g=set(pairs.values()); residual_edges=[]
    for i,d in enumerate(pool):
        gid=pairs.get(d['key']); j=gi.get(gid)
        score=float(ious[i,j]) if j is not None else None
        other=max((float(ious[i,k]) for k in range(len(gt)) if k!=j),default=0.)
        margin=score-other if score is not None else None
        strong=gid is not None and margin>=.10
        row=dict(key=d['key'],index=d['index'],tid=d.get('tid'),box=list(d['box']),
                 assigned_gid=gid,gt_id=gid if strong else None,
                 gt_class=gt[j]['cls'] if j is not None else None,
                 gt_line=gt[j]['gt_line'] if j is not None else None,
                 assigned_iou=score,second_best_iou=other,margin=margin,
                 status='valid' if strong else ('ambiguous' if gid is not None else 'unmatched'))
        records.append(row)
        if strong: bygt[gid]['strong'].append(row)
        elif gid is not None: bygt[gid]['ambiguous'].append(d['index'])
        for k,g in enumerate(gt):
            v=float(ious[i,k]); c=float(ioas[i,k]); z=bygt[g['gid']]
            z['max_iou']=max(z['max_iou'],v);z['max_ioa']=max(z['max_ioa'],c)
            if v>=.5:
                z['any_iou']=True
                if gid != g['gid']:z['competition'].append(d['index'])
            if c>=.8:
                z['any_ioa']=True;z['containment'].append(dict(index=d['index'],iou=v,ioa=c,assigned_gid=gid))
                if gid is None and g['gid'] not in assigned_g:
                    residual_edges.append((d['index'],g['gid']))
    dd=defaultdict(int);gg=defaultdict(int)
    for d,g in residual_edges:dd[d]+=1;gg[g]+=1
    residual=[dict(index=d,gid=g,unique_compatibility=(dd[d]==1 and gg[g]==1)) for d,g in residual_edges]
    audit=dict(pairs=[list(p) for p in solution['pairs']], cardinality=solution['cardinality'],
               exact_cost=str(solution['total_cost']),
               iou_edges=[dict(index=pool[i]['index'],gid=gt[j]['gid'],iou=float(ious[i,j]),gt_line=gt[j]['gt_line'])
                          for i,j in zip(*numpy.where(ious>=.5))],
               containment_edges=[dict(index=pool[i]['index'],gid=gt[j]['gid'],ioa=float(ioas[i,j]),gt_line=gt[j]['gt_line'])
                                   for i,j in zip(*numpy.where(ioas>=.8))], residual_containment=residual)
    return records,bygt,audit


def pools(frame, system):
    ds=frame['detections'];dets={int(d['raw_detection_index']):d for d in ds}
    if len(dets)!=len(ds):raise ValueError('Duplicate raw indices')
    for idx,d in dets.items():
        if idx!=d['raw_detection_index'] or not math.isfinite(d['confidence']):raise ValueError('Index/score invalid')
        valid_box(d['box'])
    if system=='O2':
        if frame['tracker_rows']:raise ValueError('O2 unexpectedly has tracker rows')
        if any(d['track_id']!=d['source_gt_id'] for d in ds):raise ValueError('O2 source identity mismatch')
        raw=[dict(key=i,index=i,tid=d['track_id'],box=d['box']) for i,d in sorted(dets.items())]
        return raw,raw,{i:r for i,r in zip(sorted(dets),raw)},dets
    threshold=.10 if system=='v11' else .25
    indices=[int(i) for i in frame['tracker_frame_metadata']['tracker_input_raw_indices']]
    eligible=[i for i,d in dets.items() if d['confidence']>=threshold]
    if len(set(indices))!=len(indices) or set(indices)!=set(eligible):raise ValueError('Actual input threshold differs')
    if any(d.get('tracking_eligible')!=(i in indices) for i,d in dets.items()):raise ValueError('tracking_eligible differs')
    out=[];mapping={};seen=set()
    for r in frame['tracker_rows']:
        if len(r)!=8:raise ValueError('Tracker row width')
        idx=int(r[7]);tid=int(r[4]);valid_box(r[:4])
        if idx!=r[7] or tid!=r[4] or idx not in indices or idx in mapping or tid in seen:raise ValueError('Output index/id relation')
        if dets[idx]['track_id']!=tid:raise ValueError('Output/detection ID differs')
        if system=='v11' and 'original_track_id' not in dets[idx]:raise ValueError('Missing M4 lineage')
        # Output boxes use the same raw-index tie order as admitted input boxes.
        row=dict(key=idx,index=idx,tid=tid,box=r[:4]);out.append(row);mapping[idx]=row;seen.add(tid)
    if any(d['track_id'] is not None and i not in mapping for i,d in dets.items()):raise ValueError('Unemitted detection has ID')
    raw=[dict(key=i,index=i,tid=mapping[i]['tid'] if i in mapping else None,box=dets[i]['box']) for i in sorted(indices)]
    return raw,sorted(out,key=lambda r:r['key']),mapping,dets


def signed_distance(point, vertices):
    # Same float64 rule as r15e3_regions_common; neither clipping nor epsilon change.
    x,y=point;best=math.inf
    for a,b in zip(vertices,vertices[1:]+vertices[:1]):
        dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
        if length==0:continue
        t=max(0.,min(1.,((x-a[0])*dx+(y-a[1])*dy)/(length*length)))
        best=min(best,math.hypot(x-(a[0]+t*dx),y-(a[1]+t*dy)))
    if best==math.inf:raise ValueError('Degenerate polygon')
    if best<=1e-9:return 0.
    inside=False
    for a,b in zip(vertices,vertices[1:]+vertices[:1]):
        if (a[1]>y)!=(b[1]>y) and x<a[0]+(y-a[1])*(b[0]-a[0])/(b[1]-a[1]):inside=not inside
    return best if inside else -best


def gt_zone(g, polygons, width, height):
    b=g['box']
    if b[0]<=0 or b[2]>=width-1 or b[3]>=height-1:return None
    p=[(b[0]+b[2])/2,b[3]]
    zs=[z for z,poly in polygons.items() if signed_distance(p,poly)>=-1e-9]
    if len(zs)>1:raise ValueError('Overlapping frozen regions')
    return zs[0] if zs else 'gap'


def fragments_from_points(points):
    tracks=defaultdict(list)
    for p in points:tracks[p['track_id']].append(p)
    fs=[];lookup={}
    for tid,obs in sorted(tracks.items()):
        previous=None;fi=-1;frag=None
        for o in obs:
            if previous is not None and o['frame']<=previous['frame']:raise ValueError('Point order or duplicate')
            reset=previous is None or o['time_s']-previous['time_s']>.5+1e-9
            if reset:
                if frag:fs.append(frag)
                fi+=1;frag=dict(track_id=tid,fragment_index=fi,first_frame=o['frame'],first_time_s=o['time_s'],last_frame=o['frame'],last_time_s=o['time_s'],raw_observations=0)
            frag['last_frame']=o['frame'];frag['last_time_s']=o['time_s'];frag['raw_observations']+=1
            lookup[(o['source_frame'],tid)]=(tid,fi);previous=o
        if frag:fs.append(frag)
    return fs,lookup


def legal(p,g):
    return p['direction']==g['direction'] and abs(p['source_frame']-g['frame'])<=25 and math.dist(p['crossing_position_native_px'],g['position'])<=g['h']+1e-9


def event_matching(preds, truths, solve, can_match):
    # Keys fixed from observable fields, not visibility. No annotation-dependent tie choice.
    pk=lambda i:(preds[i]['source_frame'],preds[i]['track_id'],int(preds[i]['prediction_id'][1:]),i)
    gk=lambda i:(truths[i]['frame'],truths[i]['gid'],i)
    left=[pk(i) for i in range(len(preds))];right=[gk(i) for i in range(len(truths))]
    li={x:i for i,x in enumerate(left)};ri={x:i for i,x in enumerate(right)}
    edges=[];anonymous=defaultdict(list);anonymous_edges=[]
    pred_records=[dict(prediction_index=i,matching_key=left[i],prediction_id=p['prediction_id'],
                       track_id=p['track_id'],fragment_index=p['fragment_index'],source_frame=p['source_frame'],
                       direction=p['direction'],position_native_px=p['crossing_position_native_px'],
                       identity=p['_identity']) for i,p in enumerate(preds)]
    for i,p in enumerate(preds):
        for j,g in enumerate(truths):
            if not legal(p,g):continue
            anonymous[j].append(i)
            ident=p['_identity']
            anonymous_edges.append(dict(prediction_index=i,prediction_id=p['prediction_id'],left=left[i],
                                        gt_index=j,gt_event_id=g['id'],right=right[j],
                                        time_cost=Fraction(abs(p['source_frame']-g['frame']),25),
                                        position_distance=math.dist(p['crossing_position_native_px'],g['position']),
                                        gt_height=g['h'],identity_status=ident['status'],identity_gid=ident.get('gid')))
            if ident['status']=='known' and ident['gid']==g['gid']:
                edges.append(dict(left=left[i],right=right[j],cost=Fraction(abs(p['source_frame']-g['frame']),25)))
    sol=solve(left,right,edges);matched={ri[g]:li[p] for p,g in sol['pairs']};ties={};membership=[]
    optimum=(sol['cardinality'],sol['total_cost'])
    for j in range(len(truths)):
        check=dict(gt_index=j,gt_event_id=truths[j]['id'],gt_key=right[j],canonical_matched=j in matched,
                   can_be_matched=j in matched,can_be_unmatched=j not in matched,
                   membership_tie=False,optimum_certificate=None)
        if j in matched:
            # Penalize this GT only after cardinality and exact time cost. A zero
            # penalty is a witness that the canonical matched GT may be absent.
            weights={(e['left'],e['right']):1 for e in edges if e['right']==right[j]}
            alt=solve(left,right,edges,secondary_weights=weights)
            if (alt['cardinality'],alt['total_cost'])!=optimum:raise AssertionError('Optimality changed')
            absent=all(r!=right[j] for _,r in alt['pairs'])
            if (alt['secondary_total']==0)!=absent:raise AssertionError('Membership penalty inconsistent')
            check.update(can_be_unmatched=absent,forced_matched=not absent)
            if absent:ties[j]=alt
        elif any(e['right']==right[j] for e in edges):
            alt=can_match(left,right,edges,right[j])
            if alt['possible']:
                if (alt['solution']['cardinality'],alt['solution']['total_cost'])!=optimum:raise AssertionError('Optimality changed')
                ties[j]=alt['solution']
                check['can_be_matched']=True
        if j in ties:check.update(membership_tie=True,optimum_certificate=ties[j])
        membership.append(check)
    return matched,ties,anonymous,dict(solution=sol,edges=edges,pred_keys=left,gt_keys=right,
                                      predictions=pred_records,anonymous_legal_edges=anonymous_edges,
                                      gt_membership_checks=membership)


def decode_family(g, coherent, saved, identities):
    raw=[e for e in saved['raw_candidates'] if (e['track_id'],e['fragment_index']) in coherent and abs(e['source_frame']-g['frame'])<=75]
    keys={e['prediction_id'] for e in raw};ref=dict(raw_candidate_ids=sorted(keys))
    final=[e for e in saved['final_events'] if keys.intersection(e.get('member_prediction_ids',[e['prediction_id']]))]
    confirmed=[e for e in saved['raw_confirmed_events'] if e['prediction_id'] in keys]
    ref['final_group_ids']=[e.get('group_id') for e in final]
    if final:
        f1=[e for e in final if e['direction']==g['direction']]
        f2=[e for e in f1 if abs(e['source_frame']-g['frame'])<=25]
        f3=[e for e in f2 if math.dist(e['crossing_position_native_px'],g['position'])<=g['h']+1e-9]
        if not f1:return 'WRONG_DIRECTION',ref
        if not f2:return 'TIME_OUTSIDE_1S',ref
        if not f3:return 'POSITION_OUTSIDE_HG',ref
        ids=[identities[e['prediction_id']] for e in f3];ref['legal_family_identities']=ids
        if any(i['status'] in UNKNOWN for i in ids):return 'U_IDENTITY',ref
        if any(i['status']=='known' and i['gid']==g['gid'] for i in ids):return 'MATCH_COMPETITION',ref
        return 'OUTPUT_IDENTITY_CONFLICT',ref
    if confirmed:
        groups=[gr for gr in saved['groups'] if keys.intersection(gr['member_prediction_ids'])]
        if not groups:raise ValueError('Confirmed candidate lacks R1 group')
        details={r['group_id']:r for r in saved['group_details']}
        if any(gr['group_id'] not in details for gr in groups):raise ValueError('Missing group detail')
        ref['groups']=[dict(group_id=gr['group_id'],keep=gr['keep'],decision=gr['decision'],r2_keep=details[gr['group_id']]['r2_keep']) for gr in groups]
        if all(not gr['keep'] and not details[gr['group_id']]['r2_keep'] for gr in groups):return 'R2_DROPPED',ref
        return 'MERGE_OR_OTHER_DECODER',ref
    if raw:
        if not all(e['confirmer']['keep'] is False for e in raw):raise ValueError('Unconfirmed candidate has C1 keep')
        ref['c1']=[dict(prediction_id=e['prediction_id'],confirmer=e['confirmer']) for e in raw]
        return 'C1_DROPPED',ref
    return 'NO_LOCAL_REGION_TRANSITION',ref


def attribute(g, evidence, matched, tie, anonymous_unknown, support, gtframes, polygons,
              width,height,fragment_lookup,outputobs,saved,identities):
    """All detection evidence is assembled before this precedence is applied."""
    if matched is not None:
        return 'RECOVERED',None,dict(matched_prediction_id=matched,matching_membership_tie=tie is not None,
                                    may_be_unmatched_in_equivalent_optimum=tie is not None,optimum_certificate=tie)
    if anonymous_unknown:return 'U_IDENTITY',None,dict(unknown_prediction_ids=anonymous_unknown)
    if tie:return 'U_MATCH_TIE',None,dict(optimum_certificate=tie)
    sf=evidence['gt_frames'];strong=[(f,r) for f in sf for r in support[f]['strong']]
    if not sf:return 'U_NO_GT_SUPPORT',None,{}
    if not any(support[f]['any_iou'] or support[f]['any_ioa'] for f in sf):return 'NO_COMPATIBLE_ADMITTED_DETECTION',None,{}
    if not strong:
        weak=any(support[f]['any_ioa'] or support[f]['ambiguous'] for f in sf)
        return ('U_GEOMETRY' if weak else 'U_DETECTION_COMPETITION'),None,{}
    emitted=[(f,r) for f,r in strong if r['tid'] is not None]
    if not emitted:return 'DETECTED_NOT_EMITTED',None,{}
    source,target=('tunnel','plaza') if g['direction']=='IN' else ('plaza','tunnel')
    zones={f:gt_zone(gtframes[f],polygons,width,height) for f in sf}
    S=[f for f in sf if f<g['frame'] and zones[f]==source];T=[f for f in sf if f>=g['frame'] and zones[f]==target]
    ref=dict(S=S,T=T,gt_zones=zones)
    if not S or not T:return 'U_SIDE_REFERENCE',None,ref
    sd=[(f,r) for f,r in strong if f in S];td=[(f,r) for f,r in strong if f in T]
    if not sd or not td:return 'U_ONE_SIDED_DETECTION',None,ref
    ss=defaultdict(list);ts=defaultdict(list)
    for dest,rows in ((ss,sd),(ts,td)):
        for f,r in rows:
            if r['tid'] is not None:
                if (f,r['tid']) not in fragment_lookup:raise ValueError('Emitted support lacks saved fragment')
                dest[fragment_lookup[f,r['tid']]].append(f)
    common=set(ss)&set(ts)
    ref['source_fragments']=[dict(key=list(k),frames=v) for k,v in sorted(ss.items())]
    ref['target_fragments']=[dict(key=list(k),frames=v) for k,v in sorted(ts.items())]
    if not common:
        sub='ONE_SIDE_NOT_EMITTED' if not ss or not ts else ('SAME_ID_DIFFERENT_FRAGMENT' if {k[0] for k in ss}&{k[0] for k in ts} else 'DIFFERENT_IDS')
        return 'TRACK_SIDE_CONNECTION_MISSING',sub,ref
    clean=set();conflicts=[]
    for k in sorted(common):
        lo,hi=max(ss[k]),min(ts[k]);bad=[o for o in outputobs[k[0]] if lo<=o['source_frame']<=hi and o['gt_id'] is not None and o['gt_class']==1 and o['gt_id']!=g['gid']]
        conflicts.append(dict(fragment=list(k),support_interval=[lo,hi],different_gt_observations=bad))
        if not bad:clean.add(k)
    ref['cross_side_checks']=conflicts
    if not clean:return 'U_MIXED_TRACK',None,ref
    sub,family=decode_family(g,clean,saved,identities);ref['family']=family
    return ('U_IDENTITY' if sub=='U_IDENTITY' else 'DECODING_OR_EVENT_LOCALIZATION'),sub,ref
