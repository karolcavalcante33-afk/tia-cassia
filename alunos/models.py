from django.db import models
from django.utils import timezone
from django.db.models import Sum
from django.core.validators import MinValueValidator, MaxValueValidator
import urllib.parse


# ==================================================
# ALUNO
# ==================================================
class Aluno(models.Model):
    nome = models.CharField(max_length=200)
    responsavel = models.CharField(max_length=200)

    telefone = models.CharField(
        "WhatsApp do Responsável",
        max_length=20,
        blank=True,
        null=True,
        help_text="Digite DDD + Número (Ex: 11999998888)"
    )

    data_nascimento = models.DateField(null=True, blank=True)

    atipico = models.BooleanField(default=False)
    tipo_atipico = models.CharField("Condição", max_length=100, blank=True, null=True)

    observacoes = models.TextField(blank=True, null=True)
    ativo = models.BooleanField(default=True)

    valor_mensalidade = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)]
    )

    dia_vencimento = models.PositiveIntegerField(
        "Dia de Vencimento",
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text="Dia fixo para vencimento (Ex: 5, 10, 15)"
    )

    def __str__(self):
        return self.nome

    # -----------------------------------------------
    # Utilitário interno para gerar link WhatsApp
    # -----------------------------------------------
    def _gerar_link_whatsapp(self, texto):
        if not self.telefone:
            return None

        msg = urllib.parse.quote(texto)

        # remove tudo que não for número
        fone_limpo = "".join(filter(str.isdigit, self.telefone))

        # adiciona código do Brasil se necessário
        if not fone_limpo.startswith("55"):
            fone_limpo = f"55{fone_limpo}"

        return f"https://wa.me/{fone_limpo}?text={msg}"

    # -----------------------------------------------
    # Link de aniversário
    # -----------------------------------------------
    def msg_aniversario_whatsapp(self):
        texto = (
            f"Olá {self.nome}! 🎉\n\n"
            "A Tia Cássia e toda a equipe do Studio desejam um feliz aniversário! 🎂✨\n\n"
            "Muita saúde e ótimas braçadas na natação! 🏊‍♂️🎉"
        )
        return self._gerar_link_whatsapp(texto)

    # -----------------------------------------------
    # Propriedade: é aniversário hoje?
    # -----------------------------------------------
    @property
    def e_aniversario(self):
        if not self.data_nascimento:
            return False
        hoje = timezone.now().date()
        return (
            self.data_nascimento.day == hoje.day and
            self.data_nascimento.month == hoje.month
        )


# ==================================================
# MENSALIDADE
# ==================================================
class Mensalidade(models.Model):
    aluno = models.ForeignKey(
        Aluno,
        related_name="mensalidades",
        on_delete=models.CASCADE
    )

    valor = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    vencimento = models.DateField()
    criada_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.aluno.nome} - {self.vencimento.strftime('%m/%Y')}"

    # -----------------------------------------------
    # Valor em aberto
    # -----------------------------------------------
    @property
    def em_aberto(self):
        total_pago = self.pagamentos.aggregate(
            total=Sum("valor")
        )["total"] or 0

        resultado = self.valor - total_pago
        return max(resultado, 0)

    # -----------------------------------------------
    # Link lembrete de vencimento
    # -----------------------------------------------
    def link_lembrete_vencimento(self):
        texto = (
            f"Olá! 😊\n\n"
            f"A mensalidade de natação de {self.aluno.nome} "
            f"vence em {self.vencimento.strftime('%d/%m/%Y')}.\n\n"
            f"💰 Valor: R$ {self.valor}\n\n"
            "Caso já tenha pago, desconsidere esta mensagem. 🙏"
        )

        return self.aluno._gerar_link_whatsapp(texto)


# ==================================================
# PAGAMENTO
# ==================================================
class Pagamento(models.Model):

    FORMAS = (
        ("PIX", "PIX"),
        ("DINHEIRO", "Dinheiro"),
        ("CARTAO", "Cartão"),
    )

    mensalidade = models.ForeignKey(
        Mensalidade,
        related_name="pagamentos",
        on_delete=models.CASCADE
    )

    valor = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    forma = models.CharField(max_length=20, choices=FORMAS)
    data_pagamento = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Pagamento: {self.mensalidade.aluno.nome} - R$ {self.valor}"

    # -----------------------------------------------
    # Link comprovante
    # -----------------------------------------------
    def link_whatsapp_direto(self):
        texto = (
            f"✅ COMPROVANTE DE RECEBIMENTO\n\n"
            f"Aluno: {self.mensalidade.aluno.nome}\n"
            f"💰 Valor: R$ {self.valor}\n"
            f"📅 Referente a: {self.mensalidade.vencimento.strftime('%m/%Y')}\n"
            f"💳 Forma: {self.forma}\n"
            f"🗓️ Data: {self.data_pagamento.strftime('%d/%m/%Y')}\n\n"
            "Muito obrigado! 🙏"
        )

        return self.mensalidade.aluno._gerar_link_whatsapp(texto)