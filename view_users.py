"""
Script hiển thị bảng dữ liệu người dùng (Player & PlayerRanking) trong flappy_bird_db
Chạy lệnh: python view_users.py
"""
import sys
import os

# Thiet lap ma hoa UTF-8 cho Terminal Windows
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Them thu muc hien tai vao sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dao.dao import DAO

def display_table(title, headers, rows):
    print("\n" + "=" * 90)
    print(f" {title} (Tổng cộng: {len(rows)} bản ghi)")
    print("=" * 90)
    
    if not rows:
        print(" (Bảng trống)")
        return
        
    # Tính độ rộng cột tự động
    col_widths = [len(h) for h in headers]
    formatted_rows = []
    
    for r in rows:
        row_str = [str(r.get(h, '')) if isinstance(r, dict) else str(r[i]) for i, h in enumerate(headers)]
        formatted_rows.append(row_str)
        for i, val in enumerate(row_str):
            if len(val) > col_widths[i]:
                col_widths[i] = len(val)
                
    # In Header
    header_line = " | ".join(f"{headers[i]:<{col_widths[i]}}" for i in range(len(headers)))
    print(header_line)
    print("-+-".join("-" * col_widths[i] for i in range(len(headers))))
    
    # In Rows
    for row_str in formatted_rows:
        print(" | ".join(f"{row_str[i]:<{col_widths[i]}}" for i in range(len(headers))))
    print("=" * 90)

def main():
    dao = DAO()
    
    # 1. Bảng Player
    player_cols = ["id", "username", "password_hash", "score", "total_points", "total_wins", "email", "created_at"]
    players = dao.execute_query(
        "SELECT id, username, password_hash, score, total_points, total_wins, email, created_at "
        "FROM Player ORDER BY id ASC"
    )
    display_table("BẢNG NGƯỜI DÙNG: Player", player_cols, players)
    
    # 2. Bảng PlayerRanking (Bảng xếp hạng)
    ranking_cols = ["Playerid", "rank", "HighestPoint", "totalPoints", "totalWins"]
    rankings = dao.execute_query(
        "SELECT Playerid, `rank`, HighestPoint, totalPoints, totalWins "
        "FROM PlayerRanking ORDER BY HighestPoint DESC, totalPoints DESC"
    )
    display_table("BẢNG XẾP HẠNG: PlayerRanking", ranking_cols, rankings)

if __name__ == "__main__":
    main()
