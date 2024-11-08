# myapp/forms.py
from django import forms

class TopicForm(forms.Form):
    topic = forms.CharField(
        label="Введите тему для теста",
        max_length=100,
        required=False,  # Убираем обязательность заполнения
        widget=forms.TextInput(attrs={
            'class': 'form-control',  # Стилизация поля с Bootstrap
            'placeholder': 'Введите тему для теста'  # Подсказка
        })
    )
