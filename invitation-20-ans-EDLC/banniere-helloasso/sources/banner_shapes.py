import json
exec(open('shapes.py').read().split("PX=794/210")[0])
font=TTFont('fonts/fontsource-open-sans/files/open-sans-latin-800-normal.woff2')
em=440; sc=em/2048; x0=-30; top=-38; base=top+1483*sc
two=glyph_poly(font,'two',em,x0,base); zero=glyph_poly(font,'zero',em,x0+1200*sc,base)
W=4.5
S={}
for n,g in [('2',two),('0',zero)]:
    S['contour_'+n]=g.buffer(W/2,join_style=1); S['fond_'+n]=g.buffer(-W/2,join_style=1)
# pin (goutte) et calendrier
pin=Point(14,14).buffer(14,32).union(Polygon([(1.5,20),(26.5,20),(14,40)])).difference(Point(14,14).buffer(5.5,32))
S['pin']=affinity.translate(pin,1318,92)
cal=box(0,0,30,30).difference(box(3,10,27,27)).union(box(6,-4,10,4)).union(box(20,-4,24,4))
S['cal']=affinity.translate(cal,1317,158)
S['sep']=box(1270,40,1272.5,210)
out={}
for n,g in S.items():
    minx,miny,maxx,maxy=g.bounds
    out[n]=dict(left=round(minx,2),top=round(miny,2),width=round(maxx-minx,2),height=round(maxy-miny,2),path=to_path(g,minx,miny,1),abs=to_path(g,0,0,1))
    print(n,out[n]['left'],out[n]['top'],out[n]['width'],out[n]['height'],len(out[n]['path']))
json.dump(out,open('banner_shapes.json','w'))
