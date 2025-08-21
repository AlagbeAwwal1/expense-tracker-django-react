# Expense Tracker Backend (Django + DRF)

## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8000
# (optional) seed default categories
curl -X POST http://127.0.0.1:8000/api/seed/
```
API base: `http://127.0.0.1:8000/api/`

### Endpoints
- `POST /api/files/` (multipart CSV upload)
- `GET /api/transactions/?month=YYYY-MM`
- `PATCH /api/transactions/{id}/`  { "category": "Dining" }
- `GET /api/analytics/spend-by-category/?month=YYYY-MM`
