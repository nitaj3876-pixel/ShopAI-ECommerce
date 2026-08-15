# ShopAI — AI-Powered E-Commerce Platform

A full-stack e-commerce site (FastAPI + SQLAlchemy + vanilla JS/Bootstrap) with JWT auth,
content-based AI product recommendations (TF-IDF + cosine similarity), a rule-based AI
shopping assistant, an admin panel with analytics, and seeded demo data.

> **Honest scope note:** this is a strong, runnable foundation covering the full request →
> response → database loop for every core flow (auth, catalog, cart, wishlist, orders,
> reviews, recommendations, chatbot, admin). It is not a pixel-perfect Amazon clone and a
> few things are intentionally simplified for a project of this size — see
> [What's simplified](#whats-simplified-vs-the-full-spec) at the bottom.

---

## 1. Quick Start (local, no Docker)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt --break-system-packages   # omit the flag on a normal venv

cp .env.example .env            # defaults to SQLite — works with zero setup
python seed.py                  # creates & fills the database with demo data
uvicorn app.main:app --reload   # http://localhost:8000  (docs at /docs)
```

### Frontend

The frontend is plain HTML/CSS/JS — no build step. Serve it with any static server, e.g.:

```bash
cd frontend
python -m http.server 5500      # http://localhost:5500
```

Open `http://localhost:5500/index.html`. If your backend runs somewhere other than
`http://localhost:8000`, set it before the other scripts load, e.g. add this to each HTML
`<head>` (or edit `assets/js/api.js`):

```html
<script>window.SHOPAI_API_BASE = "https://your-api-url.com";</script>
```

### Demo logins (created by `seed.py`)

| Role  | Email               | Password      |
|-------|---------------------|----------------|
| Admin | admin@shopai.com    | Admin@123      |
| User  | (any seeded user — printed at the end of `seed.py`, e.g. row 1) | Password@123 |

---

## 2. Quick Start (Docker) — PostgreSQL + pgAdmin included

```bash
docker-compose up --build
```

This starts:
- **db** — PostgreSQL on `localhost:5432` (user `ecommerce_user` / pass `ecommerce_pass` / db `ecommerce_db`)
- **backend** — FastAPI on `localhost:8000`, already pointed at that PostgreSQL instance
- **frontend** — static files served by nginx on `localhost:5500`
- **pgadmin** — pgAdmin4 UI on `localhost:5050` (login `admin@shopai.com` / `Admin@123`)

Run the seed script once the containers are up (creates all tables + demo data):

```bash
docker-compose exec backend python seed.py
```

### Connecting pgAdmin to the database

1. Open `http://localhost:5050` and log in with `admin@shopai.com` / `Admin@123`.
2. Right-click **Servers → Register → Server...**
3. **General tab** → Name: `ShopAI DB` (anything you like).
4. **Connection tab**:
   - Host name/address: `db`   *(the docker-compose service name — not `localhost`, since pgAdmin runs in its own container)*
   - Port: `5432`
   - Maintenance database: `ecommerce_db`
   - Username: `ecommerce_user`
   - Password: `ecommerce_pass`
5. Save. You'll see `ecommerce_db → Schemas → public → Tables` with all the app's tables
   (users, products, orders, etc.) once `seed.py` has run.

---

## 2b. Using PostgreSQL + pgAdmin without Docker (native install)

If you'd rather run Postgres directly on your machine instead of in Docker:

1. **Install PostgreSQL** (includes pgAdmin on Windows/Mac installers, or install pgAdmin
   separately on Linux): https://www.postgresql.org/download/
2. **Create the database** — easiest via pgAdmin:
   - Open pgAdmin → connect to your local server (host `localhost`, port `5432`, the
     postgres superuser password you set during install).
   - Right-click **Databases → Create → Database...** → name it `ecommerce_db`.
   - Optionally right-click **Login/Group Roles → Create → Login/Group Role...** to make a
     dedicated `ecommerce_user` role (Definition tab: set a password; Privileges tab:
     enable "Can login?"), then grant it ownership of `ecommerce_db`.
3. **Point the backend at it** — edit `backend/.env`:
   ```
   DATABASE_URL=postgresql://ecommerce_user:your_password@localhost:5432/ecommerce_db
   ```
   (or use the postgres superuser + its password if you skipped creating a dedicated role)
4. **Install the Postgres driver** (already in `requirements.txt`, just make sure it installed):
   ```bash
   pip install psycopg2-binary --break-system-packages
   ```
5. **Create tables + demo data**:
   ```bash
   cd backend
   python seed.py
   ```
6. Refresh pgAdmin's Tables list under `ecommerce_db → Schemas → public → Tables` — you
   should see `users`, `products`, `orders`, `categories`, etc., all populated.

> Note: `seed.py` calls `Base.metadata.drop_all()` then `create_all()` — running it again
> wipes and regenerates all demo data. Don't run it against a database with real data you
> want to keep.

---

## 3. Project Structure

```
backend/
  app/
    models/           # SQLAlchemy models (users, products, orders, etc.)
    schemas/          # Pydantic request/response schemas
    routers/           # auth, users, products, cart, wishlist, reviews,
                        # orders, recommendations, chatbot, admin
    services/
      recommendation.py  # TF-IDF + cosine similarity AI engine
    auth.py            # JWT + password hashing + role guards
    database.py         # SQLAlchemy engine/session
    main.py              # FastAPI app + router wiring + CORS
  seed.py                # generates 15 categories, 100 products, 200 users, ~500 orders
  requirements.txt
  Dockerfile
  .env.example

frontend/
  index.html, login.html, register.html, forgot_password.html,
  products.html, product_details.html, cart.html, checkout.html,
  orders.html, wishlist.html, profile.html, admin.html
  assets/
    css/style.css
    js/api.js       # fetch wrapper for every backend endpoint
    js/main.js      # navbar/footer/product-card rendering
    js/chatbot.js   # floating AI assistant widget

docker-compose.yml
README.md
```

---

## 4. AI Features — how they actually work

- **Similar Products / Frequently Bought Together** — `app/services/recommendation.py`
  builds a TF-IDF matrix over each product's name + brand + category + description, then
  ranks other products by cosine similarity. "Frequently bought together" additionally
  checks real co-occurrence across past orders and falls back to content similarity when
  there's no order history yet.
- **Personalized Recommendations** — blends a signed-in user's order history, wishlist, and
  recently-viewed items into a single "taste profile" vector, then ranks the catalog against
  it. New users with no history get top-rated products instead.
- **AI Shopping Assistant** — a lightweight keyword-intent classifier (`app/routers/chatbot.py`)
  that recognizes greetings, FAQs (returns, shipping, payments, tracking) and product search
  requests, then queries the real product catalog for matches. It's isolated behind one
  `detect_intent()` function, so swapping in a real LLM call (e.g. to the Anthropic API) later
  is a small, contained change.

---

## 5. Deployment

- **Backend** → Render / Railway: point them at `backend/`, set `DATABASE_URL` to a managed
  PostgreSQL instance, set `JWT_SECRET_KEY` to a real secret, and set the start command to
  `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- **Frontend** → Vercel / Netlify: deploy the `frontend/` folder as a static site, and set
  `window.SHOPAI_API_BASE` to your deployed backend URL.

---

## 6. What's simplified vs. the full spec

Being upfront about the gap between "diploma final-year project" and "production Amazon
clone" so you know exactly what to extend:

- **Payments** — Razorpay/Stripe/UPI are wired as selectable methods and recorded on the
  order, but there's no live gateway integration (no real charge is made — this is standard
  for a demo/academic project; wiring a real gateway is a well-documented, separate step
  per provider).
- **Images** — demo products use placeholder photos (picsum.photos), not an image upload
  pipeline. The backend does mount `/uploads` as static storage and has `python-multipart`
  installed, ready for an admin image-upload endpoint to be added.
  **Invoices** — generated as clean plain-text files, not styled PDFs (the `pdf` toolchain
  can be added if you want branded PDF invoices).
- **Admin analytics** — real bar-chart visualizations built with plain HTML/CSS (no charting
  library dependency), not Chart.js/D3 graphs — swap in a charting lib for animated charts.
- **Chatbot** — rule-based keyword intent matching (works fully offline, no API key needed),
  not an LLM. The code is structured so a real LLM call is a one-function swap.
- **List view on the product listing page** — the grid/list toggle is wired but list view
  currently reuses the grid card styling rather than a distinct dense row layout.

None of the above are placeholders — every endpoint listed in the spec is implemented and
functional end-to-end. These are the specific spots where "production Amazon" and "a real,
gradeable, run-it-yourself project" diverge, called out so nothing surprises you.
