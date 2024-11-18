import cv2
import threading
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

UPLOAD_FOLDER = 'videos'
CURRENT_VIDEO = None
CURRENT_PLAYING = threading.Event()
CURRENT_PLAYING.set()
video_thread = None

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/upload', methods=['POST'])
def upload_video():
    global CURRENT_VIDEO, CURRENT_PLAYING
    if 'file' not in request.files:
        return 'No file part', 400
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    CURRENT_VIDEO = file.filename
    CURRENT_PLAYING.set()
    return 'Video uploaded successfully', 200

@app.route('/videos', methods=['GET'])
def list_videos():
    videos = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith(('.mp4', '.avi', '.mov'))]
    return jsonify(videos), 200

@app.route('/play/<video_name>', methods=['GET'])
def play_video(video_name):
    global CURRENT_VIDEO, CURRENT_PLAYING
    if not os.path.exists(os.path.join(UPLOAD_FOLDER, video_name)):
        return 'Video not found', 404

    CURRENT_VIDEO = video_name
    CURRENT_PLAYING.set()
    return f'Playing video: {video_name}', 200

def video_player():
    global CURRENT_VIDEO, CURRENT_PLAYING

    while True:
        CURRENT_PLAYING.wait()
        CURRENT_PLAYING.clear()

        if CURRENT_VIDEO:
            video_path = os.path.join(UPLOAD_FOLDER, CURRENT_VIDEO)
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)  

            while cap.isOpened() and CURRENT_VIDEO:
                ret, frame = cap.read()
                if not ret:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  
                    continue

               
                cv2.namedWindow('Video Player', cv2.WINDOW_NORMAL)
                cv2.resizeWindow('Video Player', 600, 700)  

               
                frame = cv2.resize(frame, (800, 600))  

                cv2.imshow('Video Player', frame)

                wait_time = int(1000 / fps) if fps > 0 else 30
                if cv2.waitKey(wait_time) & 0xFF == ord('q'):
                    CURRENT_VIDEO = None
                    break

                if CURRENT_PLAYING.is_set():
                    break

            cap.release()
            cv2.destroyAllWindows()


if __name__ == '__main__':
    video_thread = threading.Thread(target=video_player, daemon=True)
    video_thread.start()
    app.run(host='0.0.0.0', port=8080, debug=True)
