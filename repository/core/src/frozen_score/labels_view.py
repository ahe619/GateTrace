"""Verbatim frozen scientific functions; pure and no import-time I/O.
Source: scripts/r15_c1star_t3_eval75.py; software notice in package LICENSE_CODE.
"""
from fractions import Fraction
import math,re
SEQS=('MOT20-01','MOT20-02')
GATES=('H_30','H_50','H_70','V_25','V_50','V_75')
BINS=('low','mid_low','mid_high','high')
UNKNOWN={'insufficient_observations','unidentified','ambiguous','mixed_unknown'}


def number_suffix(text):
    match=re.search(r'(\d+)$',str(text))
    if not match:raise ValueError('No stable numeric suffix: '+str(text))
    return int(match.group(1))


def stable(prefix,key):
    if any(type(x) is not int or x<0 or x>=10**12 for x in key):raise ValueError('Unsupported stable numeric key')
    return prefix+':'+':'.join(f'{x:012d}' for x in key)


def exact_time(frame,value):
    if type(frame) is not int or frame<1:raise ValueError('Invalid source frame')
    result=Fraction(frame-1,25)
    if not math.isfinite(float(value)) or abs(float(result)-float(value))>1e-9:raise ValueError('Frame/time inconsistency')
    return result


def position(pos):
    if len(pos)!=2 or not all(math.isfinite(float(x)) for x in pos):raise ValueError('Invalid event position')
    return tuple(map(float,pos))


def gt_row(r,path,line):
    seq=r['sequence'];gate=r['line_id']
    if seq not in SEQS or gate not in GATES:raise ValueError('GT outside scope')
    f=int(r['gt_frame_1based']);gid=int(r['track_id']);at=r['attributes']
    h=float(at['h_g']);vis=float(at['mean_visibility'])
    if not math.isfinite(h) or h<=0 or not math.isfinite(vis) or not 0<=vis<=1:raise ValueError('GT height/visibility invalid')
    vb=BINS[min(3,int(vis*4))]
    if vb!=at['visibility_bin']:raise ValueError('Visibility bin mismatch')
    key=(int(seq[-2:]),GATES.index(gate),f,gid,number_suffix(r['event_id']))
    x,y=position(r['position_native_px'])
    return dict(id=stable('G',key),key=key,seq=seq,gate=gate,frame=f,t=exact_time(f,r['time_s']),
                dir=r['direction'],x=x,y=y,h=h,gid=gid,vis=vis,bin=vb,rho=at['rho'],static=at['static_occ'],
                confirmed=bool(r['confirmed']),original_id=r['event_id'],source=dict(path=path,jsonl_line=line),
                frozen_transition=r['frozen_transition'],confirmation=r['confirmation'])
