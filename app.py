"""
app.py - Flask Application Entry Point
========================================
BlockVerify — Blockchain-Based Product Verification System

Routes:
  GET  /                    → Dashboard
  GET  /add                 → Add Product page
  POST /add                 → Submit new product
  GET  /verify              → Verify Product page
  POST /verify              → Verify product by ID
  GET  /blockchain          → Blockchain visualization
  GET  /admin               → Admin dashboard
  POST /admin/delete/<id>   → Delete a product
  GET  /admin/search        → Search products (AJAX)
  GET  /api/stats           → JSON stats for dashboard
  GET  /api/chain           → Full blockchain JSON
  GET  /export              → Export products as CSV
  GET  /api/qr/<product_id> → Generate QR code PNG
"""

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, jsonify, send_file, abort
)
import io
import csv
import qrcode
import json
from datetime import datetime

import database as db
from blockchain import Blockchain

# ── App Setup ────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = "blockverify-secret-2024"

# ── Blockchain Singleton ──────────────────────────────────────────────────────
# The blockchain lives in memory; the DB is the source of truth for persistence.
blockchain = Blockchain()

def _rebuild_chain():
    """
    On startup, replay all saved products into the in-memory blockchain
    so the chain stays consistent with the database.
    """
    global blockchain
    blockchain = Blockchain()  # Fresh chain with genesis block
    saved = db.rebuild_blockchain_data()
    for p in saved:
        blockchain.add_block({
            "product_id":   p["product_id"],
            "name":         p["name"],
            "manufacturer": p["manufacturer"],
            "category":     p["category"],
            "date_added":   p["date_added"],
        })

# ── Initialise on startup ─────────────────────────────────────────────────────
db.init_db()
_rebuild_chain()


# ══════════════════════════════════════════════════════════════════════════════
# ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    """Dashboard home — statistics + recent activity."""
    stats   = db.get_stats()
    recent  = db.get_recent_activity(8)
    chain_valid = blockchain.is_chain_valid()
    blocks  = len(blockchain.chain)
    return render_template(
        "index.html",
        stats=stats,
        recent=recent,
        chain_valid=chain_valid,
        blocks=blocks
    )


@app.route("/add", methods=["GET", "POST"])
def add_product():
    """Add a new product to the blockchain."""
    if request.method == "POST":
        product_data = {
            "product_id":   request.form.get("product_id", "").strip().upper(),
            "name":         request.form.get("name", "").strip(),
            "manufacturer": request.form.get("manufacturer", "").strip(),
            "category":     request.form.get("category", "").strip(),
            "date_added":   request.form.get("date_added", datetime.today().strftime("%Y-%m-%d")),
        }

        # Basic validation
        if not all(product_data.values()):
            flash("All fields are required.", "error")
            return render_template("add_product.html", form=product_data)

        # Check duplicate
        if db.get_product_by_id(product_data["product_id"]):
            flash(f"Product ID '{product_data['product_id']}' already exists.", "error")
            return render_template("add_product.html", form=product_data)

        # Add block to blockchain
        new_block = blockchain.add_block(product_data)

        # Persist to DB
        success = db.save_product(product_data, new_block)
        if success:
            flash(
                f"✅ Product '{product_data['name']}' added to blockchain! Block #{new_block.index}",
                "success"
            )
            return redirect(url_for("index"))
        else:
            # Rollback the in-memory block if DB save failed
            blockchain.chain.pop()
            flash("Database error. Please try again.", "error")

    return render_template("add_product.html", form={})


@app.route("/verify", methods=["GET", "POST"])
def verify_product():
    """Verify a product by Product ID."""
    result = None
    if request.method == "POST":
        pid = request.form.get("product_id", "").strip().upper()
        if not pid:
            flash("Please enter a Product ID.", "error")
        else:
            # Search blockchain
            block = blockchain.find_product(pid)
            product = db.get_product_by_id(pid)
            db.log_verification(pid, bool(block and product))

            if block and product:
                result = {
                    "genuine":       True,
                    "product":       product,
                    "block_hash":    block.hash,
                    "prev_hash":     block.previous_hash,
                    "timestamp":     block.timestamp,
                    "block_index":   block.index,
                    "chain_valid":   blockchain.is_chain_valid(),
                }
            else:
                result = {"genuine": False, "product_id": pid}

    return render_template("verify.html", result=result)


@app.route("/blockchain")
def view_blockchain():
    """Visual blockchain explorer."""
    chain   = blockchain.get_all_blocks()
    valid   = blockchain.is_chain_valid()
    return render_template("blockchain.html", chain=chain, valid=valid)


@app.route("/admin")
def admin():
    """Admin panel — all products, search, delete."""
    query    = request.args.get("q", "")
    if query:
        products = db.search_products(query)
    else:
        products = db.get_all_products()
    stats    = db.get_stats()
    recent   = db.get_recent_activity(20)
    categories = {}
    for p in db.get_all_products():
        categories[p["category"]] = categories.get(p["category"], 0) + 1
    return render_template(
        "admin.html",
        products=products,
        stats=stats,
        recent=recent,
        query=query,
        categories=json.dumps(categories)
    )


@app.route("/admin/delete/<product_id>", methods=["POST"])
def delete_product(product_id):
    """Delete a product and rebuild the blockchain from DB."""
    global blockchain
    db.delete_product(product_id)
    _rebuild_chain()   # Rebuild chain to keep it consistent
    flash(f"Product '{product_id}' deleted and blockchain rebuilt.", "info")
    return redirect(url_for("admin"))


# ── API Endpoints ─────────────────────────────────────────────────────────────

@app.route("/api/stats")
def api_stats():
    stats = db.get_stats()
    stats["blocks"] = len(blockchain.chain)
    stats["chain_valid"] = blockchain.is_chain_valid()
    return jsonify(stats)


@app.route("/api/chain")
def api_chain():
    return jsonify(blockchain.to_dict())


@app.route("/api/qr/<product_id>")
def generate_qr(product_id):
    """Generate a QR code PNG for the given product_id's verify URL."""
    verify_url = request.host_url + f"verify?pid={product_id.upper()}"
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(verify_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#00f5ff", back_color="#0a0a1a")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")


@app.route("/export")
def export_csv():
    """Export all products as a downloadable CSV file."""
    products = db.get_all_products()
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=[
        "product_id","name","manufacturer","category",
        "date_added","block_index","block_hash","prev_hash","timestamp"
    ])
    writer.writeheader()
    for p in products:
        writer.writerow({k: p.get(k, "") for k in writer.fieldnames})
    buf.seek(0)
    return send_file(
        io.BytesIO(buf.getvalue().encode()),
        mimetype="text/csv",
        as_attachment=True,
        download_name="blockverify_products.csv"
    )


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=5000)
