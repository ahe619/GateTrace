class ByteTrackTracker:
    """One fresh shared idxfix ByteTrack per sequence; preserves every raw row.

    update(raw,image=None,native_shape=(H,W)) returns (all_raw, tracker_rows).
    Returned tracker_rows last column is mapped to the original complete raw
    list. The passed high-score sublist mapping is explicit in frame metadata.
    """
    def __init__(self,reader,fps=25):
        _require(float(fps)==25.0,'MOT20 tracker frame_rate is frozen at 25')
        self.reader=reader
        self.last_frame_metadata=None
        self._runtime_packages=_register_packages(reader,('numpy','scipy','lap','yaml','ultralytics'))
        self.np=_seed(False)
        _bound_bytes(reader,_root()/'scripts/r15_tracker_idxfix.py',IDXFIX_SHA,'Verify shared frozen idxfix before tracker construction')
        adapter,self._adapter_ref=_load_adapter(reader,'r15e17_trackers.py',TRACKER_ADAPTER_SHA)
        self.backend=adapter.SmokeTracker(kind='P2',fps=25,gate=reader)
        self._frames=0;self._all_raw=0;self._eligible=0;self._no_image_frames=0

    def reset(self):
        self.backend.reset()
        self._frames=0;self._all_raw=0;self._eligible=0;self._no_image_frames=0
        self.last_frame_metadata=None

    def _without_image(self,high,shape):
        """Same frozen validation/arithmetic, with known shape and no pixels."""
        from copy import deepcopy
        import math
        np=self.np;rows=[]
        for d in high:
            box=d['box'];score=float(d['confidence']);cls=float(d['class_id'])
            _require(len(box)==4 and all(math.isfinite(float(x)) for x in box),'Nonfinite native detector box')
            _require(math.isfinite(score) and .25<=score<=1,'Tracker input must be >= .25')
            _require(math.isfinite(cls) and cls.is_integer(),'Class must be integral')
            rows.append([*box,score,cls])
        array=np.asarray(rows,dtype=np.float32).reshape((-1,6))
        boxes=self.backend.Boxes(array,orig_shape=shape)
        tracks=self.backend.tracker.update(boxes,None)
        matrix=np.asarray(tracks)
        if matrix.size==0:matrix=np.empty((0,8),dtype=np.float32)
        _require(matrix.ndim==2 and matrix.shape[1]==8 and bool(np.isfinite(matrix).all()),'Unexpected tracker matrix')
        by_index={};ids=set()
        for row in matrix:
            raw_index,track_id=float(row[-1]),float(row[4])
            _require(raw_index.is_integer() and 0<=raw_index<len(high),'Invalid tracker input index')
            _require(track_id.is_integer() and track_id>0,'Invalid tracker ID')
            j,tid=int(raw_index),int(track_id)
            _require(j not in by_index and tid not in ids,'Tracker index/ID is not one-to-one')
            _require(row[5]==array[j,4] and row[6]==array[j,5],'Indexed score/class differ')
            by_index[j]=tid;ids.add(tid)
        output=[]
        for j,d in enumerate(high):
            item=deepcopy(d);item['track_id']=by_index.get(j);output.append(item)
        self.backend.counts.update(frames=1,empty_frames=int(not high),input_detections=len(high),
            returned_tracks=len(matrix),frames_with_all_high_pool=1,validated_index_frames=1)
        self.backend.image_shapes[str(tuple(shape))]+=1
        return output,matrix.tolist()

    def update(self,raw_detections,image=None,native_shape=None):
        from copy import deepcopy
        import math
        _require(isinstance(raw_detections,(list,tuple)),'Raw detections must preserve list order')
        if image is None:
            _require(isinstance(native_shape,(tuple,list)) and len(native_shape)==2 and
                     all(type(v) is int and v>0 for v in native_shape),'O1 without image requires native_shape=(H,W)')
            shape=tuple(native_shape)
        else:
            shape=_native_bgr(image,self.np)
            _require(native_shape is None or tuple(native_shape)==shape,'native_shape disagrees with image')
        output=deepcopy(list(raw_detections));eligible=[]
        for i,d in enumerate(output):
            _require(d.get('raw_detection_index')==i,'Expected consecutive complete raw indices')
            score=float(d['confidence'])
            _require(math.isfinite(score) and 0<=score<=1,'Invalid raw confidence')
            _require(d.get('track_id') is None,'Tracker input must not contain supplied/GT track identities')
            d['track_id']=None;d['tracking_eligible']=score>=.25
            if score>=.25:eligible.append(i)
        high=[output[i] for i in eligible]
        if image is None:
            tracked,native_rows=self._without_image(high,shape);self._no_image_frames+=1
        else:
            tracked,native_rows=self.backend.update(high,image)
        _require(len(tracked)==len(high),'Tracker wrapper dropped high-score detections')
        for j,d in enumerate(tracked):
            raw_i=eligible[j]
            _require(d['raw_detection_index']==raw_i,'Original raw index changed in tracking')
            _require(d['box']==output[raw_i]['box'] and d.get('keypoints')==output[raw_i].get('keypoints'),
                     'Tracker substituted raw geometry/keypoints')
            output[raw_i]['track_id']=d['track_id']
        returned=[]
        for row in native_rows:
            mapped=list(row);j=int(mapped[-1]);_require(float(mapped[-1])==j and 0<=j<len(eligible),'Invalid tracker sublist index')
            mapped[-1]=eligible[j];returned.append(mapped)
        self._frames+=1;self._all_raw+=len(output);self._eligible+=len(eligible)
        self.last_frame_metadata=dict(native_shape=list(shape),image_supplied=image is not None,
            raw_detection_count=len(output),tracking_eligible_count=len(eligible),tracked_count=sum(d['track_id'] is not None for d in output),
            tracker_input_raw_indices=list(eligible),tracker_rows_last_column='global complete raw_detection_index',
            original_tracker_indices=[int(r[-1]) for r in native_rows])
        return output,returned

    @property
    def metadata(self):
        from copy import deepcopy
        return dict(kind='shared_idxfix_ByteTrack',seed=SEED,adapter=self._adapter_ref,
            backend=deepcopy(self.backend.metadata()),runtime_packages=deepcopy(self._runtime_packages),
            frames=self._frames,all_raw_detections=self._all_raw,tracking_eligible_detections=self._eligible,
            frames_without_image=self._no_image_frames,synthetic_pixels_created=False,
            tracker_input_threshold='confidence >= 0.25',low_raw_policy='retained with track_id=None',
            tracker_output_columns=['x1','y1','x2','y2','track_id','score','class','raw_detection_index'])
