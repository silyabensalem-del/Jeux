import json
exec(open('shapes.py').read().split("PX=794/210")[0])
font=TTFont('fonts/fontsource-open-sans/files/open-sans-latin-800-normal.woff2')
em=700; sc=em/2048; x0=-90; top=106; base=top+1483*sc
two=glyph_poly(font,'two',em,x0,base); zero=glyph_poly(font,'zero',em,x0+1200*sc,base)
W=6; S={}
for n,g in [('2',two),('0',zero)]:
    S['contour_'+n]=g.buffer(W/2,join_style=1); S['fond_'+n]=g.buffer(-W/2,join_style=1)
S['barre']=box(752,338,812,343)
out={}
for n,g in S.items():
    minx,miny,maxx,maxy=g.bounds
    out[n]=dict(left=round(minx,2),top=round(miny,2),width=round(maxx-minx,2),height=round(maxy-miny,2),path=to_path(g,minx,miny,1),abs=to_path(g,0,0,1))
    print(n,out[n]['left'],out[n]['top'],out[n]['width'],out[n]['height'],len(out[n]['path']))
json.dump(out,open('vig_shapes.json','w'))
