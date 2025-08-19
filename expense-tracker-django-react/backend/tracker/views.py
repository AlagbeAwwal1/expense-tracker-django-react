import csv
import io
import json
import re
from dateutil import parser as dateparser
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction as dbtx

from .models import Transaction, Category, SourceFile
from .serializers import TransactionSerializer

from decimal import Decimal
from collections import defaultdict
from datetime import datetime

_CURRENCY_RX = re.compile(r'[,\s$]')

def _to_float(x):
    """Robust amount parser: handles $, commas, negatives, (1,234.56), etc."""
    if x is None:
        return 0.0
    if isinstance(x, (int, float, Decimal)):
        return float(x)
    s = str(x).strip()
    neg = False
    if s.startswith('(') and s.endswith(')'):  # (123.45) -> -123.45
        neg, s = True, s[1:-1]
    s = _CURRENCY_RX.sub('', s)
    try:
        v = float(s)
    except Exception:
        try:
            v = float(Decimal(s))
        except Exception:
            return 0.0
    return -v if neg else v

def _to_month(d):
    """Accept date/datetime or string -> 'YYYY-MM'. Returns '' if unknown."""
    if not d:
        return ''
    # datetime/date-like
    if hasattr(d, 'strftime'):
        return d.strftime('%Y-%m')
    s = str(d).strip()
    # Already looks like YYYY-MM or YYYY-MM-DD / YYYY/MM/DD
    m = re.match(r'^(\d{4})[-/](\d{2})(?:[-/]\d{2})?$', s)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    # Try common formats
    for fmt in ('%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y', '%d-%m-%Y'):
        try:
            return datetime.strptime(s, fmt).strftime('%Y-%m')
        except Exception:
            pass
    return ''

def _as_text(x):
    """Coerce None/list/tuple/str to a single string for matching."""
    if x is None:
        return ""
    if isinstance(x, (list, tuple, set)):
        return " ".join(map(str, x))
    return str(x)

def _safe_rules(rules):
    """Accept dict or JSON string; always return dict."""
    if isinstance(rules, dict):
        return rules
    if isinstance(rules, str):
        try:
            return json.loads(rules or "{}")
        except json.JSONDecodeError:
            return {}
    return {}

def _match_any(text, patterns):
    """Case-insensitive substring or regex match against a list of patterns."""
    text = _as_text(text)
    if not text or not patterns:
        return False
    U = text.upper()
    for p in (patterns or []):
        if p is None:
            continue
        if isinstance(p, (list, tuple, set)):
            p = " ".join(map(str, p))
        s = str(p)
        if s.startswith("re:"):
            try:
                if re.search(s[3:], text, flags=re.I):
                    return True
            except re.error:
                continue
        else:
            if s.strip().upper() in U:
                return True
    return False

def _infer_category(merchant, categories, description=""):
    """
    merchant/description may be str or list (from CSV parsing quirks).
    categories: iterable of Category model instances having name & rules_json.
    """
    m = _as_text(merchant)
    d = _as_text(description)

    for cat in categories:
        rules = _safe_rules(getattr(cat, "rules_json", {}))
        if _match_any(m, rules.get("merchant")) or _match_any(d, rules.get("description")):
            return cat.name
    return "Other"


def _pick(mapping, name, fallbacks):
    for k in [name] + fallbacks:
        if k in mapping:
            return k
    return None


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_csv(request):
    f = request.FILES.get('file')
    if not f:
        return Response({'detail': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)
    if not f.name.lower().endswith('.csv'):
        return Response({'detail': 'Upload a CSV file'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        text = f.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return Response({'detail': f'Failed to read CSV: {e}'}, status=400)

    reader = csv.DictReader(io.StringIO(text))
    fieldnames = {(name or '').strip().lower()                  : name for name in (reader.fieldnames or [])}

    col_date = _pick(fieldnames, 'date', ['transaction date', 'posted date'])
    col_desc = _pick(fieldnames, 'description', ['details', 'memo'])
    col_merchant = _pick(fieldnames, 'merchant', ['name', 'payee'])
    col_amount = _pick(fieldnames, 'amount', ['debit', 'credit', 'amt'])
    col_type = _pick(fieldnames, 'type', ['transaction type'])

    if not (col_date and col_amount):
        return Response({'detail': 'CSV must contain at least Date and Amount columns'}, status=400)

    sf = SourceFile.objects.create(filename=f.name)
    cats = list(Category.objects.all())

    with dbtx.atomic():
        for row in reader:
            date_raw = (row.get(fieldnames[col_date]) or '').strip()
            try:
                # normalize to YYYY-MM-DD if possible, else keep as-is
                date_val = dateparser.parse(date_raw).date().isoformat()
            except Exception:
                date_val = date_raw

            desc_val = (row.get(fieldnames.get(
                col_desc, ''), '') or '').strip()
            merch_val = (row.get(fieldnames.get(col_merchant, ''),
                         '') or '').strip() or desc_val
            amt_raw = (row.get(fieldnames[col_amount]) or '0').replace(
                ',', '').strip()
            try:
                amt_val = float(amt_raw)
            except Exception:
                amt_val = 0.0
            typ_val = (row.get(fieldnames.get(col_type, ''), '') or '').strip()
            if not typ_val:
                typ_val = 'debit' if amt_val < 0 else 'credit'

            cat_val = _infer_category(merch_val, cats, desc_val)

            Transaction.objects.create(
                date=date_val,
                description=desc_val,
                merchant=merch_val,
                amount=amt_val,
                type=typ_val,
                category=cat_val,
                source_file=sf
            )

    return Response({'status': 'ok', 'file_id': sf.id})


@api_view(['GET'])
def transactions_list(request):
    month = request.GET.get('month')
    qs = Transaction.objects.all().order_by('-id')
    if month:
        qs = [t for t in qs if str(t.date).startswith(month)]
        return Response(TransactionSerializer(qs, many=True).data)
    return Response(TransactionSerializer(qs, many=True).data)


@api_view(['PATCH'])
def transaction_detail(request, pk: int):
    try:
        tx = Transaction.objects.get(pk=pk)
    except Transaction.DoesNotExist:
        return Response({'detail': 'Not found'}, status=404)
    cat = request.data.get('category')
    if cat:
        tx.category = cat
        tx.save()
    return Response(TransactionSerializer(tx).data)


@api_view(['GET'])
def spend_by_category(request):
    month = request.GET.get('month')
    qs = Transaction.objects.filter(type='debit')  # expenses only
    if month:
        y, m = month.split('-')
        qs = qs.filter(date__year=int(y), date__month=int(m))

    by_cat = defaultdict(float)
    for t in qs:
        amt = _to_float(t.amount)
        if amt < 0:
            amt = -amt  # store as positive spend
        by_cat[(t.category or 'Other')] += amt

    data = [{'category': k, 'amount': round(v, 2)} for k, v in by_cat.items()]
    # Optional: sort largest-first
    data.sort(key=lambda x: x['amount'], reverse=True)
    return Response(data)


@api_view(['POST'])
def seed_defaults(request):
    """Seed rich default categories & rules. Add ?reset=1 to wipe existing first."""
    if request.GET.get('reset') == '1':
        Category.objects.all().delete()

    defaults = [
        ("Groceries", {
            "merchant": ["COSTCO", "WALMART", "NO FRILLS", "SUPERSTORE", "LOBLAWS", "SOBEYS", "FOODLAND", "GIANT TIGER", "FRESHCO", "REAL CANADIAN SUPERSTORE"],
            "description": ["GROCERY", "SUPERMARKET"]
        }),
        ("Dining", {
            "merchant": ["STARBUCKS", "TIM HORTONS", "MCDONALD", "SUBWAY", "KFC", "PIZZA PIZZA", "DOMINO", "POPEYES", "BURGER KING", "A&W", "WENDY", "HARVEYS"],
            "description": ["DINING", "RESTAURANT", "CAFE", "COFFEE", "FAST FOOD"]
        }),
        ("Transport", {
            "merchant": ["UBER", "LYFT", "TTC", "TRANSIT", "HALIFAX TRANSIT", "YYZ EXPRESS", "PRESTO"],
            "description": ["TRANSIT", "BUS", "SUBWAY", "TRAIN", "TAXI", "RIDE"]
        }),
        ("Utilities", {
            "merchant": ["BELL", "ROGERS", "TELUS", "KOODO", "FIDO", "EASTLINK", "NOVA SCOTIA POWER", "NS POWER", "HYDRO", "ENMAX", "FORTIS", "EPCOR"],
            "description": ["INTERNET", "MOBILE", "PHONE", "ELECTRIC", "UTILITY", "HYDRO", "POWER", "WATER", "GAS BILL"]
        }),
        ("Fuel & Gas", {
            "merchant": ["IRVING", "ESSO", "SHELL", "PETRO", "PETRO-CANADA", "ULTRAMAR", "HUSKY", "PIONEER"],
            "description": ["FUEL", "GAS STATION", "PUMP"]
        }),
        ("Entertainment", {
            "merchant": ["NETFLIX", "SPOTIFY", "DISNEY", "APPLE.COM", "GOOGLE", "YOUTUBE", "MICROSOFT XBOX", "PLAYSTATION"],
            "description": ["SUBSCRIPTION", "STREAM", "ENTERTAINMENT"]
        }),
        ("Pharmacy", {
            "merchant": ["SHOPPERS DRUG MART", "LAWTONS", "PHARMASAVE", "JEAN COUTU", "REXALL"],
            "description": ["PHARMACY", "PRESCRIPTION"]
        }),
        ("Shopping", {
            "merchant": ["AMAZON", "BEST BUY", "CANADIAN TIRE", "H&M", "ZARA", "WALMART ONLINE", "EBAY", "ETSY"],
            "description": ["ONLINE ORDER", "MARKETPLACE", "RETAIL"]
        }),
        ("Travel", {
            "merchant": ["AIR CANADA", "WESTJET", "PORTER", "EXPEDIA", "BOOKING.COM", "AIRBNB"],
            "description": ["FLIGHT", "HOTEL", "TRAVEL", "BAGGAGE"]
        }),
        ("Rent", {
            "merchant": ["RENT", "PROPERTY MGMT", "PAD", "YARDI", "AVENUE LIVING", "CAPREIT", "MORGARD", "HOMESTEAD"],
            "description": ["RENT", "LEASE", "TENANCY", "re:^PAD\\s*RENT"]
        }),
        ("Fees", {
            "merchant": ["BANK FEE", "NSF", "SERVICE CHARGE", "MAINTENANCE FEE"],
            "description": ["FEE", "SURCHARGE", "SERVICE CHARGE", "OVERDRAFT"]
        }),
        ("Income", {
            "merchant": ["PAYROLL", "DIRECT DEPOSIT", "GOVERNMENT OF CANADA", "CRA", "EI"],
            "description": ["PAYCHEQUE", "SALARY", "SCHOLARSHIP", "STIPEND"]
        }),
        ("Other", {"merchant": [], "description": []}),
    ]

    for name, rules in defaults:
        Category.objects.get_or_create(
            name=name, defaults={'rules_json': json.dumps(rules)})
    return Response({"status": "ok"})


@api_view(['GET'])
def monthly_category_totals(request):
    qs = Transaction.objects.all().order_by('date')

    # month -> {category: total}
    buckets = defaultdict(lambda: defaultdict(float))

    for t in qs:
        mon = _to_month(t.date)
        amt = _to_float(t.amount)

        if t.type == 'debit':
            # record spend as positive number
            if amt < 0:
                amt = -amt
            cat = t.category or 'Other'
            buckets[mon][cat] += amt
        elif t.type == 'credit':
            # accumulate income separately (positive)
            buckets[mon]['Income'] += abs(amt)

    # shape for chart: [{ month: "YYYY-MM", Groceries: 123, Dining: 45, Income: 1500, ...}, ...]
    result = []
    for mon in sorted(buckets.keys()):
        row = {'month': mon}
        for cat, total in buckets[mon].items():
            row[cat] = round(total, 2)
        result.append(row)

    return Response(result)


@api_view(['DELETE'])
def delete_transaction(request):
    Transaction.objects.all().delete()
    return Response({'status': 'All transactions deleted'})

# tracker/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(["GET"])
def health(request):
    return Response({"ok": True})


