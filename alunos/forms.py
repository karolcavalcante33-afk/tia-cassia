from django import forms
from .models import Aluno, Mensalidade, Pagamento
from decimal import Decimal, InvalidOperation

class AlunoForm(forms.ModelForm):
    # CharField permite que o JavaScript coloque pontos e vírgulas sem o Django reclamar
    valor_mensalidade = forms.CharField(
        label="Valor da Mensalidade",
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'id_valor_mensalidade'})
    )

    class Meta:
        model = Aluno
        fields = ["nome", "responsavel", "telefone", "valor_mensalidade", "dia_vencimento", "data_nascimento", "atipico", "tipo_atipico", "observacoes", "ativo"]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control"}),
            "responsavel": forms.TextInput(attrs={"class": "form-control"}),
            "telefone": forms.TextInput(attrs={"class": "form-control"}),
            "dia_vencimento": forms.NumberInput(attrs={"class": "form-control"}),
            "data_nascimento": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "atipico": forms.CheckboxInput(attrs={"class": "form-check-input", "id": "id_atipico"}),
            "tipo_atipico": forms.TextInput(attrs={"class": "form-control"}),
            "observacoes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "ativo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_valor_mensalidade(self):
        valor = self.cleaned_data.get("valor_mensalidade")
        if valor:
            valor = str(valor).replace('.', '').replace(',', '.') # Remove ponto de milhar e troca vírgula
            try:
                return Decimal(valor)
            except (InvalidOperation, ValueError):
                raise forms.ValidationError("Informe um valor válido.")
        return valor

class MensalidadeForm(forms.ModelForm):
    class Meta:
        model = Mensalidade
        fields = ["valor", "vencimento"]
        widgets = {
            "valor": forms.TextInput(attrs={"class": "form-control", "id": "id_valor_mensalidade"}),
            "vencimento": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        }

    def clean_valor(self):
        valor = self.cleaned_data.get("valor")
        if valor:
            return Decimal(str(valor).replace('.', '').replace(',', '.'))
        return valor

class PagamentoForm(forms.ModelForm):
    class Meta:
        model = Pagamento
        fields = ["valor", "forma"]
        widgets = {
            "valor": forms.TextInput(attrs={"class": "form-control", "id": "id_valor"}),
            "forma": forms.Select(attrs={"class": "form-select"}),
        }

    def clean_valor(self):
        valor = self.cleaned_data.get("valor")
        if valor:
            return Decimal(str(valor).replace('.', '').replace(',', '.'))
        return valor