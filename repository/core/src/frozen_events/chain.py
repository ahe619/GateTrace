"""Verbatim frozen event-chain members; pure and no import-time data I/O.
Sources: the members compiled by scripts/r15e24_events.py::load_frozen, in its order;
software notice in package LICENSE_CODE. The module namespace mirrors load_frozen:
math, defaultdict, Counter, deepcopy and np (NumPy) plus the copied members.
"""
import math
from collections import defaultdict, Counter
from copy import deepcopy
import numpy as np


def nearest_boundary(point,vertices):
    x,y=map(float,point);best=None;arc=0.
    for i,(a,b) in enumerate(zip(vertices,vertices[1:]+vertices[:1])):
        dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
        if length==0:continue
        t=max(0.,min(1.,((x-a[0])*dx+(y-a[1])*dy)/(length*length)))
        q=[a[0]+t*dx,a[1]+t*dy];distance=math.hypot(x-q[0],y-q[1])
        item=dict(distance=distance,edge_index=i,edge_fraction=t,nearest_xy=q,
            arc_px=arc+t*length)
        if best is None or distance<best['distance']:best=item
        arc+=length
    if best is None:raise ValueError('Degenerate polygon')
    best['perimeter_px']=arc
    return best


def signed_distance(point,vertices):
    nearest=nearest_boundary(point,vertices)
    if nearest['distance']<=1e-9:return 0.
    x,y=point;inside=False
    for a,b in zip(vertices,vertices[1:]+vertices[:1]):
        if (a[1]>y)!=(b[1]>y) and x<a[0]+(y-a[1])*(b[0]-a[0])/(b[1]-a[1]):
            inside=not inside
    return nearest['distance'] if inside else -nearest['distance']


def zone_from_distances(distances,margin):
    zones=[k for k,v in distances.items() if v is not None and v>=margin-1e-9]
    if len(zones)>1:raise ValueError('Overlapping declared regions')
    return zones[0] if zones else 'gap'


def extract_region_events(observations,margin,max_gap_s=.5):
    """Only raw-ID absence > gap resets; point=None is excluded for this frame.

    Event time is first observed target-region entry, not interpolation over
    the unobserved region gap. Repeated transitions are retained without cooldown.
    """
    tracks=defaultdict(list)
    for o in observations:
        if o['track_id'] is not None:tracks[o['track_id']].append(o)
    result=[];fragments=[];stats=Counter()
    for tid,obs in sorted(tracks.items()):
        previous=None;source=None;source_zone=None;fragment=-1;frag=None
        gap_points=missing_points=skipped_frames=0;max_step=0.
        for o in obs:
            step=None if previous is None else o['time_s']-previous['time_s']
            if step is not None:assert step>0,('duplicate/out-of-order track observations',tid,o['frame'])
            reset=previous is None or step>max_gap_s+1e-9
            if reset:
                if frag is not None:fragments.append(frag)
                fragment+=1;source=None;source_zone=None
                gap_points=missing_points=skipped_frames=0;max_step=0.
                frag=dict(track_id=tid,fragment_index=fragment,first_frame=o['frame'],first_time_s=o['time_s'],
                    last_frame=o['frame'],last_time_s=o['time_s'],raw_observations=0)
                stats['raw_track_fragments']+=1
                if previous is not None:stats['raw_gap_resets']+=1
            elif source is not None:
                skipped_frames+=max(0,o['frame']-previous['frame']-1);max_step=max(max_step,step)
            previous=o;frag['last_frame']=o['frame'];frag['last_time_s']=o['time_s'];frag['raw_observations']+=1
            if o['point'] is None:
                stats['point_excluded_observations']+=1
                if source is not None:missing_points+=1
                continue
            zone=zone_from_distances(o['signed_distances'],margin);stats[zone+'_observations']+=1
            if zone=='gap':
                if source is not None:gap_points+=1
                continue
            if source is not None and zone!=source_zone:
                direction='IN' if (source_zone,zone)==('tunnel','plaza') else 'OUT'
                result.append(dict(track_id=tid,fragment_index=fragment,direction=direction,
                    time_s=o['time_s'],time_semantics='first_observed_target_region_entry_not_exact_crossing',
                    source_zone=source_zone,target_zone=zone,last_source_zone_time_s=source['time_s'],
                    first_target_zone_time_s=o['time_s'],transition_bracket_s=[source['time_s'],o['time_s']],
                    bracket_duration_s=o['time_s']-source['time_s'],gap_zone_observations=gap_points,
                    excluded_point_observations=missing_points,unobserved_native_frames=skipped_frames,
                    maximum_raw_observation_gap_s=max_step,margin_native_px=margin,
                    point_reference_switch=source['point_source']!=o['point_source'],endpoints=[source,o]))
            source=o;source_zone=zone;gap_points=missing_points=skipped_frames=0;max_step=0.
        if frag is not None:fragments.append(frag)
    result.sort(key=lambda r:(r['time_s'],r['track_id'],r['direction'],r['fragment_index']))
    for index,event in enumerate(result):event['prediction_id']=f'r{index:06d}'
    return result,fragments,dict(stats)


def height_at_foot(model,point,size):
    if not model.get('available'):return None,None,'model_unavailable'
    a,b,c=model['coefficients'];w,h=size;den=1+c/h
    if not math.isfinite(den) or den<=0:return None,None,'invalid_inverse_denominator'
    z=(a+b*point[0]/w+c*point[1]/h)/den
    if not math.isfinite(z) or z<=0:return None,None,'invalid_height'
    head=[point[0],point[1]-z]
    assert math.isclose(z,a+b*head[0]/w+c*head[1]/h,rel_tol=1e-10,abs_tol=1e-8)
    ranges=model['fitting_coordinate_range']
    ext=any(not (ranges[k][0]<=v<=ranges[k][1]) for k,v in
            [('head_x_norm',head[0]/w),('head_y_norm',head[1]/h)])
    return z,ext,None


def edge_distance(point,poly,indices):
    best=None
    for i in indices:
        a=poly[i];b=poly[(i+1)%len(poly)];v=[b[0]-a[0],b[1]-a[1]];n=v[0]**2+v[1]**2
        assert n>0
        s=max(0.,min(1.,((point[0]-a[0])*v[0]+(point[1]-a[1])*v[1])/n))
        q=[a[0]+s*v[0],a[1]+s*v[1]];d=math.hypot(point[0]-q[0],point[1]-q[1])
        if best is None or d<best['distance_px']:best=dict(distance_px=d,edge_index=i,edge_fraction=s,nearest_xy=q)
    return best


def evidence(event,track,frag,clip,model,polys,cfg):
    t=event['time_s'];end=t+cfg['window_s'];eps=cfg['epsilon']
    last=(clip['metadata']['nb_frames']-1)/clip['metadata']['fps'];size=[clip['metadata']['width'],clip['metadata']['height']]
    obs=[o for o in track if frag['first_time_s']-eps<=o['time_s']<=frag['last_time_s']+eps and t-eps<=o['time_s']<=end+eps]
    assert obs and obs[0]['frame']==event['target_frame'] and obs[0]['point']==event['endpoints'][1]['point']
    vals=[];returns=[];valid=0;future=0;height_bad=0;target_count=0;ext_count=0
    for base in obs:
        o=dict(base);p=o['point'];zone=zone_from_distances(o['signed_distances'],0) if p is not None else 'unavailable'
        o.update(zone=zone,height_px=None,height_invalid_reason=None,height_extrapolated=None,mouth_distance_px=None,
                 depth_height_ratio=None,nearest_edge=None)
        if p is not None:
            valid+=1;future+=o['time_s']>t+eps
            if o['time_s']>t+eps and zone==event['source_zone']:returns.append(o['frame'])
            z,ext,bad=height_at_foot(model,p,size);o.update(height_px=z,height_invalid_reason=bad,height_extrapolated=ext)
            if zone==event['target_zone']:
                target_count+=1;height_bad+=z is None;ext_count+=ext is True
                near=edge_distance(p,polys[event['target_zone']],cfg['geometry']['facing_edges_zero_based'][clip['camera']][event['target_zone']])
                o.update(mouth_distance_px=near['distance_px'],nearest_edge=near,depth_height_ratio=near['distance_px']/z if z else None)
        vals.append(o)
    ratios=[o for o in vals if o['depth_height_ratio'] is not None]
    best=max(ratios,key=lambda o:o['depth_height_ratio']) if ratios else None
    clip_short=last<end-eps;frag_short=frag['last_time_s']<end-eps
    track_early=frag['last_time_s']<min(last,end)-eps
    expected=max(0,math.floor(end*clip['metadata']['fps']+eps)-event['target_frame']+1)
    verdicts={}
    for spec in cfg['conditions']:
        q=spec['coefficient'];c1=best is not None and (q is None or best['depth_height_ratio']>=q-eps)
        c2=not returns;logic=(c1 and c2) if spec['rule']=='C1C2' else c1 if spec['rule']=='C1' else c2
        full=not clip_short and not frag_short;keep=logic and (full or spec['coverage']=='observed')
        verdicts[spec['key']]=dict(keep=bool(keep),C1=None if q is None else bool(c1),C2=bool(c2),logic_pass=bool(logic),
            coverage_pass=full,first_depth_frame=next((o['frame'] for o in ratios if q is not None and o['depth_height_ratio']>=q-eps),None))
    return dict(prediction_id=event['prediction_id'],track_id=event['track_id'],fragment_index=event['fragment_index'],direction=event['direction'],
        time_s=t,target_frame=event['target_frame'],source_zone=event['source_zone'],target_zone=event['target_zone'],deadline_s=end,
        fragment=frag,clip_last_time_s=last,clip_short=clip_short,fragment_short=frag_short,track_ends_before_clip_or_deadline=track_early,
        full2s=not clip_short and not frag_short,expected_native_observations=expected,raw_observations=len(obs),valid_points=valid,
        future_valid_points=future,zero_future_valid_points=future==0,missing_native_observations=expected-len(obs),
        unavailable_hybrid_observations=len(obs)-valid,target_zone_observations=target_count,invalid_target_heights=height_bad,
        extrapolated_target_heights=ext_count,max_depth_height_ratio=best['depth_height_ratio'] if best else None,
        max_depth_frame=best['frame'] if best else None,return_frames=returns,observed_return=bool(returns),
        observations=vals,verdicts=verdicts)


VARIANTS = ('frozen', 'R1', 'R2', 'R1+R2', 'R1+R2+R3')


SOURCE_ZONE = {'IN':'tunnel', 'OUT':'plaza'}


TARGET_ZONE = {'IN':'plaza', 'OUT':'tunnel'}


def _event_frame(event):
    for key in ('target_frame','frame'):
        if key in event:return int(event[key])
    if event.get('endpoints') and 'frame' in event['endpoints'][-1]:
        return int(event['endpoints'][-1]['frame'])
    raise ValueError('An event requires target_frame/frame or a saved endpoint frame')


def _event_key(event):
    return (float(event['time_s']),_event_frame(event),str(event['prediction_id']))


def _valid_point(point):
    try:
        return point is not None and len(point)==2 and all(math.isfinite(float(v)) for v in point)
    except (TypeError,ValueError,OverflowError):
        return False


def _observation_detail(observation):
    # Physical row references are copied when available, not reconstructed.
    keys=('clip_id','frame','time_s','track_id','zone','point_source','point',
          'raw_detection_index','points_jsonl_line','raw_jsonl_line',
          'source_frame','source_frame_estimated','source_time_s')
    return {key:deepcopy(observation[key]) for key in keys if key in observation}


def _window(observations,start,end,left_closed,right_closed):
    raw=[o for o in observations if
         (o['time_s']>=start if left_closed else o['time_s']>start) and
         (o['time_s']<=end if right_closed else o['time_s']<end)]
    eligible=[o for o in raw if o['zone'] in ('tunnel','plaza') and _valid_point(o['point'])]
    return dict(start_s=start,end_s=end,left_closed=left_closed,right_closed=right_closed,
                raw_observation_count=len(raw),eligible_count=len(eligible),excluded_count=len(raw)-len(eligible),
                eligible_frames=[int(o['frame']) for o in eligible],
                eligible_zones=[o['zone'] for o in eligible],
                eligible_observations=[_observation_detail(o) for o in eligible])


def transform_events(events, observations, variant):
    """Return (all_groups, one_detail_row_per_group), including rejected groups.

    Every event/observation requires clip_id, time_s and track_id; all input
    records must belong to one clip. Events additionally require direction,
    prediction_id, and a frame (target_frame/frame or last saved endpoint).
    Observations additionally require frame, point (possibly None), and zone
    ('tunnel', 'plaza' or a non-participating value such as None/'gap').

    Groups contain the unchanged first representative event and all member
    events/IDs, first_t/last_t, keep, decision and notes. R1 does not break a
    same-direction chain when an opposite-direction event occurs between its
    members. R2 evidence insufficiency takes priority over a failed proportion.
    R3 executes only if R2 retained the group, using only the representative's
    literal boolean True flag; unknown/non-boolean flags conservatively retain.
    No person identity is inferred from a track ID.
    """
    if variant not in VARIANTS:raise ValueError(f'Unsupported variant: {variant}')
    events=list(events);observations=list(observations)
    clip_ids={r['clip_id'] for r in [*events,*observations]}
    if len(clip_ids)>1:raise ValueError('transform_events operates on exactly one clip per call')
    for event in events:
        if not math.isfinite(float(event['time_s'])):raise ValueError('Event time must be finite')
        if event['direction'] not in SOURCE_ZONE:raise ValueError('Event direction must be IN or OUT')
        _event_frame(event)
    if len({e['prediction_id'] for e in events})!=len(events):raise ValueError('Prediction IDs must be unique in one clip')
    for observation in observations:
        if not math.isfinite(float(observation['time_s'])):raise ValueError('Observation time must be finite')
        for key in ('frame','track_id','zone','point'):observation[key]
    use_r1=variant in ('R1','R1+R2','R1+R2+R3')
    use_r2=variant in ('R2','R1+R2','R1+R2+R3')
    use_r3=variant=='R1+R2+R3'
    ordered=sorted(events,key=_event_key)
    member_groups=[]
    if use_r1:
        buckets=defaultdict(list)
        for event in ordered:
            track=event['track_id']
            # Unknown IDs never provide evidence that two events share a track.
            key=(event['clip_id'],('unknown_event',event['prediction_id']) if track is None else ('known_track',track),event['direction'])
            buckets[key].append(event)
        for bucket in buckets.values():
            group=[]
            for event in bucket:
                if group and float(event['time_s'])-float(group[-1]['time_s'])>2.0:
                    member_groups.append(group);group=[]
                group.append(event)
            if group:member_groups.append(group)
    else:
        member_groups=[[event] for event in ordered]
    member_groups.sort(key=lambda group:_event_key(group[0]))
    by_track=defaultdict(list)
    for observation in observations:
        if observation['track_id'] is not None:by_track[observation['track_id']].append(observation)
    for track in by_track:
        by_track[track].sort(key=lambda o:(float(o['time_s']),int(o['frame']),int(o.get('raw_detection_index',-1))))
    groups=[];details=[]
    for number,members in enumerate(member_groups,1):
        representative=members[0];track=representative['track_id'];direction=representative['direction']
        first_t=float(representative['time_s']);last_t=float(members[-1]['time_s'])
        group_id=f'g{number:06d}';notes=[];r2_keep=True;insufficient=False
        before=after=None;before_fraction=after_fraction=None;before_support=after_support=None
        r2_status='not_applied'
        if track is None:notes.append('Unknown track ID: no cross-event merge or track-direction evidence inferred')
        if use_r2:
            track_observations=by_track.get(track,[]) if track is not None else []
            before=_window(track_observations,first_t-1.,first_t,True,False)
            after=_window(track_observations,last_t,last_t+1.,False,True)
            before_support=before['eligible_zones'].count(SOURCE_ZONE[direction])
            after_support=after['eligible_zones'].count(TARGET_ZONE[direction])
            bn,an=before['eligible_count'],after['eligible_count']
            before_fraction=before_support/bn if bn else None
            after_fraction=after_support/an if an else None
            insufficient=bn<3 or an<3
            if insufficient:
                r2_keep=True;r2_status='insufficient_evidence_kept'
                notes.append('At least one eligible window has fewer than 3 points; R2 retains even if the other proportion fails')
            else:
                r2_keep=(2*before_support>=bn and 2*after_support>=an)
                r2_status='net_direction_supported' if r2_keep else 'net_direction_rejected'
        flag=representative.get('point_reference_switch')
        r3_executed=use_r3 and r2_keep;r3_keep=True
        r3_status='not_applied' if not use_r3 else 'not_executed_R2_rejected'
        if r3_executed:
            if flag is True:
                r3_keep=False;r3_status='representative_saved_switch_true_rejected'
            elif flag is False:
                r3_status='representative_saved_switch_false_kept'
            else:
                r3_status='representative_switch_unknown_kept'
                notes.append('Missing/non-boolean representative switch flag is unknown and retained; no member OR or inferred switch')
        keep=r2_keep and r3_keep
        decision='drop_R2' if not r2_keep else 'drop_R3' if not r3_keep else 'keep_R2_insufficient' if insufficient else 'keep'
        group=dict(group_id=group_id,clip_id=representative['clip_id'],variant=variant,
            track_id=track,direction=direction,first_t=first_t,last_t=last_t,
            representative=deepcopy(representative),representative_prediction_id=representative['prediction_id'],
            member_prediction_ids=[e['prediction_id'] for e in members],member_events=deepcopy(members),
            member_count=len(members),r1_applied=use_r1,r1_merged=use_r1 and len(members)>1,
            keep=keep,decision=decision,notes=notes)
        detail=dict(group_id=group_id,clip_id=representative['clip_id'],variant=variant,
            representative_prediction_id=representative['prediction_id'],member_prediction_ids=group['member_prediction_ids'],
            track_id=track,direction=direction,first_t=first_t,last_t=last_t,
            before=before,after=after,source_zone=SOURCE_ZONE[direction],target_zone=TARGET_ZONE[direction],
            before_source_count=before_support,after_target_count=after_support,
            before_source_proportion=before_fraction,after_target_proportion=after_fraction,
            r2_applied=use_r2,r2_status=r2_status,r2_insufficient=insufficient,r2_keep=r2_keep,
            r3_applied=use_r3,r3_executed=r3_executed,r3_flag=deepcopy(flag),
            r3_flag_known=isinstance(flag,bool),r3_flag_authority_prediction_id=representative['prediction_id'],
            r3_status=r3_status,r3_keep=r3_keep,keep=keep,decision=decision,notes=list(notes))
        groups.append(group);details.append(detail)
    return groups,details


def finite_point(p):
    return p is not None and len(p) >= 2 and all(math.isfinite(float(v)) for v in p[:2])


def keypoint_mean(detection, indices, confidence=.5, require_all=False):
    kp=detection.get('keypoints', [])
    valid=[i for i in indices if i < len(kp) and len(kp[i]) >= 3
           and math.isfinite(float(kp[i][2])) and float(kp[i][2]) >= confidence
           and finite_point(kp[i])]
    if not valid or (require_all and len(valid) != len(indices)):
        return None,valid
    return [float(np.mean([kp[i][k] for i in valid])) for k in (0,1)],valid


def predict_height(model,head,size):
    if not model.get('available'):return None
    a,b,c=model['coefficients'];return float(a+b*head[0]/size[0]+c*head[1]/size[1])


def select_point(detection,version,model,size,confidence=.5):
    """No-ID rows still receive points for source-rate denominators, not events."""
    assert version in ('foot','head','hybrid')
    if version=='foot':
        p=detection.get('foot');valid=finite_point(p)
        return dict(point=list(map(float,p[:2])) if valid else None,
            point_source='saved_'+detection.get('foot_method','unknown') if valid else 'excluded',
            exclusion_reason=None if valid else 'saved_foot_invalid',predicted_height_px=None)
    if version=='hybrid':
        ankle,indices=keypoint_mean(detection,(15,16),confidence,True)
        if ankle is not None:return dict(point=ankle,point_source='both_ankles_conf05',
            exclusion_reason=None,predicted_height_px=None)
    head,indices=keypoint_mean(detection,range(5),confidence)
    if head is None:return dict(point=None,point_source='excluded',exclusion_reason='head_unavailable',predicted_height_px=None)
    if not model.get('available'):
        return dict(point=None,point_source='excluded',exclusion_reason='camera_height_model_unavailable',predicted_height_px=None)
    height=predict_height(model,head,size)
    if not math.isfinite(height) or height<=0:
        return dict(point=None,point_source='excluded',exclusion_reason='predicted_height_nonpositive_or_nonfinite',predicted_height_px=height if math.isfinite(height) else None)
    return dict(point=[head[0],head[1]+height],point_source='head_affine_vertical',
        exclusion_reason=None,predicted_height_px=height,head_indices=indices)
