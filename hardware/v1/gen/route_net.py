#!/usr/bin/env python3
"""Single-net A* maze router for V5_CHG. Obstacles from real copper shapes (pcbnew TransformShapeToPolygon),
inflated by clearance + half width. Needs numpy + Pillow. Used 2026-11-15 to close V5_CHG after Freerouting converged with it open. Usage: route_net.py board.kicad_pcb out.json [allow_in1]"""
import pcbnew, sys, json, heapq, numpy as np
from PIL import Image, ImageDraw
B=pcbnew.LoadBoard(sys.argv[1]); M=pcbnew.ToMM; NET='V5_CHG'
ALLOW_IN1 = len(sys.argv)>3
G=0.05; X0,Y0,X1,Y1=121.0,101.0,185.0,153.0; W,H=int((X1-X0)/G),int((Y1-Y0)/G)
LAYERS=['F.Cu','In1.Cu','In2.Cu','B.Cu']; LID=[B.GetLayerID(l) for l in LAYERS]
TW=0.3; CLR=0.18; VD=0.5
def blank(): return Image.new('1',(W,H),0)
T=[blank() for _ in LAYERS]; V=[blank() for _ in LAYERS]
def draw(img, item, lid, infl):
    ps=pcbnew.SHAPE_POLY_SET()
    item.TransformShapeToPolygon(ps, lid, pcbnew.FromMM(infl), pcbnew.FromMM(0.005), pcbnew.ERROR_OUTSIDE)
    d=ImageDraw.Draw(img)
    for i in range(ps.OutlineCount()):
        pts=[((M(p.x)-X0)/G,(M(p.y)-Y0)/G) for p in ps.Outline(i).CPoints()]
        if len(pts)>2: d.polygon(pts, fill=1)
items=list(B.GetTracks())+[p for fp in B.GetFootprints() for p in fp.Pads()]
for it in items:
    if it.GetNetname()==NET: continue
    for k,lid in enumerate(LID):
        if not it.IsOnLayer(lid): continue
        draw(T[k],it,lid,CLR+TW/2); draw(V[k],it,lid,CLR+VD/2)
    # holes: hole-to-hole 0.25 -> block via centers
    if it.GetClass()=='PCB_VIA' or (it.GetClass()=='PAD' and it.HasHole()):
        x,y=M(it.GetX()),M(it.GetY()); r=(0.25+0.125+ (M(it.GetDrillValue()) if it.GetClass()=='PCB_VIA' else M(it.GetDrillSize().x))/2)/G
        for k in range(4): ImageDraw.Draw(V[k]).ellipse([(x-X0)/G-r,(y-Y0)/G-r,(x-X0)/G+r,(y-Y0)/G+r],fill=1)
for z in B.Zones():
    if not z.GetIsRuleArea() or not z.GetDoNotAllowTracks(): continue
    for k,lid in enumerate(LID):
        if z.GetLayerSet().Contains(lid):
            o=z.Outline()
            for i in range(o.OutlineCount()):
                pts=[((M(p.x)-X0)/G,(M(p.y)-Y0)/G) for p in o.Outline(i).CPoints()]
                ImageDraw.Draw(T[k]).polygon(pts,fill=1); ImageDraw.Draw(V[k]).polygon(pts,fill=1)
# grow keepouts by clearance+half width with a dilation
from PIL import ImageFilter
T=[np.array(t,dtype=bool) for t in T]; V=[np.array(v,dtype=bool) for v in V]
for k in range(4):
    T[k][0,:]=T[k][-1,:]=T[k][:,0]=T[k][:,-1]=True
VIA_OK=~(V[0]|V[1]|V[2]|V[3])
use=[0,2,3]+([1] if ALLOW_IN1 else [])
cost_l={0:1.0,1:3.0,2:1.0,3:1.0}
# islands
src=[];dst=[]
def cells_seg(x1,y1,x2,y2):
    n=max(2,int(np.hypot(x2-x1,y2-y1)/G)+1)
    return [(int(round((x1+(x2-x1)*t-X0)/G)),int(round((y1+(y2-y1)*t-Y0)/G))) for t in np.linspace(0,1,n)]
for t in B.GetTracks():
    if t.GetNetname()!=NET: continue
    xs=M(t.GetX()) if t.GetClass()=='PCB_VIA' else M(t.GetStart().x)
    side = src if xs>155 else dst
    if t.GetClass()=='PCB_VIA':
        for k in range(4): side.append((k,int(round((M(t.GetX())-X0)/G)),int(round((M(t.GetY())-Y0)/G))))
    else:
        k=LAYERS.index(B.GetLayerName(t.GetLayer()))
        for (i,j) in cells_seg(M(t.GetStart().x),M(t.GetStart().y),M(t.GetEnd().x),M(t.GetEnd().y)): side.append((k,i,j))
dset=set(dst); tx=np.mean([d[1] for d in dst]); ty=np.mean([d[2] for d in dst])
dpts=np.array([(d[1],d[2]) for d in dst])
def h(i,j): return float(np.min(np.hypot(dpts[:,0]-i,dpts[:,1]-j)))*G*0.999
VIA_COST=1.5
moves=[(1,0,G),(-1,0,G),(0,1,G),(0,-1,G),(1,1,G*1.4142),(1,-1,G*1.4142),(-1,1,G*1.4142),(-1,-1,G*1.4142)]
dist={}; prev={}; pq=[]
# subsample dst for heuristic speed
dpts=dpts[::5]
for s in src:
    if s[0] in use and 0<=s[1]<W and 0<=s[2]<H:
        dist[s]=0; heapq.heappush(pq,(h(s[1],s[2]),0.0,s))
# allow leaving own-net copper even if obstacle map marks nearby (own copper not drawn, fine)
end=None; n=0
while pq:
    f,g,u=heapq.heappop(pq)
    if g>dist.get(u,1e9): continue
    n+=1
    if u in dset: end=u; break
    k,i,j=u
    for di,dj,c in moves:
        ii,jj=i+di,j+dj
        if not(0<=ii<W and 0<=jj<H) or T[k][jj,ii]: continue
        v=(k,ii,jj); ng=g+c*cost_l[k]
        if ng<dist.get(v,1e9): dist[v]=ng; prev[v]=u; heapq.heappush(pq,(ng+h(ii,jj),ng,v))
    if VIA_OK[j,i]:
        for k2 in use:
            if k2==k or T[k2][j,i]: continue
            v=(k2,i,j); ng=g+VIA_COST
            if ng<dist.get(v,1e9): dist[v]=ng; prev[v]=u; heapq.heappush(pq,(ng+h(i,j),ng,v))
print('expanded',n,'found',end is not None)
if end is None: sys.exit(1)
path=[end]
while path[-1] in prev: path.append(prev[path[-1]])
path=path[::-1]
pts=[(LAYERS[k],round(X0+i*G,3),round(Y0+j*G,3)) for k,i,j in path]
print('length mm ~',round(dist[end],2),'vias',sum(1 for a,b in zip(path,path[1:]) if a[0]!=b[0]))
json.dump(pts,open(sys.argv[2],'w'))
