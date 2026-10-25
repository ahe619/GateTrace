def fresh_raw(saved):
    """Retain raw pixels/indices, discard old identity/point fields before replay."""
    result=[]
    for i,d in enumerate(saved):
        require(d['raw_detection_index']==i,'Saved raw index mismatch')
        result.append(dict(raw_detection_index=i,box=copy.deepcopy(d['box']),confidence=d['confidence'],class_id=d['class_id'],
            pose_available=d.get('pose_available',d.get('keypoints') is not None),keypoints=copy.deepcopy(d.get('keypoints')),
            track_id=None))
    return result
