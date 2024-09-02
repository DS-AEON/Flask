import pandas as pd
import numpy as np

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
