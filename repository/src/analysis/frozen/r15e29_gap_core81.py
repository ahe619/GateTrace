"""Pure descriptive functions for #81. No I/O, inference or event recomputation."""
import math
from collections import defaultdict

EPS=1e-9

def rectangle(poly):
    pts=[tuple(map(float,p)) for p in poly]
    if len(pts)==5 and pts[0]==pts[-1]: pts=pts[:-1]
    xs=sorted(set(p[0] for p in pts));ys=sorted(set(p[1] for p in pts))
    if len(xs)!=2 or len(ys)!=2 or set(pts)!={(x,y) for x in xs for y in ys}:
        raise ValueError('Expected an axis aligned rectangle')
    return xs[0],ys[0],xs[-1],ys[-1]

def within(point,rect):
    return rect[0]-EPS<=point[0]<=rect[2]+EPS and rect[1]-EPS<=point[1]<=rect[3]+EPS

def zone(point,rects):
    if point is None:return 'invalid'
    if len(point)!=2 or not all(math.isfinite(float(x)) for x in point):raise ValueError('Invalid point')
    z=[k for k,v in rects.items() if within(point,v)]
    if len(z)>1:raise ValueError('Overlapping regions')
    return z[0] if z else 'gap'

def rect_distance(point,rect):
    if point is None:return None
    return math.hypot(max(rect[0]-point[0],0,point[0]-rect[2]),max(rect[1]-point[1],0,point[1]-rect[3]))

def gap_rectangle(g):
    lo,hi=g['line_extent_px'];c=g['line_coordinate_px'];h=g['gap_half_width']
    if g['orientation']=='H':return (lo,c-h,hi,c+h)
    if g['orientation']=='V':return (c-h,lo,c+h,hi)
    raise ValueError('Unknown orientation')

def duration_bin(dt):
    if dt<=.5+EPS:return 'le_0p5'
    if dt<=1+EPS:return 'gt_0p5_le_1'
    if dt<=2+EPS:return 'gt_1_le_2'
    return 'gt_2'

def gaps(timelines,fps=25):
    result=[]
    for tid,obs in sorted(timelines.items()):
        for a,b in zip(obs,obs[1:]):
            delta=b['source_frame']-a['source_frame']
            if delta<=0:raise ValueError('Duplicate/nonmonotone same-ID observation')
            if delta==1:continue
            result.append(dict(track_id=tid,before_frame=a['source_frame'],after_frame=b['source_frame'],
                endpoint_delta_frames=delta,missing_frames=delta-1,dt_s=delta/fps,
                missing_duration_s=(delta-1)/fps,duration_bin=duration_bin(delta/fps),
                before_point=a['point'],after_point=b['point']))
    return result

def oriented_gap(gap,rects):
    a=zone(gap['before_point'],rects);b=zone(gap['after_point'],rects)
    if a=='tunnel' and b=='plaza':return 'IN'
    if a=='plaza' and b=='tunnel':return 'OUT'
    return None

def time_compatible(gap,frame,window=25,strict=True):
    a,b=gap['before_frame'],gap['after_frame']
    if strict:return a>=frame-window and b<=frame+window
    return a<=frame+window and b>=frame-window

def selftest():
    rects={'tunnel':(0,0,10,10),'plaza':(0,12,10,22)}
    g={'track_id':7,'before_frame':100,'after_frame':113,'before_point':[5,5],'after_point':[5,15]}
    assert duration_bin(.5)=='le_0p5' and duration_bin(13/25)=='gt_0p5_le_1'
    assert duration_bin(1)=='gt_0p5_le_1' and duration_bin(26/25)=='gt_1_le_2'
    assert oriented_gap(g,rects)=='IN'
    assert oriented_gap(dict(g,before_point=None),rects) is None
    assert time_compatible(g,106) and not time_compatible(g,140)
    assert time_compatible(g,140,strict=False) is False
    assert rect_distance([20,11],(0,10,10,12))==10
    assert zone([11,11],rects)=='gap'
    assert rectangle([[0,0],[10,0],[10,10],[0,10]])==(0,0,10,10)
    rows={7:[{'source_frame':100,'point':[5,5]},{'source_frame':113,'point':[5,15]}]}
    out=gaps(rows);assert out[0]['missing_frames']==12 and out[0]['dt_s']==.52
    rows[7].insert(1,{'source_frame':106,'point':None})
    assert all(x['dt_s']<=.5 for x in gaps(rows))
    assert gaps({1:[{'source_frame':100,'point':[5,5]}],2:[{'source_frame':113,'point':[5,15]}]})==[]
    try:gaps({1:[{'source_frame':1,'point':None},{'source_frame':1,'point':None}]})
    except ValueError:pass
    else:raise AssertionError('duplicate source frame not rejected')
    return {'passed':True,'synthetic_only':True,'checks':['strict_boundaries','endpoint_vs_missing','direction',
        'invalid_endpoint','time_window','finite_gate','rectangular_region','invalid_point_observation_clock',
        'separate_ids','duplicate_frame_rejection']}
