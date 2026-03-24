from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, StreamingResponse
import sqlite3
import io
import csv
from typing import Optional
from database import get_connection, init_db, generate_vault_ticket_no
import os
from datetime import date

app = FastAPI(title="ShimawaNever", description="蔵置管理システム")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
def startup():
    init_db()


# ─── ユーティリティ ───────────────────────────────────────────

def get_next_record_seq(conn, issuer_id, issuer_sub):
    """同一発行者・subコード内の次の連番を取得"""
    row = conn.execute(
        "SELECT MAX(record_seq) as m FROM vault_records WHERE issuer_id=? AND issuer_sub=?",
        (issuer_id, issuer_sub)
    ).fetchone()
    return (row["m"] or 0) + 1


# ─── トップ / ダッシュボード ──────────────────────────────────

@app.get("/")
def index(request: Request):
    conn = get_connection()
    stats = {
        "total": conn.execute("SELECT COUNT(*) as c FROM vault_records").fetchone()["c"],
        "documents": conn.execute("SELECT COUNT(*) as c FROM vault_records WHERE category='document'").fetchone()["c"],
        "books": conn.execute("SELECT COUNT(*) as c FROM vault_records WHERE category='book'").fetchone()["c"],
        "locations": conn.execute("SELECT COUNT(*) as c FROM locations").fetchone()["c"],
        "issuers": conn.execute("SELECT COUNT(*) as c FROM issuers").fetchone()["c"],
    }
    recent = conn.execute(
        "SELECT vr.*, l.name as loc_name, i.code as iss_code FROM vault_records vr "
        "LEFT JOIN locations l ON l.id=vr.location_id "
        "LEFT JOIN issuers i ON i.id=vr.issuer_id "
        "ORDER BY vr.registered_at DESC LIMIT 10"
    ).fetchall()
    conn.close()
    return templates.TemplateResponse("index.html", {"request": request, "stats": stats, "recent": recent})


# ─── 蔵置管理票 CRUD ─────────────────────────────────────────

@app.get("/records")
def list_records(request: Request, q: str = "", category: str = "", vault_type: str = ""):
    conn = get_connection()
    base = ("SELECT vr.*, l.name as loc_name, l.shelf as loc_shelf, "
            "i.code as iss_code, pc.name as parent_cat_name "
            "FROM vault_records vr "
            "LEFT JOIN locations l ON l.id=vr.location_id "
            "LEFT JOIN issuers i ON i.id=vr.issuer_id "
            "LEFT JOIN parent_categories pc ON pc.id=vr.parent_category_id "
            "WHERE 1=1 ")
    params = []
    if q:
        base += " AND (vr.name_ja LIKE ? OR vr.name_en LIKE ? OR vr.vault_ticket_no LIKE ? OR vr.issuer_name LIKE ?)"
        params += [f"%{q}%"] * 4
    if category:
        base += " AND vr.category=?"
        params.append(category)
    if vault_type:
        base += " AND vr.vault_type=?"
        params.append(vault_type)
    base += " ORDER BY vr.registered_at DESC"
    records = conn.execute(base, params).fetchall()
    conn.close()
    return templates.TemplateResponse("records/list.html", {
        "request": request, "records": records,
        "q": q, "category": category, "vault_type": vault_type
    })


@app.get("/records/new")
def new_record_form(request: Request):
    conn = get_connection()
    issuers = conn.execute("SELECT * FROM issuers ORDER BY code").fetchall()
    locations = conn.execute("SELECT * FROM locations ORDER BY place_code").fetchall()
    parent_cats = conn.execute("SELECT * FROM parent_categories ORDER BY name").fetchall()
    conn.close()
    return templates.TemplateResponse("records/form.html", {
        "request": request, "record": None,
        "issuers": issuers, "locations": locations, "parent_cats": parent_cats,
        "vault_types": ["LS", "LI", "LH", "LW", "LB", "OTHER"]
    })


@app.post("/records/new")
def create_record(
    request: Request,
    category: str = Form(...),
    vault_type: str = Form(...),
    name_ja: str = Form(...),
    name_en: str = Form(""),
    issuer_id: int = Form(...),
    issuer_sub: str = Form("000"),
    location_id: int = Form(...),
    issuer_name: str = Form(""),
    isbn: str = Form(""),
    parent_category_id: str = Form(""),
    retention_start: str = Form(""),
    retention_end: str = Form(""),
    notes: str = Form(""),
):
    conn = get_connection()
    seq = get_next_record_seq(conn, issuer_id, issuer_sub)
    loc = conn.execute("SELECT place_code FROM locations WHERE id=?", (location_id,)).fetchone()
    iss = conn.execute("SELECT code FROM issuers WHERE id=?", (issuer_id,)).fetchone()
    ticket_no = generate_vault_ticket_no(
        vault_type, loc["place_code"], issuer_sub, issuer_sub, seq
    )
    # issuerコードをゼロパディング3桁で使う
    ticket_no = f"TSV-{vault_type}-{loc['place_code']}-I{iss['code']}-C{issuer_sub}-R{seq:03d}"

    pc_id = int(parent_category_id) if parent_category_id else None
    conn.execute("""
        INSERT INTO vault_records
        (category, vault_type, name_ja, name_en, issuer_id, issuer_sub, location_id,
         issuer_name, isbn, parent_category_id, retention_start, retention_end, notes,
         record_seq, vault_ticket_no)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (category, vault_type, name_ja, name_en, issuer_id, issuer_sub, location_id,
          issuer_name, isbn or None, pc_id,
          retention_start or None, retention_end or None, notes, seq, ticket_no))
    conn.commit()
    conn.close()
    return RedirectResponse("/records", status_code=303)


@app.get("/records/{record_id}")
def view_record(request: Request, record_id: int):
    conn = get_connection()
    record = conn.execute(
        "SELECT vr.*, l.name as loc_name, l.shelf as loc_shelf, l.address as loc_address, "
        "i.code as iss_code, i.name as iss_fullname, pc.name as parent_cat_name "
        "FROM vault_records vr "
        "LEFT JOIN locations l ON l.id=vr.location_id "
        "LEFT JOIN issuers i ON i.id=vr.issuer_id "
        "LEFT JOIN parent_categories pc ON pc.id=vr.parent_category_id "
        "WHERE vr.id=?", (record_id,)
    ).fetchone()
    conn.close()
    if not record:
        raise HTTPException(404)
    return templates.TemplateResponse("records/detail.html", {
        "request": request,
        "record": record,
        "today": date.today().isoformat()
    })


@app.get("/records/{record_id}/edit")
def edit_record_form(request: Request, record_id: int):
    conn = get_connection()
    record = conn.execute("SELECT * FROM vault_records WHERE id=?", (record_id,)).fetchone()
    issuers = conn.execute("SELECT * FROM issuers ORDER BY code").fetchall()
    locations = conn.execute("SELECT * FROM locations ORDER BY place_code").fetchall()
    parent_cats = conn.execute("SELECT * FROM parent_categories ORDER BY name").fetchall()
    conn.close()
    if not record:
        raise HTTPException(404)
    return templates.TemplateResponse("records/form.html", {
        "request": request, "record": record,
        "issuers": issuers, "locations": locations, "parent_cats": parent_cats,
        "vault_types": ["LS", "LI", "LH", "LW", "LB", "OTHER"]
    })


@app.post("/records/{record_id}/edit")
def update_record(
    record_id: int,
    name_ja: str = Form(...),
    name_en: str = Form(""),
    vault_type: str = Form(...),
    issuer_id: int = Form(...),
    issuer_sub: str = Form("000"),
    location_id: int = Form(...),
    issuer_name: str = Form(""),
    isbn: str = Form(""),
    parent_category_id: str = Form(""),
    retention_start: str = Form(""),
    retention_end: str = Form(""),
    notes: str = Form(""),
):
    conn = get_connection()
    pc_id = int(parent_category_id) if parent_category_id else None
    loc = conn.execute("SELECT place_code FROM locations WHERE id=?", (location_id,)).fetchone()
    iss = conn.execute("SELECT code FROM issuers WHERE id=?", (issuer_id,)).fetchone()
    rec = conn.execute("SELECT record_seq FROM vault_records WHERE id=?", (record_id,)).fetchone()
    ticket_no = f"TSV-{vault_type}-{loc['place_code']}-I{iss['code']}-C{issuer_sub}-R{rec['record_seq']:03d}"
    conn.execute("""
        UPDATE vault_records SET
        name_ja=?, name_en=?, vault_type=?, issuer_id=?, issuer_sub=?, location_id=?,
        issuer_name=?, isbn=?, parent_category_id=?, retention_start=?, retention_end=?,
        notes=?, vault_ticket_no=?
        WHERE id=?
    """, (name_ja, name_en, vault_type, issuer_id, issuer_sub, location_id,
          issuer_name, isbn or None, pc_id,
          retention_start or None, retention_end or None, notes, ticket_no, record_id))
    conn.commit()
    conn.close()
    return RedirectResponse(f"/records/{record_id}", status_code=303)


@app.post("/records/{record_id}/delete")
def delete_record(record_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM vault_records WHERE id=?", (record_id,))
    conn.commit()
    conn.close()
    return RedirectResponse("/records", status_code=303)


# ─── CSV エクスポート ─────────────────────────────────────────

@app.get("/export/csv")
def export_csv():
    conn = get_connection()
    rows = conn.execute("""
        SELECT vr.vault_ticket_no, vr.vault_type, vr.category,
               vr.name_ja, vr.name_en,
               i.code as issuer_code, vr.issuer_sub, vr.issuer_name,
               vr.isbn,
               (i.code || '-' || vr.issuer_sub || '-' || printf('%03d', vr.record_seq)) as identifier,
               l.name as location_name, l.shelf as location_shelf, l.address as location_address,
               pc.name as parent_category,
               vr.retention_start, vr.retention_end,
               vr.registered_at, vr.notes
        FROM vault_records vr
        LEFT JOIN issuers i ON i.id=vr.issuer_id
        LEFT JOIN locations l ON l.id=vr.location_id
        LEFT JOIN parent_categories pc ON pc.id=vr.parent_category_id
        ORDER BY vr.registered_at DESC
    """).fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "蔵置管理票番号", "区分", "種別（書類/書籍）",
        "名称（日本語）", "名称（英語）",
        "発行者コード", "発行者サブコード", "発行者名",
        "ISBN", "識別符号",
        "蔵置場所名", "棚・区画", "住所",
        "親分類", "蔵置開始日", "蔵置終了日",
        "登録日時", "備考"
    ])
    for row in rows:
        writer.writerow(list(row))

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=shimanev_export.csv"}
    )


# ─── 発行者マスタ ─────────────────────────────────────────────

@app.get("/issuers")
def list_issuers(request: Request):
    conn = get_connection()
    issuers = conn.execute("SELECT * FROM issuers ORDER BY code").fetchall()
    conn.close()
    return templates.TemplateResponse("masters/issuers.html", {"request": request, "issuers": issuers})


@app.post("/issuers/new")
def create_issuer(code: str = Form(...), name: str = Form(...)):
    conn = get_connection()
    conn.execute("INSERT INTO issuers (code, name) VALUES (?,?)", (code.upper(), name))
    conn.commit()
    conn.close()
    return RedirectResponse("/issuers", status_code=303)


@app.post("/issuers/{issuer_id}/delete")
def delete_issuer(issuer_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM issuers WHERE id=?", (issuer_id,))
    conn.commit()
    conn.close()
    return RedirectResponse("/issuers", status_code=303)


# ─── 場所マスタ ───────────────────────────────────────────────

@app.get("/locations")
def list_locations(request: Request):
    conn = get_connection()
    locations = conn.execute("SELECT * FROM locations ORDER BY place_code").fetchall()
    conn.close()
    return templates.TemplateResponse("masters/locations.html", {"request": request, "locations": locations})


@app.post("/locations/new")
def create_location(
    place_code: str = Form(...), name: str = Form(...),
    shelf: str = Form(""), address: str = Form("")
):
    conn = get_connection()
    conn.execute("INSERT INTO locations (place_code, name, shelf, address) VALUES (?,?,?,?)",
                 (place_code.upper(), name, shelf, address))
    conn.commit()
    conn.close()
    return RedirectResponse("/locations", status_code=303)


@app.post("/locations/{loc_id}/delete")
def delete_location(loc_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM locations WHERE id=?", (loc_id,))
    conn.commit()
    conn.close()
    return RedirectResponse("/locations", status_code=303)


# ─── 親分類マスタ ─────────────────────────────────────────────

@app.get("/categories")
def list_categories(request: Request):
    conn = get_connection()
    cats = conn.execute("SELECT * FROM parent_categories ORDER BY name").fetchall()
    conn.close()
    return templates.TemplateResponse("masters/categories.html", {"request": request, "cats": cats})


@app.post("/categories/new")
def create_category(name: str = Form(...), description: str = Form("")):
    conn = get_connection()
    conn.execute("INSERT INTO parent_categories (name, description) VALUES (?,?)", (name, description))
    conn.commit()
    conn.close()
    return RedirectResponse("/categories", status_code=303)


@app.post("/categories/{cat_id}/delete")
def delete_category(cat_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM parent_categories WHERE id=?", (cat_id,))
    conn.commit()
    conn.close()
    return RedirectResponse("/categories", status_code=303)
