import sys 
import json
import numpy as np
import tensorflow as tf
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
model = tf.keras.models.load_model(os.path.join(base_dir, "model/asl_model.h5"))
classes = np.load(os.path.join(base_dir, "model/classes.npy"), allow_pickle=True)


def normalize_landmarks(landmarks, is_left =False):

    if isinstance(landmarks[0], dict):
        lm = np.array([[p['x'], p['y'], p['z']] for p in landmarks])
    
    else:
        lm = np.array(landmarks).reshape(21, 3)

    lm = lm.reshape(1, 21,3)
    if is_left:
        lm[:,:, 0] = 1 -lm[:,:, 0]

    wrist = lm[:, 0:1, :]
    lm = lm - wrist
    max_val = np.max(np.abs(lm), axis=(1,2), keepdims=True)
    lm = lm / (max_val + 1e-6)
    return lm.reshape(1,63)


for line in sys.stdin:
    try: 
        input_data = json.loads(line.strip())
        landmarks = input_data["landmarks"]
        is_left = input_data.get("is_left", False)

        normalized = normalize_landmarks(landmarks, is_left)
        prediction = model.predict(normalized, verbose=0)
        index = np.argmax(prediction)
        label = classes[index]
        confidence = float(np.max(prediction) *100)
        print(json.dumps({"label": str(label), "confidence": confidence}), flush=True)
    except Exception as e:
        print(json.dumps({"error": str(e)}), flush=True)