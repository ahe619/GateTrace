"""Verbatim frozen scientific functions; pure and no import-time I/O.
Source: scripts/r15_c1star_t3_identity75.py; software notice in package LICENSE_CODE.
"""
import math
from collections import Counter,defaultdict


def integer(x):
    n=int(x)
    if n!=x or isinstance(x,bool):raise ValueError('Expected integer field')
    return n


def valid_box(box):
    if len(box)!=4 or not all(math.isfinite(float(x)) for x in box) or box[2]<=box[0] or box[3]<=box[1]:
        raise ValueError('Invalid matching-pool box')
    return tuple(map(float,box))


def parse_gt(text,length):
    frames=defaultdict(list);classes={}
    for line_no,line in enumerate(text.splitlines(),1):
        if not line.strip():continue
        values=[float(x) for x in line.strip().split(',')]
        if len(values)!=9 or not all(math.isfinite(x) for x in values):raise ValueError('GT schema')
        f,gid,flag,cls=[integer(values[i]) for i in (0,1,6,7)]
        if not 1<=f<=length:raise ValueError('GT frame outside sequence')
        if not ((flag==1 and cls==1) or cls in (6,7)):continue
        x,y,w,h=values[2:6];box=valid_box((x-1,y-1,x-1+w,y-1+h))
        if gid in classes and classes[gid]!=cls:raise ValueError('GT class changes for identity')
        classes[gid]=cls
        frames[f].append(dict(gid=gid,cls=cls,box=box,gt_line=line_no,vis=values[8]))
    for f,rows in frames.items():
        if len({x['gid'] for x in rows})!=len(rows):raise ValueError('Duplicate GT ID in frame')
        rows.sort(key=lambda x:x['gid'])
    return frames,classes


def modal(observations,anchor,classes,old_tie=False):
    votes=Counter(o['gt_id'] for o in observations if o['gt_id'] is not None)
    n=len(observations)
    base=dict(n_obs=n,n_valid=sum(votes.values()),votes=[{'gt_id':k,'count':v} for k,v in sorted(votes.items())],
              n_ambiguous=sum(o['status']=='ambiguous' for o in observations),
              n_unmatched=sum(o['status']=='unmatched' for o in observations),gid=None)
    if n<3:return dict(base,status='insufficient_observations')
    if not votes:return dict(base,status='unidentified')
    high=max(votes.values());modes=sorted(k for k,v in votes.items() if v==high)
    if high*2<n or (len(modes)>1 and not old_tie):return dict(base,status='ambiguous',mode_candidates=modes)
    winner=min(modes,key=lambda gid:(min(abs(o['source_frame']-anchor) for o in observations if o['gt_id']==gid),gid))
    base['gid']=winner
    return dict(base,status='ignore' if classes[winner] in (6,7) else 'known',mode_fraction=high/n,mode_candidates=modes)


def event_identity(observations,anchor,classes,old_tie=False):
    obs=[o for o in observations if anchor-25<=o['source_frame']<=anchor+25]
    entire=modal(obs,anchor,classes,old_tie)
    before=modal([o for o in obs if o['source_frame']<anchor],anchor,classes,old_tie)
    after=modal([o for o in obs if o['source_frame']>=anchor],anchor,classes,old_tie)
    if before['status']=='known' and after['status']=='known' and before['gid']!=after['gid']:
        entire=dict(entire,status='mixed_unknown',gid=None)
    return dict(entire,pre=before,post=after,observed_source_frames=[o['source_frame'] for o in obs],
                observation_count=len(obs))
