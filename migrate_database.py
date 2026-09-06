"""
Script Migration: Thêm cột total_crafted và chuyển đổi dữ liệu cũ
Chạy file này MỘT LẦN để cập nhật database hiện tại.
"""
import sqlite3

DB_NAME = "mid_autumn_event.db"

def migrate_database():
    """Thêm cột total_crafted và chuyển đổi dữ liệu từ hop_banh sang total_crafted"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        # Bước 1: Kiểm tra xem cột total_crafted đã tồn tại chưa
        cursor.execute("PRAGMA table_info(inventory)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'total_crafted' in columns:
            print("⚠️  Cột 'total_crafted' đã tồn tại. Migration đã được chạy trước đó.")
            conn.close()
            return

        print("📦 Bắt đầu migration database...")

        # Bước 2: Thêm cột total_crafted với giá trị mặc định là 0
        cursor.execute("ALTER TABLE inventory ADD COLUMN total_crafted INTEGER DEFAULT 0")
        print("✅ Đã thêm cột 'total_crafted' vào bảng inventory")

        # Bước 3: Chuyển đổi dữ liệu cũ - Giả định rằng số hộp bánh hiện tại = tổng số đã ghép
        # (Vì trước đây chưa có ai đổi thưởng hoặc số liệu cũ được giữ nguyên)
        cursor.execute("""
            UPDATE inventory
            SET total_crafted = hop_banh
            WHERE hop_banh > 0
        """)

        affected_rows = cursor.rowcount
        print(f"✅ Đã chuyển đổi dữ liệu cho {affected_rows} người chơi")

        # Bước 4: Kiểm tra kết quả
        cursor.execute("SELECT COUNT(*) FROM inventory WHERE total_crafted > 0")
        total_users = cursor.fetchone()[0]
        print(f"📊 Tổng số người chơi có hộp bánh đã ghép: {total_users}")

        conn.commit()
        print("\n🎉 Migration hoàn tất thành công!")
        print("💡 Từ giờ, mỗi lần ghép bánh sẽ tự động tăng total_crafted")

    except sqlite3.Error as e:
        print(f"❌ Lỗi khi migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("   MIGRATION SCRIPT - THÊM TÍNH NĂNG TỔNG HỘP ĐÃ GHÉP")
    print("=" * 60)
    print()

    migrate_database()
