"""Fixed C1/C2 post-confirmation of saved E3 hybrid events. No model runs."""
from collections import defaultdict,Counter
import math,time
from r15e6_common import *
from r15e2_events import optimal_match
from r15e3_e2_core import zone_from_distances
from r15e5_core import stats,aggregate,reverse

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

def load_points(path):
    tracks=defaultdict(list)
    with Path(path).open(encoding='utf-8') as f:
        for line,text in enumerate(f,1):
            r=json.loads(text);assert r['jsonl_line']==line
            for d in r['detections']:
                if d['track_id'] is None:continue
                p=d['versions']['hybrid']
                o=dict(frame=r['frame'],time_s=r['time_s'],track_id=d['track_id'],raw_detection_index=d['raw_detection_index'],
                    points_jsonl_line=line,raw_jsonl_line=r['raw_jsonl_line'],source_frame_estimated=r.get('source_frame_estimated'),
                    point=p['point'],point_source=p['point_source'],exclusion_reason=p['exclusion_reason'],
                    signed_distances=p['signed_distances'],out_of_frame=p['out_of_frame'])
                tracks[d['track_id']].append(o)
    for tr in tracks.values():assert all(a['time_s']<b['time_s'] for a,b in zip(tr,tr[1:]))
    return tracks

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

def manual_rows(clip,name,base,current,evidence_by_id):
    bm={m['manual_event_id']:m for m in base['matching']['matches']};cm={m['manual_event_id']:m for m in current['matching']['matches']}
    kept={p['prediction_id'] for p in current['predictions']};groups=defaultdict(list);rows=[]
    for m in clip['manual_events']:groups[m['direction'],m['time']].append(m['id'])
    for i,m in enumerate(clip['manual_events']):
        b=bm.get(m['id']);c=cm.get(m['id']);g=groups[m['direction'],m['time']]
        nb=sum(x in bm for x in g);nc=sum(x in cm for x in g)
        ev=evidence_by_id[b['prediction_id']] if b else None
        removed=bool(b and b['prediction_id'] not in kept);lost=bool(b and not c)
        v=ev['verdicts'][name] if ev else None
        rows.append(dict(setting='imgsz2560',alias=clip['alias'],clip_id=clip['clip_id'],camera=clip['camera'],phase=clip['phase'],condition=name,
            manual_index=i,manual_event_id=m['id'],manual_time_s=m['time'],direction=m['direction'],manual_jsonl_line=clip['manual_jsonl_line'],
            baseline_matched=b is not None,confirmed_matched=c is not None,baseline_prediction_id=b['prediction_id'] if b else None,
            confirmed_prediction_id=c['prediction_id'] if c else None,baseline_candidate_removed=removed,lost_time_match=lost,
            retained_original_candidate=bool(b and b['prediction_id'] in kept),same_time_group_size=len(g),same_time_baseline_matched=nb,same_time_confirmed_matched=nc,
            status_assignment_ambiguous=len(g)>1 and (0<nb<len(g) or 0<nc<len(g)),track_id=ev['track_id'] if ev else None,
            candidate_time_s=ev['time_s'] if ev else None,C1=v['C1'] if v else None,C2=v['C2'] if v else None,
            full2s=ev['full2s'] if ev else None,clip_short=ev['clip_short'] if ev else None,
            track_ends_before_clip_or_deadline=ev['track_ends_before_clip_or_deadline'] if ev else None,
            zero_future_valid_points=ev['zero_future_valid_points'] if ev else None,max_depth_height_ratio=ev['max_depth_height_ratio'] if ev else None,
            observed_return=ev['observed_return'] if ev else None,
            diagnostic='Temporal manual pairing only; removed original candidate may be rematched; same-time labels lack spatial identity'))
    return rows

def diagnostic_rows(clip,evs,cfg):
    out=[]
    for spec in cfg['conditions']:
        for d in ('IN','OUT'):
            es=[e for e in evs if e['direction']==d];vs=[e['verdicts'][spec['key']] for e in es]
            out.append(dict(setting='imgsz2560',alias=clip['alias'],camera=clip['camera'],phase=clip['phase'],condition=spec['key'],direction=d,
                candidates=len(es),retained=sum(v['keep'] for v in vs),removed=sum(not v['keep'] for v in vs),
                full2s=sum(e['full2s'] for e in es),incomplete2s=sum(not e['full2s'] for e in es),clip_short=sum(e['clip_short'] for e in es),
                fragment_short=sum(e['fragment_short'] for e in es),track_ends_early=sum(e['track_ends_before_clip_or_deadline'] for e in es),
                C1_not_reached=sum(v['C1'] is False for v in vs),C2_observed_return=sum(e['observed_return'] for e in es),
                C1_not_reached_and_return=sum(v['C1'] is False and e['observed_return'] for e,v in zip(es,vs)),
                incomplete_and_return=sum(not e['full2s'] and e['observed_return'] for e in es),
                incomplete_and_C1_not_reached=sum(not e['full2s'] and v['C1'] is False for e,v in zip(es,vs)),
                zero_future_valid_points=sum(e['zero_future_valid_points'] for e in es),
                retained_zero_future_valid_points=sum(e['zero_future_valid_points'] and v['keep'] for e,v in zip(es,vs)),
                any_invalid_target_height=sum(e['invalid_target_heights']>0 for e in es),
                any_missing_observations=sum(e['missing_native_observations']>0 or e['unavailable_hybrid_observations']>0 for e in es)))
    return out

def decisions(summary):
    idx={(r['scope'],r['setting'],r['condition'],r['direction']):r for r in summary};rows=[]
    for r in summary:
        if r['condition']=='hybrid_m0':continue
        b=idx[r['scope'],r['setting'],'hybrid_m0',r['direction']]
        assert r['matched']<=b['matched'] and r['extra']<=b['extra'],'Subset filtering cannot improve maximum count or increase extra'
        rows.append(dict(scope=r['scope'],setting=r['setting'],condition=r['condition'],direction=r['direction'],
            manual_count=r['manual_count'],matched=r['matched'],missed=r['missed'],extra=r['extra'],
            recall=r['matched']/r['manual_count'] if r['manual_count'] else None,recall_ge_0p8=5*r['matched']>=4*r['manual_count'] if r['manual_count'] else None,
            baseline_matched=b['matched'],baseline_missed=b['missed'],baseline_extra=b['extra'],
            missed_change=r['missed']-b['missed'],extra_change=r['extra']-b['extra'],
            extra_reduction_fraction=(b['extra']-r['extra'])/b['extra'] if b['extra'] else None,
            fewer_extra=r['extra']<b['extra']))
    return rows

def selftest():
    z,ext,bad=height_at_foot(dict(available=True,coefficients=[100,20,30],fitting_coordinate_range={'head_x_norm':[0,1],'head_y_norm':[0,1]}),[200,430],[1000,1000])
    assert math.isclose(z,(100+4+12.9)/1.03)
    assert height_at_foot(dict(available=True,coefficients=[10,0,-1000]),[0,0],[1000,1000])[0] is None
    n=edge_distance([20,5],[[0,0],[10,0],[10,10],[0,10]],[0]);assert math.isclose(n['distance_px'],math.sqrt(125))
    assert n['edge_fraction']==1,'Finite chain, not extended line'
    assert len(condition_specs())==14
    cfg=dict(window_s=2.,epsilon=1e-9,conditions=condition_specs(),geometry={'facing_edges_zero_based':{'A':{'plaza':[0]}}})
    model=dict(available=True,coefficients=[100,0,0],fitting_coordinate_range={'head_x_norm':[0,1],'head_y_norm':[-1,1]})
    clip=dict(camera='A',metadata=dict(width=1000,height=1000,nb_frames=301,fps=30.))
    def ob(f,y,zone):return dict(frame=f,time_s=f/30.,point=[5,y],signed_distances={'plaza':1 if zone=='plaza' else -1,'tunnel':1 if zone=='tunnel' else -1})
    track=[ob(0,1,'plaza'),ob(15,1,'tunnel'),ob(30,50,'plaza'),ob(61,90,'tunnel')]
    event=dict(time_s=0.,target_frame=0,endpoints=[{},track[0]],prediction_id='x',track_id=1,fragment_index=0,direction='IN',source_zone='tunnel',target_zone='plaza')
    frag=dict(first_time_s=0.,last_time_s=61/30.)
    ev=evidence(event,track,frag,clip,model,{'plaza':[[0,0],[10,0],[10,100],[0,100]]},cfg)
    assert ev['full2s'] and ev['return_frames']==[15] and ev['raw_observations']==3
    assert ev['verdicts']['C1_q0p3_full2s']['keep'] and not ev['verdicts']['C1C2_q0p3_full2s']['keep']
    ev=evidence(event,[track[0]],dict(first_time_s=0.,last_time_s=0.),clip,model,{'plaza':[[0,0],[10,0],[10,100],[0,100]]},cfg)
    assert ev['zero_future_valid_points'] and not ev['full2s']
    assert ev['verdicts']['C2_observed']['keep'] and not ev['verdicts']['C2_full2s']['keep']
    return dict(passed=True,cases=8,scope='height/finite edge/condition grid/after-return C1/window cutoff/short-track/vacuous C2')

def main():
    setup();cfg=load(PROTOCOL);assert cfg['status']=='frozen'
    for k in ('inventory','regions','head_models','matching_code'):check(cfg[k])
    test=selftest();start=time.time();record('r15e6_core','start',script=binding(__file__),protocol=binding(PROTOCOL),tests=test)
    inv=load(cfg['inventory']['path']);clips={c['alias']:c for c in inv['clips']};models=load(cfg['head_models']['path'])['models'];regions=load(cfg['regions']['path'])
    summary=[];rev=[];manual=[];diags=[];completions=[]
    for src in cfg['sources']:
        for k in ('events','points','e3_completion'):check(src[k])
        clip=clips[src['alias']];e3=load(src['events']['path']);base=e3['conditions']['hybrid_m0'];assert base['evaluable']
        assert e3['manual_events']==clip['manual_events'];assert base['matching']==optimal_match(clip['manual_events'],base['predictions'],1.)
        w=clip['metadata']['width'];h=clip['metadata']['height'];polys={zone:[[x*w,y*h] for x,y in vertices] for zone,vertices in regions[clip['camera']].items()}
        tracks=load_points(src['points']['path']);frags={(f['track_id'],f['fragment_index']):f for f in base['raw_fragments']}
        evs=[evidence(e,tracks[e['track_id']],frags[e['track_id'],e['fragment_index']],clip,models[clip['camera']],polys,cfg) for e in base['predictions']]
        em={e['prediction_id']:e for e in evs};assert len(em)==len(evs)
        conditions={'hybrid_m0':dict(predictions=base['predictions'],matching=base['matching'])}
        for spec in cfg['conditions']:
            ps=[p for p in base['predictions'] if em[p['prediction_id']]['verdicts'][spec['key']]['keep']]
            c=dict(spec=spec,predictions=ps,matching=optimal_match(clip['manual_events'],ps,1.));conditions[spec['key']]=c
            manual+=manual_rows(clip,spec['key'],conditions['hybrid_m0'],c,em)
        details=[]
        for name,c in conditions.items():
            summary+=stats(clip,'imgsz2560',name,c['predictions'],c['matching'])
            ds,ss=reverse(c['predictions'],c['matching'],clip,'imgsz2560',name)
            details +=[dict(r,diagnostic='track_ID') for r in ds if r['diagnostic']=='foot_ID']
            rev +=[dict(r,diagnostic='track_ID') for r in ss if r['diagnostic']=='foot_ID']
        diags+=diagnostic_rows(clip,evs,cfg)
        out=OUT/'clips'/clip['alias'];ep=out/'r15e6_events.json';vp=out/'r15e6_evidence.jsonl';rp=out/'r15e6_reverse_details.json';out.mkdir(parents=True,exist_ok=True)
        write_json(ep,dict(protocol_sha256=sha(PROTOCOL),setting='imgsz2560',alias=clip['alias'],source=src,manual_events=clip['manual_events'],conditions=conditions))
        with vp.open('x',encoding='utf-8',newline='\n') as f:
            for i,e in enumerate(evs,1):f.write(json.dumps(dict(evidence_jsonl_line=i,**e),ensure_ascii=False,allow_nan=False)+'\n')
        write_json(rp,dict(rows=details));done=out/'r15e6_clip_complete.json'
        write_json(done,dict(complete=True,protocol_sha256=sha(PROTOCOL),source=src,files=dict(events=binding(ep),evidence=binding(vp,len(evs)),reverse_details=binding(rp)),
            source_video_path=clip['media_path'],frame_range=[0,clip['metadata']['nb_frames']-1],candidates=len(evs),conditions=len(conditions)))
        completions.append(binding(done));record('r15e6_core','clip_finish',alias=clip['alias'],completion=binding(done),source=src,source_video_path=clip['media_path'],
            frame_range=[0,clip['metadata']['nb_frames']-1],model_weights=cfg['source_detector'])
    scoped=[];sr=[];sd=[]
    for scope in cfg['scopes']:
        scoped +=[dict(scope=scope,**r) for r in summary if in_scope(r['camera'],scope)]
        sr +=[dict(scope=scope,**r) for r in rev if in_scope(r['camera'],scope)]
        sd +=[dict(scope=scope,**r) for r in diags if in_scope(r['camera'],scope)]
    keys=['setting','condition','direction'];vals=['manual_count','predicted_count','matched','missed','extra'];scope=aggregate(scoped,['scope']+keys,vals)
    dv=[k for k in diags[0] if k not in ['setting','alias','camera','phase','condition','direction']]
    rv=['extra_denominator','extra_with_reverse','all_event_denominator','all_events_with_reverse'];rk=keys+['diagnostic','boundary_subset']
    removed=[r for r in manual if r['baseline_candidate_removed']];lost=[r for r in manual if r['lost_time_match']]
    union=[r for r in manual if r['baseline_candidate_removed'] or r['lost_time_match']]
    tables=dict(clip_summary=summary,scope_summary=scope,phase_summary=aggregate(scoped,['scope','phase']+keys,vals),
        camera_summary=aggregate(scoped,['scope','camera']+keys,vals),decision_scope=decisions(scope),
        reverse_clip=rev,reverse_scope=aggregate(sr,['scope']+rk,rv),reverse_phase=aggregate(sr,['scope','phase']+rk,rv),
        diagnostic_clip=diags,diagnostic_scope=aggregate(sd,['scope']+keys,dv),manual_status=manual,removed_baseline_matches=removed,lost_manual=lost,review_manual=union)
    files={name:write_csv(OUT/f'r15e6_{name}.csv',rows,fields=list(manual[0]) if not rows and name in ('removed_baseline_matches','lost_manual','review_manual') else None) for name,rows in tables.items()}
    done=OUT/'r15e6_core_complete.json';unique={(r['alias'],r['manual_event_id']) for r in union}
    write_json(done,dict(complete=True,protocol_sha256=sha(PROTOCOL),script=binding(__file__),support_code=binding(ROOT/'scripts/r15e5_core.py'),
        matching_code=cfg['matching_code'],files=files,clip_completions=completions,review_condition_rows=len(union),unique_review_manual=len(unique),
        removed_condition_rows=len(removed),lost_condition_rows=len(lost),tests=test,elapsed_s=time.time()-start))
    record('r15e6_core','finish',completion=binding(done));print(json.dumps(load(done),ensure_ascii=False))

if __name__=='__main__':main()
