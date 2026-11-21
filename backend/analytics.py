from pathlib import Path
from datetime import datetime
import pandas as pd
from config.database import query
from backend.common import ok, fail

def analytics(filters=None):
    try:
        rows=query("SELECT r.report_type,r.status,r.event_date,c.name category_name FROM reports r JOIN categories c ON c.id=r.category_id")
        df=pd.DataFrame(rows)
        if df.empty: return ok({"by_type":[],"by_category":[],"by_month":[],"resolution":[]})
        df["event_date"]=pd.to_datetime(df["event_date"])
        return ok({"by_type":df.groupby("report_type").size().rename_axis("label").reset_index(name="count").to_dict("records"),
                   "by_category":df.groupby("category_name").size().rename_axis("label").reset_index(name="count").to_dict("records"),
                   "by_month":df.groupby(df["event_date"].dt.to_period("M").astype(str)).size().rename_axis("label").reset_index(name="count").to_dict("records"),
                   "resolution":df.groupby("status").size().rename_axis("label").reset_index(name="count").to_dict("records")})
    except Exception as e: return fail(e,"DATABASE_ERROR")

def export_csv(filters=None):
    from backend.reports import get_reports
    result=get_reports(filters)
    if not result["success"]: return result
    rows=result["data"]
    safe=[{k:r.get(k) for k in ("id","report_type","category_name","item_name","color","location","event_date","description","status","created_at")} for r in rows]
    folder=Path(__file__).resolve().parent.parent/"exports"; folder.mkdir(exist_ok=True)
    path=folder/f"lostlink-{datetime.now():%Y%m%d-%H%M%S}.csv"
    pd.DataFrame(safe,columns=["id","report_type","category_name","item_name","color","location","event_date","description","status","created_at"]).to_csv(path,index=False,encoding="utf-8-sig")
    return ok({"path":str(path)})
