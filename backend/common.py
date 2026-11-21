from config.database import query

def ok(data=None, **extra):
    return {"success": True, "data": data, **extra}

def fail(message, code="VALIDATION_ERROR"):
    return {"success": False, "error": {"code": code, "message": str(message)}}

def report_by_id(report_id):
    return query("""SELECT r.*, c.name category_name FROM reports r JOIN categories c ON c.id=r.category_id WHERE r.id=%s""", (report_id,), one=True)

def public_report(row):
    if not row: return None
    result = dict(row)
    if result.get("event_date"): result["event_date"] = result["event_date"].isoformat()
    if result.get("created_at"): result["created_at"] = result["created_at"].isoformat(sep=" ")
    return result
