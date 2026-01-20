from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum

# Ferramentas de Data e Calendário
from datetime import date
import calendar

# Ferramenta para exportação
from openpyxl import Workbook

# Importação dos modelos e formulários
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
        return redirect("relatorio_financeiro")
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
    mensalidades = aluno.mensalidades.all().order_by('-vencimento')
    return render(request, "aluno_detalhe.html", {
        "aluno": aluno, 
        "mensalidades": mensalidades, 
        "today": timezone.now().date()
    })

@login_required
def lista_alunos(request):
    busca = request.GET.get('q', '')
    if busca:
        alunos = Aluno.objects.filter(nome__icontains=busca).order_by('nome')
    else:
        alunos = Aluno.objects.all().order_by('nome')
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
            messages.success(request, "Mensalidade manual criada.")
            return redirect("aluno_detalhe", aluno_id=aluno.id)
    else:
        form = MensalidadeForm(initial={'valor': aluno.valor_mensalidade})
    return render(request, "mensalidade_form.html", {"form": form, "aluno": aluno})

@login_required
def gerar_mensalidades_ano(request, aluno_id):
    aluno = get_object_or_404(Aluno, id=aluno_id)
    ano_atual = timezone.now().year
    valor_aluno = aluno.valor_mensalidade
    dia_fixo = aluno.dia_vencimento 

    if not valor_aluno or valor_aluno <= 0 or not dia_fixo:
        messages.error(request, f"Erro: {aluno.nome} precisa ter Valor e Dia de Vencimento.")
        return redirect("aluno_editar", aluno_id=aluno.id)

    criadas = 0
    for mes in range(1, 13):
        ult_dia = calendar.monthrange(ano_atual, mes)[1]
        vencimento = date(ano_atual, mes, min(dia_fixo, ult_dia))

        if not Mensalidade.objects.filter(aluno=aluno, vencimento=vencimento).exists():
            Mensalidade.objects.create(aluno=aluno, valor=valor_aluno, vencimento=vencimento)
            criadas += 1

    messages.success(request, f"Sucesso! Geradas {criadas} mensalidades.")
    return redirect("aluno_detalhe", aluno_id=aluno.id)

@login_required
def excluir_mensalidade(request, mensalidade_id):
    mensalidade = get_object_or_404(Mensalidade, id=mensalidade_id)
    aluno_id = mensalidade.aluno.id
    mensalidade.delete()
    messages.success(request, "Mensalidade removida.")
    return redirect("aluno_detalhe", aluno_id=aluno_id)

# ===============================
# PAGAMENTOS E FINANCEIRO
# ===============================

@login_required
def pagar_mensalidade(request, mensalidade_id):
    mensalidade = get_object_or_404(Mensalidade, id=mensalidade_id)
    aluno = mensalidade.aluno

    if request.method == "POST":
        valor_bruto = request.POST.get("valor", "0")
        valor_limpo = valor_bruto.replace(',', '.').strip()
        forma_pago = request.POST.get("forma")

        if valor_limpo and forma_pago:
            Pagamento.objects.create(
                mensalidade=mensalidade,
                valor=valor_limpo, 
                forma=forma_pago,
                data_pagamento=timezone.now().date()
            )
            
            messages.success(request, "Pagamento registrado com sucesso!")
            return redirect("aluno_detalhe", aluno_id=aluno.id)

    return render(request, "pagamento_form.html", {"mensalidade": mensalidade})

@login_required
def relatorio_financeiro(request):
    hoje = timezone.now().date()
    busca = request.GET.get('q', '')
    
    # Filtro de alunos
    alunos = Aluno.objects.filter(nome__icontains=busca).order_by('nome') if busca else Aluno.objects.all().order_by('nome')

    # --- DADOS PARA O GRÁFICO DE FATURAMENTO (Últimos 6 meses) ---
    labels_meses = []
    dados_faturamento = []
    
    for i in range(5, -1, -1):
        data_ponto = hoje - timezone.timedelta(days=i*30)
        mes_nome = data_ponto.strftime('%b') # Jan, Fev...
        total = Pagamento.objects.filter(
            data_pagamento__month=data_ponto.month,
            data_pagamento__year=data_ponto.year
        ).aggregate(t=Sum('valor'))['t'] or 0
        labels_meses.append(mes_nome)
        dados_faturamento.append(float(total))

    # --- TOTAIS GERAIS (Cards) ---
    total_recebido_mes = Pagamento.objects.filter(data_pagamento__month=hoje.month, data_pagamento__year=hoje.year).aggregate(t=Sum("valor"))["t"] or 0
    total_recebido_ano = Pagamento.objects.filter(data_pagamento__year=hoje.year).aggregate(t=Sum("valor"))["t"] or 0
    total_hoje = Pagamento.objects.filter(data_pagamento=hoje).aggregate(t=Sum("valor"))["t"] or 0

    # Totais por Forma (Hoje)
    pix_hoje = Pagamento.objects.filter(data_pagamento=hoje, forma__iexact='PIX').aggregate(t=Sum("valor"))["t"] or 0
    dinheiro_hoje = Pagamento.objects.filter(data_pagamento=hoje, forma__iexact='DINHEIRO').aggregate(t=Sum("valor"))["t"] or 0
    cartao_hoje = Pagamento.objects.filter(data_pagamento=hoje, forma__iexact='CARTAO').aggregate(t=Sum("valor"))["t"] or 0

    # Indicadores
    aniversariantes = Aluno.objects.filter(data_nascimento__day=hoje.day, data_nascimento__month=hoje.month)
    total_atrasado = sum(m.em_aberto for m in Mensalidade.objects.filter(vencimento__lt=hoje) if m.em_aberto > 0)
    inadimplentes = Aluno.objects.filter(mensalidades__vencimento__lt=hoje, mensalidades__pagamentos__isnull=True).distinct().count()
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
        "labels_meses": labels_meses, # Para o gráfico
        "dados_faturamento": dados_faturamento, # Para o gráfico
        "today": hoje,
    })

@login_required
def relatorio_caixa(request):
    data_inicio = request.GET.get('inicio')
    data_fim = request.GET.get('fim')
    pagamentos = Pagamento.objects.all().order_by('-data_pagamento')
    
    if data_inicio: pagamentos = pagamentos.filter(data_pagamento__gte=data_inicio)
    if data_fim: pagamentos = pagamentos.filter(data_pagamento__lte=data_fim)
    
    total_caixa = pagamentos.aggregate(t=Sum('valor'))['t'] or 0
    total_pix = pagamentos.filter(forma='PIX').aggregate(t=Sum('valor'))['t'] or 0
    total_dinheiro = pagamentos.filter(forma='DINHEIRO').aggregate(t=Sum('valor'))['t'] or 0
    total_cartao = pagamentos.filter(forma='CARTAO').aggregate(t=Sum('valor'))['t'] or 0

    return render(request, "relatorio_caixa.html", {
        "pagamentos": pagamentos, 
        "total_caixa": total_caixa,
        "total_pix": total_pix,
        "total_dinheiro": total_dinheiro,
        "total_cartao": total_cartao,
    })

@login_required
def fechamento_mensal(request):
    hoje = timezone.now().date()
    mes_selecionado = int(request.GET.get('mes', hoje.month))
    ano_selecionado = int(request.GET.get('ano', hoje.year))

    meses_lista = [
        (1, "Janeiro"), (2, "Fevereiro"), (3, "Março"), (4, "Abril"),
        (5, "Maio"), (6, "Junho"), (7, "Julho"), (8, "Agosto"),
        (9, "Setembro"), (10, "Outubro"), (11, "Novembro"), (12, "Dezembro")
    ]

    pagamentos = Pagamento.objects.filter(
        data_pagamento__month=mes_selecionado,
        data_pagamento__year=ano_selecionado
    ).order_by('data_pagamento')

    total_geral = pagamentos.aggregate(total=Sum('valor'))['total'] or 0

    return render(request, "fechamento_mensal.html", {
        "pagamentos": pagamentos,
        "total_geral": total_geral,
        "mes": mes_selecionado,
        "ano": ano_selecionado,
        "meses": meses_lista,
    })

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
    
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="caixa.xlsx"'
    wb.save(response)
    return response