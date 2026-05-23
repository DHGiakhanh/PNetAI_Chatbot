"""Website database schema metadata for MongoDB query generation and validation.

Contains the schema descriptions, Whitelists, and forbidden operators.
"""

from __future__ import annotations

from typing import Any

# Website DB schema (readonly, context-only)
WEBSITE_DB_SCHEMA: dict[str, dict[str, Any]] = {
    "products": {
        "description": "Sản phẩm thú cưng (thức ăn, phụ kiện, cát vệ sinh, đồ chơi, sữa tắm...)",
        "fields": {
            "_id": "ObjectId — Khóa chính",
            "providerId": "ObjectId — ID của nhà cung cấp sản phẩm",
            "name": "str — Tên sản phẩm",
            "description": "str — Mô tả chi tiết sản phẩm",
            "price": "int — Giá bán của sản phẩm bằng VNĐ",
            "category": "str — Danh mục sản phẩm. PHẢI dùng tiếng Anh viết hoa đầu: 'Food', 'Accessories', 'Toys', 'Grooming'",
            "images": "list[str] — Danh sách URLs hình ảnh sản phẩm",
            "stock": "int — Số lượng hàng còn trong kho",
            "isHot": "bool — Sản phẩm bán chạy/nổi bật (true nếu có)",
            "isRecommended": "bool — Sản phẩm được đề xuất tốt (true nếu có)",
            "averageRating": "int — Điểm đánh giá trung bình từ người dùng (1-5)",
            "totalReviews": "int — Tổng số lượt đánh giá",
            "status": "str — Trạng thái sản phẩm (ví dụ: 'active')",
            "tags": "list[str] — Các nhãn phân loại bổ sung (ví dụ: 'chó', 'mèo', 'cún con', 'hạt')",
            "isDeleted": "bool — Đã bị xóa hay chưa (true nếu đã bị xóa mềm)",
            "createdAt": "datetime — Thời gian tạo sản phẩm",
            "updatedAt": "datetime — Thời gian cập nhật sản phẩm",
        },
        "indexes": ["category", "tags", "price", "isHot", "isRecommended"],
    },
    "pets": {
        "description": "Thông tin thú cưng của người dùng hệ thống",
        "fields": {
            "_id": "ObjectId — Khóa chính",
            "user": "ObjectId — ID của người dùng sở hữu thú cưng này",
            "name": "str — Tên thú cưng",
            "species": "str — Loài thú cưng. PHẢI dùng tiếng Anh viết hoa đầu: 'Dog', 'Cat', 'Bird', 'Rabbit', 'Hamster', 'Other'",
            "breed": "str — Giống thú cưng (ví dụ: Poodle, Corgi, mèo Anh lông ngắn...)",
            "gender": "str — Giới tính. PHẢI dùng tiếng Anh viết hoa đầu: 'Male', 'Female', 'Unknown'",
            "age": "int — Tuổi của thú cưng",
            "birthday": "datetime — Ngày sinh của thú cưng",
            "weightKg": "float | int — Cân nặng của thú cưng bằng kg",
            "isSpayed": "bool — Đã triệt sản hay chưa (true nếu đã triệt sản)",
            "healthStatus": "str — Tình trạng sức khỏe hiện tại (ví dụ: 'Healthy')",
            "allergies": "str — Các thông tin dị ứng của thú cưng",
            "medicalHistory": "str — Tiểu sử bệnh án/lịch sử y tế dạng text",
            "avatarUrl": "str — URL ảnh đại diện của thú cưng",
            "notes": "str — Các ghi chú đặc biệt khác về thú cưng",
            "createdAt": "datetime — Thời gian tạo",
            "updatedAt": "datetime — Thời gian cập nhật",
        },
        "indexes": ["species", "breed", "user"],
    },
    "orders": {
        "description": (
            "Đơn hàng mua sản phẩm thú cưng — CHỈ được truy vấn khi người dùng đã đăng nhập "
            "(is_authenticated) và hệ thống sẽ tự động lọc theo ID của họ."
        ),
        "fields": {
            "_id": "ObjectId — Khóa chính đơn hàng",
            "user": "ObjectId — ID người dùng sở hữu đơn hàng (đã được xác thực)",
            "items": (
                "list[{product: ObjectId, name: str, quantity: int, price: int}] "
                "— Danh sách sản phẩm trong đơn hàng"
            ),
            "totalAmount": "int — Tổng số tiền thanh toán của đơn hàng bằng VNĐ",
            "shippingAddress": (
                "dict — Thông tin địa chỉ nhận hàng gồm {name: str, phone: str, address: str}"
            ),
            "status": (
                "str — Trạng thái đơn hàng. PHẢI dùng các giá trị tiếng Anh: 'pending', 'processing', 'shipped', 'delivered', 'cancelled', 'return_requested'"
            ),
            "paymentMethod": "str — Phương thức thanh toán. PHẢI dùng: 'COD', 'PAYOS'",
            "paymentStatus": "str — Trạng thái thanh toán. PHẢI dùng tiếng Anh: 'unpaid', 'pending', 'paid', 'failed', 'cancelled', 'refund_pending', 'refunded'",
            "createdAt": "datetime — Thời gian tạo đơn hàng",
            "updatedAt": "datetime — Thời gian cập nhật đơn hàng",
            "shippingMethod": "str — Phương thức vận chuyển. PHẢI dùng: 'standard', 'express'",
            "paidAt": "datetime | None — Thời điểm thanh toán thành công",
        },
        "security_note": "Hệ thống sẽ luôn tự động áp bộ lọc field 'user' trùng với ID người dùng",
    },
    "blogs": {
        "description": "Bài viết chia sẻ kiến thức, tin tức chăm sóc sức khỏe thú cưng",
        "fields": {
            "_id": "ObjectId — Khóa chính bài viết",
            "title": "str — Tiêu đề bài viết",
            "content": "str — Nội dung chi tiết bài viết",
            "author": "ObjectId — ID tác giả bài viết",
            "category": "str — Danh mục bài viết (ví dụ: Dinh dưỡng, Chăm sóc, Huấn luyện...)",
            "image": "str — URL ảnh đại diện bài viết",
            "isHot": "bool — Bài viết nổi bật/nhiều người đọc (true nếu có)",
            "views": "int — Lượt xem bài viết",
            "status": "str — Trạng thái bài viết (ví dụ: 'active')",
            "createdAt": "datetime — Thời gian đăng bài",
            "updatedAt": "datetime — Thời gian cập nhật",
            "comments": "list — Danh sách bình luận",
            "likes": "list[ObjectId] — Danh sách ID người dùng thích bài viết",
            "dislikes": "list — Danh sách người dùng không thích bài viết",
        },
        "indexes": ["title", "category", "isHot"],
    },
    "ratings": {
        "description": "Đánh giá và phản hồi của người dùng về sản phẩm",
        "fields": {
            "_id": "ObjectId — Khóa chính đánh giá",
            "product": "ObjectId — ID sản phẩm được đánh giá",
            "user": "ObjectId — ID người dùng gửi đánh giá",
            "rating": "int — Số sao đánh giá từ 1 đến 5",
            "comment": "str — Nội dung đánh giá/phản hồi chi tiết",
            "createdAt": "datetime — Thời gian đánh giá",
            "updatedAt": "datetime — Thời gian cập nhật",
        },
    },
    "services": {
        "description": "Các dịch vụ chăm sóc thú cưng có sẵn tại hệ thống (Khám bệnh, Grooming, Spa, Lưu chuồng)",
        "fields": {
            "_id": "ObjectId — Khóa chính dịch vụ",
            "title": "str — Tên dịch vụ",
            "description": "str — Mô tả chi tiết dịch vụ",
            "category": "str — Danh mục dịch vụ. PHẢI dùng tiếng Anh viết hoa đầu: 'Grooming', 'Veterinary', 'Training', 'Spa', 'Hotel', etc.",
            "basePrice": "int — Giá cơ bản của dịch vụ bằng VNĐ",
            "duration": "int — Thời gian thực hiện tính bằng phút",
            "images": "list[str] — Danh sách URLs hình ảnh của dịch vụ",
            "features": "list[str] — Các tính năng, tiện ích đi kèm của dịch vụ",
            "isPopular": "bool — Dịch vụ phổ biến/yêu thích (true nếu có)",
            "isAvailable": "bool — Trạng thái hoạt động của dịch vụ (true nếu sẵn sàng phục vụ)",
            "averageRating": "float | int — Điểm đánh giá trung bình từ khách hàng (1-5)",
            "totalReviews": "int — Tổng số lượt đánh giá dịch vụ",
            "providerId": "ObjectId — ID của nhà cung cấp/phòng khám cung cấp dịch vụ này",
            "location": (
                "dict — Địa điểm cung cấp gồm {address: str, city: str, coordinates: {lat: float, lng: float}}"
            ),
            "availability": (
                "dict — Lịch hoạt động gồm {days: list[str], hours: {start: str, end: str}}"
            ),
            "createdAt": "datetime — Lập ngày dịch vụ",
            "updatedAt": "datetime — Cập nhật ngày dịch vụ",
            "tags": "list[str] — Các nhãn phân loại (ví dụ: 'tắm rửa', 'khám', 'cắt lông', 'chó', 'mèo')",
        },
        "indexes": ["category", "basePrice", "isAvailable", "isPopular"],
    },
}

# Whitelist of allowed collections for query generation
ALLOWED_COLLECTIONS: set[str] = {"products", "pets", "orders", "blogs", "ratings", "services"}

# Forbidden operators to prevent MongoDB injection / execution exploitation
FORBIDDEN_OPERATORS: set[str] = {"$where", "$eval", "$function", "$accumulator"}
