import sys, json
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
class CubicPen(BasePen):
    def __init__(s,gs,sc,dx,dy): super().__init__(gs); s.c=[]; s.sc=sc; s.dx=dx; s.dy=dy
    def t(s,p): return (round(p[0]*s.sc+s.dx,2), round(-p[1]*s.sc+s.dy,2))
    def _moveTo(s,p): s.c.append("M%s %s"%s.t(p)); s.cur=p
    def _lineTo(s,p): s.c.append("L%s %s"%s.t(p)); s.cur=p
    def _curveToOne(s,a,b,p): s.c.append("C%s %s %s %s %s %s"%(s.t(a)+s.t(b)+s.t(p))); s.cur=p
    def _qCurveToOne(s,q,p):
        p0=s._getCurrentPoint()
        c1=(p0[0]+2/3*(q[0]-p0[0]),p0[1]+2/3*(q[1]-p0[1])); c2=(p[0]+2/3*(q[0]-p[0]),p[1]+2/3*(q[1]-p[1]))
        s._curveToOne(c1,c2,p)
    def _closePath(s): s.c.append("Z")
f=TTFont(sys.argv[1]); gs=f.getGlyphSet(); cmap=f.getBestCmap(); upm=f['head'].unitsPerEm
em=float(sys.argv[3]); sc=em/upm; x=float(sys.argv[4]); base=float(sys.argv[5]); out={}
for ch in sys.argv[2]:
    g=cmap[ord(ch)]; pen=CubicPen(gs,sc,x,base); gs[g].draw(pen); out[ch]=" ".join(pen.c); x+=gs[g].width*sc
json.dump(out,open(sys.argv[6],'w')); print({k:len(v) for k,v in out.items()})
