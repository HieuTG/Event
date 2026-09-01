import sqlite3

DB_NAME = "mid_autumn_event.db"

def init_db():
    """Khởi tạo database và tạo bảng nếu chưa tồn tại."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Bảng lưu trữ túi đồ của user (Đã thêm cột manh_vo)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            user_id TEXT PRIMARY KEY,
            dau_xanh INTEGER DEFAULT 0,
            thap_cam INTEGER DEFAULT 0,
            me_den INTEGER DEFAULT 0,
            hat_sen INTEGER DEFAULT 0,
            khoai_mon INTEGER DEFAULT 0,
            trung_muoi INTEGER DEFAULT 0,
            hop_banh INTEGER DEFAULT 0,
            manh_vo INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trade_limits (
            user_id TEXT,
            trade_date TEXT,
            count INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, trade_date)
        )
    """)

    cursor.execute("""
            CREATE TABLE IF NOT EXISTS event_settings (
            key TEXT PRIMARY KEY,
            value TEXT  
        )
    """)
    cursor.execute("""
     CREATE TABLE IF NOT EXISTS spawn_channels (
         channel_id TEXT PRIMARY KEY
     )
 """)
    conn.commit()
    conn.close()

def get_user_inventory(user_id: str):
    """Lấy dữ liệu túi đồ của một user. Trả về 8 vật phẩm."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT dau_xanh, thap_cam, me_den, hat_sen, khoai_mon, trung_muoi, hop_banh, manh_vo FROM inventory WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    if row is None:
        cursor.execute("INSERT INTO inventory (user_id) VALUES (?)", (user_id,))
        conn.commit()
        conn.close()
        return (0, 0, 0, 0, 0, 0, 0, 0) # 8 số 0 tương ứng 8 cột
    
    conn.close()
    return row

def add_item_to_inventory(user_id: str, item_name: str, amount: int = 1):
    """Cộng thêm số lượng vào một vật phẩm cụ thể của user."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    get_user_inventory(user_id)
    
    query = f"UPDATE inventory SET {item_name} = {item_name} + ? WHERE user_id = ?"
    cursor.execute(query, (amount, user_id))
    
    conn.commit()
    conn.close()

def admin_modify_inventory(user_id: str, item_name: str, amount: int) -> int:
    """Admin thay đổi số lượng vật phẩm (chặn không cho âm)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    get_user_inventory(user_id)
    
    cursor.execute(f"SELECT {item_name} FROM inventory WHERE user_id = ?", (user_id,))
    current_amount = cursor.fetchone()[0]
    
    new_amount = current_amount + amount
    if new_amount < 0:
        new_amount = 0
        
    cursor.execute(f"UPDATE inventory SET {item_name} = ? WHERE user_id = ?", (new_amount, user_id))
    conn.commit()
    conn.close()
    return new_amount

def craft_mooncakes(user_id: str) -> bool:
    """Ghép bộ 6 nguyên liệu thành 1 Hộp Bánh."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT dau_xanh, thap_cam, me_den, hat_sen, khoai_mon, trung_muoi FROM inventory WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    if row is None or any(count < 1 for count in row):
        conn.close()
        return False
        
    cursor.execute("""
        UPDATE inventory 
        SET dau_xanh = dau_xanh - 1, thap_cam = thap_cam - 1, me_den = me_den - 1,
            hat_sen = hat_sen - 1, khoai_mon = khoai_mon - 1, trung_muoi = trung_muoi - 1,
            hop_banh = hop_banh + 1
        WHERE user_id = ?
    """, (user_id,))
    conn.commit()
    conn.close()
    return True

def redeem_reward(user_id: str) -> bool:
    """Đổi 1 hộp bánh lấy quà."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT hop_banh FROM inventory WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row is None or row[0] < 1:
        conn.close()
        return False
    cursor.execute("UPDATE inventory SET hop_banh = hop_banh - 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    return True

def execute_trade(user_a_id: str, item_a: str, user_b_id: str, item_b: str, amount: int = 1) -> bool:
    """Thực hiện trao đổi giữa 2 người dùng."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute(f"SELECT {item_a} FROM inventory WHERE user_id = ?", (user_a_id,))
    row_a = cursor.fetchone()
    if row_a is None or row_a[0] < amount:
        conn.close()
        return False
        
    cursor.execute(f"SELECT {item_b} FROM inventory WHERE user_id = ?", (user_b_id,))
    row_b = cursor.fetchone()
    if row_b is None or row_b[0] < amount:
        conn.close()
        return False
        
    cursor.execute(f"UPDATE inventory SET {item_a} = {item_a} - ?, {item_b} = {item_b} + ? WHERE user_id = ?", (amount, amount, user_a_id))
    cursor.execute(f"UPDATE inventory SET {item_b} = {item_b} - ?, {item_a} = {item_a} + ? WHERE user_id = ?", (amount, amount, user_b_id))
    conn.commit()
    conn.close()
    return True

# --- HÀM MỚI: XỬ LÝ NẤU BÁNH TỪ MẢNH VỠ ---
def cook_cake_db(user_id: str, target_item: str, cost: int) -> bool:
    """Trừ mảnh vỡ bánh và đúc thành 1 chiếc bánh nguyên vẹn."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Kiểm tra số lượng mảnh vỡ hiện tại
    cursor.execute("SELECT manh_vo FROM inventory WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row is None or row[0] < cost:
        conn.close()
        return False # Không đủ mảnh vỡ
        
    # Tiến hành trừ mảnh vỡ và cộng bánh
    cursor.execute(f"UPDATE inventory SET manh_vo = manh_vo - ?, {target_item} = {target_item} + 1 WHERE user_id = ?", (cost, user_id))
    conn.commit()
    conn.close()
    return True

def check_trade_limit(user_id: str) -> bool:
    """Kiểm tra xem người dùng đã dùng hết 2 lượt tạo lệnh trade trong ngày chưa."""
    import datetime
    today = datetime.date.today().isoformat() # Lấy ngày định dạng YYYY-MM-DD
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT count FROM trade_limits WHERE user_id = ? AND trade_date = ?", (user_id, today))
    row = cursor.fetchone()
    conn.close()
    if row and row[0] >= 2:
        return False # Đã chạm giới hạn 2 lần/ngày
    return True

def increment_trade_limit(user_id: str):
    """Tăng số lần sử dụng lệnh trade trong ngày của người dùng lên 1."""
    import datetime
    today = datetime.date.today().isoformat()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO trade_limits (user_id, trade_date, count) 
        VALUES (?, ?, 1) 
        ON CONFLICT(user_id, trade_date) 
        DO UPDATE SET count = count + 1
    """, (user_id, today))
    conn.commit()
    conn.close()

def execute_flexible_trade(user_a_id: str, item_a: str, amount_a: int, user_b_id: str, item_b: str, amount_b: int) -> bool:
    """Thực hiện giao dịch với số lượng chênh lệch tùy ý giữa bên A và bên B."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Kiểm tra túi đồ người đề xuất (Bên A)
    cursor.execute(f"SELECT {item_a} FROM inventory WHERE user_id = ?", (user_a_id,))
    row_a = cursor.fetchone()
    if row_a is None or row_a[0] < amount_a:
        conn.close()
        return False
        
    # Kiểm tra túi đồ đối phương (Bên B)
    cursor.execute(f"SELECT {item_b} FROM inventory WHERE user_id = ?", (user_b_id,))
    row_b = cursor.fetchone()
    if row_b is None or row_b[0] < amount_b:
        conn.close()
        return False
        
    # Khấu trừ số lượng tương ứng và chuyển giao tài sản chéo công bằng
    cursor.execute(f"UPDATE inventory SET {item_a} = {item_a} - ?, {item_b} = {item_b} + ? WHERE user_id = ?", (amount_a, amount_b, user_a_id))
    cursor.execute(f"UPDATE inventory SET {item_b} = {item_b} - ?, {item_a} = {item_a} + ? WHERE user_id = ?", (amount_b, amount_a, user_b_id))
    
    conn.commit()
    conn.close()
    return True

def get_top_bakers(limit: int = 10) -> list:
    """
    Lấy danh sách top những người ghép được nhiều hộp bánh nhất.
    Lưu ý: Bạn hãy thay đổi tên bảng hoặc tên cột bên dưới cho đúng với cấu hình 
    bảng lưu trữ số hộp bánh đã ghép (inventory / users) trong DB của bạn.
    Ví dụ ở đây giả định bảng 'inventory' có cột 'user_id', 'hop_banh' (hoặc tương tự).
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Giả sử bạn lưu số hộp bánh ghép được trong bảng dữ liệu người dùng/kho đồ.
    # Thay đổi câu lệnh SQL này cho khớp với cấu trúc Database hiện tại của bạn:
    cursor.execute("""
        SELECT user_id, hop_banh 
        FROM inventory 
        WHERE hop_banh > 0 
        ORDER BY hop_banh DESC 
        LIMIT ?
    """, (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    return rows # Trả về danh sách [(user_id, so_luong), ...]

def get_user_rank_and_count(user_id: str):
    """
    Tìm thứ hạng và số lượng hộp bánh hiện có của một người chơi.
    Trả về: (rank, count) - Ví dụ: (15, 3) nghĩa là hạng 15 với 3 hộp bánh.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Lấy số lượng hộp bánh của người chơi
    # (Hãy nhớ sửa tên bảng 'inventory' và tên cột 'hop_banh' cho khớp với DB của bạn)
    cursor.execute("SELECT hop_banh FROM inventory WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    if not row or row[0] <= 0:
        conn.close()
        return None, 0 # Chưa có hộp bánh nào
        
    user_count = row[0]
    
    # 2. Đếm xem có bao nhiêu người có số hộp bánh NHIỀU HƠN người này -> Cộng 1 ra thứ hạng
    cursor.execute("SELECT COUNT(*) FROM inventory WHERE hop_banh > ?", (user_count,))
    rank = cursor.fetchone()[0] + 1
    
    conn.close()
    return rank, user_count

# --- THÊM HÀM NÀY VÀO CUỐI FILE database.py ---

def get_total_crafted_boxes(user_id: str) -> int:
    """
    Lấy tổng số Hộp Bánh Trung Thu mà người chơi đã ghép được trong suốt sự kiện.
    (Phục vụ cho việc hiển thị thống kê trong túi đồ và tính Bảng Xếp Hạng)
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Giả sử bạn lưu tổng số hộp đã ghép ở bảng 'inventory' (cột hop_banh hoặc cột thống kê riêng).
    # Hãy điều chỉnh tên bảng/cột cho khớp với Database thực tế của bạn:
    cursor.execute("SELECT hop_banh FROM inventory WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    conn.close()
    
    # Nếu tìm thấy dữ liệu thì trả về con số, nếu chưa có thì trả về 0
    return row[0] if row else 0

def add_spawn_channel(channel_id: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO spawn_channels (channel_id) VALUES (?)", (channel_id,))
    conn.commit()
    conn.close()

def remove_spawn_channel(channel_id: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM spawn_channels WHERE channel_id = ?", (channel_id,))
    conn.commit()
    conn.close()

def get_all_spawn_channels() -> list:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT channel_id FROM spawn_channels")
    rows = cursor.fetchall()
    conn.close()
    return [int(row[0]) for row in rows]

def set_setting(key: str, value: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS event_settings (key TEXT PRIMARY KEY, value TEXT)")
    cursor.execute("INSERT OR REPLACE INTO event_settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def get_setting(key: str) -> str:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT value FROM event_settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None
    except sqlite3.OperationalError: # Xử lý trường hợp bảng chưa được tạo
        conn.close()
        return None