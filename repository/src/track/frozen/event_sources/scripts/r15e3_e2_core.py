"""Pure E3 region transitions and paired rule comparisons on saved track IDs."""
from __future__ import annotations
from collections import defaultdict,Counter
from r15e2_events import optimal_match


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


def compare_line_region(line_events,region_events,fragments,tolerance_s=5.):
    """Compare two algorithms, keeping IDs within the same saved tracker run."""
    line=[r for r in line_events if r['finite']];pairs=[]
    tids=sorted({r['track_id'] for r in line}|{r['track_id'] for r in region_events})
    for tid in tids:
        ls=[r for r in line if r['track_id']==tid];rs=[r for r in region_events if r['track_id']==tid]
        manual=[dict(id=r['prediction_id'],time=r['time_s'],direction=r['direction']) for r in ls]
        result=optimal_match(manual,rs,tolerance_s)
        for m in result['matches']:
            pairs.append(dict(track_id=tid,direction=m['direction'],line_prediction_id=m['manual_event_id'],
                region_prediction_id=m['prediction_id'],line_time_s=m['manual_time_s'],
                region_time_s=m['prediction_time_s'],absolute_dt_s=m['absolute_dt_s']))
    used_line={p['line_prediction_id'] for p in pairs};used_region={p['region_prediction_id'] for p in pairs}
    fragmap={(f['track_id'],f['fragment_index']):f for f in fragments};annotated=[]
    for e in region_events:
        frag=fragmap[e['track_id'],e['fragment_index']]
        same=[l for l in line_events if l['track_id']==e['track_id'] and l['direction']==e['direction']]
        finite_fragment=[l['prediction_id'] for l in same if l['finite'] and
            frag['first_time_s']-1e-9<=l['time_s']<=frag['last_time_s']+1e-9]
        outside_near=[l['prediction_id'] for l in same if not l['finite'] and abs(l['time_s']-e['time_s'])<=tolerance_s+1e-9]
        annotated.append(dict(region_prediction_id=e['prediction_id'],track_id=e['track_id'],direction=e['direction'],
            status='paired_rules' if e['prediction_id'] in used_region else 'new_region_rule_candidate',
            same_direction_finite_line_ids_in_whole_raw_fragment=finite_fragment,
            same_direction_finite_in_whole_raw_fragment=bool(finite_fragment),
            same_direction_infinite_outside_ids_within_tolerance=outside_near,
            same_direction_infinite_outside_correspondence=bool(outside_near),fragment=frag,
            limitation='Rule comparison on an algorithmic track ID; not evidence of the same physical person or actual bypass'))
    return dict(matches=pairs,unpaired_line_prediction_ids=[l['prediction_id'] for l in line if l['prediction_id'] not in used_line],
        unpaired_region_prediction_ids=[e['prediction_id'] for e in region_events if e['prediction_id'] not in used_region],
        region_annotations=annotated,objective=dict(matched_count=len(pairs),total_absolute_dt_s=sum(p['absolute_dt_s'] for p in pairs)),
        tolerance_s=tolerance_s,same_saved_track_id_required=True)


def selftest():
    def o(f,point,zone):
        return dict(frame=f,time_s=f/10.,track_id=1,point=point,point_source='test',
            signed_distances={'tunnel':10 if zone=='tunnel' else -10,'plaza':10 if zone=='plaza' else -10})
    obs=[o(0,[1,1],'tunnel'),o(1,None,'gap'),o(2,[1,1],'gap'),o(3,[1,1],'plaza'),o(4,[1,1],'tunnel')]
    e,f,s=extract_region_events(obs,0)
    assert [r['direction'] for r in e]==['IN','OUT']
    assert e[0]['excluded_point_observations']==1 and e[0]['gap_zone_observations']==1
    assert e[0]['transition_bracket_s']==[0.,.3]
    assert not extract_region_events([obs[0],o(6,[1,1],'plaza')],0)[0]
    assert not extract_region_events(obs,20)[0]
    return dict(status='passed',synthetic_only=True)


if __name__=='__main__':print(selftest())
