# Dummy Unit Lot Traceability System — v3

## How to run

1. Double-click **START_SERVER.bat**
   - OR open terminal in this folder and run:
   - `python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8100 --reload`

2. Wait for: `INFO: Application startup complete`

3. Open browser: http://localhost:8100

4. Hard refresh: Ctrl + Shift + R

---

## Important — before running

Make sure `frontend\img\NXP_logo.png` exists.
Copy your NXP logo image into that folder if missing.

---

## Admin login
- Master admin: farzanaJ / Dmyt2@Master
- Other admins: username = WBI, password = Nx{digits}#{FirstThree}

---

## Database connection
Edit `backend\app\database.py` if your DB details change:
```
postgresql://traceability_user:TraceDB2024@92.120.147.79:5432/dummy_traceability
```

---

## File structure
```
dummy-traceability-v3\
├── START_SERVER.bat          ← double click to start
├── backend\
│   ├── requirements.txt
│   └── app\
│       ├── main.py
│       ├── database.py
│       ├── models.py
│       ├── schemas.py
│       └── routers\
│           ├── auth.py
│           ├── dashboard.py
│           ├── lots.py
│           ├── packages.py
│           ├── request.py
│           └── technicians.py
└── frontend\
    ├── index.html
    ├── img\
    │   └── NXP_logo.png      ← copy your logo here
    ├── css\
    │   └── style.css
    └── js\
        ├── api.js
        └── app.js
```
