import streamlit as st
import mysql.connector
import sounddevice as sd
import wavio
import os
import speech_recognition as sr
from collections import Counter
from predict import predict_emotion

# Kết nối đến cơ sở dữ liệu MySQL
def create_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="123456",
        database="login_db"
    )

# Đăng ký người dùng
def register_user(username, password):
    conn = create_connection()
    cursor = conn.cursor(buffered=True)

    try:
        # Kiểm tra xem username đã tồn tại chưa
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = %s", (username,))
        (count,) = cursor.fetchone()

        if count > 0:
            st.error("❌ Tên người dùng đã tồn tại. Vui lòng chọn tên khác.")
        else:
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
            conn.commit()
            st.success("✅ Đăng ký thành công! Vui lòng đăng nhập.")
            st.session_state.register_success = True  # Đánh dấu đăng ký thành công
            st.rerun()  # Chỉ rerun khi đăng ký thành công

    except mysql.connector.Error as e:
        st.error(f"❌ Lỗi khi đăng ký: {e}")

    finally:
        cursor.close()
        conn.close()

# Đăng nhập người dùng
def login_user(username, password):
    conn = create_connection()
    cursor = conn.cursor(buffered=True)
    cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user is not None

# Kiểm tra xem người dùng đã đăng nhập chưa
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# Giao diện đăng nhập/đăng ký
def login_page():
    st.title("🔐 Đăng nhập / Đăng ký")

    # Nếu đăng ký thành công, chuyển sang trang đăng nhập
    if "register_success" in st.session_state and st.session_state["register_success"]:
        st.session_state["register_success"] = False  # Reset trạng thái
        page = "Đăng nhập"
    else:
        page = st.radio("Chọn chức năng", ["Đăng nhập", "Đăng ký"])

    if page == "Đăng ký":
        st.subheader("📝 Tạo tài khoản mới")
        with st.form("register_form"):
            username = st.text_input("Tên người dùng")
            password = st.text_input("Mật khẩu", type="password")
            register_button = st.form_submit_button("Đăng ký")

        if register_button:
            if username and password:
                register_user(username, password)
            else:
                st.warning("⚠️ Vui lòng nhập đầy đủ thông tin.")

    elif page == "Đăng nhập":
        st.subheader("🔑 Đăng nhập")
        with st.form("login_form"):
            username = st.text_input("Tên người dùng")
            password = st.text_input("Mật khẩu", type="password")
            login_button = st.form_submit_button("Đăng nhập")

        if login_button:
            if login_user(username, password):
                st.success("🎉 Đăng nhập thành công!")
                st.session_state.logged_in = True
                st.session_state.username = username  # Lưu tên người dùng vào session
                st.rerun()
            else:
                st.error("❌ Tên người dùng hoặc mật khẩu không đúng.")

# Giao diện chính của ứng dụng
def main_app():
    st.title("🌟 Nhận diện cảm xúc từ giọng nói")
    st.markdown("""
        Chào mừng bạn đến với ứng dụng nhận diện cảm xúc! 
        Bạn có thể ghi âm giọng nói của mình hoặc tải lên một file âm thanh để dự đoán cảm xúc.
    """)
    
    # Thêm nút Đăng xuất
    if st.sidebar.button("Đăng xuất"):
        st.session_state.logged_in = False
        st.success("Bạn đã đăng xuất thành công!")
        st.rerun()  # Tải lại ứng dụng để quay lại trang đăng nhập

    # Constants
    SAMPLE_RATE = 44100
    DURATION = 5

    def save_prediction(file_path, model, emotion, transcription):
        """Lưu lịch sử dự đoán vào cơ sở dữ liệu."""
        username = st.session_state.username  # Lấy tên người dùng từ session
        conn = create_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO predictions (username, file_path, model, emotion, transcription) VALUES (%s, %s, %s, %s, %s)",
                (username, file_path, model, emotion, transcription)
            )
            conn.commit()
            st.success("✅ Lịch sử dự đoán đã được lưu vào cơ sở dữ liệu.")
        except mysql.connector.Error as e:
            st.error(f"❌ Lỗi khi lưu lịch sử: {e}")
        finally:
            cursor.close()
            conn.close()

    def load_history():
        """Tải lịch sử dự đoán từ cơ sở dữ liệu."""
        conn = create_connection()
        cursor = conn.cursor(dictionary=True)
        username = st.session_state.username  # Lấy tên người dùng từ session
        cursor.execute("SELECT * FROM predictions WHERE username = %s ORDER BY timestamp DESC LIMIT 5", (username,))
        history = cursor.fetchall()
        cursor.close()
        conn.close()
        return history

    def get_emotion_counts():
        """Tính tần suất xuất hiện của từng cảm xúc từ cơ sở dữ liệu."""
        conn = create_connection()
        cursor = conn.cursor()
        username = st.session_state.username  # Lấy tên người dùng từ session
        cursor.execute("SELECT emotion FROM predictions WHERE username = %s", (username,))
        emotions = cursor.fetchall()
        cursor.close()
        conn.close()

        # Đếm tần suất cảm xúc
        emotion_list = [emotion[0] for emotion in emotions]  # Chuyển đổi tuple thành list
        return Counter(emotion_list)

    def record_audio():
        """Record audio and save to file."""
        st.info("🎤 Bắt đầu ghi âm trong 5 giây...")
        audio_data = sd.rec(int(SAMPLE_RATE * DURATION), samplerate=SAMPLE_RATE, channels=1, dtype='int16')
        sd.wait()
        wavio.write("recorded_audio.wav", audio_data, SAMPLE_RATE, sampwidth=2)
        st.success("✅ Ghi âm hoàn tất! File đã được lưu là 'recorded_audio.wav'.")
        return "recorded_audio.wav"

    def upload_file():
        """Upload audio file."""
        uploaded_file = st.file_uploader("📥 Tải file .wav hoặc .mp3", type=["wav", "mp3"])
        if uploaded_file is not None:
            with open("uploaded_audio.wav", "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success("✅ File đã được tải lên thành công!")
            return "uploaded_audio.wav"
        return None

    def transcribe_audio(file_path):
        """Transcribe audio file to text."""
        recognizer = sr.Recognizer()
        with sr.AudioFile(file_path) as source:
            audio = recognizer.record(source)
            try:
                transcription = recognizer.recognize_google(audio)
                return transcription
            except sr.UnknownValueError:
                return "Không thể nhận diện âm thanh."
            except sr.RequestError as e:
                return f"Có lỗi xảy ra: {e}"

    def predict(file_path, selected_model):
        """Predict emotion from audio file."""
        if not os.path.exists(file_path):
            st.warning("⚠️ Vui lòng chọn file hợp lệ!")
            return None

        try:
            # Giả sử predict_emotion là một hàm đã được định nghĩa ở nơi khác
            emotion = predict_emotion(file_path, selected_model)
            if emotion:
                st.success(f"🎉 Cảm xúc dự đoán: {emotion}")
                return emotion
        except Exception as e:
            st.error(f"❌ Có lỗi xảy ra trong quá trình dự đoán: {e}")
        return None

    # Layout
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🎤 Ghi âm"):
            recorded_file_path = record_audio()
            st.session_state.uploaded_file_path = recorded_file_path

    with col2:
        uploaded_file_path = upload_file()

    # Determine file path
    if uploaded_file_path:
        file_path = uploaded_file_path
        st.success(f"📂 File đã được tải lên: {file_path}")
    else:
        file_path = st.session_state.get('uploaded_file_path', None)

    # Model selection
    st.subheader("🔍 Chọn mô hình dự đoán:")
    model_var = st.radio("Chọn mô hình:", ["KNN", "Neural Network", "Decision Tree"])

    # Emotion prediction
    if st.button("🔍 Dự đoán cảm xúc"):
        if file_path:
            emotion = predict(file_path, model_var)
            if emotion:
                transcription = transcribe_audio(file_path)
                st.subheader("📝 Nội dung đã được ghi âm:")
                st.write(transcription)

                # Lưu kết quả vào lịch sử
                save_prediction(file_path, model_var, emotion, transcription)

                # Gợi ý hoạt động dựa trên cảm xúc
                st.subheader("🎯 Gợi ý hoạt động:")
                if emotion == "Happy":
                    st.write("Nghe nhạc vui tươi, đi dạo, gặp gỡ bạn bè.")
                elif emotion == "Sad":
                    st.write("Đọc sách, xem phim, thiền hoặc yoga.")
                elif emotion == "Angry":
                    st.write("Nghe nhạc thư giãn, tập thể dục, thực hành hít thở sâu.")
                elif emotion == "Fearful":
                    st.write("Thực hành thiền, tập thể dục, viết nhật ký.")
                elif emotion == "Surprised":
                    st.write("Khám phá sở thích mới, đi dạo, tham gia vào các hoạt động xã hội.")
                elif emotion == "Disgusted":
                    st.write("Tham gia vào các hoạt động sáng tạo, chia sẻ niềm vui.")
                elif emotion == "Neutral":
                    st.write("Thư giãn, xem phim, hoặc đọc sách.")

        else:
            st.warning("⚠️ Vui lòng ghi âm hoặc tải lên file âm thanh trước khi dự đoán.")

    # Tính toán tần suất cảm xúc
    emotion_counts = get_emotion_counts()

    st.subheader("📊 Thống kê cảm xúc dự đoán")

    if emotion_counts and len(emotion_counts) > 0:
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots()
        ax.bar(emotion_counts.keys(), emotion_counts.values(), color=['red', 'blue', 'green', 'purple', 'orange'])
        ax.set_xlabel("Cảm xúc")
        ax.set_ylabel("Số lần xuất hiện")
        ax.set_title("Tần suất các cảm xúc dự đoán")
        st.pyplot(fig)
    else:
        st.info("⚠️ Chưa có dữ liệu dự đoán để hiển thị biểu đồ.")

    st.subheader("📜 Lịch sử dự đoán gần đây")

    history = load_history()
    if history:
        for entry in history:
            with st.expander(f"📅 {entry['timestamp']} - 📂 {os.path.basename(entry['file_path'])}"):
                st.write(f"🎭 **Dự đoán:** {entry['emotion']}")
                st.write(f"📝 **Nội dung ghi âm:** {entry['transcription']}")
                st.audio(entry['file_path'], format='audio/wav')
                st.markdown("---")
    else:
        st.info("⚠️ Chưa có lịch sử dự đoán.")

# Chạy ứng dụng
if not st.session_state.logged_in:
    login_page()
else:
    main_app()