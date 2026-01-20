from django.urls import path
from . import views

urlpatterns = [
    # HOME / FINANCEIRO (Dashboard)
    path("", views.relatorio_financeiro, name="relatorio_financeiro"),

    # ALUNO (Cadastro e Detalhes)
    path("aluno/novo/", views.aluno_novo, name="aluno_novo"),
    path("aluno/<int:aluno_id>/", views.aluno_detalhe, name="aluno_detalhe"),
    path("aluno/<int:aluno_id>/editar/", views.aluno_editar, name="aluno_editar"),
    path('alunos/', views.lista_alunos, name='lista_alunos'),

    # MENSALIDADES (Controle de Cobranças)
    path("aluno/<int:aluno_id>/mensalidade/nova/", views.criar_mensalidade, name="criar_mensalidade"),
    path("aluno/<int:aluno_id>/gerar-mensalidades/", views.gerar_mensalidades_ano, name="gerar_mensalidades_ano"),
    path("mensalidade/<int:mensalidade_id>/pagar/", views.pagar_mensalidade, name="pagar_mensalidade"),
    path("mensalidade/<int:mensalidade_id>/excluir/", views.excluir_mensalidade, name="excluir_mensalidade"),

    # CAIXA (Relatórios e Exportação)
    path("caixa/", views.relatorio_caixa, name="relatorio_caixa"),
    path("caixa/fechamento/", views.fechamento_mensal, name="fechamento_mensal"),
    path("caixa/exportar/", views.exportar_caixa_excel, name="exportar_caixa_excel"),
]