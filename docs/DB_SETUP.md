# Database setup

## 1) Install dependencies

```bash
pip install -r requirements.txt
```

## 2) Initialize the SQLite database

```bash
python ./scripts/init_db.py
```

You should now have data/app.db.

## 3) Run the API

```bash
uvicorn src.main:app --reload
```

Example request:

```bash
curl "http://127.0.0.1:8000/stations/nearest?lon=34.78&lat=32.08"
```
