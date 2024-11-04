# myapp/views.py
from django.shortcuts import render
from .forms import TopicForm
from g4f.client import Client  # Импортируем нужный клиент
import random

def generate_test(request):
    if request.method == "POST":
        form = TopicForm(request.POST)
        if form.is_valid():
            topic = form.cleaned_data['topic']
            test_data = generate_test_from_topic(topic)
            return render(request, 'myapp/test_result.html', {'test_data': test_data, 'topic': topic})
    else:
        form = TopicForm()
    return render(request, 'myapp/generate_test.html', {'form': form})

def generate_test_from_topic(topic):
    # Формируем инструкцию для генерации вопросов и ответов
    prompt = (
        f"Создай тест на тему '{topic}'.\n\n"
        "Пожалуйста, составь 10 вопросов, связанных с данной темой. Для каждого вопроса предоставь 4 варианта ответа, "
        "из которых только один является правильным. Форматируй каждый вопрос и ответы следующим образом:\n\n"
        "Вопрос: [Текст вопроса]\n"
        "A) [Вариант ответа 1]\n"
        "B) [Вариант ответа 2]\n"
        "C) [Вариант ответа 3]\n"
        "D) [Вариант ответа 4]\n"
        "Ответ: [Правильный вариант ответа (A, B, C или D)]\n\n"
        "Убедись, что вопросы чёткие и имеют только один правильный ответ. Варианты ответов должны быть похожи по форме "
        "и быть реалистичными, чтобы создать небольшой элемент сложности для пользователя."
    )

    try:
        # Инициализация клиента
        client = Client()
        
        # Отправляем запрос к модели GPT-3.5 с нужными параметрами
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты помощник, который создает тесты."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.7
        )

        # Извлекаем контент из ответа
        content = response.choices[0].message.content
        print(content)
        # Парсим результат для формирования вопросов и ответов
        questions = parse_test_response(content)
        return questions

    except Exception as e:
        print(f"Ошибка при генерации теста: {e}")
        return []

def parse_test_response(response_text):
    # Разбираем ответ в формате вопросов и вариантов
    questions = []
    for item in response_text.strip().split("\n\n"):
        lines = item.split("\n")
        if len(lines) >= 5:
            question = lines[0]
            answers = lines[1:5]
            correct_answer = lines[5] if len(lines) > 5 else "Не указан"
            questions.append({
                'question': question,
                'answers': answers,
                'correct_answer': correct_answer
            })
    return questions
