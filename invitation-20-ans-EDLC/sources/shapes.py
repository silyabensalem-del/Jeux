import json, math
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from shapely.geometry import Polygon, Point, box, MultiPolygon
from shapely.ops import unary_union
from shapely import affinity
from shapely.geometry.polygon import orient

class FlatPen(BasePen):
    def __init__(s,gs): super().__init__(gs); s.rings=[]; s.cur=[]
    def _moveTo(s,p): s.cur=[p]
    def _lineTo(s,p): s.cur.append(p)
    def _curveToOne(s,a,b,p):
        p0=s.cur[-1]
        for i in range(1,13):
            t=i/12; mt=1-t
            s.cur.append((mt**3*p0[0]+3*mt*mt*t*a[0]+3*mt*t*t*b[0]+t**3*p[0], mt**3*p0[1]+3*mt*mt*t*a[1]+3*mt*t*t*b[1]+t**3*p[1]))
    def _qCurveToOne(s,q,p):
        p0=s.cur[-1]
        for i in range(1,11):
            t=i/10; mt=1-t
            s.cur.append((mt*mt*p0[0]+2*mt*t*q[0]+t*t*p[0], mt*mt*p0[1]+2*mt*t*q[1]+t*t*p[1]))
    def _closePath(s): s.rings.append(s.cur); s.cur=[]

def glyph_poly(font, gname, em, x, base):
    gs=font.getGlyphSet(); sc=em/font['head'].unitsPerEm
    pen=FlatPen(gs); gs[gname].draw(pen)
    geom=None
    polys=[Polygon([(x+px*sc, base-py*sc) for px,py in r]) for r in pen.rings]
    polys.sort(key=lambda p:-p.area)
    g=polys[0]
    for p in polys[1:]:
        g = g.difference(p) if g.contains(p) else g.union(p)
    return g

def picto_solid():
    head=Point(76.5,33.5).buffer(33.5,256)
    def half_annulus(cx,cy,R,r,lower):
        ring=Point(cx,cy).buffer(R,256).difference(Point(cx,cy).buffer(r,256))
        clip=box(cx-R-1, cy, cx+R+1, cy+R+1) if lower else box(cx-R-1, cy-R-1, cx+R+1, cy)
        return ring.intersection(clip)
    return unary_union([head, half_annulus(76.5,35,76.5,45.5,True), half_annulus(76.5,193,76.5,45.5,False)])

def to_path(geom, ox, oy, k):
    geom=geom if isinstance(geom,MultiPolygon) else MultiPolygon([geom]) if geom.geom_type=='Polygon' else MultiPolygon([g for g in geom.geoms if g.geom_type=='Polygon'])
    parts=[]
    for p in geom.geoms:
        p=orient(p.simplify(0.02),1.0)
        for ring in [p.exterior]+list(p.interiors):
            c=list(ring.coords)[:-1]
            parts.append("M"+" L".join("%.2f %.2f"%((X-ox)*k,(Y-oy)*k) for X,Y in c)+"Z")
    return " ".join(parts)

PX=794/210
font=TTFont('fonts/fontsource-open-sans/files/open-sans-latin-800-normal.woff2')
em=205; sc=em/2048; x0=-16; base=138
two=glyph_poly(font,'two',em,x0,base); zero=glyph_poly(font,'zero',em,x0+1200*sc,base)
W=1.2  # épaisseur du contour en mm
shapes={}
for name,g in [('2',two),('0',zero)]:
    shapes['contour_'+name]=g.buffer(W/2, join_style=1)
    shapes['fond_'+name]=g.buffer(-W/2, join_style=1)
# pictogramme au trait
ps=picto_solid(); s=55/193
ps=affinity.scale(ps, s, s, origin=(0,0)); ps=affinity.translate(ps, -9, 186)
ps=affinity.rotate(ps, -14, origin='center')
lw=0.5
shapes['picto_trait']=ps.buffer(lw/2).difference(ps.buffer(-lw/2))
# pictogramme plein (référence)
shapes['cadre_date']=box(48,192,162,222).difference(box(48.35,192.35,161.65,221.65))
shapes['trait_date']=box(94.75,197,95.25,217)
out={}
for n,g in shapes.items():
    minx,miny,maxx,maxy=g.bounds
    out[n]=dict(mm=dict(left=minx,top=miny,width=maxx-minx,height=maxy-miny),
                svg_mm=to_path(g,0,0,1),
                px=dict(left=round(minx*PX,2),top=round(miny*PX,2),width=round((maxx-minx)*PX,2),height=round((maxy-miny)*PX,2)),
                path_px=to_path(g,minx,miny,PX))
    print(n, out[n]['px'], len(out[n]['path_px']))
json.dump(out,open('shapes.json','w'))
