import cv2
import mediapipe as mp
import tensorflow as tf
import numpy as np
import csv

label = "Z"  # Set target letter to collect samples for

#Initialise MediaPipe Hands
mp_hands = mp.solutions.hands

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7
)

cap = cv2.VideoCapture(0)
collecting = False
sample_count = 0
max_samples =  500


# normalizing data
def normalize_landmarks(landmarks, is_left =False):
    landmarks = np.array(landmarks).reshape(1, 21, 3)
    
    # Mirror x-coordinates for left-hand input to match right-hand orientation
    if is_left:
        landmarks[:,:,0] =  1 - landmarks[:,:,0]
        
    # Subtract wrist position to make coordinates relative to the wrist 
    wrist = landmarks[:, 0:1,: ]
    landmarks = landmarks - wrist
    
    # scale normalization
    max_val = np.max(np.abs(landmarks), axis=(1,2), keepdims=True) 
    landmarks = landmarks / (max_val + 1e-6)

    return landmarks.reshape(1, 63) # Flatten to 1D array of 63 values
 
while True:
    ret, frame = cap.read() # Mirror frames 
    frame = cv2.flip(frame, 1)
    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(image_rgb) # Run hand detection
    

    if results.multi_hand_landmarks:
        hand_landmarks = results.multi_hand_landmarks[0]

        #Detect whether the hand is left or right
        which_hand = results.multi_handedness[0].classification[0].label
        is_left = which_hand == "Left"

        #Extract x, y, z coordinates for all 21 landmarks
        landmark_list = []
        for lm in hand_landmarks.landmark:
            landmark_list.extend([lm.x, lm.y, lm.z])


        # normalize
        normalize = normalize_landmarks(landmark_list, is_left)

        # Save normalised landmarks to CSV if collectioni is active
        if collecting and sample_count < max_samples:
            with open("dataset.csv", mode="a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(list(normalize[0]) + [label]) # Apply label to each row
            sample_count +=1
            print(f"Saved Sample {sample_count}/{max_samples} for {label}")

            if sample_count >=max_samples:
                collecting = False
                print(f"Done collecting {max_samples} samples for {label}")



    status = f"COLLECTING {label}: {sample_count}/ {max_samples}" if collecting else f"Press S to start collecting {label}"
    color = (0, 255, 0) if collecting else (0,0,255)


    cv2.putText(frame, status,
                    (20, 50), cv2.FONT_HERSHEY_COMPLEX, 1,(0.255,0),
                     2)

    cv2.imshow("Collect Data", frame)

    key = cv2.waitKey(1)
    # Toggle collection on/off with "S" key (only if a hand is detected)
    if key == ord('s') and results.multi_hand_landmarks:
        collecting = not collecting
        if collecting:
            print(f"Start collecting for  {label}")
        else: 
            print("paused")

    if key == ord('q'):
        break


cap.release()
cv2.destroyAllWindows()

