import json
import time
import os
from typing import Tuple, Optional, Dict, Any, Callable
from services import custom_setup


def load_levels_config() -> Optional[dict]:
    """加载关卡配置并返回配置字典"""
    try:
        with open('levels_config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading levels config: {e}")
        return None


def load_practice_progress() -> dict:
    """加载练习进度并返回字典。若不存在则创建默认进度。"""
    try:
        with open('practice_progress.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        practice_progress = {
            "player_progress": {
                "completed_levels": [],
                "current_level": 1,
                "total_levels": 5,
                "last_played": None
            },
            "level_records": {
                str(i): {
                    "completed": False,
                    "attempts": 0,
                    "best_moves": None,
                    "completion_time": None
                } for i in range(1, 6)
            }
        }
        save_practice_progress(practice_progress)
        return practice_progress


def save_practice_progress(practice_progress: dict) -> bool:
    """保存练习进度"""
    try:
        with open('practice_progress.json', 'w', encoding='utf-8') as f:
            json.dump(practice_progress, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving practice progress: {e}")
        return False


def reset_practice_progress() -> dict:
    """重置练习进度并保存，返回重置后的字典"""
    total_levels = load_levels_config()['total_levels']
    practice_progress = {
        "player_progress": {
            "completed_levels": [],
            "current_level": 1,
            "total_levels": total_levels,
            "last_played": None
        },
        "level_records": {
            str(i): {
                "completed": False,
                "attempts": 0,
                "best_moves": None,
                "completion_time": None
            } for i in range(1, total_levels + 1)
        }
    }
    save_practice_progress(practice_progress)
    print("Practice progress has been reset!")
    return practice_progress


def start_level(level_id: int,
                levels_config: dict,
                practice_progress: dict) -> Tuple[bool, Optional[Dict[int, Any]], Optional[Dict[int, Any]], Optional[Tuple[str, int]], dict, float, int, int]:
    """
    开始指定关卡。
    返回: (success, BLUE_PIECES, RED_PIECES, allowed_piece, updated_practice_progress, level_start_time, level_move_count, current_level)
    """
    if not levels_config or level_id > len(levels_config['levels']):
        return False, None, None, None, practice_progress, 0.0, 0, 0

    level_info = levels_config['levels'][level_id - 1]
    loaded_positions = custom_setup.load_custom_setup_file(level_info['file'])
    if not loaded_positions:
        return False, None, None, None, practice_progress, 0.0, 0, 0

    blue_pieces, red_pieces = loaded_positions

    target_piece = level_info['target_piece']
    allowed_piece = (target_piece['color'], target_piece['number'])

    # 更新尝试次数
    practice_progress['level_records'][str(level_id)]['attempts'] += 1
    save_practice_progress(practice_progress)

    return True, blue_pieces, red_pieces, allowed_piece, practice_progress, time.time(), 0, level_id


def check_level_victory(current_level: int,
                        levels_config: dict,
                        BLUE_PIECES: dict,
                        RED_PIECES: dict,
                        calculation_result: Any,
                        game_record: list,
                        point_map: Optional[dict],
                        get_numbers_func: Optional[Callable[[Tuple[int, int], Tuple[int, int], dict], list]] = None,
                        level_move_count: int = 0) -> bool:
    """检查关卡胜利条件"""
    if not levels_config or current_level > len(levels_config['levels']):
        return False

    level_info = levels_config['levels'][current_level - 1]
    win_condition = level_info['win_condition']
    
    # 检查步数限制（如果设置了max_moves）
    if 'max_moves' in level_info:
        if level_move_count > level_info['max_moves']:
            return False  # 超过最大步数，直接失败

    if win_condition['type'] == 'move_piece':
        piece_info = win_condition['piece']
        original_pos = win_condition['from']
        pieces = BLUE_PIECES if piece_info['color'] == 'blue' else RED_PIECES
        current_pos = pieces.get(piece_info['number'])
        return current_pos != original_pos

    elif win_condition['type'] == 'escape_encirclement':
        piece_info = win_condition['piece']
        pieces = BLUE_PIECES if piece_info['color'] == 'blue' else RED_PIECES
        current_pos = pieces.get(piece_info['number'])
        escape_area = win_condition['escape_area']
        return current_pos not in escape_area

    elif win_condition['type'] == 'position_and_calculation':
        piece_info = win_condition['piece']
        target_pos = win_condition['target_position']
        target_result = win_condition['calculation_result']
        pieces = BLUE_PIECES if piece_info['color'] == 'blue' else RED_PIECES
        current_pos = pieces.get(piece_info['number'])
        if current_pos != target_pos:
            return False
        if calculation_result is not None:
            return calculation_result == target_result
        else:
            if game_record and len(game_record) > 0 and get_numbers_func is not None and point_map is not None:
                last_move = game_record[-1]
                if (last_move['player'] == piece_info['color'] and
                    last_move['piece_number'] == piece_info['number']):
                    start_pos = (last_move['start_position']['col'], last_move['start_position']['row'])
                    end_pos = (last_move['end_position']['col'], last_move['end_position']['row'])
                    crossed_numbers = get_numbers_func(start_pos, end_pos, point_map)
                    return sum(crossed_numbers) == target_result
            return False

    elif win_condition['type'] == 'position_and_equal_paths':
        piece_info = win_condition['piece']
        target_pos = win_condition['target_position']
        pieces = BLUE_PIECES if piece_info['color'] == 'blue' else RED_PIECES
        current_pos = pieces.get(piece_info['number'])
        return current_pos == target_pos

    elif win_condition['type'] == 'position':
        piece_info = win_condition['piece']
        target_pos = win_condition['target_position']
        pieces = BLUE_PIECES if piece_info['color'] == 'blue' else RED_PIECES
        current_pos = pieces.get(piece_info['number'])
        return current_pos == target_pos

    return False


def complete_level(current_level: int,
                   level_start_time: float,
                   level_move_count: int,
                   practice_progress: dict) -> Tuple[bool, dict, str]:
    """
    完成关卡，返回 (success, updated_practice_progress, new_state)
    """
    if not current_level or not level_start_time:
        return False, practice_progress, "MENU"

    completion_time = time.time() - level_start_time
    level_record = practice_progress['level_records'][str(current_level)]
    level_record['completed'] = True
    level_record['completion_time'] = completion_time
    if level_record['best_moves'] is None or level_move_count < level_record['best_moves']:
        level_record['best_moves'] = level_move_count
    
    # 检查关卡是否已经完成过
    is_first_completion = current_level not in practice_progress['player_progress']['completed_levels']
    
    if is_first_completion:
        # 首次完成：添加到已完成列表，并更新当前关卡进度
        practice_progress['player_progress']['completed_levels'].append(current_level)
    if current_level < practice_progress['player_progress']['total_levels']:
        practice_progress['player_progress']['current_level'] = current_level + 1
    # 如果关卡已经完成过，再次完成时不更新current_level，只更新最佳步数和完成时间
    
    practice_progress['player_progress']['last_played'] = time.strftime('%Y-%m-%d %H:%M:%S')
    save_practice_progress(practice_progress)
    return True, practice_progress, "LEVEL_COMPLETE"