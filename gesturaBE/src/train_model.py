import pandas as pd
import numpy  as np
from sklearn.preprocessing import LabelEncoder 
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns
from clearml import Task
import tensorflow as tf
from tensorflow.keras import layers,models
import os
import matplotlib.pyplot as plt

os.makedirs("model", exist_ok=True)



task = Task.init(project_name="<Gestura_UG_Project>", task_name="<landmark_ML_experiment>")


data = pd.read_csv("data/landmarks_merged.csv", low_memory=False)
le = LabelEncoder()

x = data.drop("label", axis= 1)
x = x.apply(pd.to_numeric, errors= 'coerce')
x = x.fillna(0).values.astype(np.float32)
y = data["label"].values

print("X shape:", x.shape)
print("Y shape:", y.shape)

# label encoding 
y_encoded = le.fit_transform(y)
print(f"Classes", y_encoded)
print(le.classes_)

np.save("model/classes.npy", le.classes_)


# train split
x_train, x_test, y_train, y_test = train_test_split(x,y_encoded,random_state=42,test_size=0.2,stratify=y_encoded)

print("Train shape: ", x_train.shape)
print("test shape: ", x_test.shape)

# normalizing data
def normalize_landmarks(x):
    x = x.reshape(-1, 21, 3)

    #subtract wrist - landmark 0
  # subtracting the wrist so the coordinates look the same everytime
    wrist = x[:, 0:1,: ]
    x = x - wrist
    
    # scale normalization
    max_val = np.max(np.abs(x), axis=(1,2), keepdims=True) # finds the biggest coordinate value for each image
    x = x / (max_val + 1e-6) # 1e-6 prevents dividnig by 0

    return x.reshape(-1, 63)


x_train = normalize_landmarks(x_train)
x_test =  normalize_landmarks( x_test)

print("after Normalization")
print("Train shape: ", x_train.shape)
print("test shape: ", x_test.shape)

print("Min: ", x_train.min())
print("Max: ", x_train.max())


num_classes = len(le.classes_)
print(num_classes)

# training the data with tensorflow
model = models.Sequential([
    layers.Dense(128, activation='relu', input_shape=(63,)),
    layers.Dense(64, activation='relu'),
    layers.Dense(num_classes, activation='softmax')
])

model.compile(
    optimizer = 'adam',
    loss= 'sparse_categorical_crossentropy',
    metrics= ['accuracy']
)

model.summary()

history = model.fit(
    x_train, y_train, 
    validation_data=(x_test, y_test),
    epochs= 15,
    batch_size=32
)

loss,accuracy = model.evaluate(x_test, y_test)
print("Test Accuracy: ," , accuracy)

y_pred = model.predict(x_test)
y_pred_classes = np.argmax(y_pred, axis=1)
y_true = y_test

print(classification_report(y_true, y_pred_classes))

cm =  confusion_matrix(y_true, y_pred_classes)

plt.figure(figsize=(16,14))
sns.heatmap(cm, annot=True, fmt='d' ,cmap="Blues", xticklabels=le.classes_, yticklabels=le.classes_)
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.title("Confusion Matrix")
plt.tight_layout()
plt.savefig("model/confusion_matirx.png", dpi=150)
plt.close()

plt.figure()
plt.plot(history.history['accuracy'], label='Train Accuracy')
plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
plt.title('Model Accuracy over Epochs')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.legend()
plt.tight_layout()
plt.savefig("model/training_accuracy.png", dpi=150)
plt.close()


report = classification_report(y_true, y_pred_classes, target_names=le.classes_)
with open("model/classification_report.txt", "w") as f:
    f.write(report)
print(report)

model.save("model/asl_model.h5")