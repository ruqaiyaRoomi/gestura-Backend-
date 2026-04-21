import sys 
import json
import numpy as np
import tensorflow as tf
import os

# Resolve absolute path to current file's directory for reliable model loading
base_dir = os.path.dirname(os.path.abspath(__file__))
# Load trained ASL classification model
model = tf.keras.models.load_model(os.path.join(base_dir, "model/asl_model.h5"))
# Load class labels corresponding to model output indices
classes = np.load(os.path.join(base_dir, "model/classes.npy"), allow_pickle=True)

def normalize_landmarks(landmarks, is_left =False):
    # Parse landmarks from dict format if received as a list of coordinate objects
    if isinstance(landmarks[0], dict):
        lm = np.array([[p['x'], p['y'], p['z']] for p in landmarks])
    
    else:
        # Reshape flat array of 63 values into 21 landmarks with x, y, z coordinates
        lm = np.array(landmarks).reshape(21, 3)

    lm = lm.reshape(1, 21,3)
    # Mirror x-axis for left hand to match right-hand training data 
    if is_left:
        lm[:,:, 0] = 1 -lm[:,:, 0]
    
    # Translate landmarks relative to wrist to remove positional bias
    wrist = lm[:, 0:1, :]
    lm = lm - wrist

    # Scale landmarks to [-1, 1] range to normalise for different hand sizes
    max_val = np.max(np.abs(lm), axis=(1,2), keepdims=True)
    lm = lm / (max_val + 1e-6) # avoid division by 0
    return lm.reshape(1,63)

# Continously read JSON input from stdin 
for line in sys.stdin:
    try: 
        input_data = json.loads(line.strip())
        landmarks = input_data["landmarks"]
        # Default to right hand if handedness not provided
        is_left = input_data.get("is_left", False)

        # Normalise landmarks beofre passing to model
        normalized = normalize_landmarks(landmarks, is_left)
        prediction = model.predict(normalized, verbose=0)

        # Get index of highest probability class
        index = np.argmax(prediction)
        label = classes[index]

        # Convert confidence to perecentage
        confidence = float(np.max(prediction) *100)

        # Output prediction result as JSON to stdout
        print(json.dumps({"label": str(label), "confidence": confidence}), flush=True)
    except Exception as e:
        # Output error as JSON 
        print(json.dumps({"error": str(e)}), flush=True)