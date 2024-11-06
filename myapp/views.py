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

            # Сохраняем правильные ответы в сессии
            correct_answers = {f"Вопрос {i+1}": item['correct_answer'] for i, item in enumerate(test_data)}
            request.session['correct_answers'] = correct_answers

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
        # print(content)
        # Парсим результат для формирования вопросов и ответов
        questions = parse_test_response(content)
        return questions

    except Exception as e:
        print(f"Ошибка при генерации теста: {e}")
        return []
    
def check_answers(request):
    if request.method == "POST":
        # Получаем ответы пользователя и правильные ответы из сессии
        correct_answers = request.session.get('correct_answers', {})
        user_answers = request.POST

        # Сравниваем ответы пользователя с правильными ответами
        results = []
        for i, (question, correct_answer) in enumerate(correct_answers.items(), start=1):
            # Извлекаем ответ пользователя для данного вопроса
            
            user_answer = user_answers.get(f"answer_{i}", "").strip().upper()[0]  
            correct_answer = correct_answer.strip().upper()[0]  

            user_answer_text = user_answers.get(f"answer_{i}", "") 
            
           
            # print(correct_answer)
            is_correct = (user_answer == correct_answer)

            # Добавляем результат для каждого вопроса
            results.append({
                'question': question,
                'user_answer': user_answer,
                'correct_answer': correct_answer,
                'is_correct': is_correct,
                'user_answer_text': user_answer_text,
            })

        return render(request, 'myapp/test_results.html', {'results': results})
    else:
        return render(request, 'myapp/generate_test.html')


def parse_test_response(response_text):
    # Разбираем ответ в формате вопросов и вариантов
    questions = []
    for item in response_text.strip().split("\n\n"):
        lines = item.split("\n")
        if len(lines) >= 5:
            question = lines[0].replace("Вопрос: ", "").strip()  # Убираем "Вопрос: " из текста вопроса
            answers = [line.strip() for line in lines[1:5]]
            correct_answer = lines[5].replace("Ответ:", "").strip()  # Извлекаем только букву
            questions.append({
                'question': question,
                'answers': answers,
                'correct_answer': correct_answer
            })
    return questions

