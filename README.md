Location_ID: Mã định danh của địa điểm.
Location_Type: Loại địa điểm (trường học, công viên, trung tâm thương mại, văn phòng, nhà ga).
Daily_Foot_Traffic: Lưu lượng người qua lại hàng ngày.
Nearby_Competitors: Số lượng máy bán hàng tự động của đối thủ trong khu vực.
Average_Income_Area: Thu nhập trung bình của khu vực (USD/tháng).
Peak_Hours: Giờ cao điểm mà khu vực này có nhiều người nhất.
Potential_Demand: Nhu cầu tiềm năng cho máy bán hàng tự động (tỷ lệ phần trăm).
R2: Nếu R2 gần 1, mô hình của bạn có khả năng giải thích tốt dữ liệu. Nếu R2 gần 0, mô hình không thể giải thích sự biến động trong dữ liệu.
MAE: Một giá trị MAE nhỏ cho thấy mô hình có sai số nhỏ và dự đoán chính xác.
MSE: MSE càng nhỏ, mô hình càng chính xác, nhưng nếu có ngoại lệ lớn (outliers), MSE có thể bị ảnh hưởng nhiều hơn so với MAE.s
chạy trên môi trường ảo 
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass


pip install -r requirements.txt
.\env\Scripts\Activate
 cd D:\Vsvode\Python\CDIO3
 streamlit run gui.py