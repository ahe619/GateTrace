"""Pure E3 head-to-foot affine fitting and point selection; no model inference."""
from __future__ import annotations
import math
import numpy as np


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


def positive_box_overlap(a,b):
    return min(a[2],b[2]) > max(a[0],b[0]) and min(a[3],b[3]) > max(a[1],b[1])


def fit_sample(detection, other_boxes, size, confidence=.5):
    """Return all exclusion reasons; no outcome-dependent filtering."""
    w,h=size;box=detection['box'];head,head_indices=keypoint_mean(detection,range(5),confidence)
    ankle,ankle_indices=keypoint_mean(detection,(15,16),confidence,True)
    reasons=[]
    if detection.get('track_id') is None:reasons.append('untracked')
    if head is None:reasons.append('head_unavailable')
    if ankle is None:reasons.append('both_ankles_unavailable')
    if not (len(box)==4 and all(math.isfinite(float(x)) for x in box)
            and 0 < box[0] < box[2] < w and 0 < box[1] < box[3] < h):
        reasons.append('bbox_not_strictly_inside_frame')
    overlap_count=sum(positive_box_overlap(box,other) for other in other_boxes)
    if overlap_count:reasons.append('positive_area_bbox_overlap')
    height=ankle[1]-head[1] if head is not None and ankle is not None else None
    if height is not None and (not math.isfinite(height) or height <= 0):
        reasons.append('nonpositive_or_nonfinite_observed_height')
    return dict(eligible=not reasons,exclusion_reasons=reasons,head_indices=head_indices,
        ankle_indices=ankle_indices,head_xy=head,ankle_xy=ankle,height_native_px=height,
        head_x_norm=head[0]/w if head else None,head_y_norm=head[1]/h if head else None,
        head_minus_ankle_x_px=head[0]-ankle[0] if head and ankle else None,
        overlapping_raw_box_count=overlap_count)


def standardized_design(x,rank_rtol=1e-8):
    """Rank check in normalized centered/scaled coordinates, intercept retained."""
    x=np.asarray(x,dtype=np.float64).reshape(-1,2)
    if not len(x):return None,dict(rank=0,mean=None,scale=None,singular_values=[])
    mean=x.mean(axis=0);scale=x.std(axis=0)
    safe=np.where(scale>0,scale,1.)
    z=np.column_stack((np.ones(len(x)),(x-mean)/safe))
    singular=np.linalg.svd(z,compute_uv=False)
    rank=int(np.count_nonzero(singular > singular[0]*rank_rtol)) if len(singular) and singular[0]>0 else 0
    return z,dict(rank=rank,mean=mean.tolist(),scale=safe.tolist(),raw_scale=scale.tolist(),
        singular_values=singular.tolist(),rank_relative_tolerance=rank_rtol)


def affine_ols(samples,rank_rtol=1e-8):
    x=[[r['head_x_norm'],r['head_y_norm']] for r in samples]
    z,design=standardized_design(x,rank_rtol)
    if design['rank'] != 3:
        return dict(available=False,status='unavailable_design_rank_below_3',design=design,
                    sample_count=len(samples),coefficients=None)
    beta=np.linalg.lstsq(z,np.asarray([r['height_native_px'] for r in samples]),rcond=rank_rtol)[0]
    mean=np.asarray(design['mean']);scale=np.asarray(design['scale'])
    slopes=beta[1:]/scale
    coeff=[float(beta[0]-np.dot(slopes,mean)),*map(float,slopes)]
    return dict(available=True,status='available',design=design,sample_count=len(samples),coefficients=coeff,
                coefficient_order=['intercept_native_px','head_x_norm','head_y_norm'])


def predict_height(model,head,size):
    if not model.get('available'):return None
    a,b,c=model['coefficients'];return float(a+b*head[0]/size[0]+c*head[1]/size[1])


def error_summary(errors):
    """One sample one weight, including signed errors for audit."""
    keys=('absolute_height_error_px','absolute_foot_x_error_px','absolute_foot_y_error_px','foot_xy_error_px')
    result=dict(sample_count=len(errors))
    for key in keys:
        a=np.asarray([r[key] for r in errors],dtype=float)
        result[key]=dict(median=float(np.median(a)) if len(a) else None,
            p90=float(np.quantile(a,.9,method='linear')) if len(a) else None,
            rmse=float(np.sqrt(np.mean(a*a))) if len(a) else None)
    return result


def errors_for(samples,model,kind,heldout_group=None):
    out=[]
    for r in samples:
        pred=float(np.dot([1.,r['head_x_norm'],r['head_y_norm']],model['coefficients']))
        dy=pred-r['height_native_px'];dx=r['head_minus_ankle_x_px']
        out.append(dict(sample_id=r['sample_id'],sample_csv_line=r.get('sample_csv_line'),
            group=r['group'],kind=kind,heldout_group=heldout_group,
            predicted_height_px=pred,observed_height_px=r['height_native_px'],
            signed_height_error_px=dy,absolute_height_error_px=abs(dy),
            signed_foot_x_error_px=dx,signed_foot_y_error_px=dy,
            absolute_foot_x_error_px=abs(dx),absolute_foot_y_error_px=abs(dy),
            foot_xy_error_px=math.hypot(dx,dy),prediction_nonpositive=pred<=0))
    return out


def fit_camera(samples,rank_rtol=1e-8):
    model=affine_ols(samples,rank_rtol);groups=sorted({r['group'] for r in samples})
    model['track_group_count']=len(groups)
    train=errors_for(samples,model,'full_train') if model['available'] else []
    folds=[];cv=[]
    for group in groups:
        train_samples=[r for r in samples if r['group'] != group]
        test_samples=[r for r in samples if r['group'] == group]
        fold=affine_ols(train_samples,rank_rtol)
        fold.update(heldout_group=group,heldout_sample_count=len(test_samples),
                    train_track_group_count=len(groups)-1)
        errs=errors_for(test_samples,fold,'leave_one_track_out',group) if fold['available'] else []
        fold['error_summary']=error_summary(errs);folds.append(fold);cv.extend(errs)
    model.update(full_training_errors=error_summary(train),leave_one_track_out=error_summary(cv),
        loto_valid_folds=sum(f['available'] for f in folds),loto_total_folds=len(folds),
        loto_valid_samples=len(cv),loto_total_samples=len(samples),
        loto_sample_coverage=len(cv)/len(samples) if samples else None,
        fitting_coordinate_range={key:[min(r[key] for r in samples),max(r[key] for r in samples)] if samples else None
                                  for key in ('head_x_norm','head_y_norm','height_native_px')},
        interpretation='Diagnostic errors against stored pose-derived ankles in source clips; not independent physical foot truth or out-of-camera generalization')
    return model,folds,train+cv


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


def selftest():
    samples=[]
    for i,(x,y,g) in enumerate([(0,0,'a'),(1,0,'a'),(0,1,'b'),(1,1,'b'),(.2,.7,'c'),(.8,.3,'c')]):
        samples.append(dict(sample_id=str(i),group=g,head_x_norm=x,head_y_norm=y,
            height_native_px=100+20*x+30*y,head_minus_ankle_x_px=3.))
    model,folds,errors=fit_camera(samples)
    assert model['available'] and model['loto_valid_folds']==3
    assert np.allclose(model['coefficients'],[100,20,30])
    assert model['full_training_errors']['foot_xy_error_px']['median']>=3.
    assert not affine_ols(samples[:2])['available']
    assert not positive_box_overlap([0,0,1,1],[1,0,2,1])
    assert positive_box_overlap([0,0,1,1],[.9,0,2,1])
    return dict(status='passed',synthetic_only=True)


if __name__=='__main__':print(selftest())
