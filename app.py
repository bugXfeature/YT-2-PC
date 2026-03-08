from flask import Flask, request, render_template, send_file
import yt_dlp
import os
import uuid

app = Flask(__name__)

TEMP_DIR = '/tmp'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/info', methods=['POST'])
def info():
    url = request.form['url']
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title'),
                'thumbnail': info.get('thumbnail'),
                'duration': info.get('duration_string', ''),
            }
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/download', methods=['POST'])
def download():
    url = request.form['url']
    unique_id = str(uuid.uuid4())[:8]
    output_path = os.path.join(TEMP_DIR, f'yt_{unique_id}.mp4')

    try:
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': output_path,
            'merge_output_format': 'mp4',
            'quiet': True,
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'video')

        return send_file(output_path, as_attachment=True, download_name=f"{title}.mp4")

    except Exception as e:
        if os.path.exists(output_path):
            os.remove(output_path)
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)
