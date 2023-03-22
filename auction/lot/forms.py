from django import forms


class SearchForm(forms.Form):
    QUERY_N = 'query'
    QUERY_LEN = 120
    INPUT_LEN = 40
    PLACEHOLDER = 'Find in lot description'

    query = forms.CharField(
        max_length=QUERY_LEN, strip=True,
        widget=forms.TextInput(attrs={'size': INPUT_LEN, 'placeholder': PLACEHOLDER,
                                      'autofocus': True})
    )
