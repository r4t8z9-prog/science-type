import os
import random
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from questions import QUESTIONS, TYPES, TYPE_DETAILS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

def calculate_results(answers):
    """回答データからスコアを計算する関数"""
    scores = {t: 0 for t in TYPES}
    for q_idx, option_key in enumerate(answers):
        if q_idx >= len(QUESTIONS):
            break
        question = QUESTIONS[q_idx]
        selected_option = question["options"].get(option_key)
        if selected_option:
            scores[selected_option["main"]] += 2
            scores[selected_option["sub"]] += 1
    
    # 公平なタイブレイク（同点処理）
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
    """スタート画面"""
    return render_template('index.html')

@app.route('/robots.txt')
def robots_txt():
    return send_from_directory(app.static_folder, 'robots.txt')

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory(app.static_folder, 'sitemap.xml')

@app.route('/quiz', methods=['POST'])  # 🌟 GETは使わず、常にPOSTでデータを受け取る仕様にします
def quiz():
    """診断中の1問1画面の処理"""
    # 🌟 画面から「これまでの回答履歴（カンマ区切りの文字列）」を受け取る
    past_answers_str = request.form.get('past_answers', '')
    
    # 文字列をリストに変換する（空文字なら空リスト）
    if past_answers_str:
        answers = past_answers_str.split(',')
    else:
        answers = []
        
    # 今回押されたボタンの回答を取得
    selected_option = request.form.get('answer')
    if selected_option:
        answers.append(selected_option)

    current_idx = len(answers)

    # 20問すべて解き終わったら結果画面へ
    if current_idx >= len(QUESTIONS):
        primary, near, all_scores = calculate_results(answers)
        detail_data = TYPE_DETAILS.get(primary)
        
        return render_template(
            'result.html',
            primary_type=primary,
            near_types=near,
            detail=detail_data,
            all_details=TYPE_DETAILS
        )

    # 現在の質問
    current_question = QUESTIONS[current_idx]
    
    # 選択肢のシャッフル
    options_items = list(current_question["options"].items())
    random.shuffle(options_items)
    shuffled_options = dict(options_items)
    
    display_question = {
        "text": current_question["text"],
        "options": shuffled_options
    }

    # 🌟 次の画面へ引き渡すための「新しい回答履歴文字列」を作成
    next_past_answers = ','.join(answers)

    return render_template(
        'quiz.html',
        question=display_question,
        current_num=current_idx + 1,
        total_questions=len(QUESTIONS),
        next_past_answers=next_past_answers  # 🌟 HTML側に引き渡す
    )

def main():
    port = int(os.environ.get('PORT', 80))
    app.run(host='0.0.0.0', port=port, debug=True)

if __name__ == '__main__':
    main()