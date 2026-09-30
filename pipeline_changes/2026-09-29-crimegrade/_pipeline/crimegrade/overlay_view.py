#!/usr/bin/env python3
"""Draw the 2020 block-group outlines over a fitted map view, to check an alignment by eye.

Usage: overlay_view.py <batch folder> <view number> [<out.png>]
Reads fits/view_NN.json and the block groups TIGERweb returns for the view's extent (same cache as
build_crime_bg.py); outlines should follow the colour edges and the streets.
"""
import sys, os, json, math
from PIL import Image, ImageDraw
PIPE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,PIPE)
from georef import load_rgb, map_bounds
from colour_read import merc_y
from build_crime_bg import fetch_bgs
folder=os.path.abspath(sys.argv[1]); v=int(sys.argv[2]); out=sys.argv[3] if len(sys.argv)>3 else os.path.join(folder,'overlay_view_%02d.png'%v)
man=json.load(open(os.path.join(folder,'manifest.json'))); files=sorted(f for f,m in man.items() if m['view']==v)
fit=json.load(open(os.path.join(folder,'fits','view_%02d.json'%v))); s,tx,ty=fit['s'],fit['tx'],fit['ty']
proj=lambda lo,la:(s*lo+tx,-s*merc_y(la)+ty)
im=Image.open(os.path.join(folder,'x',files[0])).convert('RGB'); W,H=im.size; A=load_rgb(os.path.join(folder,'x',files[0])); top,left,right=map_bounds(A); bottom=H-48
def inv(px,py):
    lon=(px-tx)/s; my=(ty-py)/s; return lon, math.degrees(2*math.atan(math.exp(math.radians(my)))-math.pi/2)
lon0,lat1=inv(left,top); lon1,lat0=inv(right,bottom)
dr=ImageDraw.Draw(im)
for ft in fetch_bgs([lon0,lat0,lon1,lat1]):
    g=ft.get('geometry')
    if not g: continue
    polys=[g['coordinates']] if g['type']=='Polygon' else g['coordinates']
    for poly in polys:
        pts=[proj(x,y) for x,y in poly[0]]
        dr.line(pts+[pts[0]],fill=(0,0,0),width=1)
dr.text((left+6,top+6),'%s view %d zoom %.3f score %.3f'%(man[files[0]]['zip'],v,fit['zoom'],fit['score']),fill=(255,0,0))
im.save(out); print(out)
