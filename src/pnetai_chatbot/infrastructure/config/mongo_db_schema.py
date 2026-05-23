"""Website database schema metadata for MongoDB query generation and validation.

Contains the schema descriptions, Whitelists, and forbidden operators.
"""

from __future__ import annotations

from typing import Any

# Website DB schema (readonly, context-only)
WEBSITE_DB_SCHEMA: dict[str, dict[str, Any]] = {
    "products": {
        "description": "Sản phẩm thú cưng (thức ăn, phụ kiện, thuốc)",
        "fields": {
            "_id": "ObjectId — Khóa chính",
            "name": "str — Tên sản phẩm",
            "slug": "str — Tên thân thiện với URL",
            "category": "str — Enum: dog_food|cat_food|accessories|medicine|...",
            "tags": "list[str] — Các nhãn phân loại (ví dụ: poodle, puppy, small_breed, cat)",
            "price": "int — Giá bán gốc bằng VNĐ",
            "sale_price": "int | None — Giá khuyến mãi bằng VNĐ",
            "description": "str — Mô tả chi tiết sản phẩm",
            "brand": "str — Thương hiệu sản phẩm",
            "images": "list[str] — Danh sách URLs ảnh sản phẩm",
            "stock": "int — Số lượng hàng còn trong kho",
            "is_active": "bool — Trạng thái sản phẩm (true nếu đang bán)",
            "rating": "float — Điểm đánh giá trung bình (1.0 - 5.0)",
            "review_count": "int — Số lượt đánh giá",
            "created_at": "datetime — Thời gian tạo sản phẩm",
        },
        "indexes": ["category", "tags", "price", "brand", "is_active"],
        "sample_queries": [
            "Tìm sản phẩm theo category + price range",
            "Tìm sản phẩm theo brand",
            "Tìm sản phẩm theo tags (loài thú, kích cỡ, ...)",
        ],
    },
    "pets": {
        "description": "Thú cưng đang bán tại cửa hàng",
        "fields": {
            "_id": "ObjectId — Khóa chính",
            "name": "str — Tên thú cưng",
            "species": "str — Loài thú (Enum: dog|cat|bird|fish|rabbit|...)",
            "breed": "str — Giống thú cưng (ví dụ: Poodle, Corgi, British Shorthair)",
            "age_months": "int — Tuổi của thú cưng tính theo tháng",
            "gender": "str — Giới tính (male|female)",
            "price": "int — Giá bán bằng VNĐ",
            "health_status": "str — Tình trạng sức khỏe",
            "vaccinated": "bool — Đã tiêm phòng đầy đủ hay chưa",
            "images": "list[str] — Danh sách URLs hình ảnh thú cưng",
            "is_available": "bool — Thú cưng còn có sẵn để nhận nuôi/mua hay không (true nếu còn)",
            "description": "str — Mô tả tính cách, đặc điểm thú cưng",
        },
        "indexes": ["species", "breed", "price", "is_available"],
    },
    "orders": {
        "description": (
            "Đơn hàng của khách hàng — CHỈ được query khi người dùng đã đăng nhập "
            "(is_authenticated) và muốn tìm kiếm đơn hàng CỦA HỌ."
        ),
        "fields": {
            "_id": "ObjectId — Khóa chính đơn hàng",
            "user_id": "str — Mã người dùng sở hữu đơn hàng này (ObjectId dưới dạng chuỗi)",
            "items": (
                "list[{product_id: str, name: str, quantity: int, price: int}] "
                "— Danh sách mặt hàng mua"
            ),
            "total": "int — Tổng số tiền của đơn hàng",
            "status": (
                "str — Trạng thái đơn hàng (pending|confirmed|shipping|delivered|cancelled)"
            ),
            "created_at": "datetime — Thời gian tạo đơn hàng",
        },
        "security_note": "ALWAYS filter by user_id khi query collection này",
    },
    "articles": {
        "description": "Bài viết kiến thức, tin tức chăm sóc thú cưng",
        "fields": {
            "_id": "ObjectId — Khóa chính bài viết",
            "title": "str — Tiêu đề bài viết",
            "content": "str — Nội dung bài viết",
            "category": "str — Thể loại bài viết",
            "tags": "list[str] — Nhãn phân loại",
            "published_at": "datetime — Thời gian đăng bài",
        },
    },
    "reviews": {
        "description": "Đánh giá sản phẩm của người dùng",
        "fields": {
            "_id": "ObjectId — Khóa chính đánh giá",
            "product_id": "str — ID sản phẩm được đánh giá",
            "user_id": "str — ID người dùng đánh giá",
            "username": "str — Tên hiển thị người dùng",
            "rating": "int — Số sao đánh giá (1-5)",
            "comment": "str — Nội dung bình luận",
            "created_at": "datetime — Thời gian đánh giá",
        },
    },
}

# Whitelist of allowed collections for query generation
ALLOWED_COLLECTIONS: set[str] = {"products", "pets", "orders", "articles", "reviews"}

# Forbidden operators to prevent MongoDB injection / execution exploitation
FORBIDDEN_OPERATORS: set[str] = {"$where", "$eval", "$function", "$accumulator"}
