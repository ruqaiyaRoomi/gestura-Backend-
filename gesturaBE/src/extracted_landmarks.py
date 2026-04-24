import os
import cv2
import csv
import mediapipe as mp

DATASET_PATH = "data/asl_alphabet_train"
OUTPUT_FILE = "data/landmarks.csv" 

mp_hands = mp.solutions.hands

hands = mp_hands.Hands(
    static_image_mode=True, 
    max_num_hands=1, 
    min_detection_confidence= 0.7
)

with open(OUTPUT_FILE, mode= 'w', newline='') as f:
    writer = csv.writer(f)

    header = [f"f{i}" for i in range(63)] + ["label"]
    writer.writerow(header)

    for label in sorted(os.listdir(DATASET_PATH)):
        valid_classes = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + ["space"] + ["del"] 

        if label not in valid_classes:
            continue

        label_path = os.path.join(DATASET_PATH, label)

        for img_name in os.listdir(label_path):

            img_path = os.path.join(label_path,img_name)

            image = cv2.imread(img_path)

            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            results = hands.process(image_rgb)

            if results.multi_hand_landmarks:
                
                hand_landmarks = results.multi_hand_landmarks[0]
                features = []
                for lm in hand_landmarks.landmark:
                    features.extend([lm.x, lm.y, lm.z])
                    if len(features) == 63:
                        writer.writerow(features + [label])
            
hands.close()
print("Landmark extraction complete.")