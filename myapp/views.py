from django.shortcuts import render
from django.http import HttpResponse
from .forms import TopicForm
from g4f.client import Client  
import re
from openpyxl import Workbook
import time


def download_test_as_excel(request):
    test_data = request.session.get('test_data', [])
    topic = request.session.get('topic', 'Неизвестная тема')

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Тест"

    sheet.append(["Тема:", topic])
    sheet.append([])  
    sheet.append(["Вопрос", "Вариант A", "Вариант B", "Вариант C", "Вариант D", "Правильный ответ"])

    for item in test_data:
        sheet.append([
            item['question'],
            item['answers'][0],
            item['answers'][1],
            item['answers'][2],
            item['answers'][3],
            item['correct_answer']
        ])

    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = 'attachment; filename="test.xlsx"'
    workbook.save(response)

    return response


def generate_test(request):
    if request.method == "POST":
        form = TopicForm(request.POST)
        if form.is_valid():
            topic = form.cleaned_data['topic']
            test_data = generate_test_from_topic(topic)

            request.session['test_data'] = test_data
            correct_answers = {i + 1: item['correct_answer'] for i, item in enumerate(test_data)}
            request.session['correct_answers'] = correct_answers
            request.session['topic'] = topic

            return render(request, 'myapp/test_result.html', {'test_data': test_data, 'topic': topic})
    else:
        form = TopicForm()
    return render(request, 'myapp/generate_test.html', {'form': form})


def generate_test_from_topic(topic):
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

    while True: 
        try:
            client = Client()
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "Ты помощник, который создает тесты."},
                          {"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.7
            )


            content = response.choices[0].message.content

            questions = parse_test_response(content)
            
            return questions  

        except Exception as e:
            print(f"Ошибка при парсинге или запросе: {e}. Пробуем снова через 1 секунду...")
            time.sleep(1)  
            
def check_answers(request):
    if request.method == "POST":
        correct_answers = request.session.get('correct_answers', {})
        user_answers = request.POST
        
        test_data = request.session.get('test_data', None)

        print("Test Data:", test_data)  
        
        results = []
        for i, (question, correct_answer) in enumerate(correct_answers.items(), start=1):
            user_answer = user_answers.get(f"answer_{i}", "").strip().upper() 
            correct_answer = correct_answer.strip().upper()  


            user_answer_text = user_answers.get(f"answer_{i}", "")

            test_data_item = test_data[i - 1] if test_data and len(test_data) >= i else None
            if test_data_item:
                test_data_item['question'] = re.sub(r"\*\*", "", test_data_item['question'])
                answers = test_data_item.get('answers', [])  
                correct_answer_text = "Нет данных"  

                if correct_answer == 'A' and len(answers) > 0:
                    correct_answer_text = answers[0]
                elif correct_answer == 'B' and len(answers) > 1:
                    correct_answer_text = answers[1]
                elif correct_answer == 'C' and len(answers) > 2:
                    correct_answer_text = answers[2]
                elif correct_answer == 'D' and len(answers) > 3:
                    correct_answer_text = answers[3]

            is_correct = (user_answer == correct_answer)

            results.append({
                'question': test_data_item,
                'user_answer': user_answer_text,
                'correct_answer': correct_answer_text,
                'is_correct': is_correct
            })
        
        print("Results:", results)

        return render(request, 'myapp/test_results.html', {'results': results})


def parse_test_response(content):
    questions = []
    raw_questions = content.strip().split("\n\n")  

    for raw_question in raw_questions:
        try:
            lines = raw_question.strip().split("\n")

            if len(lines) < 6:
                print(f"Ошибка при парсинге вопроса: недостаточно строк. Данные: {lines}")
                raise ValueError("Недостаточно строк для парсинга вопроса.")

            question_text = lines[0].replace("Вопрос: ", "").strip()

            answers = [line.replace(f"{letter}) ", "").strip() for letter, line in zip("ABCD", lines[1:5])]
            if len(answers) != 4:
                print(f"Ошибка при парсинге ответов. Данные: {lines}")
                raise ValueError("Некорректное количество вариантов ответа.")

            correct_answer_line = lines[5]
            if not correct_answer_line.startswith("Ответ:"):
                print(f"Ошибка при парсинге правильного ответа. Данные: {correct_answer_line}")
                raise ValueError("Невалидный формат правильного ответа.")

            correct_answer = correct_answer_line.replace("Ответ:", "").strip()
            if correct_answer not in ["A", "B", "C", "D"]:
                print(f"Ошибка: некорректный правильный ответ. Данные: {correct_answer}")
                raise ValueError("Невалидный правильный ответ.")

            questions.append({
                "question": question_text,
                "answers": answers,
                "correct_answer": correct_answer,
            })

        except Exception as e:
            print(f"Ошибка при парсинге вопроса: {e}. Пробуем заново парсить все вопросы.")
            raise  

    return questions