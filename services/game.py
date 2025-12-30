import os
import json
import datetime
from typing import Tuple, List, Dict, Any

# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME_RECORDS_DIR = os.path.join(BASE_DIR, 'game_records')


def get_game_info(filename: str) -> Tuple[int, str]:
    """读取棋谱文件信息并返回总步数与日期字符串"""
    try:
        with open(os.path.join(GAME_RECORDS_DIR, filename), 'r', encoding='utf-8') as f:
            data = json.load(f)
            game_info = data.get('game_info', {})
            total_moves = game_info.get('total_moves', 0)
            start_time = game_info.get('start_time', '')
            if start_time:
                try:
                    dt = datetime.datetime.fromisoformat(start_time)
                    date_str = f"{dt.year % 100}-{dt.month}-{dt.day}"
                except Exception:
                    date_str = "Unknown"
            else:
                date_str = "Unknown"
            return total_moves, date_str
    except Exception:
        return 0, "Unknown"


# save_custom_setup 已迁移到 services/custom_setup.py


def init_game_record(game_mode: str) -> Tuple[List[dict], Any, int]:
    """初始化游戏记录并根据模式返回初始状态"""
    game_record: List[dict] = []
    game_start_time = None
    move_count = 0
    if game_mode != 'practice':
        game_start_time = datetime.datetime.now()
        if not os.path.exists(GAME_RECORDS_DIR):
            os.makedirs(GAME_RECORDS_DIR)
    return game_record, game_start_time, move_count


def record_move(
    piece_info: Tuple[str, int, Any, Any],
    start_pos: Tuple[int, int],
    target_pos: Tuple[int, int],
    move_type: str,
    formula: Any,
    res: Any,
    *,
    game_mode: str,
    color_locked: bool,
    god_mode: bool,
    try_mode: bool,
    try_current_index: int,
    try_step: int,
    game_record: List[dict],
    move_count: int,
) -> Tuple[List[dict], int]:
    """根据当前状态记录一步棋并返回更新后的记录与步数"""
    if game_mode == 'practice':
        return game_record, move_count
    if color_locked or god_mode:
        return game_record, move_count
    move_count += 1
    color, piece_num, _, _ = piece_info
    move_record = {
        "move_number": move_count,
        "player": color,
        "piece_number": piece_num,
        "start_position": {"col": start_pos[0], "row": start_pos[1]},
        "end_position": {"col": target_pos[0], "row": target_pos[1]},
        "move_type": move_type,
        "timestamp": datetime.datetime.now().isoformat(),
        "paths": res,
    }
    if formula:
        move_record["formula"] = formula
    if try_mode:
        move_record["context"] = "try"
        move_record["try_step_index"] = try_current_index + 1
        move_record["try_step_total"] = try_step + 1
    game_record.append(move_record)
    return game_record, move_count