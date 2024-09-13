from flask import Flask, request, jsonify, send_file
import os
import deeplabcut
from movement_analysis import calculate_movement_distances
from movement_analysis import movement_0
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})


# 학습된 모델의 config 파일 경로 설정
config_path = 'C:\\blackDog-yoon-2024-07-15-20240810T011325Z-001\\blackDog-yoon-2024-07-15\\config.yaml'

# 관절좌표 CSV 파일 경로
csv_path = 'C:\\blackDog-yoon-2024-07-15-20240810T011325Z-001\\blackDog-yoon-2024-07-15\\videos\\4211036-hd_1280_720_25fpsDLC_resnet50_blackDogJul15shuffle1_40000.csv'

# 로그 파일 경로
log_file_path = 'server.log'

# 예시로 제공된 이름 목록 (파일 또는 데이터베이스에서 읽어오는 부분)
name_to_segment = {
    '초코': 1,
    '보리': 2,
    '호두': 3,
    '두부': 4,
    '모찌': 5,
    '코코': 6
    # 추가 이름 및 구간
}

@app.route('/')
def index():
    return "DeepLabCut Flask Server is running!"

@app.route('/predict', methods=['POST'])
def predict():
    if 'video' not in request.files:
        log_error("No video file provided")
        return jsonify({"error": "No video file provided"}), 400

    video = request.files['video']
    video_path = os.path.join('C:\\coding\\Hadog\\uploads\\', video.filename)
    video.save(video_path)

    log_info(f"Received video file: {video.filename}")
    log_info(f"Saved video path: {video_path}")

    try:
        deeplabcut.analyze_videos(config_path, [video_path], save_as_csv=False)

        labeled_video_filename = video.filename.replace('.mp4', 'DLC_resnet50_blackDogJul15shuffle1_40000_filtered_labeled.MP4')
        labeled_video_path = os.path.join('C:\\coding\\Hadog\\uploads\\', labeled_video_filename)

        deeplabcut.filterpredictions(config_path, [video_path], filtertype='median')
        deeplabcut.create_labeled_video(config_path, [video_path], filtered=True, draw_skeleton=True, save_frames=False, overwrite=True)

        if os.path.exists(labeled_video_path):
            return jsonify({"result": labeled_video_path}), 200
        else:
            log_error("Labeled video not found")
            return jsonify({"error": "Labeled video not found"}), 500
    except Exception as e:
        log_error(f"Exception occurred: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/logs', methods=['GET'])
def get_logs():
    if os.path.exists(log_file_path):
        with open(log_file_path, 'r') as log_file:
            logs = log_file.read()
        return jsonify({"logs": logs}), 200
    else:
        return jsonify({"error": "Log file not found"}), 404

@app.route('/results/<filename>', methods=['GET'])
def get_result_video(filename):
    video_path = os.path.join('C:\\coding\\Hadog\\uploads\\', filename)
    if os.path.exists(video_path):
        return send_file(video_path, as_attachment=True)
    else:
        return jsonify({"error": "File not found"}), 404

@app.route('/calculate_movement', methods=['POST'])
def calculate_movement():
    if 'names' not in request.json:
        return jsonify({"error": "No names provided"}), 400

    names = request.json['names']
    segment_size = 30

    # 구간별 이동 거리 계산
    segment_distances = calculate_movement_distances(csv_path, segment_size)

    # 이름에 따른 구간의 이동 거리 찾기
    name_segment_distances = []
    for name in names:
        if name in name_to_segment:
            segment_num = name_to_segment[name]
            # 구간 번호는 1부터 시작하므로, 인덱스는 -1
            segment_distance = next((dist for num, dist in segment_distances if num == segment_num), 0)
            name_segment_distances.append((name, segment_distance))
        else:
            name_segment_distances.append((name, 0))  # 이름이 없으면 0으로 처리

    # 이동 거리 기준으로 정렬
    name_segment_distances.sort(key=lambda x: x[1], reverse=True)

    return jsonify({"name_segment_distances": name_segment_distances})

@app.route('/get_ranking', methods=['GET'])
def get_ranking():
    # 기본 이름 목록 설정 (예: 사용자가 업로드한 반려견 이름 목록을 포함)
    # 실제 사용 시에는 사용자가 제공한 이름 목록을 사용하는 것이 맞습니다.
    names = [
        "초코",
        "보리",
        "호두",
        "두부",
        "모찌",
        "코코"
    ]
    
    segment_size = 30
    # 구간별 이동 거리 계산
    segment_distances = calculate_movement_distances(csv_path, segment_size)

    # 이름에 따른 구간의 이동 거리 찾기
    name_segment_distances = []
    for name in names:
        if name in name_to_segment:
            segment_num = name_to_segment[name]
            # 구간 번호는 1부터 시작하므로, 인덱스는 -1
            segment_distance = next((dist for num, dist in segment_distances if num == segment_num), 0)
            name_segment_distances.append((name, segment_distance))
        else:
            name_segment_distances.append((name, 0))  # 이름이 없으면 0으로 처리

    # 이동 거리 기준으로 정렬
    name_segment_distances.sort(key=lambda x: x[1], reverse=True)

    # 순위 매기기
    ranked_list = [{"rank": i + 1, "name": name, "distance": distance} for i, (name, distance) in enumerate(name_segment_distances)]

    return jsonify({"ranking": ranked_list})

#++++++++++++++++++++++
# 감정 분석
@app.route('/emotion', methods=['POST'])
def analyze_emotion():
    data = request.json
    csv_path = data.get('csv_path')

    if not csv_path or not os.path.exists(csv_path):
        log_error("CSV file not found")
        return jsonify({"error": "CSV file not found"}), 400

    result = movement_0(csv_path)

    try:
        return jsonify({"result": result}), 200

    except Exception as e:
        log_error(f"Exception occurred: {str(e)}")
        return jsonify({"error": str(e)}), 500

def log_info(message):
    with open(log_file_path, 'a') as log_file:
        log_file.write(f"INFO: {message}\n")

def log_error(message):
    with open(log_file_path, 'a') as log_file:
        log_file.write(f"ERROR: {message}\n")

if __name__ == '__main__':
    if not os.path.exists('uploads\\'):
        os.makedirs('uploads\\')
    if not os.path.exists(log_file_path):
        open(log_file_path, 'w').close()
    app.run(debug=True)
