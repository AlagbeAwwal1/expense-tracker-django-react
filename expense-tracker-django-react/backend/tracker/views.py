import csv, io, json
from dateutil import parser as dateparser
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction as dbtx

from .models import Transaction, Category, SourceFile
from .serializers import TransactionSerializer

def _infer_category(merchant:str, categories):
    m = (merchant or '').upper()
    for c in categories:
        try:
            rules = json.loads(c.rules_json or '{}')
        except Exception:
            rules = {}
        for kw in (rules.get('merchant') or []):
            if kw.upper() in m:
                return c.name
    return 'Other'

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
        return Response({'detail':'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)
    if not f.name.lower().endswith('.csv'):
        return Response({'detail':'Upload a CSV file'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        text = f.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return Response({'detail': f'Failed to read CSV: {e}'}, status=400)

    reader = csv.DictReader(io.StringIO(text))
    fieldnames = { (name or '').strip().lower(): name for name in (reader.fieldnames or []) }

    col_date = _pick(fieldnames, 'date', ['transaction date','posted date'])
    col_desc = _pick(fieldnames, 'description', ['details','memo'])
    col_merchant = _pick(fieldnames, 'merchant', ['name','payee'])
    col_amount = _pick(fieldnames, 'amount', ['debit','credit','amt'])
    col_type = _pick(fieldnames, 'type', ['transaction type'])

    if not (col_date and col_amount):
        return Response({'detail':'CSV must contain at least Date and Amount columns'}, status=400)

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

            desc_val = (row.get(fieldnames.get(col_desc,''), '') or '').strip()
            merch_val = (row.get(fieldnames.get(col_merchant,''), '') or '').strip() or desc_val
            amt_raw = (row.get(fieldnames[col_amount]) or '0').replace(',', '').strip()
            try:
                amt_val = float(amt_raw)
            except Exception:
                amt_val = 0.0
            typ_val = (row.get(fieldnames.get(col_type,''), '') or '').strip()
            if not typ_val:
                typ_val = 'debit' if amt_val < 0 else 'credit'

            cat_val = _infer_category(merch_val, cats)

            Transaction.objects.create(
                date=date_val,
                description=desc_val,
                merchant=merch_val,
                amount=amt_val,
                type=typ_val,
                category=cat_val,
                source_file=sf
            )

    return Response({'status':'ok','file_id': sf.id})

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
        return Response({'detail':'Not found'}, status=404)
    cat = request.data.get('category')
    if cat:
        tx.category = cat
        tx.save()
    return Response(TransactionSerializer(tx).data)

@api_view(['GET'])
def spend_by_category(request):
    month = request.GET.get('month')
    qs = Transaction.objects.all()
    if month:
        qs = [t for t in qs if str(t.date).startswith(month)]
    agg = {}
    for t in qs:
        amt = abs(t.amount) if (t.type.lower().startswith('debit') or t.amount < 0) else 0.0
        agg[t.category] = agg.get(t.category, 0.0) + amt
    data = [{'category': k, 'amount': v} for k, v in sorted(agg.items(), key=lambda x: -x[1])]
    return Response(data)

@api_view(['POST'])
def seed_defaults(request):
     """Seed common categories with simple merchant keyword rules."""
     defaults = [
        ('Transport', {'merchant': ['UBER', 'LYFT', 'TTC', 'TRANSIT']}),
        ('Groceries', {'merchant': ['COSTCO', 'WALMART', 'NO FRILLS', 'SUPERSTORE', 'LOBLAWS']}),
        ('Dining', {'merchant': ['STARBUCKS', 'TIM HORTONS', 'MCDONALD', 'SUBWAY']}),
        ('Rent', {}),
        ('Utilities', {'merchant': ['BELL', 'ROGERS', 'NOVA SCOTIA POWER', 'NS POWER']}),
        ('Other', {}),
    ]
     for name, rules in defaults:
         Category.objects.get_or_create(name=name, defaults={'rules_json': json.dumps(rules)})
     return Response({'status': 'ok'})