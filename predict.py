import os
import librosa
import numpy as np
import joblib
import tensorflow as tf
from tkinter import messagebox

EMOTIONS = ["Angry", "Disgusted", "Fearful", "Happy", "Neutral", "Sad", "Surprised"]

def extract_features(file_path):
    """Trích xuất đặc trưng MFCC từ file âm thanh"""
    try:
        audio, sr = librosa.load(file_path, sr=None)
        mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
        return np.mean(mfcc, axis=1).reshape(1, -1)
    except Exception as e:
        print(f"Lỗi khi đọc file {file_path}: {e}")
        return None

def load_selected_model(selected_model):
    """Tải mô hình theo lựa chọn"""
    if selected_model == "KNN":
        model_path = "knn_model.pkl"
    elif selected_model == "Decision Tree":
        model_path = "decision_tree_model.pkl"
    elif selected_model == "Neural Network":
        model_path = "neural_network_model.keras"
    else:
        return None

    if not os.path.exists(model_path):
        messagebox.showerror("Lỗi", f"Mô hình {selected_model} chưa được huấn luyện!")
        return None

    return tf.keras.models.load_model(model_path) if selected_model == "Neural Network" else joblib.load(model_path)

def predict_emotion(file_path, selected_model):
    """Dự đoán cảm xúc từ file âm thanh"""
    model = load_selected_model(selected_model)
    if model is None:
        return None

    scaler = joblib.load("scaler.pkl")
    features = extract_features(file_path)
    if features is None:
        return None
    
    features = scaler.transform(features)
    prediction = model.predict(features)

    if isinstance(model, tf.keras.Model):
        prediction = np.argmax(prediction, axis=1)

    return EMOTIONS[int(prediction[0])]

# print("Bắt đầu dự đoán...")
# features = extract_features(r"D:\CDIO3\data\Angry\03-01-05-01-01-01-01.wav")
# print("Đặc trưng đầu vào:", features)

# prediction = model.predict(features)
# print("Kết quả dự đoán:", prediction)
