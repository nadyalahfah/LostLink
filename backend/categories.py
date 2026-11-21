from config.database import query, execute
from backend.common import ok, fail

def list_categories():
    try: return ok(query("SELECT id,name FROM categories ORDER BY name"))
    except Exception as e: return fail(e, "DATABASE_ERROR")

def save_category(payload):
    name = str((payload or {}).get("name", "")).strip()
    if not name: return fail("Nama kategori wajib diisi.")
    try:
        category_id = (payload or {}).get("id")
        if category_id: execute("UPDATE categories SET name=%s WHERE id=%s", (name, category_id))
        else: execute("INSERT INTO categories(name) VALUES(%s)", (name,))
        return ok()
    except Exception as e: return fail("Nama kategori sudah digunakan atau database tidak tersedia.", "DATABASE_ERROR")

def delete_category(category_id):
    try:
        used = query("SELECT COUNT(*) total FROM reports WHERE category_id=%s", (category_id,), one=True)["total"]
        if used: return fail("Kategori tidak dapat dihapus karena sudah dipakai laporan.")
        execute("DELETE FROM categories WHERE id=%s", (category_id,)); return ok()
    except Exception as e: return fail(e, "DATABASE_ERROR")
