import os, eel
from dotenv import load_dotenv
from backend import reports, categories, matching, claims, analytics
load_dotenv()
eel.init("web")

@eel.expose
def get_dashboard():
    from config.database import query
    try:
        stats=query("SELECT COUNT(*) total, COALESCE(SUM(report_type='lost' AND status='open'),0) lost_open, COALESCE(SUM(report_type='found' AND status='open'),0) found_open, COALESCE(SUM(status='resolved'),0) resolved FROM reports",one=True)
        stats={key:int(value or 0) for key,value in stats.items()}
        latest=query("SELECT r.id,r.report_type,r.item_name,r.location,r.status,r.event_date,c.name category_name FROM reports r JOIN categories c ON c.id=r.category_id ORDER BY r.created_at DESC LIMIT 5")
        for row in latest: row["event_date"]=row["event_date"].isoformat()
        charts=analytics.analytics()
        return {"success":True,"data":{"stats":stats,"latest":latest,"analytics":charts.get("data",{})}}
    except Exception as e: return {"success":False,"error":{"code":"DATABASE_ERROR","message":str(e)}}
@eel.expose
def get_reports(filters=None): return reports.get_reports(filters)
@eel.expose
def get_report(report_id): return reports.get_report(report_id)
@eel.expose
def create_report(payload): return reports.save_report(payload)
@eel.expose
def update_report(report_id,payload): return reports.save_report(payload,report_id)
@eel.expose
def delete_report(report_id): return reports.delete_report(report_id)
@eel.expose
def get_categories(): return categories.list_categories()
@eel.expose
def save_category(payload): return categories.save_category(payload)
@eel.expose
def delete_category(category_id): return categories.delete_category(category_id)
@eel.expose
def get_matches(report_id): return matching.get_matches(report_id)
@eel.expose
def get_claims(status=None): return claims.list_claims(status)
@eel.expose
def create_claim(payload): return claims.create_claim(payload)
@eel.expose
def review_claim(claim_id,decision): return claims.review_claim(claim_id,decision)
@eel.expose
def get_analytics(filters=None): return analytics.analytics(filters)
@eel.expose
def export_reports_csv(filters=None): return analytics.export_csv(filters)
if __name__ == "__main__":
    try: eel.start("index.html",size=(1360,850),port=int(os.getenv("APP_PORT","8765")))
    except Exception as exc: print(f"LostLink gagal dimulai: {exc}\nPastikan MySQL aktif dan .env sudah dikonfigurasi.")
