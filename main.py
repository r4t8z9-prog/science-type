import os
import random
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session
from questions import QUESTIONS, TYPES, TYPE_DETAILS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='static')
app.secret_key = os.getenv('SECRET_KEY')

def calculate_results(answers):
    scores = {t: 0 for t in TYPES}
    for q_idx, option_key in enumerate(answers):
        if q_idx >= len(QUESTIONS):
            break
        question = QUESTIONS[q_idx]
        selected_option = question["options"].get(option_key)
        if selected_option:
            scores[selected_option["main"]] += 2
            scores[selected_option["sub"]] += 1
    
    max_score = max(scores.values())
    highest_types = [t for t in TYPES if scores[t] == max_score]
    primary_type = random.choice(highest_types)
    
    shuffled_all_types = list(TYPES)
    random.shuffle(shuffled_all_types)
    sorted_types = sorted(shuffled_all_types, key=lambda t: scores[t], reverse=True)
    
    remaining_types = [t for t in sorted_types if t != primary_type]
    near_types = remaining_types[:2]
    
    return primary_type, near_types, scores

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/robots.txt')
def robots_txt():
    return send_from_directory(app.static_folder, 'robots.txt')

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory(app.static_folder, 'sitemap.xml')

@app.route('/quiz', methods=['POST'])
def quiz():
    past_answers_str = request.form.get('past_answers', '')
    
    if past_answers_str:
        answers = past_answers_str.split(',')
    else:
        answers = []
        
    selected_option = request.form.get('answer')
    if selected_option:
        answers.append(selected_option)

    current_idx = len(answers)

    if current_idx >= len(QUESTIONS):
        primary, near, _ = calculate_results(answers)
        session['result_data'] = {
            'primary': primary,
            'near': near
        }
        return redirect(url_for('show_result', type_name=primary))

    current_question = QUESTIONS[current_idx]
    
    options_items = list(current_question["options"].items())
    random.shuffle(options_items)
    shuffled_options = dict(options_items)
    
    display_question = {
        "text": current_question["text"],
        "options": shuffled_options
    }

    next_past_answers = ','.join(answers)

    return render_template(
        'quiz.html',
        question=display_question,
        current_num=current_idx + 1,
        total_questions=len(QUESTIONS),
        next_past_answers=next_past_answers
    )

@app.route('/result/<type_name>')
def show_result(type_name):
    if type_name not in TYPE_DETAILS:
        return redirect(url_for('index'))

    detail_data = TYPE_DETAILS.get(type_name)

    result_data = session.pop('result_data', None)
    
    near_types = []
    if result_data and result_data.get('primary') == type_name:
        near_types = result_data.get('near', [])

    return render_template(
        'result.html',
        primary_type=type_name,
        near_types=near_types,
        detail=detail_data,
        all_details=TYPE_DETAILS
    )

def main():
    port = int(os.environ.get('PORT', 80))
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    main()