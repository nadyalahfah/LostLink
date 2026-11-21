import re
from difflib import SequenceMatcher
from pathlib import Path
import numpy as np
from PIL import Image, ImageOps
from config.database import query, execute
from backend.common import ok, fail

THRESHOLD=60; MAX_DAYS=30
PHOTO_BONUS=35
ROOT=Path(__file__).resolve().parent.parent

def norm(v): return re.sub(r"\s+"," ",str(v or "").strip().lower())

def _perceptual_hash(photo_path):
    if not photo_path: return None
    path=(ROOT / str(photo_path)).resolve()
    if ROOT.resolve() not in path.parents: return None
    try:
        with Image.open(path) as image:
            pixels=np.asarray(ImageOps.grayscale(image).resize((32,32),Image.Resampling.LANCZOS),dtype=np.float32)
        size=32
        coords=np.arange(size)
        basis=np.cos(np.pi*(2*coords[None,:]+1)*coords[:,None]/(2*size))
        basis[0,:]*=1/np.sqrt(2)
        basis*=np.sqrt(2/size)
        low=(basis @ pixels @ basis.T)[:8,:8].flatten()
        median=np.median(low[1:])
        return low>median
    except (OSError, ValueError):
        return None

def photo_similarity(lost,found):
    left=_perceptual_hash(lost.get("photo_path")); right=_perceptual_hash(found.get("photo_path"))
    if left is None or right is None: return None
    return float(1-np.count_nonzero(left != right)/64)

def score_pair(lost, found):
    if lost["category_id"] != found["category_id"]: return None
    delta=(found["event_date"]-lost["event_date"]).days
    if delta < 0 or delta > MAX_DAYS: return None
    parts={}
    parts["category"]=(1.0,30)
    parts["name"]=(SequenceMatcher(None,norm(lost["item_name"]),norm(found["item_name"])).ratio(),25)
    a,b=norm(lost.get("color")),norm(found.get("color")); parts["color"]=(float(a==b) if a and b else 0,20)
    a,b=norm(lost.get("location")),norm(found.get("location"))
    location=1.0 if a and a==b else (0.5 if a and b and a.split()[0]==b.split()[0] else 0.0)
    parts["location"]=(location,15); parts["date"]=(max(0,1-delta/MAX_DAYS),10)
    photo=photo_similarity(lost,found)
    contributions={k:round(v*w,2) for k,(v,w) in parts.items()}
    similarities={k:round(v,3) for k,(v,_) in parts.items()}
    if photo is not None:
        base_score=sum(contributions.values())
        contributions["photo"]=round(min(100-base_score,photo*PHOTO_BONUS),2)
        similarities["photo"]=round(photo,3)
    return {"score":round(sum(contributions.values()),2),"contributions":contributions,"similarities":similarities,"days_apart":delta}

def get_matches(report_id):
    try:
        report=query("SELECT * FROM reports WHERE id=%s",(report_id,),one=True)
        if not report: return fail("Laporan tidak ditemukan.","NOT_FOUND")
        if report["status"]!="open": return ok([])
        if report["report_type"]=="lost": lost=report; candidates=query("SELECT * FROM reports WHERE report_type='found' AND status='open' AND category_id=%s AND event_date BETWEEN %s AND DATE_ADD(%s, INTERVAL %s DAY)",(report["category_id"],report["event_date"],report["event_date"],MAX_DAYS))
        else: lost=None; candidates=query("SELECT * FROM reports WHERE report_type='lost' AND status='open' AND category_id=%s AND event_date BETWEEN DATE_SUB(%s, INTERVAL %s DAY) AND %s",(report["category_id"],report["event_date"],MAX_DAYS,report["event_date"]))
        results=[]
        for candidate in candidates:
            l,f=(lost,candidate) if lost else (candidate,report); scored=score_pair(l,f)
            if not scored or scored["score"]<THRESHOLD: continue
            execute("INSERT INTO matches(lost_report_id,found_report_id,score,contributions) VALUES(%s,%s,%s,%s) ON DUPLICATE KEY UPDATE score=VALUES(score),contributions=VALUES(contributions)",(l["id"],f["id"],scored["score"],__import__('json').dumps(scored["contributions"])))
            pair=query("SELECT id FROM matches WHERE lost_report_id=%s AND found_report_id=%s",(l["id"],f["id"]),one=True)
            for r in (l,f):
                if r.get("event_date"): r["event_date"]=r["event_date"].isoformat()
            results.append({"lost":l,"found":f,"match_id":pair["id"],**scored})
        return ok(sorted(results,key=lambda x:x["score"],reverse=True))
    except Exception as e: return fail(e,"DATABASE_ERROR")
