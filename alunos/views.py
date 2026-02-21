from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum
from django.db.models.functions import ExtractMonth

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

    return render(request, "lista_alunos.html", {
        "alunos": alunos
    })

    return render(request, "lista_alunos.html", {
        "alunos": alunos
    })


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
            messages.success(request, "Mensalidade manual criada.")
            return redirect("aluno_detalhe", aluno_id=aluno.id)
    else:
        form = MensalidadeForm(initial={"valor": aluno.valor_mensalidade})

    return render(request, "mensalidade_form.html", {"form": form, "aluno": aluno})


@login_required
def gerar_mensalidades_ano(request, aluno_id):
    aluno = get_object_or_404(Aluno, id=aluno_id)
    ano_atual = timezone.now().year
    valor_aluno = aluno.valor_mensalidade
    dia_fixo = aluno.dia_vencimento

    if not valor_aluno or valor_aluno <= 0 or not dia_fixo:
        messages.error(request, f"{aluno.nome} precisa ter Valor e Dia de Vencimento.")
        return redirect("aluno_editar", aluno_id=aluno.id)

    criadas = 0

    for mes in range(1, 13):
        ult_dia = calendar.monthrange(ano_atual, mes)[1]
        vencimento = date(ano_atual, mes, min(dia_fixo, ult_dia))

        if not Mensalidade.objects.filter(aluno=aluno, vencimento=vencimento).exists():
            Mensalidade.objects.create(
                aluno=aluno,
                valor=valor_aluno,
                vencimento=vencimento
            )
            criadas += 1

    messages.success(request, f"Geradas {criadas} mensalidades.")
    return redirect("aluno_detalhe", aluno_id=aluno.id)


@login_required
def excluir_mensalidade(request, mensalidade_id):
    mensalidade = get_object_or_404(Mensalidade, id=mensalidade_id)
    aluno_id = mensalidade.aluno.id
    mensalidade.delete()
    messages.success(request, "Mensalidade removida.")
    return redirect("aluno_detalhe", aluno_id=aluno_id)


# ===============================
# PAGAMENTOS
# ===============================

@login_required
def pagar_mensalidade(request, mensalidade_id):
    mensalidade = get_object_or_404(Mensalidade, id=mensalidade_id)
    aluno = mensalidade.aluno

    if request.method == "POST":
        valor_bruto = request.POST.get("valor", "0").replace(",", ".").strip()
        forma_pago = request.POST.get("forma")

        try:
            valor_decimal = Decimal(valor_bruto)
        except:
            messages.error(request, "Valor inválido.")
            return redirect("aluno_detalhe", aluno_id=aluno.id)

        if valor_decimal > 0 and forma_pago:
            Pagamento.objects.create(
                mensalidade=mensalidade,
                valor=valor_decimal,
                forma=forma_pago,
                data_pagamento=timezone.now().date()
            )
            messages.success(request, "Pagamento registrado com sucesso!")
            return redirect("aluno_detalhe", aluno_id=aluno.id)

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

    # =============================
    # 🥧 GRÁFICO POR FORMA (ANO)
    # =============================
    formas_pagamento = (
        Pagamento.objects
        .filter(data_pagamento__year=hoje.year)
        .values("forma")
        .annotate(total=Sum("valor"))
    )

    grafico_formas = {
        "PIX": 0,
        "DINHEIRO": 0,
        "CARTAO": 0,
    }

    for item in formas_pagamento:
        grafico_formas[item["forma"]] = float(item["total"])

    # =============================
    # 📊 GRÁFICO ANUAL (12 MESES)
    # =============================
    ano_atual = hoje.year

    dados_mensais = (
        Pagamento.objects
        .filter(data_pagamento__year=ano_atual)
        .annotate(mes=ExtractMonth("data_pagamento"))
        .values("mes")
        .annotate(total=Sum("valor"))
        .order_by("mes")
    )

    grafico_meses = [0] * 12

    for item in dados_mensais:
        grafico_meses[item["mes"] - 1] = float(item["total"])

    # =============================
    # 💰 TOTAIS
    # =============================
    total_recebido_mes = Pagamento.objects.filter(
        data_pagamento__month=hoje.month,
        data_pagamento__year=hoje.year
    ).aggregate(t=Sum("valor"))["t"] or 0

    total_recebido_ano = Pagamento.objects.filter(
        data_pagamento__year=hoje.year
    ).aggregate(t=Sum("valor"))["t"] or 0

    total_hoje = Pagamento.objects.filter(
        data_pagamento=hoje
    ).aggregate(t=Sum("valor"))["t"] or 0

    pix_hoje = Pagamento.objects.filter(
        data_pagamento=hoje,
        forma="PIX"
    ).aggregate(t=Sum("valor"))["t"] or 0

    dinheiro_hoje = Pagamento.objects.filter(
        data_pagamento=hoje,
        forma="DINHEIRO"
    ).aggregate(t=Sum("valor"))["t"] or 0

    cartao_hoje = Pagamento.objects.filter(
        data_pagamento=hoje,
        forma="CARTAO"
    ).aggregate(t=Sum("valor"))["t"] or 0

    # =============================
    # 🎂 ANIVERSARIANTES
    # =============================
    aniversariantes = Aluno.objects.filter(
    data_nascimento__isnull=False,
    data_nascimento__day=hoje.day,
    data_nascimento__month=hoje.month,
    ativo=True
)

    # =============================
    # 📌 INDICADORES
    # =============================
    total_atrasado = sum(
        m.em_aberto
        for m in Mensalidade.objects.filter(vencimento__lt=hoje)
        if m.em_aberto > 0
    )

    inadimplentes = Aluno.objects.filter(
        mensalidades__vencimento__lt=hoje,
        mensalidades__pagamentos__isnull=True
    ).distinct().count()

    total_atipicos = Aluno.objects.filter(atipico=True).count()

    return render(request, "relatorio_financeiro.html", {
        "alunos": alunos,
        "total_recebido_mes": total_recebido_mes,
        "total_recebido_ano": total_recebido_ano,
        "total_atrasado": total_atrasado,
        "inadimplentes": inadimplentes,
        "total_atipicos": total_atipicos,
        "total_hoje": total_hoje,
        "pix_hoje": pix_hoje,
        "dinheiro_hoje": dinheiro_hoje,
        "cartao_hoje": cartao_hoje,
        "aniversariantes": aniversariantes,
        "grafico_meses": grafico_meses,
        "grafico_formas": grafico_formas,
        "today": hoje,
    })


# ===============================
# RELATÓRIO DE CAIXA
# ===============================

@login_required
def relatorio_caixa(request):
    data_inicio = request.GET.get("inicio")
    data_fim = request.GET.get("fim")

    pagamentos = Pagamento.objects.all().order_by("-data_pagamento")

    if data_inicio:
        pagamentos = pagamentos.filter(data_pagamento__gte=data_inicio)

    if data_fim:
        pagamentos = pagamentos.filter(data_pagamento__lte=data_fim)

    total_caixa = pagamentos.aggregate(t=Sum("valor"))["t"] or 0
    total_pix = pagamentos.filter(forma="PIX").aggregate(t=Sum("valor"))["t"] or 0
    total_dinheiro = pagamentos.filter(forma="DINHEIRO").aggregate(t=Sum("valor"))["t"] or 0
    total_cartao = pagamentos.filter(forma="CARTAO").aggregate(t=Sum("valor"))["t"] or 0

    return render(request, "relatorio_caixa.html", {
        "pagamentos": pagamentos,
        "total_caixa": total_caixa,
        "total_pix": total_pix,
        "total_dinheiro": total_dinheiro,
        "total_cartao": total_cartao,
    })


# ===============================
# FECHAMENTO MENSAL
# ===============================

@login_required
def fechamento_mensal(request):
    hoje = timezone.now().date()

    mes_selecionado = int(request.GET.get("mes", hoje.month))
    ano_selecionado = int(request.GET.get("ano", hoje.year))

    meses_lista = [(i, calendar.month_name[i].capitalize()) for i in range(1, 13)]

    pagamentos = Pagamento.objects.filter(
        data_pagamento__month=mes_selecionado,
        data_pagamento__year=ano_selecionado
    ).order_by("data_pagamento")

    total_geral = pagamentos.aggregate(total=Sum("valor"))["total"] or 0

    return render(request, "fechamento_mensal.html", {
        "pagamentos": pagamentos,
        "total_geral": total_geral,
        "mes": mes_selecionado,
        "ano": ano_selecionado,
        "meses": meses_lista,
    })


# ===============================
# EXPORTAR CAIXA EXCEL
# ===============================

@login_required
def exportar_caixa_excel(request):
    pagamentos = Pagamento.objects.all()

    wb = Workbook()
    ws = wb.active
    ws.title = "Caixa"

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