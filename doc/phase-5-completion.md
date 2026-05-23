# Báo Cáo Hoàn Thành — Phase 5: Session & History System

Tài liệu này tổng hợp chi tiết kết quả thiết kế, bộ lưu trữ lịch sử bất đồng bộ và cơ chế tự động tóm tắt ngữ cảnh hội thoại (**Phase 5: Session & History System**) cho PetBot AI Chatbot.

---

## 🗄️ 1. Hệ Thống Lưu Trữ Bất Đồng Bộ MongoDB (Motor)
Chúng tôi triển khai các Repository tương thích tuyệt đối với Driver bất đồng bộ `motor` nhằm tránh gây nghẽn (block) luồng xử lý chính của FastAPI:
- **`SessionRepository`**: Quản lý vòng đời lưu trữ của các phiên chat (`chat_sessions` collection). Lưu trữ các metadata bổ sung như nguồn truy cập, số lượng tin nhắn hiện tại và văn bản tóm tắt hội thoại bằng AI.
- **`HistoryRepository`**: Lưu trữ lịch sử tất cả các tin nhắn gửi đi và nhận lại trong các phiên chat (`chat_messages` collection). Khi một tin nhắn được thêm mới vào history, hệ thống tự động tăng biến đếm tin nhắn (`message_count`) và cập nhật thời gian thay đổi (`updated_at`) của session tương ứng trong một transaction phẳng.

---

## 🛡️ 2. Cơ Chế Phân Quyền Bảo Mật (Permission Systems)
Hệ thống thực thi chặt chẽ các chính sách bảo mật tại tầng ứng dụng (`PermissionService`):
- **Guest Flow (Khách ẩn danh)**:
  - Khi phát hiện request gửi từ người dùng chưa đăng nhập, hệ thống tự tạo một phiên chat ẩn danh (`ChatSession.create_ephemeral()`).
  - Toàn bộ lịch sử chat của khách được giữ trong bộ nhớ đệm phục vụ suy nghĩ của Agent nhưng **không bao giờ ghi nhận hay lưu trữ vĩnh viễn** vào MongoDB để đảm bảo tính riêng tư và tiết kiệm tài nguyên lưu trữ.
- **Member Flow (Thành viên đăng nhập)**:
  - Khi có thông tin xác thực, hệ thống kiểm tra và xác nhận quyền sở hữu phiên chat. 
  - Chỉ có chủ sở hữu hợp pháp của phiên chat (`user_id` trùng khớp) mới có quyền đọc lịch sử hoặc xóa phiên chat đó. Tất cả các nỗ lực xâm phạm từ người dùng khác đều bị chặn lại và trả về lỗi `403 Access Denied`.

---

## 🤖 3. AI Auto-Summarization (Tự động tóm tắt hội thoại nền)
Để giải quyết bài toán giới hạn kích thước cửa sổ ngữ cảnh (Context Window) của các dòng LLM khi cuộc trò chuyện kéo dài quá lâu, hệ thống xây dựng cơ chế tóm tắt tự động:
- **Ngưỡng kích hoạt**: Mỗi khi số lượng tin nhắn trong phiên chat chia hết cho 10 (`message_count % 10 == 0`), hệ thống sẽ phát động tiến trình tóm tắt.
- **Background Task**: Tiến trình này được gửi vào hàng đợi xử lý ngầm (`FastAPI.BackgroundTasks`) để chạy hoàn toàn độc lập ở nền mà không làm tăng thời gian chờ phản hồi của người dùng ở luồng chính.
- **Nội dung tóm tắt**: Sử dụng mô hình LLM chất lượng cao để nén lịch sử 20 tin nhắn gần nhất cùng bản tóm tắt cũ thành bản tóm tắt mới dạng tiếng Việt có cấu trúc gọn gàng (chứa các thông tin về loài thú cưng, triệu chứng sức khỏe đã chia sẻ và trạng thái vấn đề đã được giải quyết hay chưa).
- Ngữ cảnh tóm tắt này sau đó được tự động tái nhúng vào prompt của Agent ở các lượt chat tiếp theo giúp Agent luôn nhớ sâu thông tin cốt lõi mà không bị tràn ngữ cảnh.
