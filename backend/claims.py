from config.database import query, execute, connect
from backend.common import ok, fail

def list_claims(status=None):
    try:
        sql="""SELECT cl.id,cl.match_id,cl.claimant_name,cl.contact,cl.proof_description,cl.status,cl.reviewed_at,m.lost_report_id,m.found_report_id,l.item_name lost_name,f.item_name found_name,cl.created_at FROM claims cl JOIN matches m ON m.id=cl.match_id JOIN reports l ON l.id=m.lost_report_id JOIN reports f ON f.id=m.found_report_id"""
        params=()
        if status: sql += " WHERE cl.status=%s"; params=(status,)
        sql += " ORDER BY cl.created_at DESC"
        rows=query(sql,params)
        for r in rows:
            for k in ("created_at","reviewed_at"):
                if r.get(k): r[k]=r[k].isoformat(sep=" ")
        return ok(rows)
    except Exception as e: return fail(e,"DATABASE_ERROR")

def create_claim(p):
    p=p or {}
    if not all(str(p.get(k,"")).strip() for k in ("match_id","claimant_name","proof_description")): return fail("Pasangan, nama pengklaim, dan uraian bukti wajib diisi.")
    conn=connect()
    try:
        cur=conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM matches WHERE id=%s",(p["match_id"],)); m=cur.fetchone()
        if not m: raise ValueError("Pasangan laporan tidak ditemukan.")
        cur.execute("SELECT id,status FROM reports WHERE id IN (%s,%s) ORDER BY id FOR UPDATE",(m["lost_report_id"],m["found_report_id"]))
        states=cur.fetchall()
        if len(states)!=2 or any(r["status"]!="open" for r in states): raise ValueError("Klaim hanya dapat dibuat untuk dua laporan yang masih terbuka.")
        cur.execute("SELECT COUNT(*) n FROM claims WHERE match_id=%s AND status='pending'",(p["match_id"],))
        if cur.fetchone()["n"]: raise ValueError("Masih ada klaim tertunda untuk pasangan ini.")
        cur.execute("INSERT INTO claims(match_id,claimant_name,contact,proof_description) VALUES(%s,%s,%s,%s)",(p["match_id"],p["claimant_name"].strip(),p.get("contact") or None,p["proof_description"].strip()))
        cid=cur.lastrowid; conn.commit(); return ok({"id":cid})
    except ValueError as e: conn.rollback(); return fail(e)
    except Exception as e: conn.rollback(); return fail(e,"DATABASE_ERROR")
    finally: conn.close()

def review_claim(claim_id, decision):
    if decision not in ("approved","rejected"): return fail("Keputusan tidak valid.")
    conn=connect()
    try:
        cur=conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM claims WHERE id=%s FOR UPDATE",(claim_id,)); cl=cur.fetchone()
        if not cl or cl["status"]!="pending": raise ValueError("Klaim tidak ditemukan atau sudah diputuskan.")
        cur.execute("SELECT lost_report_id,found_report_id FROM matches WHERE id=%s",(cl["match_id"],)); m=cur.fetchone()
        cur.execute("SELECT id,status FROM reports WHERE id IN (%s,%s) ORDER BY id FOR UPDATE",(m["lost_report_id"],m["found_report_id"])); reports=cur.fetchall()
        if decision=="approved":
            if len(reports)!=2 or any(r["status"]!="open" for r in reports): raise ValueError("Persetujuan ditolak karena salah satu laporan telah selesai.")
            cur.execute("SELECT COUNT(*) n FROM claims c JOIN matches m ON m.id=c.match_id WHERE c.status='approved' AND (m.lost_report_id IN (%s,%s) OR m.found_report_id IN (%s,%s))",(m["lost_report_id"],m["found_report_id"],m["lost_report_id"],m["found_report_id"]))
            if cur.fetchone()["n"]: raise ValueError("Laporan terkait sudah memiliki klaim yang disetujui.")
            cur.execute("UPDATE reports SET status='resolved' WHERE id IN (%s,%s)",(m["lost_report_id"],m["found_report_id"]))
        cur.execute("UPDATE claims SET status=%s,reviewed_at=NOW() WHERE id=%s",(decision,claim_id)); conn.commit(); return ok()
    except ValueError as e: conn.rollback(); return fail(e)
    except Exception as e: conn.rollback(); return fail(e,"DATABASE_ERROR")
    finally: conn.close()
