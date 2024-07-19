from flask import Flask, render_template, request, redirect, url_for, send_file
import csv
import os
import time

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        text = request.form['text']
        generate_csv(text)
        # return redirect(url_for('download_csv'))
    return render_template('index.html')

def generate_csv(text):
    lines = text.strip().split('\n')
    for attempt in range(2):  # 尝试5次
        try:
            with open('prompt.csv', 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['PageNumber', 'Scene', 'Text'])
                for line in lines:
                    if line.startswith('Page '):
                        page_number = line.strip().replace(':', '')
                    elif 'Scene:' in line:
                        scene = line.split(':', 1)[1].strip().replace('Scene:', '')
                    elif 'Text:' in line:
                        text = line.split(':', 1)[1].strip().replace('Text:', '')
                        writer.writerow([page_number, scene, text])
        except PermissionError:
            print(f"Permission denied, retrying... ({attempt + 1})")
            time.sleep(1)  # 等待1秒后重试
        else:
            break


@app.route('/download')
def download_csv():
    try:
        return send_file('prompt.csv', as_attachment=True)
    except FileNotFoundError:
        return "CSV file not found.", 404

if __name__ == '__main__':
    app.run(debug=True)