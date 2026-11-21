import base64, binascii, os, re, uuid
from datetime import date
from io import BytesIO
from pathlib import Path
from PIL import Image
from config.database import query, execute, connect
from backend.common import ok, fail, public_report

ROOT = Path(__file__).resolve().parent.parent
UPLOADS = ROOT / "uploads"
MAX_PHOTO = 5 * 1024 * 1024

def _photo(data):
    if not data: return None
    try:
        header, encoded = data.split(",", 1)
        raw = base64.b64decode(encoded, validate=True)
        if len(raw) > MAX_PHOTO: raise ValueError("Ukuran foto maksimal 5 MB.")
        image = Image.open(BytesIO(raw)); image.verify()
        fmt = image.format
        extensions = {"JPEG":"jpg", "PNG":"png", "WEBP":"webp"}
        if fmt not in extensions: raise ValueError("Foto harus berformat JPG, PNG, atau WebP.")
        name = f"{uuid.uuid4().hex}.{extensions[fmt]}"
        UPLOADS.mkdir(exist_ok=True)
        (UPLOADS / name).write_bytes(raw)
        return f"uploads/{name}"
    except (ValueError, binascii.Error, OSError) as e:
        raise ValueError(str(e) if str(e) else "Isi file gambar tidak valid.")

def get_reports(filters=None):
    filters = filters or {}; where=[]; params=[]
    search = str(filters.get("search", "")).strip()
    if search: where.append("(r.item_name LIKE %s OR r.description LIKE %s)"); params += [f"%{search}%",f"%{search}%"]
    for key, col in (("report_type","r.report_type"),("status","r.status"),("category_id","r.category_id")):
        if filters.get(key): where.append(f"{col}=%s"); params.append(filters[key])
    if filters.get("location"): where.append("r.location LIKE %s"); params.append(f"%{filters['location']}%")
    if filters.get("date_from"): where.append("r.event_date >= %s"); params.append(filters["date_from"])
    if filters.get("date_to"): where.append("r.event_date <= %s"); params.append(filters["date_to"])
    sql="SELECT r.*,c.name category_name FROM reports r JOIN categories c ON c.id=r.category_id"
    if where: sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY r.created_at DESC, r.id DESC"
    try: return ok([public_report(x) for x in query(sql,tuple(params))])
    except Exception as e: return fail(e,"DATABASE_ERROR")

def get_report(report_id):
    try:
        row=public_report(query("SELECT r.*,c.name category_name FROM reports r JOIN categories c ON c.id=r.category_id WHERE r.id=%s",(report_id,),one=True))
        return ok(row) if row else fail("Laporan tidak ditemukan.","NOT_FOUND")
    except Exception as e: return fail(e,"DATABASE_ERROR")

def save_report(payload, report_id=None):
    p=payload or {}; required=("report_type","category_id","item_name","location","event_date")
    if any(not str(p.get(k,"")).strip() for k in required): return fail("Jenis, kategori, nama barang, lokasi, dan tanggal wajib diisi.")
    if p["report_type"] not in ("lost","found"): return fail("Jenis laporan tidak valid.")
    try:
        event_date=date.fromisoformat(str(p["event_date"]))
        if event_date > date.today(): return fail("Tanggal kejadian tidak boleh melebihi tanggal hari ini.")
        if len(str(p["item_name"])) > 150 or len(str(p["location"])) > 150: return fail("Nama barang atau lokasi terlalu panjang.")
        photo_path=_photo(p.get("photo_data")) if p.get("photo_data") else p.get("photo_path")
        if report_id:
            old=query("SELECT * FROM reports WHERE id=%s",(report_id,),one=True)
            if not old: return fail("Laporan tidak ditemukan.","NOT_FOUND")
            if old["report_type"] != p["report_type"]:
                linked=query("SELECT (SELECT COUNT(*) FROM matches WHERE lost_report_id=%s OR found_report_id=%s) + (SELECT COUNT(*) FROM claims cl JOIN matches m ON m.id=cl.match_id WHERE m.lost_report_id=%s OR m.found_report_id=%s) n",(report_id,report_id,report_id,report_id),one=True)["n"]
                if linked: return fail("Jenis laporan tidak dapat diubah setelah masuk proses matching/klaim.")
            execute("UPDATE reports SET category_id=%s,report_type=%s,item_name=%s,color=%s,location=%s,event_date=%s,description=%s,photo_path=%s WHERE id=%s",
                    (p["category_id"],p["report_type"],p["item_name"].strip(),p.get("color") or None,p["location"].strip(),event_date,p.get("description") or None,photo_path,report_id))
            return ok({"id":report_id})
        new_id,_=execute("INSERT INTO reports(category_id,report_type,item_name,color,location,event_date,description,photo_path) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
                    (p["category_id"],p["report_type"],p["item_name"].strip(),p.get("color") or None,p["location"].strip(),event_date,p.get("description") or None,photo_path))
        return ok({"id":new_id})
    except ValueError as e: return fail(e)
    except Exception as e: return fail(e,"DATABASE_ERROR")

def delete_report(report_id):
    try:
        linked=query("SELECT (SELECT COUNT(*) FROM matches WHERE lost_report_id=%s OR found_report_id=%s) + (SELECT COUNT(*) FROM claims cl JOIN matches m ON m.id=cl.match_id WHERE m.lost_report_id=%s OR m.found_report_id=%s) n",(report_id,report_id,report_id,report_id),one=True)["n"]
        if linked: return fail("Laporan yang memiliki relasi matching/klaim tidak dapat dihapus.")
        execute("DELETE FROM reports WHERE id=%s",(report_id,)); return ok()
    except Exception as e: return fail(e,"DATABASE_ERROR")
