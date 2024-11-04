# myapp/forms.py
from django import forms

class TopicForm(forms.Form):
    topic = forms.CharField(label="Введите тему для теста", max_length=100)
