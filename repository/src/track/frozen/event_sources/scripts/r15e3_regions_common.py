"""Double precision native-pixel polygon membership; no geometry edits."""
from __future__ import annotations
import json
import math
from pathlib import Path


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


class RegionClassifier:
    def __init__(self,region_path,size=(3840,2160)):
        self.path=Path(region_path)
        self.regions=json.loads(self.path.read_text(encoding='utf-8-sig'))
        self.size=list(size)
        self.native={camera:{name:[[float(x)*size[0],float(y)*size[1]] for x,y in poly]
            for name,poly in zones.items()} for camera,zones in self.regions.items()}
        assert set(self.native)==set('ABCDEF')
        assert all(set(zones)=={'tunnel','plaza'} for zones in self.native.values())

    def signed_distances(self,camera,point):
        if point is None or len(point)!=2 or not all(math.isfinite(float(x)) for x in point):
            return dict(tunnel=None,plaza=None)
        return {name:signed_distance(point,poly) for name,poly in self.native[camera].items()}

    def classify(self,camera,point,m=0):
        distances=self.signed_distances(camera,point)
        matched=[name for name,d in distances.items() if d is not None and d>=float(m)-1e-9]
        if len(matched)>1:raise ValueError(f'Overlapping zones at {camera}:{point}')
        return matched[0] if matched else 'gap'

    def tunnel_boundary(self,camera,point):
        result=nearest_boundary(point,self.native[camera]['tunnel'])
        result['signed_distance']=signed_distance(point,self.native[camera]['tunnel'])
        result['arc_fraction']=result['arc_px']/result['perimeter_px']
        return result


def selftest():
    square=[[0.,0.],[10.,0.],[10.,10.],[0.,10.]]
    assert signed_distance([5,5],square)==5
    assert signed_distance([0,3],square)==0
    assert signed_distance([-1,3],square)==-1
    concave=[[0.,0.],[10.,0.],[10.,4.],[4.,4.],[4.,10.],[0.,10.]]
    assert signed_distance([8,8],concave)<0
    assert signed_distance([2,8],concave)==2
    assert nearest_boundary([5,-1],square)['edge_fraction']==.5
    return dict(passed=True,synthetic_tests=6,randomness=False)


if __name__=='__main__':print(selftest())
