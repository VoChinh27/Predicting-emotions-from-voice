import os
import librosa
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import Sequential # type: ignore
from tensorflow.keras.layers import Dense, Input # type: ignore

# Thư mục chứa dữ liệu
dataset_path = "data"
emotions = os.listdir(dataset_path)

# Danh sách nhãn cảm xúc
EMOTIONS = ["Angry", "Disgusted", "Fearful", "Happy", "Neutral", "Sad", "Surprised"]

def extract_features(file_path):
    """Trích xuất đặc trưng MFCC từ file âm thanh"""
    try:
        audio, sr = librosa.load(file_path, sr=None)
        mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
        return np.mean(mfcc, axis=1)
    except Exception as e:
        print(f"Lỗi khi đọc file {file_path}: {e}")
        return None

# Chuẩn bị dữ liệu
X, y = [], []
for label, emotion in enumerate(emotions):
    emotion_path = os.path.join(dataset_path, emotion)
    for file in os.listdir(emotion_path):
        file_path = os.path.join(emotion_path, file)
        features = extract_features(file_path)
        if features is not None:
            X.append(features)
            y.append(label)

X, y = np.array(X), np.array(y)

# Chuẩn hóa dữ liệu
scaler = StandardScaler()
X = scaler.fit_transform(X)

# Lưu bộ chuẩn hóa
joblib.dump(scaler, "scaler.pkl")

# Chia tập dữ liệu
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Huấn luyện mô hình KNN
knn = KNeighborsClassifier(n_neighbors=5)
knn.fit(X_train, y_train)
joblib.dump(knn, "knn_model.pkl")
print(f"Độ chính xác KNN: {knn.score(X_test, y_test):.2f}")

# Huấn luyện mô hình Decision Tree
dt = DecisionTreeClassifier()
dt.fit(X_train, y_train)
joblib.dump(dt, "decision_tree_model.pkl")
print(f"Độ chính xác Decision Tree: {dt.score(X_test, y_test):.2f}")

# Huấn luyện Neural Network
nn = Sequential([
    Input(shape=(13,)),
    Dense(16, activation='relu'),
    Dense(8, activation='relu'),
    Dense(len(emotions), activation='softmax')
])
nn.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
nn.fit(X_train, y_train, epochs=30, batch_size=8, verbose=1)
nn.save("neural_network_model.keras")
print(f"Độ chính xác Neural Network: {nn.evaluate(X_test, y_test, verbose=0)[1]:.2f}")

print("Đã lưu tất cả mô hình!")
# Chọn mô hình tốt nhất
models = {
    "KNN": (knn, knn.score(X_test, y_test)),
    "Decision Tree": (dt, dt.score(X_test, y_test)),
    "Neural Network": (nn, nn.evaluate(X_test, y_test, verbose=0)[1])
}

best_model_name, (best_model, best_acc) = max(models.items(), key=lambda x: x[1][1])

# Lưu tên mô hình tốt nhất
with open("best_model.txt", "w") as f:
    f.write(best_model_name)

print(f"Mô hình tốt nhất: {best_model_name} ({best_acc:.2f})")
