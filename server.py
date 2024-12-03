import cv2
import threading
import os
from flask import Flask, request, jsonify, send_from_directory

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

    # CURRENT_VIDEO = file.filename
    # CURRENT_PLAYING.set()
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

@app.route('/delete/<video_name>', methods=['DELETE'])
def delete_video(video_name):
    print(f"Attempting to delete video: {video_name}")
    video_path = os.path.join(UPLOAD_FOLDER, video_name)
    if not os.path.exists(video_path):
        print(f"Video not found: {video_path}")
        return jsonify({"message": "Video not found"}), 404

    try:
        os.remove(video_path)
        print(f"Video deleted: {video_path}")
        return jsonify({"message": f"Video {video_name} deleted successfully"}), 200
    except Exception as e:
        print(f"Error deleting video: {e}")
        return jsonify({"message": f"Error deleting video: {str(e)}"}), 500


@app.route('/update_settings', methods=['POST'])
def update_settings():
    global CURRENT_VIDEO, CURRENT_PLAYING

    data = request.json
    if not CURRENT_VIDEO:
        return jsonify({"message": "No video is currently playing"}), 400

    
    volume = data.get("volume", 1.0)  
    action = data.get("action", "play")  

   
    print(f"Updating settings: Volume={volume}, Action={action}")
    if action == "pause":
        CURRENT_PLAYING.clear()
    elif action == "play":
        CURRENT_PLAYING.set()

    return jsonify({"message": "Settings updated successfully"}), 200

@app.route('/videos/<video_name>', methods=['GET'])
def get_video(video_name):
    video_path = os.path.join(UPLOAD_FOLDER, video_name)
    print(f"Attempting to access: {video_path}")  # طباعة المسار
    if not os.path.exists(video_path):
        print(f"Video not found at: {video_path}")  # إذا لم يتم العثور على الفيديو
        return 'Video not found', 404
    return send_from_directory(UPLOAD_FOLDER,video_name)

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
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Loop the video
                    continue

                # Create a named window and set it to full screen
                cv2.namedWindow('Video Player', cv2.WINDOW_NORMAL)
                cv2.setWindowProperty('Video Player', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

                # Display the frame
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
