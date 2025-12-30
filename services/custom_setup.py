import os
import json
import datetime

# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CUSTOM_SETUPS_DIR = os.path.join(BASE_DIR, 'custom_setups')
GAME_RECORDS_DIR = os.path.join(BASE_DIR, 'game_records')
CUSTOM_NAMES_FILE = os.path.join(GAME_RECORDS_DIR, 'custom_names.json')


def load_custom_setup_files():
    """加载自定义棋谱文件列表"""
    custom_files = []
    if os.path.exists(CUSTOM_SETUPS_DIR):
        for filename in os.listdir(CUSTOM_SETUPS_DIR):
            if filename.endswith('.json') and filename.startswith('custom_setup_'):
                custom_files.append(filename)
    return sorted(custom_files, reverse=True)  # 按时间倒序排列


def get_custom_setup_info(filename):
    """获取自定义棋谱的信息"""
    try:
        with open(os.path.join(CUSTOM_SETUPS_DIR, filename), 'r', encoding='utf-8') as f:
            data = json.load(f)
            setup_info = data.get('setup_info', {})
            blue_count = setup_info.get('blue_pieces_count', 0)
            red_count = setup_info.get('red_pieces_count', 0)
            created_time = setup_info.get('created_time', '')

            # 解析时间格式
            if created_time:
                try:
                    dt = datetime.datetime.fromisoformat(created_time)
                    date_str = f"{dt.year % 100}-{dt.month}-{dt.day}"
                except:
                    date_str = "Unknown"
            else:
                date_str = "Unknown"

            return f"B:{blue_count} R:{red_count}", date_str
    except:
        return "Unknown", "Unknown"


def load_custom_setup_file(filename):
    """加载指定的自定义棋谱文件并返回棋子位置字典 (blue_pieces, red_pieces)"""
    try:
        with open(os.path.join(CUSTOM_SETUPS_DIR, filename), 'r', encoding='utf-8') as f:
            setup_data = json.load(f)

        # 只加载文件中记录的棋子
        blue_pieces_src = setup_data.get('blue_pieces', {})
        red_pieces_src = setup_data.get('red_pieces', {})

        blue_pieces = {int(piece_num): pos for piece_num, pos in blue_pieces_src.items()}
        red_pieces = {int(piece_num): pos for piece_num, pos in red_pieces_src.items()}

        return blue_pieces, red_pieces
    except Exception as e:
        print(f"Error loading custom setup file: {e}")
        return None


def load_custom_names():
    """加载自定义棋谱名称并返回字典"""
    try:
        with open(CUSTOM_NAMES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}


def save_custom_names(custom_names):
    """保存自定义棋谱名称"""
    try:
        if not os.path.exists(GAME_RECORDS_DIR):
            os.makedirs(GAME_RECORDS_DIR)
        with open(CUSTOM_NAMES_FILE, 'w', encoding='utf-8') as f:
            json.dump(custom_names, f, indent=2, ensure_ascii=False)
        return True
    except:
        return False


def save_custom_setup(custom_setup_pieces):
    """保存自定义摆棋设置到文件"""
    if not custom_setup_pieces:
        return
    if not os.path.exists(CUSTOM_SETUPS_DIR):
        os.makedirs(CUSTOM_SETUPS_DIR)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"custom_setup_{timestamp}.json"
    blue_pieces = {}
    red_pieces = {}
    for pos, (color, num) in custom_setup_pieces.items():
        if color == 'blue':
            blue_pieces[num] = list(pos)
        else:
            red_pieces[num] = list(pos)
    setup_data = {
        "setup_info": {
            "created_time": datetime.datetime.now().isoformat(),
            "type": "custom_setup",
            "blue_pieces_count": len(blue_pieces),
            "red_pieces_count": len(red_pieces)
        },
        "blue_pieces": blue_pieces,
        "red_pieces": red_pieces
    }
    try:
        with open(os.path.join(CUSTOM_SETUPS_DIR, filename), 'w', encoding='utf-8') as f:
            json.dump(setup_data, f, indent=2, ensure_ascii=False)
        print(f"Custom setup saved as {filename}")
    except Exception as e:
        print(f"Failed to save custom setup: {e}")