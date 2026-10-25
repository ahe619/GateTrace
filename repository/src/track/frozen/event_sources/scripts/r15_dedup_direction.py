"""Instruction 35 pure R1/R2/R3 rules for one clip of saved confirmed events.

No files, inference, tracking, annotations or geometry are loaded here. The
caller supplies unchanged saved hybrid points and m=0 zone assignments. Input
times are the same processing-local clock. Direct Python float comparisons
implement the registered open/closed windows without added tolerances.
"""
from __future__ import annotations
from collections import defaultdict
from copy import deepcopy
import math

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


if __name__=='__main__':
    from r15e10_core import main
    main()
