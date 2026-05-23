"""Pet knowledge base documents in Vietnamese.

These are sample documents for seeding Qdrant's pet_knowledge_base collection.
Covers: nutrition, health, behavior, grooming, common diseases.
"""

PET_KNOWLEDGE_DOCUMENTS: list[dict] = [
    {
        "id": "doc-001",
        "title": "Chế độ dinh dưỡng cho chó con từ 2-6 tháng tuổi",
        "content": (
            "Chó con từ 2-6 tháng tuổi cần chế độ dinh dưỡng giàu protein (28-32%) "
            "và chất béo (15-18%) để hỗ trợ phát triển cơ và xương. Nên cho ăn 3-4 bữa/ngày "
            "với thức ăn hạt chuyên dụng cho puppy. Tránh cho ăn xương nhỏ, socola, nho, hành tỏi "
            "vì có thể gây ngộ độc. Luôn đảm bảo nước sạch có sẵn. Bổ sung canxi và vitamin D "
            "theo chỉ định bác sĩ thú y."
        ),
        "category": "nutrition",
        "species": "dog",
        "tags": ["chó con", "dinh dưỡng", "puppy", "thức ăn", "protein"],
    },
    {
        "id": "doc-002",
        "title": "Thức ăn phù hợp cho mèo trưởng thành",
        "content": (
            "Mèo trưởng thành (1-7 tuổi) là động vật ăn thịt bắt buộc, cần protein từ động vật. "
            "Thức ăn nên chứa tối thiểu 26% protein và 9% chất béo. Taurine là axit amin thiết yếu "
            "cho mèo, giúp ngăn ngừa bệnh tim và mù lòa. Nên cho ăn 2 bữa/ngày, kết hợp thức ăn khô "
            "và ướt để đảm bảo đủ nước. Tránh thức ăn cho chó vì thiếu taurine và protein phù hợp."
        ),
        "category": "nutrition",
        "species": "cat",
        "tags": ["mèo", "dinh dưỡng", "taurine", "thức ăn", "protein"],
    },
    {
        "id": "doc-003",
        "title": "Lịch tiêm phòng cho chó — Hướng dẫn đầy đủ",
        "content": (
            "Chó cần được tiêm phòng đầy đủ để phòng các bệnh nguy hiểm: Parvo, Care (Sài sốt), "
            "Viêm gan truyền nhiễm, Ho cũi chó, Dại. Lịch tiêm cơ bản: Mũi 1 lúc 6-8 tuần tuổi "
            "(DHPPi), Mũi 2 lúc 10-12 tuần (DHPPi + Leptospirosis), Mũi 3 lúc 14-16 tuần "
            "(DHPPi + Leptospirosis + Dại). Tiêm nhắc hàng năm. Tẩy giun định kỳ mỗi 3 tháng. "
            "Sau tiêm, chó có thể mệt mỏi 1-2 ngày, cần theo dõi và giữ ấm."
        ),
        "category": "healthcare",
        "species": "dog",
        "tags": ["tiêm phòng", "chó", "vaccine", "sức khỏe", "parvo", "care", "dại"],
    },
    {
        "id": "doc-004",
        "title": "Cách nhận biết và xử lý khi chó bị ve, rận",
        "content": (
            "Ve và rận là ký sinh trùng phổ biến ở chó, đặc biệt vào mùa mưa. Dấu hiệu: chó gãi "
            "nhiều, da đỏ, rụng lông từng mảng, có thể nhìn thấy ve bám trên da. Cách xử lý: Sử "
            "dụng thuốc nhỏ gáy (Frontline, Advocate) mỗi tháng. Tắm cho chó bằng sữa tắm trị ve "
            "chuyên dụng. Vệ sinh môi trường sống: giặt đệm, chăn, hút bụi thường xuyên. Nếu chó "
            "có dấu hiệu thiếu máu (lợi nhợt nhạt, mệt mỏi), cần đưa đi thú y ngay."
        ),
        "category": "healthcare",
        "species": "dog",
        "tags": ["ve", "rận", "ký sinh trùng", "chó", "sức khỏe", "phòng bệnh"],
    },
    {
        "id": "doc-005",
        "title": "Chăm sóc mèo trong mùa hè nóng bức",
        "content": (
            "Mùa hè nắng nóng có thể gây say nắng ở mèo. Đảm bảo mèo luôn có nước sạch, đặt nhiều "
            "bát nước trong nhà. Giữ phòng thoáng mát, có thể dùng quạt hoặc điều hòa (26-28°C). "
            "Chải lông thường xuyên để loại bỏ lông chết giúp mèo thoát nhiệt tốt hơn. Dấu hiệu "
            "say nắng: thở hổn hển, lưỡi và lợi đỏ, nôn mửa, yếu ớt. Nếu nghi ngờ say nắng, "
            "làm mát từ từ bằng khăn ẩm và đưa đến bác sĩ thú y."
        ),
        "category": "care",
        "species": "cat",
        "tags": ["mèo", "mùa hè", "chăm sóc", "say nắng", "nhiệt độ"],
    },
    {
        "id": "doc-006",
        "title": "Huấn luyện chó đi vệ sinh đúng chỗ",
        "content": (
            "Huấn luyện chó đi vệ sinh cần kiên nhẫn và nhất quán. Chọn một vị trí cố định và dẫn "
            "chó đến đó sau khi ăn (15-20 phút), sau khi ngủ dậy, và sau khi chơi. Khen thưởng "
            "ngay khi chó đi đúng chỗ bằng treat hoặc lời khen. Không la mắng hay phạt khi chó đi "
            "sai vì sẽ gây sợ hãi. Vệ sinh sạch chỗ đi sai bằng enzyme cleaner để loại bỏ mùi. "
            "Với chó con, nên cho ra ngoài mỗi 2-3 giờ. Thời gian huấn luyện thường mất 2-4 tuần."
        ),
        "category": "behavior",
        "species": "dog",
        "tags": ["huấn luyện", "chó", "vệ sinh", "hành vi", "puppy"],
    },
    {
        "id": "doc-007",
        "title": "Các bệnh thường gặp ở mèo và cách phòng tránh",
        "content": (
            "Mèo thường gặp các bệnh: Viêm phúc mạc truyền nhiễm (FIP), Giảm bạch cầu (FPV), "
            "Viêm mũi-khí quản (FVR), Sỏi thận, Bệnh răng miệng. Phòng tránh bằng cách: tiêm "
            "vaccine đầy đủ, khám sức khỏe định kỳ 6 tháng/lần, vệ sinh răng miệng thường xuyên, "
            "đảm bảo chế độ ăn cân bằng, giữ môi trường sống sạch sẽ. Dấu hiệu cần đi khám: bỏ ăn "
            "trên 24h, nôn mửa liên tục, tiêu chảy, khó thở, sút cân nhanh."
        ),
        "category": "healthcare",
        "species": "cat",
        "tags": ["mèo", "bệnh", "FIP", "FPV", "phòng bệnh", "sức khỏe"],
    },
    {
        "id": "doc-008",
        "title": "Cách tắm và vệ sinh cho chó đúng cách",
        "content": (
            "Tắm cho chó 2-4 tuần/lần tùy giống và mức độ hoạt động. Sử dụng sữa tắm chuyên dụng "
            "cho chó (pH cân bằng), không dùng sữa tắm người. Các bước: Chải lông trước khi tắm, "
            "làm ướt toàn thân bằng nước ấm (37-39°C), thoa sữa tắm từ cổ xuống đuôi, massage nhẹ "
            "nhàng, xả sạch hoàn toàn. Lau khô bằng khăn và sấy ở nhiệt độ thấp. Vệ sinh tai bằng "
            "dung dịch chuyên dụng, cắt móng nếu cần, đánh răng 2-3 lần/tuần."
        ),
        "category": "grooming",
        "species": "dog",
        "tags": ["tắm", "vệ sinh", "chó", "chải lông", "cắt móng", "sữa tắm"],
    },
    {
        "id": "doc-009",
        "title": "Dinh dưỡng cho thú cưng bị dị ứng thức ăn",
        "content": (
            "Dị ứng thức ăn ở chó mèo thường biểu hiện qua: ngứa da, nổi mẩn, rụng lông, viêm tai "
            "tái phát, tiêu chảy, nôn mửa. Nguyên nhân thường gặp: protein bò, gà, sữa, lúa mì, "
            "đậu nành. Chế độ ăn loại trừ (elimination diet): sử dụng protein mới (cá hồi, thỏ, "
            "vịt, kangaroo) trong 8-12 tuần. Thức ăn hydrolyzed protein giúp giảm dị ứng. Không "
            "cho ăn thức ăn thừa của người. Ghi nhật ký ăn uống để xác định nguyên nhân."
        ),
        "category": "nutrition",
        "species": "all",
        "tags": ["dị ứng", "thức ăn", "chó", "mèo", "dinh dưỡng", "protein"],
    },
    {
        "id": "doc-010",
        "title": "Chuẩn bị đồ dùng cần thiết khi đón chó con về nhà",
        "content": (
            "Danh sách đồ dùng cần chuẩn bị: 1) Chuồng/lồng hoặc đệm nằm phù hợp kích thước. "
            "2) Bát ăn và bát uống bằng inox hoặc gốm (tránh nhựa). 3) Thức ăn hạt chất lượng "
            "cao dành cho puppy. 4) Dây dắt và vòng cổ (có gắn thẻ tên + số điện thoại). "
            "5) Đồ chơi gặm (giúp giảm đau khi thay răng). 6) Tấm lót vệ sinh hoặc khay vệ sinh. "
            "7) Sữa tắm, bàn chải, kìm cắt móng. 8) Túi đựng phân khi đi dạo. Nên đưa chó đi "
            "khám thú y trong tuần đầu tiên để kiểm tra sức khỏe tổng quát."
        ),
        "category": "care",
        "species": "dog",
        "tags": ["chó con", "chuẩn bị", "đồ dùng", "puppy", "mới về"],
    },
    {
        "id": "doc-011",
        "title": "Tại sao mèo cào móng và cách bảo vệ đồ đạc",
        "content": (
            "Mèo cào móng là hành vi tự nhiên để: đánh dấu lãnh thổ (có tuyến mùi ở chân), "
            "mài móng, kéo giãn cơ, giải tỏa stress. Cách bảo vệ đồ đạc: Đặt trụ cào (cat tree) "
            "ở vị trí mèo thường qua lại. Chọn chất liệu mèo thích (sisal, thảm, bìa carton). "
            "Rắc catnip lên trụ cào để thu hút. Dán băng dính 2 mặt hoặc bọc vải chống cào lên "
            "đồ đạc cần bảo vệ. Tuyệt đối không cắt móng (declawing) vì gây đau đớn và ảnh hưởng "
            "tâm lý mèo. Cắt móng định kỳ 2-3 tuần/lần là đủ."
        ),
        "category": "behavior",
        "species": "cat",
        "tags": ["mèo", "cào móng", "hành vi", "trụ cào", "đồ đạc"],
    },
    {
        "id": "doc-012",
        "title": "Cách chọn thức ăn hạt chất lượng cho chó",
        "content": (
            "Tiêu chí chọn thức ăn hạt tốt: 1) Thành phần đầu tiên phải là protein động vật "
            "(gà, bò, cá hồi...) không phải ngũ cốc. 2) Hàm lượng protein tối thiểu 25% với chó "
            "trưởng thành, 28% với chó con. 3) Có ghi rõ nguồn gốc chất béo (mỡ gà, dầu cá hồi). "
            "4) Không chứa phẩm màu, hương liệu nhân tạo. 5) Đạt chuẩn AAFCO. Tránh thức ăn có "
            "thành phần mập mờ như 'meat meal', 'animal by-product'. Các thương hiệu tốt: Royal "
            "Canin, Hill's, Taste of the Wild, Acana, Orijen. Chuyển đổi thức ăn từ từ trong "
            "7-10 ngày để tránh rối loạn tiêu hóa."
        ),
        "category": "nutrition",
        "species": "dog",
        "tags": ["thức ăn", "chó", "dinh dưỡng", "chất lượng", "AAFCO", "hạt"],
    },
    {
        "id": "doc-013",
        "title": "Phòng và trị bệnh viêm da ở chó",
        "content": (
            "Viêm da ở chó có nhiều nguyên nhân: dị ứng (thức ăn, môi trường, bọ chét), nấm, "
            "vi khuẩn, rối loạn nội tiết. Triệu chứng: ngứa, gãi nhiều, da đỏ, vảy, mụn mủ, "
            "rụng lông, mùi hôi. Điều trị tùy nguyên nhân: kháng histamin cho dị ứng, kháng sinh "
            "cho nhiễm khuẩn, thuốc trị nấm, dầu tắm thuốc. Phòng ngừa: vệ sinh sạch sẽ, chống "
            "bọ chét định kỳ, chế độ ăn lành mạnh giàu Omega-3. Không tự ý dùng thuốc người "
            "cho chó. Đưa đi thú y nếu tình trạng không cải thiện sau 3-5 ngày."
        ),
        "category": "healthcare",
        "species": "dog",
        "tags": ["viêm da", "chó", "dị ứng", "da", "sức khỏe", "nấm"],
    },
    {
        "id": "doc-014",
        "title": "Hướng dẫn cho mèo uống thuốc dễ dàng",
        "content": (
            "Cho mèo uống thuốc cần kỹ thuật và kiên nhẵn. Phương pháp 1 - Trực tiếp: quấn mèo "
            "trong khăn, giữ đầu ngửa nhẹ, dùng ngón tay đẩy khóe miệng mở ra, thả viên thuốc vào "
            "sâu trong miệng, vuốt cổ để kích thích nuốt. Phương pháp 2 - Trộn thức ăn: nghiền "
            "thuốc (nếu được phép) trộn với pate, thức ăn ướt. Phương pháp 3 - Dùng dụng cụ bơm "
            "thuốc (pill gun/popper) cho thuốc viên hoặc syringe cho thuốc nước. Luôn thưởng "
            "cho mèo sau khi uống thuốc. Nếu mèo chảy dãi nhiều, có thể thuốc có vị đắng."
        ),
        "category": "healthcare",
        "species": "cat",
        "tags": ["mèo", "uống thuốc", "chăm sóc", "sức khỏe", "kỹ thuật"],
    },
    {
        "id": "doc-015",
        "title": "Tập thể dục phù hợp cho từng giống chó",
        "content": (
            "Nhu cầu vận động khác nhau theo giống: Chó săn (Husky, Border Collie, Golden "
            "Retriever) cần 1-2 giờ/ngày vận động mạnh. Chó nhỏ (Poodle, Chihuahua, Pug) cần "
            "30-45 phút/ngày đi bộ + chơi trong nhà. Chó bulldog, pug mặt ngắn không nên vận động "
            "quá sức khi trời nóng (>28°C). Dấu hiệu vận động đủ: chó vui vẻ, không phá phách đồ "
            "đạc, ngủ ngon. Dấu hiệu quá sức: thở gấp, lưỡi thè dài, nằm bệt không dậy, chảy dãi. "
            "Nên chia thành 2-3 lần đi dạo mỗi ngày thay vì 1 lần dài."
        ),
        "category": "behavior",
        "species": "dog",
        "tags": ["tập thể dục", "chó", "vận động", "giống chó", "đi dạo"],
    },
]

# Metadata categories for filtering
CATEGORIES = ["nutrition", "healthcare", "care", "grooming", "behavior"]
SPECIES = ["dog", "cat", "all"]
