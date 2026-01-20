from django.contrib import admin
from .models import Aluno, Mensalidade, Pagamento


@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = ("nome", "responsavel", "ativo")
    list_filter = ("ativo",)
    search_fields = ("nome", "responsavel")


@admin.register(Mensalidade)
class MensalidadeAdmin(admin.ModelAdmin):
    list_display = ("aluno", "valor", "vencimento")
    list_filter = ("vencimento",)


@admin.register(Pagamento)
class PagamentoAdmin(admin.ModelAdmin):
    list_display = ("mensalidade", "valor", "forma", "data_pagamento")
    list_filter = ("forma",)
