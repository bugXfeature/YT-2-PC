from flask import Flask, request, render_template, send_file, jsonify
from pytubefix import YouTube
from pytubefix.cli import on_progress
from moviepy.editor import VideoFileClip, AudioFileClip
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_qualities', methods=['POST'])
def get_qualities():
    url = request.json.get('url')
    try:
        yt = YouTube(url)
        video_streams = yt.streams.filter(adaptive=True, file_extension='mp4', only_video=True).order_by('resolution')
        resolutions = []
        seen = set()
        for s in reversed(video_streams):
            if s.resolution and s.resolution not in seen:
                resolutions.append(s.resolution)
                seen.add(s.resolution)
        return jsonify({'title': yt.title, 'resolutions': resolutions})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download', methods=['POST'])
def download():
    url = request.form['url']
    mode = request.form.get('mode', 'video')  # 'video' or 'audio'
    resolution = request.form.get('resolution', 'highest')
    save_path = request.form.get('save_path', '').strip()

    try:
        yt = YouTube(url, on_progress_callback=on_progress)

        if mode == 'audio':
            audio_stream = yt.streams.filter(adaptive=True, file_extension='mp4', only_audio=True).order_by('abr').last()
            audio_stream.download(filename='audio_temp.mp4')
            audio = AudioFileClip('audio_temp.mp4')
            out_filename = 'final_output.mp3'
            audio.write_audiofile(out_filename)
            audio.close()
            os.remove('audio_temp.mp4')
            dl_name = f"{yt.title}.mp3"
            response = send_file(out_filename, as_attachment=True, download_name=dl_name)
        else:
            if resolution == 'highest':
                video_stream = yt.streams.filter(adaptive=True, file_extension='mp4', only_video=True).order_by('resolution').last()
            else:
                video_stream = yt.streams.filter(adaptive=True, file_extension='mp4', only_video=True, resolution=resolution).first()
                if not video_stream:
                    video_stream = yt.streams.filter(adaptive=True, file_extension='mp4', only_video=True).order_by('resolution').last()

            audio_stream = yt.streams.filter(adaptive=True, file_extension='mp4', only_audio=True).order_by('abr').last()
            video_stream.download(filename='video_temp.mp4')
            audio_stream.download(filename='audio_temp.mp4')

            video = VideoFileClip('video_temp.mp4')
            audio = AudioFileClip('audio_temp.mp4')
            final = video.set_audio(audio)
            out_filename = 'final_output.mp4'
            final.write_videofile(out_filename, codec="libx264")
            video.close()
            audio.close()
            os.remove('video_temp.mp4')
            os.remove('audio_temp.mp4')

            dl_name = f"{yt.title}.mp4"
            response = send_file(out_filename, as_attachment=True, download_name=dl_name)

        return response

    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    import webbrowser
    webbrowser.open('http://127.0.0.1:5000')
    app.run(debug=True)
