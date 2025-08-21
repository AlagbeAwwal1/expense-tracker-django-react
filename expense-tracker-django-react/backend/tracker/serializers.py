from rest_framework import serializers
from .models import Transaction, Category, SourceFile

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class SourceFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SourceFile
        fields = '__all__'
