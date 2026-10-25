"""Exact frozen region functions; no application imports or I/O."""
from collections import defaultdict, Counter
import math
SOURCE_BINDINGS = [{'path': 'scripts/r15e3_e2_core.py', 'bytes': 7310, 'sha256': 'a9d4ef470e8adbd7b6cb0f0a0017c8592873a885b3ea2b5e9423c31484476c89', 'functions': [{'name': 'zone_from_distances', 'original_file': 'scripts/r15e3_e2_core.py', 'first_line': 7, 'last_line': 10, 'source_sha256': '275655a7b66ba6fc4a4960cd197dfff1a7bb27235df4e9efd7f9f77e501b4110', 'byte_exact_source_excerpt': True}, {'name': 'extract_region_events', 'original_file': 'scripts/r15e3_e2_core.py', 'first_line': 13, 'last_line': 63, 'source_sha256': 'adf0081a3fdbcf92cd7078e77014bfa448f1b83c67bd4411df38349ed1eac793', 'byte_exact_source_excerpt': True}]}, {'path': 'scripts/r15e3_regions_common.py', 'bytes': 3169, 'sha256': 'e2dd5687f6b5574d1aa49a3396cba97baee453c20c6870e7515bc2a86f8f25e4', 'functions': [{'name': 'nearest_boundary', 'original_file': 'scripts/r15e3_regions_common.py', 'first_line': 8, 'last_line': 21, 'source_sha256': '77da1ac295a9cabe3c718b5d19bf04783921770f28457413ffb9a1c03de98d12', 'byte_exact_source_excerpt': True}, {'name': 'signed_distance', 'original_file': 'scripts/r15e3_regions_common.py', 'first_line': 24, 'last_line': 31, 'source_sha256': 'dee9ca04d8ba9c0acb652d18e7e3ddf089cbf13b0611020b6775606dc2414563', 'byte_exact_source_excerpt': True}]}]

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
