from django import forms
from .models import Aluno, Mensalidade, Pagamento
from decimal import Decimal, InvalidOperation


# ==================================================
# ALUNO
# ==================================================
class AlunoForm(forms.ModelForm):

    valor_mensalidade = forms.CharField(
        label="Valor da Mensalidade",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "id": "id_valor_mensalidade"
            }
        )
    )

    class Meta:
        model = Aluno
        fields = [
            "nome",
            "responsavel",
            "telefone",
            "valor_mensalidade",
            "dia_vencimento",
            "data_nascimento",
            "atipico",
            "tipo_atipico",
            "observacoes",
            "ativo"
        ]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control"}),
            "responsavel": forms.TextInput(attrs={"class": "form-control"}),
            "telefone": forms.TextInput(attrs={"class": "form-control"}),
            "dia_vencimento": forms.NumberInput(attrs={"class": "form-control"}),
            "data_nascimento": forms.DateInput(
                attrs={"class": "form-control", "type": "date"},
                format="%Y-%m-%d"
            ),
            "atipico": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "tipo_atipico": forms.TextInput(attrs={"class": "form-control"}),
            "observacoes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "ativo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_valor_mensalidade(self):
        valor = self.cleaned_data.get("valor_mensalidade")

        if not valor:
            return Decimal("0.00")

        valor = str(valor).strip()

        if "," in valor:
            valor = valor.replace(".", "").replace(",", ".")

        try:
            return Decimal(valor)
        except (InvalidOperation, ValueError):
            raise forms.ValidationError("Informe um valor válido.")


# ==================================================
# MENSALIDADE
# ==================================================
class MensalidadeForm(forms.ModelForm):

    class Meta:
        model = Mensalidade
        fields = ["valor", "vencimento"]
        widgets = {
            "valor": forms.TextInput(attrs={"class": "form-control"}),
            "vencimento": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        }

    def clean_valor(self):
        valor = self.cleaned_data.get("valor")

        if not valor:
            return valor

        valor = str(valor).strip()

        if "," in valor:
            valor = valor.replace(".", "").replace(",", ".")

        try:
            return Decimal(valor)
        except (InvalidOperation, ValueError):
            raise forms.ValidationError("Informe um valor válido.")


# ==================================================
# PAGAMENTO
# ==================================================
class PagamentoForm(forms.ModelForm):

    class Meta:
        model = Pagamento
        fields = ["valor", "forma"]
        widgets = {
            "valor": forms.TextInput(attrs={"class": "form-control"}),
            "forma": forms.Select(attrs={"class": "form-select"}),
        }

    def clean_valor(self):
        valor = self.cleaned_data.get("valor")

        if not valor:
            return valor

        valor = str(valor).strip()

        if "," in valor:
            valor = valor.replace(".", "").replace(",", ".")

        try:
            return Decimal(valor)
        except (InvalidOperation, ValueError):
            raise forms.ValidationError("Informe um valor válido.")