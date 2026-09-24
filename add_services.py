"""
Adds the standard service menu to Nail POS data.
Double-click this file to run — it will update the running app's data.
"""
import json, os, sys

DATA_FILE = os.path.join(os.environ.get('APPDATA', ''), 'Nail POS', 'data.json')

if not os.path.exists(DATA_FILE):
    print(f"ERROR: Data file not found at:\n  {DATA_FILE}")
    input("\nPress Enter to close...")
    sys.exit(1)

with open(DATA_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

services = [
    # ── Manicure ──────────────────────────────────────
    {"id": 1001, "name": "Manicure",            "price": 20,  "duration": 30, "category": "Manicure"},
    {"id": 1002, "name": "Gel Manicure",         "price": 35,  "duration": 45, "category": "Manicure"},
    {"id": 1003, "name": "Dip Powder",           "price": 40,  "duration": 50, "category": "Manicure"},
    {"id": 1004, "name": "French Manicure",      "price": 25,  "duration": 35, "category": "Manicure"},
    # ── Pedicure ──────────────────────────────────────
    {"id": 1005, "name": "Pedicure",             "price": 35,  "duration": 45, "category": "Pedicure"},
    {"id": 1006, "name": "Gel Pedicure",         "price": 50,  "duration": 60, "category": "Pedicure"},
    {"id": 1007, "name": "Deluxe Pedicure",      "price": 55,  "duration": 70, "category": "Pedicure"},
    # ── Acrylic ──────────────────────────────────────
    {"id": 1008, "name": "Acrylic Full Set",     "price": 50,  "duration": 75, "category": "Acrylic"},
    {"id": 1009, "name": "Acrylic Fill",         "price": 35,  "duration": 45, "category": "Acrylic"},
    {"id": 1010, "name": "Acrylic with Gel",     "price": 60,  "duration": 80, "category": "Acrylic"},
    # ── Combo ────────────────────────────────────────
    {"id": 1011, "name": "Mani + Pedi Combo",    "price": 50,  "duration": 75, "category": "Combo"},
    {"id": 1012, "name": "Gel Mani + Pedi",      "price": 75,  "duration": 90, "category": "Combo"},
    # ── Add-On ───────────────────────────────────────
    {"id": 1013, "name": "Nail Art (per nail)",  "price": 5,   "duration": 10, "category": "Add-On"},
    {"id": 1014, "name": "Paraffin Wax",         "price": 10,  "duration": 15, "category": "Add-On"},
    {"id": 1015, "name": "French Tip",           "price": 10,  "duration": 10, "category": "Add-On"},
    {"id": 1016, "name": "Nail Repair",          "price": 5,   "duration": 10, "category": "Add-On"},
    # ── Waxing ───────────────────────────────────────
    {"id": 1017, "name": "Eyebrow Wax",          "price": 12,  "duration": 15, "category": "Waxing"},
    {"id": 1018, "name": "Lip Wax",              "price": 8,   "duration": 10, "category": "Waxing"},
    {"id": 1019, "name": "Full Face Wax",        "price": 25,  "duration": 25, "category": "Waxing"},
]

data['npos_services'] = json.dumps(services)

with open(DATA_FILE, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)

print("=" * 50)
print("  SUCCESS! Services added to Nail POS:")
print("=" * 50)
for s in services:
    print(f"  {s['category']:10}  {s['name']:25}  ${s['price']}")
print()
print("  Restart Nail POS to see the services.")
print()
input("Press Enter to close...")
