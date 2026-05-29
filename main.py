import os
import random
from flask import Flask, render_template, request, redirect, url_for
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
    return """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>理系タイプ診断</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/picocss@1/css/pico.min.css">
        <style>
            html { background-color: #0f172a; }
            body {
                max-width: 600px; margin: 0 auto; padding: 20px;
                background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                color: #f8fafc; min-height: 100dvh;
                display: flex; flex-direction: column; justify-content: center;
                font-family: sans-serif; text-align: center;
                box-sizing: border-box;
            }
            .card {
                background: rgba(30, 41, 59, 0.7);
                border: 1px solid rgba(255, 255, 255, 0.1);
                padding: 40px 30px; border-radius: 20px;
                box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
            }
            h1 { font-size: 2.2rem; color: #ffffff; font-weight: 800; margin-bottom: 15px; }
            .accent { color: #38bdf8; text-shadow: 0 0 10px rgba(56, 189, 248, 0.3); }
            p { color: #94a3b8; font-size: 1.05rem; line-height: 1.6; margin-bottom: 35px; }
            .start-btn {
                display: inline-block;
                background: linear-gradient(90deg, #2563eb, #1d4ed8);
                color: white; padding: 16px 32px;
                text-decoration: none; border-radius: 12px;
                font-weight: bold; font-size: 1.1rem;
                transition: all 0.2s ease;
                box-shadow: 0 4px 14px rgba(37, 99, 235, 0.4);
            }
            .start-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(37, 99, 235, 0.6);
                background: linear-gradient(90deg, #3b82f6, #2563eb);
            }
            @media (max-width: 480px) {
                body { padding: 16px; }
                .card { padding: 35px 20px; border-radius: 16px; }
                h1 { font-size: 1.8rem; }
                p { font-size: 0.95rem; margin-bottom: 25px; }
                .start-btn { width: 100%; box-sizing: border-box; padding: 14px; font-size: 1rem; }
            }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🚀 <span class="accent">理系タイプ診断</span></h1>
            <p>「自分は本当に理系に向いているのかな」と、進路に悩んでいませんか？20の質問であなたに潜む理系のポテンシャルを解き明かします。</p>
            <form action="/quiz" method="POST">
                <input type="hidden" name="past_answers" value="">
                <button type="submit" class="start-btn" style="border:none; cursor:pointer;">診断をスタートする</button>
            </form>
        </div>
    </body>
    </html>
    """

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