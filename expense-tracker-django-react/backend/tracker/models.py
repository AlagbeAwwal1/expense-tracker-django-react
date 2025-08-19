from django.db import models

class SourceFile(models.Model):
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

class Category(models.Model):
    name = models.CharField(max_length=64, unique=True)
    rules_json = models.TextField(default='{}')  # merchant keyword rules

    def __str__(self):
        return self.name

class Transaction(models.Model):
    date = models.CharField(max_length=32)  # keep simple for varied CSVs
    description = models.TextField(blank=True)
    merchant = models.CharField(max_length=255, blank=True)
    amount = models.FloatField(default=0.0)
    type = models.CharField(max_length=32, default='debit')
    category = models.CharField(max_length=64, default='Other')
    source_file = models.ForeignKey(SourceFile, null=True, blank=True, on_delete=models.SET_NULL)
