from django import forms


class AccountDeletionRequestForm(forms.Form):
    email = forms.EmailField(
        label='E-mail da conta',
        max_length=254,
        widget=forms.EmailInput(attrs={
            'autocomplete': 'email',
            'placeholder': 'seuemail@exemplo.com',
        }),
    )
    reason = forms.CharField(
        label='Motivo (opcional)',
        max_length=1000,
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 4,
            'placeholder': 'Se desejar, conte por que quer excluir sua conta.',
        }),
    )
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'autocomplete': 'off',
            'tabindex': '-1',
        }),
    )

    def clean_email(self):
        return self.cleaned_data['email'].strip().lower()
