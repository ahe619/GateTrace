"""Exact frozen census pure functions; development constants only; no top-level I/O."""
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict, namedtuple
import configparser
import csv
import io
import math
FPS = 25
EPS = 1e-9
Row = namedtuple('Row', 'frame track_id x0 y0 x1 y1 width height flag class_id visibility source_line')
EXPECTED = {'01': {'transitions': 90, 'confirmed': 74, 'AB_share_3dp': '0.716', 'length': 429, 'coefficients': [-52.619, -20.604, 426.041], 'h_mid': [46.535, 107.638, 168.742, 111.332, 107.638, 103.944], 'windows': 1}, '02': {'transitions': 747, 'confirmed': 597, 'AB_share_3dp': '0.806', 'length': 2782, 'coefficients': [74.839, 0.662, 321.587], 'h_mid': [132.263, 181.823, 231.383, 181.695, 181.823, 181.95], 'windows': 5}}
EXPECTED_INPUTS = {'MOT20-01': {'gt': '89fd0196d67a5eb6011a470dc2a49b02255403b49e8848031cdf99add8a36d9c', 'seqinfo': '5850098d845d1a92c4b8649ee7ab4e2b7ef2b0a2104eb855cdef9a8e93da0a5e'}, 'MOT20-02': {'gt': '10abe457a67d9919a9cbfe821d3619c8e6174c2b0ed7ecf4cb68c1fd6cad58de', 'seqinfo': 'e94c47840038e71e84613eeda0a9635728de1e488b56c5b05b16f68ff7305a44'}}
SOURCE_BINDINGS = [{'path': 'scripts/r15e24_census.py', 'bytes': 32540, 'sha256': '4a6751111fde5888bd619f742012f4e9dd478ef381f8be7aa5886a45825ebbad', 'functions': [{'name': 'require', 'original_file': 'scripts/r15e24_census.py', 'first_line': 54, 'last_line': 56, 'source_sha256': 'c40d3ac8196e4ffcd6b0aab606bca6595c6543ec0f53f3274de08d4dd26b8445', 'byte_exact_source_excerpt': True}, {'name': 'parse_seqinfo', 'original_file': 'scripts/r15e24_census.py', 'first_line': 183, 'last_line': 192, 'source_sha256': '51c40a01df152ece11925a0da8632ab496d538b3ac31bfe265ca30d29f67bbca', 'byte_exact_source_excerpt': True}, {'name': 'int_value', 'original_file': 'scripts/r15e24_census.py', 'first_line': 195, 'last_line': 197, 'source_sha256': '77790cdefda3a56e9e7045df00820e8770a6b853bfd8ec2cb439f335bb1bf378', 'byte_exact_source_excerpt': True}, {'name': 'parse_gt', 'original_file': 'scripts/r15e24_census.py', 'first_line': 200, 'last_line': 230, 'source_sha256': 'f3e7163ed606acadf6025fce4de5700dbe4c3884c19d91fb57e462bc72e098dc', 'byte_exact_source_excerpt': True}, {'name': 'foot', 'original_file': 'scripts/r15e24_census.py', 'first_line': 233, 'last_line': 236, 'source_sha256': 'e59e865deb7ee9deff78accf7e64037df69ab1ebda31761e5496836ab9bba9bb', 'byte_exact_source_excerpt': True}, {'name': 'fit_model', 'original_file': 'scripts/r15e24_census.py', 'first_line': 239, 'last_line': 252, 'source_sha256': 'cffdec5d0dee4c002bf9c5876a1813589f6c4261074112b0cd29794253569800', 'byte_exact_source_excerpt': True}, {'name': 'height_at_foot', 'original_file': 'scripts/r15e24_census.py', 'first_line': 255, 'last_line': 261, 'source_sha256': '42e972be323ba4e04128b478d38180881dbce06674dbc799df73fc1f45c43076', 'byte_exact_source_excerpt': True}, {'name': 'make_lines', 'original_file': 'scripts/r15e24_census.py', 'first_line': 264, 'last_line': 284, 'source_sha256': 'fa50bde058d44af4471eba3b956b7bc7a5041388a010454d78be4bb2736abfb6', 'byte_exact_source_excerpt': True}, {'name': 'windows_for', 'original_file': 'scripts/r15e24_census.py', 'first_line': 287, 'last_line': 293, 'source_sha256': '9b7c2c941945e633b38b8121a35250e929dec8906aaa7171c01081ac5fc4342f', 'byte_exact_source_excerpt': True}, {'name': 'edge_distance', 'original_file': 'scripts/r15e24_census.py', 'first_line': 296, 'last_line': 301, 'source_sha256': '46b790384b5ccd1e9e91942c867c946bb36721fc397ebff52250874f79e853e0', 'byte_exact_source_excerpt': True}, {'name': 'observation', 'original_file': 'scripts/r15e24_census.py', 'first_line': 304, 'last_line': 310, 'source_sha256': 'e0c53cd423b4292beb9a1a0f14fce0621b65f23b56bce409ec3c62a78cc6b9b5', 'byte_exact_source_excerpt': True}, {'name': 'truth_confirmation', 'original_file': 'scripts/r15e24_census.py', 'first_line': 313, 'last_line': 332, 'source_sha256': 'dbab07558377bf708b1ed388ce0dc55ea3bc2ac110b089be5940bdd362b58d57', 'byte_exact_source_excerpt': True}, {'name': 'attributes', 'original_file': 'scripts/r15e24_census.py', 'first_line': 335, 'last_line': 358, 'source_sha256': 'ebed0387d59c5ea9a0e4c12de2eaf6724932aef2276f17f2516ef95f35806d26', 'byte_exact_source_excerpt': True}, {'name': 'summarize_population', 'original_file': 'scripts/r15e24_census.py', 'first_line': 361, 'last_line': 375, 'source_sha256': '2b169aeb5e59c7186d42f0e73f663aec919bbf2bf6b02ea38753ec455ede94ca', 'byte_exact_source_excerpt': True}]}]

def require(value, message):
    if not value:
        raise ValueError(message)


def parse_seqinfo(content, seq):
    parser = configparser.ConfigParser(interpolation=None)
    parser.read_string(content.decode('utf-8-sig'))
    p = parser['Sequence']
    result = dict(sequence=f'MOT20-{seq}', fps=int(p['frameRate']), width=int(p['imWidth']),
                  height=int(p['imHeight']), seqLength=int(p['seqLength']))
    require(result['fps'] == FPS, 'Unexpected FPS; stop rather than adapt')
    require(result['seqLength'] == EXPECTED[seq]['length'], 'Unexpected sequence length')
    require(result['width'] > 1 and result['height'] > 1, 'Invalid native dimensions')
    return result


def int_value(value, field):
    require(math.isfinite(value) and value.is_integer(), 'Non-integer GT '+field)
    return int(value)


def parse_gt(content, meta):
    primary = []
    static = defaultdict(list)
    class_counts = Counter()
    seen = set()
    total = 0
    for line, cells in enumerate(csv.reader(io.StringIO(content.decode('utf-8-sig'))), 1):
        if not cells or all(not x.strip() for x in cells):
            continue
        require(len(cells) == 9, f'Expected 9 GT columns at physical line {line}')
        values = list(map(float, cells))
        require(all(math.isfinite(v) for v in values), f'Nonfinite GT at line {line}')
        f, tid = int_value(values[0], 'frame'), int_value(values[1], 'id')
        flag, cls = int_value(values[6], 'flag'), int_value(values[7], 'class')
        left, top, w, h = values[2:6]
        require(1 <= f <= meta['seqLength'] and w > 0 and h > 0, f'Invalid GT frame/box at line {line}')
        x0, y0 = left-1, top-1
        row = Row(f, tid, x0, y0, x0+w, y0+h, w, h, flag, cls, values[8], line)
        total += 1
        class_counts[(flag,cls)] += 1
        if flag == 1 and cls == 1:
            require(0 <= row.visibility <= 1, f'Primary visibility outside [0,1] at line {line}')
            require((f,tid) not in seen, f'Duplicate primary GT ID/frame at line {line}')
            seen.add((f,tid))
            primary.append(row)
        if cls == 11:
            static[f].append(row)
    primary.sort(key=lambda r:(r.frame,r.track_id,r.source_line))
    return primary, static, dict(original_rows=total,primary_rows=len(primary),
        original_class_flag_counts=[dict(flag=k[0],class_id=k[1],rows=v) for k,v in sorted(class_counts.items())],
        class11_rows_all_flags=sum(len(v) for v in static.values()))


def foot(row, width, height):
    if row.x0 <= 0 or row.x1 >= width-1 or row.y1 >= height-1:
        return None
    return [row.x0+row.width/2, row.y1]


def fit_model(rows, meta, np):
    W,H = meta['width'],meta['height']
    fit = [r for r in rows if r.x0>0 and r.x1<W-1 and r.y0>0 and r.y1<H-1]
    require(len(fit)>=3, 'Insufficient G1 fit rows')
    X = np.array([[1.,(r.x0+r.width/2)/W,r.y0/H] for r in fit],dtype=np.float64)
    y = np.array([r.height for r in fit],dtype=np.float64)
    coef,residuals,rank,singular = np.linalg.lstsq(X,y,rcond=None)
    require(rank==3 and bool(np.isfinite(coef).all()),'G1 fit not full rank/finite')
    return dict(coefficients=coef.tolist(),coefficient_order=['a','b','c'],rank=int(rank),fitting_rows=len(fit),
        residual_sum_squares=residuals.tolist(),singular_values=singular.tolist(),
        fitting_coordinate_range=dict(x_normalized=[float(X[:,1].min()),float(X[:,1].max())],
            y_top_normalized=[float(X[:,2].min()),float(X[:,2].max())]),
        parameterization='h=a+b*x_center/W+c*y_top/H',foot_height_formula='(a+b*x/W+c*y/H)/(1+c/H)',
        numpy_version=np.__version__,native_size=[W,H],full_precision=True)


def height_at_foot(model,x,y):
    a,b,c=model['coefficients'];W,H=model['native_size']
    denominator=1+c/H
    require(math.isfinite(denominator) and denominator!=0,'Invalid G1 inverse denominator')
    value=(a+b*x/W+c*y/H)/denominator
    require(math.isfinite(value) and value>0,'Nonpositive/nonfinite h_mid')
    return value


def make_lines(seq,meta,model):
    W,H=meta['width'],meta['height'];result=[]
    for index,(orientation,fraction) in enumerate([('H',.30),('H',.50),('H',.70),('V',.25),('V',.50),('V',.75)]):
        if orientation=='H':
            c=fraction*H;lo=.02*W;hi=.98*W;middle=[W/2,c]
        else:
            c=fraction*W;lo=.02*H;hi=.98*H;middle=[c,H/2]
        h=height_at_foot(model,*middle);g=.05*h;depth=h
        if orientation=='H':
            polys=dict(tunnel=[[hi,c-g],[lo,c-g],[lo,c-g-depth],[hi,c-g-depth]],
                       plaza=[[lo,c+g],[hi,c+g],[hi,c+g+depth],[lo,c+g+depth]])
        else:
            polys=dict(tunnel=[[c-g,lo],[c-g,hi],[c-g-depth,hi],[c-g-depth,lo]],
                       plaza=[[c+g,hi],[c+g,lo],[c+g+depth,lo],[c+g+depth,hi]])
        inframe=all(0<=x<=W-1 and 0<=y<=H-1 for poly in polys.values() for x,y in poly)
        result.append(dict(sequence=f'MOT20-{seq}',line_id=f'{orientation}_{int(round(fraction*100)):02d}',
            orientation=orientation,fraction=fraction,line_coordinate_px=c,line_extent_px=[lo,hi],
            midpoint_native_px=middle,h_mid=h,gap_half_width=g,zone_depth=depth,polygons=polys,
            facing_edges_zero_based={'tunnel':[0],'plaza':[0]},AB_direction='IN',all_vertices_in_image=inframe,
            expected_h_mid=EXPECTED[seq]['h_mid'][index],h_mid_absolute_error=abs(h-EXPECTED[seq]['h_mid'][index])))
    return result


def windows_for(seq):
    if seq=='01':
        return [dict(window_id='w00',frame_interval_zero_based_half_open=[0,429],
                     gt_frame_interval_one_based_half_open=[1,430],time_interval_half_open=[0.,17.16])]
    return [dict(window_id=f'w{k:02d}',frame_interval_zero_based_half_open=[125+500*k,625+500*k],
                 gt_frame_interval_one_based_half_open=[126+500*k,626+500*k],time_interval_half_open=[5+20*k,25+20*k])
            for k in range(EXPECTED[seq]['windows'])]


def edge_distance(point,a,b):
    dx,dy=b[0]-a[0],b[1]-a[1]
    length2=dx*dx+dy*dy
    require(length2>0,'Degenerate facing edge')
    u=max(0.,min(1.,((point[0]-a[0])*dx+(point[1]-a[1])*dy)/length2))
    return math.hypot(point[0]-a[0]-u*dx,point[1]-a[1]-u*dy)


def observation(row,meta,polys,api):
    point=foot(row,meta['width'],meta['height'])
    distances={k:None if point is None else api['signed_distance'](point,p) for k,p in polys.items()}
    return dict(frame=row.frame-1,gt_frame_1based=row.frame,time_s=(row.frame-1)/FPS,
        track_id=row.track_id,point=point,point_source='gt_amodal_bottom_center_T2',signed_distances=distances,
        gt_file_physical_line=row.source_line,gt_box_height_px=row.height,
        gt_box_xyxy_native=[row.x0,row.y0,row.x1,row.y1])


def truth_confirmation(event,track,frames,polys,meta,api):
    fg=event['endpoints'][-1]['gt_frame_1based'];target=event['target_zone'];poly=polys[target]
    selected=track[bisect_left(frames,fg):bisect_right(frames,fg+50)]
    eligible=0;target_count=0;first=None;max_ratio=None
    for row in selected:
        point=foot(row,meta['width'],meta['height'])
        if point is None:continue
        eligible+=1
        distances={k:api['signed_distance'](point,p) for k,p in polys.items()}
        if api['zone_from_distances'](distances,0)!=target:continue
        target_count+=1;distance=edge_distance(point,poly[0],poly[1]);ratio=distance/row.height
        max_ratio=ratio if max_ratio is None else max(max_ratio,ratio)
        if first is None and distance+EPS>=.2*row.height:
            first=dict(gt_frame_1based=row.frame,frame_zero_based=row.frame-1,time_s=(row.frame-1)/FPS,
                gt_file_physical_line=row.source_line,point_native_px=point,own_gt_box_height_px=row.height,
                distance_to_finite_target_edge0_px=distance,normalized_depth=ratio)
    return dict(confirmed=first is not None,first_confirming_observation=first,
        search_gt_frames_inclusive=[fg,fg+50],observed_rows=len(selected),valid_point_rows=eligible,
        target_zone_rows=target_count,maximum_target_depth_ratio=max_ratio,
        uses_own_height_not_G1=True,no_additional_fragment_or_full_tail_condition=True)


def attributes(event,track,frames,frame_rows,static):
    fg=event['endpoints'][-1]['gt_frame_1based']
    target=track[bisect_left(frames,fg)]
    require(target.frame==fg,'Missing GT target frame')
    nearby=track[bisect_left(frames,fg-25):bisect_right(frames,fg+25)]
    mean=sum(r.visibility for r in nearby)/len(nearby)
    point=event['endpoints'][-1]['point'];rho=0
    for other in frame_rows[fg]:
        if other.track_id!=target.track_id and math.hypot(other.x0+other.width/2-point[0],other.y1-point[1])<=target.height:
            rho+=1
    occ=False;first_overlap=None
    for row in nearby:
        for obj in static.get(row.frame,[]):
            intersection=max(0.,min(row.x1,obj.x1)-max(row.x0,obj.x0))*max(0.,min(row.y1,obj.y1)-max(row.y0,obj.y0))
            ioa=intersection/(row.width*row.height)
            if ioa>=.2:
                occ=True
                if first_overlap is None:
                    first_overlap=dict(gt_frame_1based=row.frame,person_gt_line=row.source_line,
                                       class11_gt_line=obj.source_line,class11_flag=obj.flag,intersection_over_person_area=ioa)
    return dict(mean_visibility=mean,visibility_observed_rows=len(nearby),visibility_gt_frames_inclusive=[fg-25,fg+25],
        visibility_bin=('low' if mean<.25 else 'mid_low' if mean<.5 else 'mid_high' if mean<.75 else 'high'),
        rho=rho,h_g=target.height,static_occ=occ,first_static_occ_evidence=first_overlap,
        rho_includes_boundary_invalid_other_raw_feet=True)


def summarize_population(events,np):
    confirmed=[e for e in events if e['confirmed']]
    bins={k:sum(e['attributes']['visibility_bin']==k for e in confirmed) for k in ('low','mid_low','mid_high','high')}
    rho=[e['attributes']['rho'] for e in confirmed]
    if rho:
        q1,q2=[float(v) for v in np.quantile(np.array(rho,dtype=np.float64),[1/3,2/3],method='linear')]
        tertile_counts=dict(low=sum(x<=q1 for x in rho),mid=sum(q1<x<=q2 for x in rho),high=sum(x>q2 for x in rho))
    else:q1=q2=None;tertile_counts=dict(low=0,mid=0,high=0)
    ab=sum(e['direction']=='IN' for e in confirmed)
    return dict(transitions=len(events),confirmed=len(confirmed),dont_care=len(events)-len(confirmed),
        confirmed_IN=ab,confirmed_OUT=len(confirmed)-ab,AB_share=None if not confirmed else ab/len(confirmed),
        AB_share_3dp=None if not confirmed else format(ab/len(confirmed),'.3f'),visibility_bins=bins,
        rho_tertiles=dict(q1=q1,q2=q2,counts=tertile_counts,method='linear; <=q1 / q1<x<=q2 / >q2'),
        static_occ_confirmed=sum(e['attributes']['static_occ'] for e in confirmed),
        static_occ_all_transitions=sum(e['attributes']['static_occ'] for e in events))
