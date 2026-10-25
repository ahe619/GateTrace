class MethodTracker:
    """Threshold-only adaptation around the frozen idxfix association engine."""
    def __init__(self,gate,threshold):
        require(threshold in (.1,.25),'Undeclared tracker threshold')
        from r15e24_inference import ByteTrackTracker
        self.base=ByteTrackTracker(gate,fps=25);self.np=self.base.np;self.threshold=threshold
        self.frames=0;self.low_frames=0;self.low_boxes=0;self.last_frame_metadata=None
    def update(self,raw,native_shape):
        np=self.np;output=copy.deepcopy(raw);eligible=[]
        for i,d in enumerate(output):
            require(d['raw_detection_index']==i,'Raw indices are not consecutive')
            require(d.get('track_id') is None,'Supplied track ID must be removed before retracking')
            require(math.isfinite(float(d['confidence'])) and 0<=d['confidence']<=1,'Invalid score')
            d['tracking_eligible']=d['confidence']>=self.threshold
            if d['tracking_eligible']:eligible.append(i)
        a=np.asarray([[*output[i]['box'],output[i]['confidence'],output[i]['class_id']] for i in eligible],dtype=np.float32).reshape(-1,6)
        require(bool(np.isfinite(a).all()),'Nonfinite tracker input')
        boxes=self.base.backend.Boxes(a,orig_shape=tuple(native_shape))
        matrix=np.asarray(self.base.backend.tracker.update(boxes,None))
        if matrix.size==0:matrix=np.empty((0,8),dtype=np.float32)
        require(matrix.ndim==2 and matrix.shape[1]==8 and bool(np.isfinite(matrix).all()),'Unexpected tracker output')
        rows=[];seen=set();ids=set()
        for rr in matrix:
            j,tid=float(rr[-1]),float(rr[4])
            require(j.is_integer() and 0<=j<len(eligible),'Invalid idxfix tracker index')
            require(tid.is_integer() and tid>0,'Invalid tracker ID');j=int(j);tid=int(tid)
            require(j not in seen and tid not in ids,'Duplicate tracker index/ID');seen.add(j);ids.add(tid)
            require(rr[5]==a[j,4] and rr[6]==a[j,5],'Indexed tracker score/class mismatch')
            raw_i=eligible[j];output[raw_i]['track_id']=tid
            row=rr.tolist();row[-1]=raw_i;rows.append(row)
        low=sum(self.threshold<=output[i]['confidence']<.25 for i in eligible)
        self.frames+=1;self.low_frames+=int(low>0);self.low_boxes+=low
        self.last_frame_metadata=dict(raw_detection_count=len(output),tracking_eligible_count=len(eligible),
            low_pool_input_count=low,tracking_threshold=self.threshold,tracker_input_raw_indices=eligible,
            original_tracker_indices=[int(r[-1]) for r in matrix],tracker_rows_last_column='global complete raw_detection_index')
        return output,rows
    @property
    def metadata(self):
        return dict(kind='r15e26_threshold_only_idxfix',association_engine='unchanged shared idxfix ByteTrack',
            association_parameters=dict(self.base.backend.args),tracking_threshold=self.threshold,
            frames=self.frames,low_pool_frames=self.low_frames,low_pool_boxes=self.low_boxes,
            adapter_sha256=FROZEN['r15_tracker_idxfix.py'],runtime_packages=self.base._runtime_packages)
