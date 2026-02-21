from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum, Value, DecimalField
from django.db.models.functions import ExtractMonth, Coalesce

from decimal import Decimal
from datetime import date
import calendar
from openpyxl import Workbook

from .models import Aluno, Mensalidade, Pagamento
from .forms import AlunoForm, MensalidadeForm, PagamentoForm


# ===============================
# ALUNOS
# ===============================

@login_required
def aluno_novo(request):
    form = AlunoForm(request.POST or None)

    if form.is_valid():
        form.save()
        messages.success(request, "Aluno cadastrado com sucesso.")
        return redirect("lista_alunos")

    return render(request, "aluno_form.html", {"form": form})


@login_required
def aluno_editar(request, aluno_id):
    aluno = get_object_or_404(Aluno, id=aluno_id)
    form = AlunoForm(request.POST or None, instance=aluno)

    if form.is_valid():
        form.save()
        messages.success(request, f"Dados de {aluno.nome} atualizados!")
        return redirect("aluno_detalhe", aluno_id=aluno.id)

    return render(request, "aluno_form.html", {"form": form, "aluno": aluno})


@login_required
def aluno_detalhe(request, aluno_id):
    aluno = get_object_or_404(Aluno, id=aluno_id)
    mensalidades = aluno.mensalidades.all().order_by("-vencimento")

    return render(request, "aluno_detalhe.html", {
        "aluno": aluno,
        "mensalidades": mensalidades,
        "today": timezone.now().date()
    })


@login_required
def lista_alunos(request):
    busca = request.GET.get("q", "")

    alunos = (
        Aluno.objects.filter(nome__icontains=busca).order_by("nome")
        if busca else
        Aluno.objects.all().order_by("nome")
    )

    return render(request, "lista_alunos.html", {"alunos": alunos})


# ===============================
# MENSALIDADES
# ===============================

@login_required
def criar_mensalidade(request, aluno_id):
    aluno = get_object_or_404(Aluno, id=aluno_id)

    if request.method == "POST":
        form = MensalidadeForm(request.POST)
        if form.is_valid():
            mensalidade = form.save(commit=False)
            mensalidade.aluno = aluno
            mensalidade.save()
            messages.success(request, "Mensalidade criada.")
            return redirect("aluno_detalhe", aluno_id=aluno.id)
    else:
        form = MensalidadeForm(initial={"valor": aluno.valor_mensalidade})

    return render(request, "mensalidade_form.html", {"form": form, "aluno": aluno})


@login_required
def gerar_mensalidades_ano(request, aluno_id):
    aluno = get_object_or_404(Aluno, id=aluno_id)
    ano = timezone.now().year

    if not aluno.valor_mensalidade or not aluno.dia_vencimento:
        messages.error(request, "Configure valor e dia de vencimento.")
        return redirect("aluno_editar", aluno_id=aluno.id)

    for mes in range(1, 13):
        ultimo_dia = calendar.monthrange(ano, mes)[1]
        vencimento = date(ano, mes, min(aluno.dia_vencimento, ultimo_dia))

        Mensalidade.objects.get_or_create(
            aluno=aluno,
            vencimento=vencimento,
            defaults={"valor": aluno.valor_mensalidade}
        )

    messages.success(request, "Mensalidades geradas.")
    return redirect("aluno_detalhe", aluno_id=aluno.id)


@login_required
def excluir_mensalidade(request, mensalidade_id):
    mensalidade = get_object_or_404(Mensalidade, id=mensalidade_id)
    aluno_id = mensalidade.aluno.id
    mensalidade.delete()
    messages.success(request, "Mensalidade removida.")
    return redirect("aluno_detalhe", aluno_id=aluno_id)


# ===============================
# PAGAMENTO
# ===============================

@login_required
def pagar_mensalidade(request, mensalidade_id):
    mensalidade = get_object_or_404(Mensalidade, id=mensalidade_id)

    if request.method == "POST":
        valor = request.POST.get("valor", "0").replace(",", ".")
        forma = request.POST.get("forma")

        try:
            valor = Decimal(valor)
        except:
            messages.error(request, "Valor inválido.")
            return redirect("aluno_detalhe", aluno_id=mensalidade.aluno.id)

        if valor > 0:
            Pagamento.objects.create(
                mensalidade=mensalidade,
                valor=valor,
                forma=forma,
                data_pagamento=timezone.now().date()
            )
            messages.success(request, "Pagamento registrado.")
            return redirect("aluno_detalhe", aluno_id=mensalidade.aluno.id)

    return render(request, "pagamento_form.html", {"mensalidade": mensalidade})


# ===============================
# RELATÓRIO FINANCEIRO
# ===============================

@login_required
def relatorio_financeiro(request):
    hoje = timezone.now().date()
    busca = request.GET.get("q", "")

    alunos = (
        Aluno.objects.filter(nome__icontains=busca).order_by("nome")
        if busca else
        Aluno.objects.all().order_by("nome")
    )

    # Totais blindados contra None
    total_mes = Pagamento.objects.filter(
        data_pagamento__month=hoje.month,
        data_pagamento__year=hoje.year
    ).aggregate(total=Coalesce(Sum("valor"), Value(0), output_field=DecimalField()))["total"]

    total_ano = Pagamento.objects.filter(
        data_pagamento__year=hoje.year
    ).aggregate(total=Coalesce(Sum("valor"), Value(0), output_field=DecimalField()))["total"]

    total_hoje = Pagamento.objects.filter(
        data_pagamento=hoje
    ).aggregate(total=Coalesce(Sum("valor"), Value(0), output_field=DecimalField()))["total"]

    # Gráfico meses
    dados = (
        Pagamento.objects
        .filter(data_pagamento__year=hoje.year)
        .annotate(mes=ExtractMonth("data_pagamento"))
        .values("mes")
        .annotate(total=Coalesce(Sum("valor"), Value(0), output_field=DecimalField()))
    )

    grafico_meses = [0] * 12
    for item in dados:
        grafico_meses[item["mes"] - 1] = float(item["total"])

    return render(request, "relatorio_financeiro.html", {
        "alunos": alunos,
        "total_recebido_mes": total_mes,
        "total_recebido_ano": total_ano,
        "total_hoje": total_hoje,
        "grafico_meses": grafico_meses,
        "today": hoje,
    })


# ===============================
# CAIXA
# ===============================

@login_required
def relatorio_caixa(request):
    pagamentos = Pagamento.objects.all().order_by("-data_pagamento")

    total = pagamentos.aggregate(total=Coalesce(Sum("valor"), Value(0), output_field=DecimalField()))["total"]

    return render(request, "relatorio_caixa.html", {
        "pagamentos": pagamentos,
        "total_caixa": total
    })


# ===============================
# EXPORTAR EXCEL
# ===============================

@login_required
def exportar_caixa_excel(request):
    pagamentos = Pagamento.objects.all()

    wb = Workbook()
    ws = wb.active
    ws.append(["Aluno", "Valor", "Forma", "Data"])

    for p in pagamentos:
        ws.append([
            p.mensalidade.aluno.nome,
            float(p.valor),
            p.forma,
            p.data_pagamento.strftime("%d/%m/%Y")
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="caixa.xlsx"'
    wb.save(response)
    return response