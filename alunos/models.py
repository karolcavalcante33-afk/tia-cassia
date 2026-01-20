from django.db import models
from django.utils import timezone
from django.db.models import Sum
import urllib.parse
from django.core.validators import MinValueValidator, MaxValueValidator

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
    valor_mensalidade = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    dia_vencimento = models.PositiveIntegerField(
        "Dia de Vencimento", 
        default=5, 
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text="Dia fixo para vencimento (Ex: 5, 10, 15)"
    )

    def __str__(self):
        return self.nome

    def msg_aniversario_whatsapp(self):
        """Gera link de parabéns personalizado"""
        texto = (f"Olá! A Tia Cássia e toda a equipe do Studio desejam um feliz aniversário para o(a) *{self.nome}*! ✨ 🎂\n\n"
                 f"Muita saúde e ótimas braçadas na natação! 🏊‍♂️🎉")
        msg = urllib.parse.quote(texto)
        if self.telefone:
            fone_limpo = "".join(filter(str.isdigit, self.telefone))
            if not fone_limpo.startswith('55'): 
                fone_limpo = f"55{fone_limpo}"
            return f"https://wa.me/{fone_limpo}?text={msg}"
        return "#"

# ==================================================
# MENSALIDADE
# ==================================================
class Mensalidade(models.Model):
    aluno = models.ForeignKey(
        Aluno,
        related_name="mensalidades",
        on_delete=models.CASCADE
    )
    valor = models.DecimalField(max_digits=8, decimal_places=2)
    vencimento = models.DateField()
    criada_em = models.DateTimeField(auto_now_add=True)

    @property
    def em_aberto(self):
        """Calcula quanto falta pagar desta mensalidade"""
        # Corrigido para garantir que a soma não retorne None
        total_pago = self.pagamentos.aggregate(Sum('valor'))['valor__sum'] or 0
        resultado = self.valor - total_pago
        return max(resultado, 0)

    def __str__(self):
        return f"{self.aluno.nome} - {self.vencimento.strftime('%m/%Y')}"

    def link_lembrete_vencimento(self):
        """Gera mensagem para enviar um dia antes do vencimento"""
        texto = (
            f"Olá! Passando para lembrar que a mensalidade de natação do(a) *{self.aluno.nome}* "
            f"vence amanhã, dia *{self.vencimento.strftime('%d/%m')}*.\n\n"
            f"Valor: R$ {self.valor}\n\n"
            f"Caso já tenha pago, por favor desconsidere esta mensagem. Obrigado! 🙏"
        )
        msg = urllib.parse.quote(texto)
        if self.aluno.telefone:
            fone_limpo = "".join(filter(str.isdigit, self.aluno.telefone))
            if not fone_limpo.startswith('55'): 
                fone_limpo = f"55{fone_limpo}"
            return f"https://wa.me/{fone_limpo}?text={msg}"
        return "#"

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
    valor = models.DecimalField(max_digits=8, decimal_places=2)
    forma = models.CharField(max_length=20, choices=FORMAS)
    data_pagamento = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Pagamento: {self.mensalidade.aluno.nome} - R$ {self.valor}"

    def link_whatsapp_direto(self):
        """Gera o comprovante para enviar ao pai/responsável"""
        texto = (
            f"✅ *COMPROVANTE DE RECEBIMENTO*\n\n"
            f"Recebemos o pagamento de: *{self.mensalidade.aluno.nome}*\n"
            f"💰 *Valor:* R$ {self.valor}\n"
            f"📅 *Referente a:* {self.mensalidade.vencimento.strftime('%m/%Y')}\n"
            f"💳 *Forma:* {self.forma}\n"
            f"🗓️ *Data:* {self.data_pagamento.strftime('%d/%m/%Y')}\n\n"
            f"Muito obrigado! 🙏"
        )
        msg = urllib.parse.quote(texto)
        
        if self.mensalidade.aluno.telefone:
            fone_limpo = "".join(filter(str.isdigit, self.mensalidade.aluno.telefone))
            if not fone_limpo.startswith('55'):
                fone_limpo = f"55{fone_limpo}"
            return f"https://wa.me/{fone_limpo}?text={msg}"
        
        return "#"