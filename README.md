# BlockVerify — Blockchain-Based Product Verification System

A full-stack web application that prevents counterfeit products using blockchain technology.
Built with Python Flask, SQLite, and SHA-256 hashing.

---

## 🚀 Quick Start

### 1. Install Python dependencies
```bash
pip install flask qrcode[pil] Pillow
```

### 2. Run the application
```bash
python app.py
```

### 3. Open your browser
```
http://localhost:5000
```

---

## 📁 Project Structure

```
blockchain_verify/
├── app.py              ← Flask routes & application entry point
├── blockchain.py       ← SHA-256 blockchain implementation
├── database.py         ← SQLite persistence layer
├── requirements.txt    ← pip dependencies
├── dataset/
│   └── products.db     ← SQLite database (auto-created on first run)
├── templates/
│   ├── base.html       ← Sidebar layout, navigation, flash messages
│   ├── index.html      ← Dashboard with stats and activity
│   ├── add_product.html← Product registration form
│   ├── verify.html     ← Product authenticity checker
│   ├── blockchain.html ← Visual block chain explorer
│   └── admin.html      ← Admin panel with charts and management
└── static/
    ├── css/main.css    ← Complete dark UI stylesheet
    └── js/main.js      ← Counters, clock, copy-to-clipboard
```

---

## 🔗 How Blockchain Is Used

### Block Structure
Each product is stored as one block:
```
Block {
  index:         3
  timestamp:     2024-01-15T10:30:00
  data:          { product_id, name, manufacturer, category, date_added }
  previous_hash: "a3f9bc..."   ← hash of block #2
  hash:          "7d21e8..."   ← SHA-256 of all above
}
```

### Chain Formation
```
[Genesis Block] → [Block 1] → [Block 2] → [Block 3]
   hash=aaa...    prev=aaa    prev=bbb    prev=ccc
                  hash=bbb    hash=ccc    hash=ddd
```

### Tamper Detection
If anyone modifies Block 2's data:
- Its hash changes from `ccc` to `xyz`
- Block 3's `previous_hash` still says `ccc` → MISMATCH!
- `is_chain_valid()` returns False → tampering detected

---

## 🌐 All Pages

| URL               | Page                     |
|-------------------|--------------------------|
| `/`               | Dashboard                |
| `/add`            | Add Product              |
| `/verify`         | Verify Product           |
| `/blockchain`     | Chain Explorer           |
| `/admin`          | Admin Panel              |
| `/export`         | Export CSV               |
| `/api/stats`      | JSON stats API           |
| `/api/chain`      | Full blockchain JSON     |
| `/api/qr/<pid>`   | QR code PNG              |

---

## 🔐 Security Features
- SHA-256 hash for each block
- Previous hash linking (tamper-proof chain)
- `is_chain_valid()` checks entire chain on every request
- SQLite for permanent storage (survives restarts)
- Blockchain rebuilt from DB on server restart
