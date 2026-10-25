def point_for(box,width,height,is_gt=None):
    x0,y0,x1,y1=map(float,box);p=[(x0+x1)/2,y1]
    if not all(math.isfinite(x) for x in p):return None,'nonfinite',False
    outside=not(0<=p[0]<width and 0<=p[1]<height)
    if x0<=0 or x1>=width-1 or y1>=height-1:return None,'T2_boundary',outside
    return p,None,outside
