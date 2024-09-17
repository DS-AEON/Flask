import pandas as pd
import numpy as np
import logging

def calculate_movement_distances(csv_path, segment_size=30):
    df = pd.read_csv(csv_path, header=[1, 2], index_col=0)
    num_frames = len(df)
    num_segments = int(np.ceil(num_frames / segment_size))

    segment_distances = []

    for i in range(num_segments):
        start_frame = i * segment_size
        end_frame = min((i + 1) * segment_size, num_frames)

        segment_distance = 0.0

        for key in df.columns.get_level_values(0).unique():
            x_coords = df[key]['x'].values[start_frame:end_frame]
            y_coords = df[key]['y'].values[start_frame:end_frame]

            frame_distances = np.sqrt(np.diff(x_coords)**2 + np.diff(y_coords)**2)
            segment_distance += np.sum(frame_distances)

        segment_distances.append((i + 1, segment_distance))  # Segment number starts from 1

    segment_distances.sort(key=lambda x: x[1], reverse=True)
    return segment_distances

# 편안한 상태
def movement_0(csv_path):
    logging.basicConfig(level=logging.INFO)
    
    # CSV 파일 읽기
    df = pd.read_csv(csv_path, skiprows=1)

    logging.info(f"CSV 열 이름: {df.columns}")

    # x와 y 좌표 추출
    def extract_coordinates(df):
        coordinates = {}

        # 열 이름을 3개씩 묶어서 'x', 'y', 'likelihood'를 추출
        for i in range(1, len(df.columns), 3):  # 'x', 'y', 'likelihood'가 3개씩 묶여 있음
            bodypart_x = df.columns[i]
            bodypart_y = df.columns[i + 1]

            try:
                bodypart_name = df.columns[i].split('_')[1]  # 신체 부위 이름 추출
            except IndexError:
                bodypart_name = f"bodypart_{(i-1)//3}"

            # 좌표 데이터를 float 형식으로 변환하고 NaN 값 제거
            x_values = pd.to_numeric(df[bodypart_x], errors='coerce').dropna().values
            y_values = pd.to_numeric(df[bodypart_y], errors='coerce').dropna().values

            coordinates[bodypart_name] = {
                'x': x_values,
                'y': y_values,
                'likelihood': pd.to_numeric(df[df.columns[i + 2]], errors='coerce').dropna().values
            }
            
        return coordinates

    # 좌표 데이터 추출
    coordinates = extract_coordinates(df)

    # 좌표 데이터 로그 출력
    for bodyparts, coords in coordinates.items():
        logging.info(f"{bodyparts} x 좌표: {coords['x']}")
        logging.info(f"{bodyparts} y 좌표: {coords['y']}")

    # 움직임 계산 함수
    def calculate_movement(coordinates):
        movements = []
        for bodyparts, coords in coordinates.items():
            x = coords['x']
            y = coords['y']
            logging.info(f"{bodyparts} x 좌표: {x}")
            logging.info(f"{bodyparts} y 좌표: {y}")

            for i in range(1, len(x)):
                prev_x, prev_y = x[i - 1], y[i - 1]
                curr_x, curr_y = x[i], y[i]
                movement = np.sqrt(np.sum((curr_x - prev_x) ** 2 + (curr_y - prev_y) ** 2))
                movements.append(movement)
                
        logging.info(f"movements: {movements}")
        return np.mean(movements) if movements else 0.0  # 빈 리스트일 경우 평균을 0.0으로 설정

    # 움직임 기준값 설정
    movement_threshold = 0.1
    average_movement = calculate_movement(coordinates)
    
    logging.info(f"movement_threshold: {movement_threshold}")
    logging.info(f"average_movement: {average_movement}")

    # 기준값 이하일 경우 '편안한 상태'로 판단
    if average_movement < movement_threshold:
        result = "편안한 상태"
    else:
        result = "움직임이 감지됨"

    return result
