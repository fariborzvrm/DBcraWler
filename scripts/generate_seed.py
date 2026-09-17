"""Generate the Northwind-style seed SQL file.

Deterministic (fixed random seed). Run once:
    uv run python scripts/generate_seed.py
Output: data/seed/northwind.sql
"""

import random
from pathlib import Path

random.seed(42)

OUT = Path(__file__).resolve().parent.parent / "data" / "seed" / "northwind.sql"

COMPANIES = [
    "Alfreds Futterkiste",
    "Anna's Creations",
    "Berglunds snabbkop",
    "Blauer See Delikatessen",
    "Bolido Comidas",
    "Bon app'",
    "Bottom-Dollar Marketways",
    "B's Beverages",
    "Cactus Comidas",
    "Centro commercial Moctezuma",
    "Chop-suey Chinese",
    "Comercio Mineiro",
    "Consolidated Holdings",
    "Drachenblut Delikatessen",
    "Du monde entier",
    "Filia Headquarters",
    "Folies gourmandes",
    "Folk och fa HB",
    "Frankenversand",
    "France restauration",
    "Franchi S.p.A.",
    "Furia Bacalhau",
    "Galeria del gastronoma",
    "Gourmet Lanchonetes",
    "Great Lakes Food Market",
    "GROSELLA-Restaurante",
    "Hanari Carnes",
    "HILARION-Abastos",
    "Hungry Coyote Market",
    "Island Trading",
    "Konigsessen",
    "Lacomble Ltd",
    "La corne d'abondance",
    "Lino Delicatesse",
    "Leka Trading",
    "Let's Stop N Shop",
    "Lonesome Pine Restaurant",
    "Magazzini Alimentari",
    "Maison Basedau",
    "Mere Loup Trading",
    "Morgansen & Sons",
    "Nord-Ost-Fisch Handel",
    "Oceano Atlantico",
    "Old World Delicatessen",
    "Ottesen Exports",
    "Palo Alto Trading",
    "Pericles Catering",
    "Piccolo Ministranti",
    "Princesa Isabella",
    "Que Delicias",
    "Queen Cozinha",
    "QUICK-Stop",
    "Rancho grande",
    "Rattlesnake Canyon Grocery",
    "Regal Foods Inc.",
    "Ricardo Adocicados",
    "Richter Supermarkt",
    "Romero y tomillo",
    "Sao Paulo Traders",
    "Save-a-lot Markets",
    "Scandi Antiques",
    "Simonsbistro",
    "Sitio Papelaria",
    "Split Rail Beer",
    "Stefano & Sons",
    "Supremes Delices",
    "Taco world",
    "Tastys Bakery",
    "The Big Cheese",
    "The Cracker Box",
    "Toms Spezialitaten",
    "Toujours Plus",
    "Trails Head Gourmet",
    "Trailto Trading",
    "United Package",
    "Vaffelstuga",
    "Victory Foods",
    "Volvo-Filipinos",
    "Wartian Herkku",
    "Wellness Foods",
    "Wellworth Importers",
    "White Clover Markets",
    "Willy Boeken",
    "Wolskis Delicatessen",
    "Zaanse Sons",
    "Zeus Trading",
    "Zverev Import",
    "Anton's Bistro",
    "Bistro Grand",
    "Casa Bella Ristorante",
    "Fisherman's Wharf Market",
    "Golden Dragon Foods",
    "Healthy Harvest Co.",
    "La Petite Boulangerie",
    "Maple Syrup Imports",
    "Nordic Seafood Export",
    "Pandora Bakery",
    "River Valley Farms",
    "Sunrise Coffee Roasters",
    "The Olive Grove",
]

SUPPLIERS_DATA = [
    ("Exotic Liquids", "Charlotte", "UK"),
    ("New Orleans Cajun Delights", "New Orleans", "USA"),
    ("Grandma Kelly's Homestead", "Ann Arbor", "USA"),
    ("Tokyo Traders", "Tokyo", "Japan"),
    ("Cooperativa de Quesos", "Oviedo", "Spain"),
    ("Mayumi's", "Osaka", "Japan"),
    ("Pavlova Ltd", "Melbourne", "Australia"),
    ("Specialty Biscuits Ltd", "Manchester", "UK"),
    ("PB Knackebrod AB", "Goteborg", "Sweden"),
    ("Refrescos Americanas LTDA", "Sao Paulo", "Brazil"),
    ("Formaggi Fortini s.r.l.", "Ravenna", "Italy"),
    ("Norske Meierier", " Oslo", "Norway"),
    ("Bigfoot Breweries", "Bend", "USA"),
    ("Lyngbysild", "Lyngby", "Denmark"),
    ("Zaanse Snuiters", "Zaandam", "Netherlands"),
    ("Karkki Oy", "Lappeenranta", "Finland"),
]

CATEGORIES = [
    "Beverages",
    "Condiments",
    "Confections",
    "Dairy Products",
    "Grains/Cereals",
    "Meat/Poultry",
    "Produce",
    "Seafood",
]

PRODUCT_NAMES = {
    "Beverages": [
        "Chai",
        "Chang",
        "Guaraná Fantástica",
        "Sasquatch Ale",
        "Steeleye Stout",
        "Irish Coffee",
        "Lakkalikööri",
        "Otto's Lager",
        "Chartreuse verte",
        "Rhönbräu Klosterbier",
    ],
    "Condiments": [
        "Aniseed Syrup",
        "Chef Anton's Cajun Seasoning",
        "Chef Anton's Gumbo Mix",
        "Grandma's Boysenberry Spread",
        "Northwoods Cranberry Sauce",
        "Genen Shouyu",
        "Gula Malacca",
        "Lakka-Lime Sauce",
    ],
    "Confections": [
        "Teatime Chocolate Biscuits",
        "Pavlova",
        "Sir Rodney's Marmalade",
        "Sir Rodney's Scones",
        "Gustaf's Knäckebröd",
        "Tunnbröd",
        "Scottish Longbreads",
        "Chocolade",
        "Zaanse Koeken",
        "Chai Toffee",
        "NuNuCa Nuß-Nougat-Creme",
        "Gorgonzola Crackers",
    ],
    "Dairy Products": [
        "Queso Cabrales",
        "Queso Manchego La Pastora",
        "Gorgonzola Telino",
        "Mascarpone Fabioli",
        "Geitost",
        "Sally's Fresh Cheese",
        "Mozzarella di Giovanni",
        "Camembert Pierrot",
    ],
    "Grains/Cereals": [
        "Ikura",
        "Tofu",
        "Mishi Kobe Niku",
        "Uncle Bob's Organic Dried Pears",
        "Konbu",
        "Filipino Granola",
        "Cajun Granola",
    ],
    "Meat/Poultry": [
        "Alice Mutton",
        "Thüringer Rostbratwurst",
        "Perth Pasties",
        "Tourtière",
        "Pâté chinois",
    ],
    "Produce": ["Longlife Tofu", "Rössle Sauerkraut", "Manjimup Dried_Apples"],
    "Seafood": [
        "Inlagd Sill",
        "Gravad lax",
        "Boston Crab Meat",
        "Jack's New England Clam Chowder",
        "Nord-Ost Matjeshering",
        "Escargots Ruens",
        "Hokkai Fish",
    ],
}

CITIES = [
    ("USA", "Seattle"),
    ("USA", "Portland"),
    ("USA", "New York"),
    ("USA", "Chicago"),
    ("USA", "Boston"),
    ("UK", "London"),
    ("UK", "Manchester"),
    ("Germany", "Berlin"),
    ("Germany", "Hamburg"),
    ("Germany", "Munich"),
    ("France", "Paris"),
    ("France", "Lyon"),
    ("Spain", "Madrid"),
    ("Spain", "Barcelona"),
    ("Italy", "Rome"),
    ("Italy", "Milan"),
    ("Netherlands", "Amsterdam"),
    ("Sweden", "Stockholm"),
    ("Norway", "Oslo"),
    ("Denmark", "Copenhagen"),
    ("Finland", "Helsinki"),
    ("Japan", "Tokyo"),
    ("Brazil", "Sao Paulo"),
    ("Brazil", "Rio de Janeiro"),
    ("Australia", "Sydney"),
    ("Canada", "Toronto"),
    ("Mexico", "Mexico City"),
    ("Switzerland", "Zurich"),
]

FNAMES = [
    "Nancy",
    "Andrew",
    "Janet",
    "Margaret",
    "Steven",
    "Michael",
    "Robert",
    "Laura",
    "Anne",
    "Albert",
    "Tim",
    "Sofia",
    "Marcus",
    "Elena",
    "David",
]
LNAMES = [
    "Davolio",
    "Fuller",
    "Leverling",
    "Peacock",
    "Buchanan",
    "Suyama",
    "King",
    "Callahan",
    "Dodsworth",
    "Hellstrom",
    "Marconi",
    "Tanaka",
    "Weber",
    "Lopez",
    "Novak",
]
TITLES = [
    "Sales Manager",
    "Sales Representative",
    "Inside Sales Coordinator",
    "Vice President, Sales",
    "Account Manager",
]
SHIPPERS = ["Speedy Express", "United Package", "Federal Shipping"]

lines: list[str] = []


def esc(x: str) -> str:
    return x.replace("'", "''")


def emit(x: str) -> None:
    lines.append(x)


emit("-- Northwind-style seed data for DBcraWler.")
emit("-- Deterministic sample dataset. Loaded by Postgres init container.")
emit("BEGIN;")
emit("")

emit("-- Read-only application user (ADR: defense in depth with app-level guardrails)")
emit("DO $$ BEGIN")
emit("  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='app_readonly') THEN")
emit("    CREATE ROLE app_readonly LOGIN PASSWORD 'readonly_password';")
emit("  END IF;")
emit("END $$;")
emit("")

emit("CREATE TABLE categories (")
emit("    category_id   INTEGER PRIMARY KEY,")
emit("    category_name TEXT NOT NULL,")
emit("    description   TEXT")
emit(");")
emit("")
emit("CREATE TABLE suppliers (")
emit("    supplier_id   INTEGER PRIMARY KEY,")
emit("    company_name  TEXT NOT NULL,")
emit("    city          TEXT,")
emit("    country       TEXT,")
emit("    phone         TEXT")
emit(");")
emit("")
emit("CREATE TABLE products (")
emit("    product_id   INTEGER PRIMARY KEY,")
emit("    product_name TEXT NOT NULL,")
emit("    supplier_id  INTEGER REFERENCES suppliers(supplier_id),")
emit("    category_id  INTEGER REFERENCES categories(category_id),")
emit("    unit_price   NUMERIC(10,2) NOT NULL CHECK (unit_price >= 0),")
emit("    units_in_stock INTEGER NOT NULL DEFAULT 0 CHECK (units_in_stock >= 0),")
emit("    discontinued INTEGER NOT NULL DEFAULT 0")
emit(");")
emit("")
emit("CREATE TABLE employees (")
emit("    employee_id INTEGER PRIMARY KEY,")
emit("    first_name  TEXT NOT NULL,")
emit("    last_name   TEXT NOT NULL,")
emit("    title       TEXT,")
emit("    hire_date   DATE NOT NULL,")
emit("    city        TEXT,")
emit("    country     TEXT,")
emit("    reports_to  INTEGER REFERENCES employees(employee_id)")
emit(");")
emit("")
emit("CREATE TABLE customers (")
emit("    customer_id  TEXT PRIMARY KEY,")
emit("    company_name TEXT NOT NULL,")
emit("    contact_name TEXT,")
emit("    city         TEXT,")
emit("    country      TEXT,")
emit("    segment      TEXT NOT NULL,")
emit("    joined_at    DATE NOT NULL")
emit(");")
emit("")
emit("CREATE TABLE shippers (")
emit("    shipper_id   INTEGER PRIMARY KEY,")
emit("    company_name TEXT NOT NULL,")
emit("    phone        TEXT")
emit(");")
emit("")
emit("CREATE TABLE orders (")
emit("    order_id     INTEGER,")
emit("    customer_id  TEXT REFERENCES customers(customer_id),")
emit("    employee_id  INTEGER REFERENCES employees(employee_id),")
emit("    shipper_id   INTEGER REFERENCES shippers(shipper_id),")
emit("    order_date   DATE NOT NULL,")
emit("    required_date DATE NOT NULL,")
emit("    shipped_date DATE,")
emit("    freight      NUMERIC(10,2) NOT NULL DEFAULT 0,")
emit("    ship_city    TEXT,")
emit("    ship_country TEXT,")
emit("    order_status TEXT NOT NULL DEFAULT 'pending',")
emit("    PRIMARY KEY (order_id, order_date)")
emit(");")
emit("")
emit("CREATE TABLE order_details (")
emit("    order_id      INTEGER,")
emit("    order_date    DATE,")
emit("    product_id    INTEGER REFERENCES products(product_id),")
emit("    quantity      INTEGER NOT NULL CHECK (quantity > 0),")
emit("    unit_price    NUMERIC(10,2) NOT NULL CHECK (unit_price >= 0),")
emit(
    "    discount      NUMERIC(3,2) NOT NULL DEFAULT 0 CHECK (discount >= 0 AND discount <= 1),"
)
emit("    PRIMARY KEY (order_id, product_id, order_date),")
emit("    FOREIGN KEY (order_id, order_date) REFERENCES orders(order_id, order_date)")
emit(");")
emit("")

# shippers
for i, s in enumerate(SHIPPERS, 1):
    emit(
        f"INSERT INTO shippers (shipper_id, company_name, phone) VALUES ({i}, '{s}', '555-{i:04d}-{random.randint(100, 999)}');"
    )
emit("")

# categories
for i, c in enumerate(CATEGORIES, 1):
    emit(
        f"INSERT INTO categories (category_id, category_name, description) VALUES ({i}, '{c}', '{c} product family.');"
    )
emit("")

# suppliers
for i, (name, city, country) in enumerate(SUPPLIERS_DATA, 1):
    emit(
        f"INSERT INTO suppliers (supplier_id, company_name, city, country, phone) VALUES ({i}, '{esc(name)}', '{esc(city.strip())}', '{country}', '555-{i:02d}-{random.randint(1000, 9999)}');"
    )
emit("")

products: list[tuple[str, int, int, float]] = []
pid = 0
for cat_i, cat in enumerate(CATEGORIES, 1):
    names = PRODUCT_NAMES[cat]
    for j, name in enumerate(names):
        pid += 1
        supplier = random.randint(1, len(SUPPLIERS_DATA))
        price = round(random.uniform(5, 120), 2)
        stock = random.choice([0, 0, 10, 25, 50, 100, 120, 200])
        disc = 1 if random.random() < 0.06 else 0
        products.append((name, cat_i, pid, price))
        emit(
            f"INSERT INTO products (product_id, product_name, supplier_id, category_id, unit_price, units_in_stock, discontinued) VALUES ({pid}, '{esc(name)}', {supplier}, {cat_i}, {price}, {stock}, {disc});"
        )
emit("")

# employees
empl = []
eid_amount = 9
for i in range(1, eid_amount + 1):
    fn = FNAMES[(i - 1) % len(FNAMES)]
    ln = LNAMES[(i - 1) % len(LNAMES)]
    title = TITLES[(i - 1) % len(TITLES)]
    hd = f"{2015 + (i % 6):04d}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
    _, city = CITIES[(i * 3) % len(CITIES)]
    country = next(c for c, cc in CITIES if cc == city)
    boss = "NULL" if i <= 2 else random.randint(1, 2)
    empl.append(i)
    emit(
        f"INSERT INTO employees (employee_id, first_name, last_name, title, hire_date, city, country, reports_to) VALUES ({i}, '{fn}', '{ln}', '{title}', DATE '{hd}', '{city}', '{country}', {boss});"
    )
emit("")

# customers
cus_amount = len(COMPANIES)
segments = ["Retail", "Wholesale", "Restaurant", "Distribution"]
cids = []
for i in range(1, cus_amount + 1):
    name = COMPANIES[i - 1]
    cid = "".join(w[0].upper() for w in name.replace("'", "").replace("&", "").split())[
        :5
    ].ljust(5, str(i % 10))
    if cid in cids:
        cid = cid[:4] + str(i % 10) + str((i * 7) % 10)
    cids.append(cid)
    country, city = CITIES[(i * 7) % len(CITIES)]
    seg = segments[i % len(segments)]
    jd = f"{2018 + (i % 6):04d}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
    contact = f"{FNAMES[i % len(FNAMES)]} {LNAMES[i % len(LNAMES)]}"
    nm = name.replace("'", "''")
    emit(
        f"INSERT INTO customers (customer_id, company_name, contact_name, city, country, segment, joined_at) VALUES ('{cid}', '{nm}', '{contact}', '{city}', '{country}', '{seg}', DATE '{jd}');"
    )
emit("")

# orders + order_details
statuses = ["completed", "completed", "completed", "shipped", "pending", "cancelled"]
for k in range(240):
    y = random.randint(2023, 2025)
    m = random.randint(1, 12)
    d = random.randint(1, 28)
    od = f"{y:04d}-{m:02d}-{d:02d}"
    req = f"{y:04d}-{m:02d}-{min(28, d + random.randint(3, 14)):02d}"
    status = statuses[random.randint(0, len(statuses) - 1)]
    shipped = "NULL"
    if status in ("completed", "shipped"):
        sh = min(28, d + random.randint(1, 10))
        shipped = f"DATE '{y:04d}-{m:02d}-{sh:02d}'"
        if m == 12 and sh < d:
            shipped = f"DATE '{y + 1:04d}-01-{sh:02d}'"
    cid = cids[random.randint(0, len(cids) - 1)]
    eid = random.choice(empl)
    shp = random.randint(1, len(SHIPPERS))
    freight = round(random.uniform(2, 90), 2)
    _, scity = CITIES[(k * 5) % len(CITIES)]
    scountry = next(c for c, cc in CITIES if cc == scity)
    emit(
        f"INSERT INTO orders (order_id, customer_id, employee_id, shipper_id, order_date, required_date, shipped_date, freight, ship_city, ship_country, order_status) VALUES ({k + 1}, '{cid}', {eid}, {shp}, DATE '{od}', DATE '{req}', {shipped}, {freight}, '{scity}', '{scountry}', '{status}');"
    )
    detail_count = random.randint(1, 5)
    pchoices = random.sample(range(len(products)), detail_count)
    for pidx in pchoices:
        pname, _, prodid, pd_price = products[pidx]
        qty = random.randint(1, 40)
        disc = random.choice([0, 0, 0, 0.05, 0.1, 0.15, 0.25])
        uprice = round(pd_price * random.uniform(0.95, 1.15), 2)
        emit(
            f"INSERT INTO order_details (order_id, order_date, product_id, quantity, unit_price, discount) VALUES ({k + 1}, DATE '{od}', {prodid}, {qty}, {uprice}, {disc});"
        )
emit("")

emit("GRANT USAGE ON SCHEMA public TO app_readonly;")
emit("GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_readonly;")
emit(
    "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO app_readonly;"
)
emit("COMMIT;")
emit("")
lines_str = "\n".join(lines) + "\n"
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(lines_str, encoding="utf-8")
print(f"wrote {OUT} ({len(lines)} lines)")
