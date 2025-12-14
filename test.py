import dis
from typing import Any
import pygame
import sys
import math
import json
import datetime
import os
import time
from services import custom_setup
from services import practice as practice_service
from services import game as game_service
from services import netplay as netplay
pygame.init()

# 修改窗口大小以适应计算版区域和上方算式区域

state = "MENU" # 状态机： MENU, GAME, SPLASH, END
god_mode = False  # 新增：上帝模式开关
winner = None

# 菜单相关变量
menu_selected = None  # 当前选中的菜单项
menu_hovered = None   # 当前鼠标悬停的菜单项
game_mode = None      # 游戏模式：'play', 'replay', 'practice'
selected_custom_file = None  # 选中的自定义棋谱文件

# Replay功能相关变量
replay_files = []     # 可用的回放文件列表
replay_page = 0       # 当前回放列表页码
selected_replay_file = None  # 选中的回放文件
replay_data = None    # 回放数据
replay_step = 0       # 当前回放步数
replay_max_steps = 0  # 最大步数
replay_playing = False # 是否正在自动播放
replay_speed = 1.0    # 播放速度
replay_last_update = 0 # 上次更新时间
replay_pieces_blue = {} # 回放中的蓝色棋子位置
replay_pieces_red = {}  # 回放中的红色棋子位置
replay_current_move = None # 当前移动信息
replay_path_points = [] # 当前移动路径上的点
replay_intermediate_points = []  # 记录连跳时的中间点（新起点）

# 试下功能相关变量
try_mode = False      # 是否处于试下模式
try_move_stack = []   # 试下移动栈，记录每步移动 []{"piece": (color, num), "from": (col, row), "to": (col, row)}]
try_original_blue = {} # 试下前的蓝色棋子位置备份
try_original_red = {}  # 试下前的红色棋子位置备份
try_current_player = 'blue'  # 试下模式下的当前玩家
try_step = 0        # 试下模式下的当前步数
try_current_index = 0  # 试下模式下当前查看的步数索引

# 自定义棋谱名称相关变量
custom_names = {}  # 存储自定义棋谱名称
renaming_file = None  # 当前正在重命名的文件
rename_input = ""  # 重命名输入文本
deleting_file = None # 当前正在确认删除的文件

# 自定义摆棋相关变量
custom_setup_pieces = {}  # 存储自定义摆棋位置 {(col, row): (color, num)}
available_pieces = {'blue': [True] * 10, 'red': [True] * 10}  # 可用棋子
dragging_piece = None  # 正在拖拽的棋子 (color, num)
drag_offset = (0, 0)  # 拖拽偏移量

# 记谱功能相关变量
game_record = []  # 存储游戏记录
game_start_time = None  # 游戏开始时间
move_count = 0  # 移动计数

# 关卡系统相关变量
current_level = None  # 当前关卡ID
levels_config = None  # 关卡配置
practice_progress = None  # 练习进度
level_start_time = None  # 关卡开始时间
level_move_count = 0  # 关卡移动计数
allowed_piece = None  # 允许移动的棋子 (color, number)
hint_box_dragging = False  # 提示框是否正在拖动
hint_box_offset = (0, 0)   # 拖动偏移量
hint_box_pos = (None, None)  # 提示框位置
hint_box_rect = None       # 提示框矩形区域
window_size = 700  # 棋盘大小
OFFSET_X = 200     # 右侧计算版宽度
OFFSET_Y = 100     # 上方算式区域高度 
window = pygame.display.set_mode((window_size + OFFSET_X, window_size + OFFSET_Y))
pygame.display.set_caption('国际数棋棋盘')

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 100, 255)
YELLOW = (255, 215, 0)
LIGHT_YELLOW = (255, 255, 153)
BACKGROUND = (240, 240, 240)
HIGHLIGHT = (0, 255, 0)
SELECT = (255, 100, 100)
GRAY = (150, 150, 150)  # 添加灰色常量用于标记备选跨越点
LIGHT_GRAY = (220, 220, 220)  # 计算版背景色
LIGHT_BLUE = (173, 216, 230)  # 新增浅蓝色作为上方算式区域背景色
PURPLE = (128, 0, 128)  

# 上方算式区域常量
FORMULA_AREA_HEIGHT = OFFSET_Y
FORMULA_AREA_WIDTH = window_size + OFFSET_X
FORMULA_AREA_X = 0
FORMULA_AREA_Y = 0

# 调整中心点位置，考虑上方偏移
CENTER_X = window_size // 2   # 错误：不应该加上OFFSET_Y
CENTER_Y = window_size // 2 + OFFSET_Y # 调整中心点Y坐标，考虑上方偏移
RADIUS = 20  # 圆点半径
GRID = 50    # 点间距
BEGIN_X = CENTER_X - GRID * 5
BEGIN_Y = CENTER_Y - GRID * 6

# 计算版区域常量
CALC_AREA_WIDTH = 200
CALC_AREA_X = 700
CALC_AREA_Y = OFFSET_Y  # 调整计算版起始Y坐标，考虑上方偏移
CALC_AREA_HEIGHT = 700

# 计算版状态变量
selected_numbers = []  # 存储选中的数字
paths = []
number_res = []
formula_res = []
calculation_result = None  # 计算结果
operation = None  # 当前选择的运算符
formula_text = ""  # 新增：存储算式文本
hovered_button = None  # 新增：当前鼠标悬停的按钮

# 局域网联机相关变量
net_session = None  # 当前网络会话对象（NetSession）
local_side = None   # 本地执子颜色 'blue' 或 'red'
processing_remote_move = False  # 标记当前是否在应用对方走子，避免回传循环

# 六个方向的向量（60度间隔）
DIRECTIONS = [(GRID, 0), (-GRID, 0),
              (GRID/2, GRID*math.sqrt(3)/2), (-GRID/2, GRID*math.sqrt(3)/2),
              (GRID/2, -GRID*math.sqrt(3)/2), (-GRID/2, -GRID*math.sqrt(3)/2)]

# 每列的点数和位置 [点数, 偏移]
POINTS = [[1, 10], [2, 9], [3, 8], [4, 7], [11, 0],
          [10, 1], [9, 2], [8, 3], [9, 2], [10, 1],
          [11, 0], [4, 7], [3, 8], [2, 9], [1, 10]]

# 定义蓝色棋子位置和数字
RED_PIECES = {
    0: [0, 10],    # 第1列第1个点
    1: [3, 7],    # 第4列第1个点
    2: [3, 11],    # 第4列第3个点
    3: [3, 9],    # 第4列第2个点
    4: [3, 13],    # 第4列第4个点
    5: [2, 12],    # 第3列第3个点
    6: [2, 10],    # 第3列第2个点
    7: [2, 8],    # 第3列第1个点
    8: [1, 9],    # 第2列第1个点
    9: [1, 11]     # 第2列第2个点
}

# 定义红色棋子位置和数字
BLUE_PIECES = {
    0: [14, 10],    # 第15列第1个点
    1: [11, 13],    # 第12列第4个点
    2: [11, 9],    # 第12列第2个点
    3: [11, 11],    # 第12列第3个点
    4: [11, 7],    # 第12列第1个点
    5: [12, 8],     # 第13列第1个点
    6: [12, 10],    # 第13列第2个点
    7: [12, 12],    # 第13列第3个点
    8: [13, 11],    # 第14列第2个点
    9: [13, 9]     # 第14列第1个点
}

# 定义固定的初始位置常量（用于回放）
BLUE_PIECES_INITIAL = {
    0: [14, 10],    # 第15列第1个点
    1: [11, 13],    # 第12列第4个点
    2: [11, 9],     # 第12列第2个点
    3: [11, 11],    # 第12列第3个点
    4: [11, 7],     # 第12列第1个点
    5: [12, 8],     # 第13列第1个点
    6: [12, 10],    # 第13列第2个点
    7: [12, 12],    # 第13列第3个点
    8: [13, 11],    # 第14列第2个点
    9: [13, 9]      # 第14列第1个点
}

RED_PIECES_INITIAL = {
    0: [0, 10],     # 第1列第1个点
    1: [3, 7],      # 第4列第1个点
    2: [3, 11],     # 第4列第3个点
    3: [3, 9],      # 第4列第2个点
    4: [3, 13],     # 第4列第4个点
    5: [2, 12],     # 第3列第3个点
    6: [2, 10],     # 第3列第2个点
    7: [2, 8],      # 第3列第1个点
    8: [1, 9],      # 第2列第1个点
    9: [1, 11]      # 第2列第2个点
}

SCORING_MAP = {
    'red': {
        (14, 10): 0,
        (11, 13): 1,
        (11, 9): 2,
        (11, 11): 3,
        (11, 7): 4,
        (12, 8): 5,
        (12, 10): 6,
        (12, 12): 7,
        (13, 11): 8,
        (13, 9): 9,
    },

    'blue': {
        (0, 10): 0,
        (3, 7): 1,
        (3, 11): 2,
        (3, 9): 3,
        (3, 13): 4,
        (2, 12): 5,
        (2, 10): 6,
        (2, 8): 7,
        (1, 9): 8,
        (1, 11): 9,
    }
}

# 定义蓝色和红色初始点（用于计分）
BLUE_START_POS = list(BLUE_PIECES.values())  # 蓝色初始点坐标
RED_START_POS = list(RED_PIECES.values())    # 红色初始点坐标

# 游戏状态变量
selected_piece = None  # 当前选中的棋子
expected_result = None
valid_moves = []       # 当前选中棋子的有效移动位置
current_player = 'blue'  # 当前玩家，蓝色先走
board_locked = False   # 棋盘锁定状态
continuous_span = False  # 连续跨越状态
selected_gray_point = None  # 选中的灰色点
color_locked = False   # 颜色锁定状态，锁定后不切换玩家颜色
continuous_span_line = -1

def set_default_positions():
    global BLUE_PIECES, RED_PIECES, current_player
    BLUE_PIECES = {
        0: [14, 10],
        1: [11, 13],
        2: [11, 9],
        3: [11, 11],
        4: [11, 7],
        5: [12, 8],
        6: [12, 10],
        7: [12, 12],
        8: [13, 11],
        9: [13, 9]
    }
    RED_PIECES = {
        0: [0, 10],
        1: [3, 7],
        2: [3, 11],
        3: [3, 9],
        4: [3, 13],
        5: [2, 12],
        6: [2, 10],
        7: [2, 8],
        8: [1, 9],
        9: [1, 11]
    }
    current_player = 'blue'

# 记谱功能相关变量
game_record = []  # 存储游戏记录
game_start_time = None  # 游戏开始时间
move_count = 0  # 移动计数
def load_levels_config():
    """加载关卡配置（委托到services.practice）"""
    global levels_config
    cfg = practice_service.load_levels_config()
    if cfg is not None:
        levels_config = cfg
        return True
    return False


def load_practice_progress():
    """加载练习进度（委托到services.practice）"""
    global practice_progress
    practice_progress = practice_service.load_practice_progress()
    return True


def save_practice_progress():
    """保存练习进度（委托到services.practice）"""
    return practice_service.save_practice_progress(practice_progress)


def reset_practice_progress():
    """重置练习进度（委托到services.practice）"""
    global practice_progress
    practice_progress = practice_service.reset_practice_progress()


def start_level(level_id):
    """开始指定关卡（委托到services.practice）"""
    global current_level, level_start_time, level_move_count, allowed_piece, BLUE_PIECES, RED_PIECES, practice_progress
    success, blue_p, red_p, allowed, prog, start_t, move_cnt, cur_lvl = practice_service.start_level(
        level_id, levels_config, practice_progress
    )
    if success:
        BLUE_PIECES = blue_p
        RED_PIECES = red_p
        allowed_piece = allowed
        practice_progress = prog
        level_start_time = start_t
        level_move_count = move_cnt
        current_level = cur_lvl
        return True
    return False


def check_level_victory():
    """检查关卡胜利条件（委托到services.practice）"""
    pm = globals().get('point_map')
    return practice_service.check_level_victory(
        current_level,
        levels_config,
        BLUE_PIECES,
        RED_PIECES,
        calculation_result,
        game_record,
        pm,
        get_numbers,
    )


def complete_level():
    """完成关卡（委托到services.practice）"""
    global practice_progress, state
    success, prog, new_state = practice_service.complete_level(
        current_level, level_start_time, level_move_count, practice_progress
    )
    if success:
        practice_progress = prog
        state = new_state
        return True
    return False


def can_move_piece(piece_color, piece_number):
    """检查是否可以移动指定棋子"""
    if game_mode != 'practice' or not allowed_piece:
        return True  # 非练习模式或未设置限制时允许移动
    
    return (piece_color, piece_number) == allowed_piece


# 已迁移到 services/custom_setup.py


def get_display_name(filename, index):
    """获取棋谱的显示名称"""
    if filename in custom_names and custom_names[filename].strip():
        return custom_names[filename]
    else:
        return f"Record{index + 1}"


def get_game_info(filename):
    """获取棋谱的步数和时间信息（委托到services.game）"""
    return game_service.get_game_info(filename)


def save_custom_setup():
    """保存自定义棋谱设置（委托到services.custom_setup）"""
    return custom_setup.save_custom_setup(custom_setup_pieces)


def init_game_record():
    """初始化游戏记录（委托到services.game）"""
    global game_record, game_start_time, move_count
    game_record, game_start_time, move_count = game_service.init_game_record(game_mode)


def record_move(piece_info, start_pos, target_pos, move_type, formula=None, res=None):
    """记录一步棋（委托到services.game）"""
    global game_record, move_count, try_mode, try_current_index, try_step
    game_record, move_count = game_service.record_move(
        piece_info, start_pos, target_pos, move_type, formula, res,
        game_mode=game_mode,
        color_locked=color_locked,
        god_mode=god_mode,
        try_mode=try_mode,
        try_current_index=try_current_index,
        try_step=try_step,
        game_record=game_record,
        move_count=move_count,
    )


def save_game_record():
    """保存游戏记录到文件"""
    global game_record, game_start_time
    
    # 仅在正式对局模式下保存，试下模式或回放模式下不保存
    if game_mode != 'play' or try_mode:
        return
    
    if not game_record or not game_start_time:
        return
    
    # 生成文件名：游戏开始时间
    filename = game_start_time.strftime("%Y%m%d_%H%M%S") + ".json"
    filepath = os.path.join('game_records', filename)
    
    # 创建完整的游戏记录
    full_record = {
        "game_info": {
            "start_time": game_start_time.isoformat(),
            "end_time": datetime.datetime.now().isoformat(),
            "total_moves": len(game_record),
            "winner": winner if winner else None
        },
        "moves": game_record
    }
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(full_record, f, indent=2, ensure_ascii=False)
        print(f"Game record saved to: {filepath}")
    except Exception as e:
        print(f"Error saving game record: {e}")
        

def load_replay_file(filename):
    """加载回放文件"""
    global replay_data, replay_max_steps, replay_step, replay_pieces_blue, replay_pieces_red
    try:
        with open(os.path.join('game_records', filename), 'r') as f:
            replay_data = json.load(f)
        replay_max_steps = len(replay_data.get('moves', []))
        replay_step = 0
        
        # 使用固定的初始位置而不是当前的BLUE_PIECES和RED_PIECES
        replay_pieces_blue = {k: v.copy() for k, v in BLUE_PIECES_INITIAL.items()}
        replay_pieces_red = {k: v.copy() for k, v in RED_PIECES_INITIAL.items()}
        
        return True
    except Exception as e:
        print(f"Error loading replay file: {e}")
        return False


def update_replay_positions():
    """根据当前回放步数更新棋子位置，并在非试下模式下同步到正常棋子集合和selected_piece"""
    global replay_pieces_blue, replay_pieces_red, replay_current_move, replay_path_points, replay_intermediate_points
    global BLUE_PIECES, RED_PIECES, game_mode, try_mode, selected_piece
    
    if not replay_data or replay_step < 0:
        return
    
    # 重置棋子位置到固定的初始状态
    replay_pieces_blue = {k: v.copy() for k, v in BLUE_PIECES_INITIAL.items()}
    replay_pieces_red = {k: v.copy() for k, v in RED_PIECES_INITIAL.items()}
    replay_current_move = None
    replay_path_points = []
    replay_intermediate_points = []  # 重置中间点列表
    
    # 应用所有步骤直到当前步数
    moves = replay_data.get('moves', [])
    for i in range(min(replay_step, len(moves))):
        move = moves[i]
        player = move['player']
        piece_num = move['piece_number']
        end_pos = [move['end_position']['col'], move['end_position']['row']]
        
        if player == 'blue':
            replay_pieces_blue[piece_num] = end_pos
        else:
            replay_pieces_red[piece_num] = end_pos
    
    # 如果当前步数有效，设置当前移动信息（显示刚完成的移动）
    if replay_step > 0 and replay_step <= len(moves):
        replay_current_move = moves[replay_step - 1]
        start_pos = (replay_current_move['start_position']['col'], replay_current_move['start_position']['row'])
        end_pos = (replay_current_move['end_position']['col'], replay_current_move['end_position']['row'])
        
        # 初始化路径点
        replay_path_points = [start_pos, end_pos]
        
        # 处理paths信息，推测跨越路径
        if 'paths' in replay_current_move and replay_current_move['paths']:
            # 获取当前棋盘上所有有效点的映射
            # 临时生成point_map用于路径计算
            temp_point_map = {}
            for col_index, [num, offset] in enumerate(POINTS):
                y = BEGIN_Y + col_index * GRID * math.sqrt(3) / 2
                for i in range(num):
                    raw_index = offset + i * 2
                    x = BEGIN_X + raw_index * GRID * 0.5
                    temp_point_map[(col_index, raw_index)] = (x, y)
            point_map = temp_point_map
            
            # 当前位置，从起始点开始
            current_pos = start_pos
            
            # 遍历每一条path
            for path_group in replay_current_move['paths']:
                if isinstance(path_group, list) and len(path_group) >= 3:
                    # 忽略负数点，只处理正数
                    valid_pieces = []
                    for i in range(len(path_group)):
                        if path_group[i] > 0:  # 只处理正数
                            valid_pieces.append(path_group[i])
                    
                    if len(valid_pieces) >= 2:
                        # 找到包含这些棋子编号的路径
                        piece1, piece2 = valid_pieces[0], valid_pieces[1]
                        
                        # 在当前位置找到包含piece1和piece2的同一行路径
                        left_diag, right_diag, horizontal = get_line_coordinates(current_pos[0], current_pos[1], point_map)
                        
                        # 合并所有可能的路径
                        all_lines = [left_diag, right_diag, horizontal]
                        
                        target_path = None
                        piece1_pos = None
                        piece2_pos = None
                        
                        # 查找包含piece1和piece2的路径
                        for line in all_lines:
                            # 在这条线上查找piece1和piece2的位置
                            found_pieces = []
                            for pos in line:
                                # 检查这个位置是否有我们要找的棋子
                                for player_pieces in [replay_pieces_blue, replay_pieces_red]:
                                    for num, piece_pos in player_pieces.items():
                                        if (piece_pos[0], piece_pos[1]) == pos:
                                            if num == piece1:
                                                piece1_pos = pos
                                                found_pieces.append((num, pos))
                                            elif num == piece2:
                                                piece2_pos = pos
                                                found_pieces.append((num, pos))
                            
                            # 如果在这条线上找到了两个棋子，确定路径
                            if len(found_pieces) >= 2 and piece1_pos and piece2_pos:
                                target_path = line
                                break
                        
                        if target_path and piece1_pos and piece2_pos:
                            # 标记piece1和piece2的位置（跨越的棋子）
                            replay_path_points.append(piece1_pos)
                            replay_path_points.append(piece2_pos)
                            
                            # 找到piece1和piece2在路径中的索引
                            try:
                                piece1_idx = target_path.index(piece1_pos)
                                piece2_idx = target_path.index(piece2_pos)
                                
                                # 确定方向（从piece1到piece2）
                                if piece1_idx < piece2_idx:
                                    # 正向，找piece2的下一个点
                                    if piece2_idx + 1 < len(target_path):
                                        next_pos = target_path[piece2_idx + 1]
                                        # 记录这个中间点（新起点）
                                        replay_intermediate_points.append(next_pos)
                                        current_pos = next_pos  # 更新当前位置为下一个起点
                                else:
                                    # 反向，找piece2的上一个点
                                    if piece2_idx - 1 >= 0:
                                        next_pos = target_path[piece2_idx - 1]
                                        # 记录这个中间点（新起点）
                                        replay_intermediate_points.append(next_pos)
                                        current_pos = next_pos  # 更新当前位置为下一个起点
                            except ValueError:
                                # 如果找不到索引，继续下一个path
                                continue
        else:
            # 对于没有paths信息的单跨，需要推断被跨越的棋子
            # 获取当前棋盘上所有有效点的映射
            temp_point_map = {}
            for col_index, [num, offset] in enumerate(POINTS):
                y = BEGIN_Y + col_index * GRID * math.sqrt(3) / 2
                for i in range(num):
                    raw_index = offset + i * 2
                    x = BEGIN_X + raw_index * GRID * 0.5
                    temp_point_map[(col_index, raw_index)] = (x, y)
            
            # 使用get_line_coordinates找到起点和终点之间的所有点
            left_diag, right_diag, horizontal = get_line_coordinates(start_pos[0], start_pos[1], temp_point_map)
            
            # 检查哪条线包含终点
            target_line = None
            if end_pos in left_diag:
                target_line = left_diag
            elif end_pos in right_diag:
                target_line = right_diag
            elif end_pos in horizontal:
                target_line = horizontal
            
            if target_line:
                start_idx = target_line.index(start_pos)
                end_idx = target_line.index(end_pos)
                
                # 获取起点和终点之间的所有点（被跨越的棋子位置）
                min_idx = min(start_idx, end_idx)
                max_idx = max(start_idx, end_idx)
                
                for i in range(min_idx + 1, max_idx):
                    crossed_pos = target_line[i]
                    # 检查这个位置是否有棋子
                    has_piece = False
                    for player_pieces in [replay_pieces_blue, replay_pieces_red]:
                        for piece_pos in player_pieces.values():
                            if (piece_pos[0], piece_pos[1]) == crossed_pos:
                                has_piece = True
                                break
                        if has_piece:
                            break
                    
                    if has_piece:
                        replay_path_points.append(crossed_pos)
    else:
        replay_current_move = None
        replay_path_points = []
        replay_intermediate_points = []

    # 在回放模式且不处于试下模式时，同步 selected_piece 为当前步的终点棋子，或在没有步数时清空
    if game_mode == 'replay' and not try_mode:
        if replay_current_move:
            piece_color = replay_current_move['player']
            piece_num = replay_current_move['piece_number']
            end_col = replay_current_move['end_position']['col']
            end_row = replay_current_move['end_position']['row']
            x = BEGIN_X + end_row * GRID * 0.5
            y = BEGIN_Y + end_col * GRID * math.sqrt(3) / 2
            selected_piece = (piece_color, piece_num, (end_col, end_row), (x, y))

    # 在回放模式且不处于试下模式时，将回放棋子位置同步到正常棋子集合，确保draw_board统一逻辑显示正确位置
    if game_mode == 'replay' and not try_mode:
        BLUE_PIECES = {k: v.copy() for k, v in replay_pieces_blue.items()}
        RED_PIECES = {k: v.copy() for k, v in replay_pieces_red.items()}


def enter_try_mode():
    """进入试下模式"""
    global try_mode, try_move_stack, try_original_blue, try_original_red, try_current_player, try_step, try_current_index, current_player, selected_piece, valid_moves, board_locked, BLUE_PIECES, RED_PIECES, formula_text, try_record_start_index, game_record
    
    # 只有在回放模式且不在试下模式时才能进入
    if game_mode != 'replay' or try_mode:
        return
    
    board_locked = False
    try_mode = True
    try_move_stack = []
    try_step = 0
    try_current_index = 0
    formula_text = "" 
    # 记录开启试下时的记谱起始位置，便于撤回时同步
    try_record_start_index = len(game_record)
    
    # 备份当前棋子位置（以回放当前局面为起点）
    try_original_blue = {k: v.copy() for k, v in replay_pieces_blue.items()}
    try_original_red = {k: v.copy() for k, v in replay_pieces_red.items()}

    # 将当前局面同步到正常棋子集合，统一绘制与选择逻辑
    BLUE_PIECES = {k: v.copy() for k, v in replay_pieces_blue.items()}
    RED_PIECES = {k: v.copy() for k, v in replay_pieces_red.items()}

    # 进入试下后取消当前选中并清空可走点
    selected_piece = None
    valid_moves = []

    # 设置当前玩家
    # 根据回放的最后一步决定下一个玩家
    if replay_step > 0 and replay_step <= len(replay_data.get('moves', [])):
        last_move = replay_data['moves'][replay_step - 1]
        try_current_player = 'red' if last_move['player'] == 'blue' else 'blue'
    else:
        try_current_player = 'blue'  # 默认蓝方先行
    # 同步正常逻辑的当前玩家，确保后续沿用同一套移动逻辑
    current_player = try_current_player


def exit_try_mode():
    """退出试下模式，恢复到原始状态"""
    global try_mode, try_move_stack, replay_pieces_blue, replay_pieces_red, try_current_player
    global try_original_blue, try_original_red, selected_piece, valid_moves, BLUE_PIECES, RED_PIECES
    
    if not try_mode:
        return
    
    try_mode = False
    try_move_stack = []
    
    # 恢复原始棋子位置
    replay_pieces_blue = {k: v.copy() for k, v in try_original_blue.items()}
    replay_pieces_red = {k: v.copy() for k, v in try_original_red.items()}
    # 同步到正常棋子集合，恢复到开启试下之前的显示与交互状态
    BLUE_PIECES = {k: v.copy() for k, v in replay_pieces_blue.items()}
    RED_PIECES = {k: v.copy() for k, v in replay_pieces_red.items()}
    
    # 重置试下相关变量
    try_current_player = 'blue'  # 默认蓝方先行
    
    # 清除选中状态
    selected_piece = None
    valid_moves = []


def undo_try_move():
    """撤销试下模式中的最后一步移动"""
    global try_mode, try_move_stack, BLUE_PIECES, RED_PIECES, try_current_player, try_step, try_current_index, current_player, game_record, move_count, try_record_start_index
    
    if not try_mode or not try_move_stack or try_current_index <= 0:
        return
    
    # 更新当前索引
    try_current_index -= 1
    
    # 获取要撤销的移动
    move_to_undo = try_move_stack[try_current_index]
    
    # 恢复棋子位置
    piece_color = move_to_undo["piece"][0]
    piece_num = move_to_undo["piece"][1]
    from_pos = move_to_undo["from"]
    
    if piece_color == 'blue':
        BLUE_PIECES[piece_num] = list(from_pos)
    else:
        RED_PIECES[piece_num] = list(from_pos)
    
    # 切换当前玩家（与正常逻辑保持一致）
    try_current_player = piece_color
    current_player = piece_color

    # 同步删除最后一条记录（仅在试下期间新增的记录范围内）
    if len(game_record) > try_record_start_index:
        # 删除最后一条并回退步数计数
        game_record.pop()
        if move_count > 0:
            move_count -= 1

def get_line_coordinates(col, row, point_map):
    """
    获取指定点所在的横行、左斜行、右斜行的所有有效点坐标
    
    斜行判定规则：
    - 右斜行：(a, b), (a-1, b-1), (a+1, b+1) 在同一行 (col - row = 常数)
    - 左斜行：(a, b), (a+1, b-1), (a-1, b+1) 在同一行 (col + row = 常数)
    
    参数:
        col: 列坐标 (0-14)
        row: 行坐标
        point_map: 包含所有有效点坐标的字典或可迭代对象
    
    返回:
        tuple: (left_diagonal, right_diagonal, horizontal_line)
        - left_diagonal: 左斜行坐标列表 [(col, row), ...]
        - right_diagonal: 右斜行坐标列表 [(col, row), ...]
        - horizontal_line: 横行坐标列表 [(col, row), ...]
    """
    
    # 获取横行坐标（相同列的所有点）
    horizontal_line = []
    for pos in point_map:
        if pos[0] == col:  # 相同列
            horizontal_line.append(pos)
    
    # 获取右斜行坐标（col - row = 常数）
    # 右斜行：(a, b), (a-1, b-1), (a+1, b+1) 都满足 col - row = 常数
    right_diagonal = []
    target_right_diff = col - row
    for pos in point_map:
        if pos[0] - pos[1] == target_right_diff:
            right_diagonal.append(pos)
    
    # 获取左斜行坐标（col + row = 常数）
    # 左斜行：(a, b), (a+1, b-1), (a-1, b+1) 都满足 col + row = 常数
    left_diagonal = []
    target_left_sum = col + row
    for pos in point_map:
        if pos[0] + pos[1] == target_left_sum:
            left_diagonal.append(pos)
    
    # 按坐标排序
    horizontal_line.sort(key=lambda x: x[1])  # 按行排序
    right_diagonal.sort(key=lambda x: (x[0], x[1]))  # 按列再按行排序
    left_diagonal.sort(key=lambda x: (x[0], x[1]))   # 按列再按行排序
    
    return left_diagonal, right_diagonal, horizontal_line


def check_win():
    red_wins = True
    blue_wins = True
    for num, (col, row) in RED_PIECES.items():
        if not (11 <= col <= 14):
            red_wins = False
            break
    if red_wins:
        return 'red'

    for num, (col, row) in BLUE_PIECES.items():
        if not (0 <= col <= 3):
            blue_wins = False
            break
    if blue_wins:
        return 'blue' 
    return None


def calculate_point():
    red_points = 0
    blue_points = 0
    for num, (col, row) in RED_PIECES.items():
        if (11 <= col <= 14):
            red_points += num * SCORING_MAP['red'][(col, row)]
    for num, (col, row) in BLUE_PIECES.items():
        if (0 <= col <= 3):
            blue_points += num * SCORING_MAP['blue'][(col, row)]
    return red_points, blue_points


def get_direction(pos1, pos2):
    """
    计算两个点之间的方向向量
    """
    x1, y1 = pos1
    x2, y2 = pos2
    dx = x2 - x1
    dy = y2 - y1
    length = math.sqrt(dx**2 + dy**2)
    if length == 0:
        return 0, 0  # 避免除以零
    # print(round(dx / length * 100), round(dy / length * 100))
    return round(dx / length * 100), round(dy / length * 100)


def in_opposite_direction(pos1, pos2, same_dir=False):
    x1, y1 = pos1
    x2, y2 = pos2
    x2 *= -1
    y2 *= -1
    if x1 == x2 and y1 == y2:
        return True  
    if same_dir and x1 == -x2 and y1 == -y2:
        return True
    return False


def xy_to_pos(x, y):
    # 根据实际的坐标生成逻辑进行反向计算
    # y = BEGIN_Y + col_index * GRID * math.sqrt(3) / 2
    # x = BEGIN_X + raw_index * GRID * 0.5
    
    # 计算列索引 (col_index)
    col_index = round((y - BEGIN_Y) / (GRID * math.sqrt(3) / 2))
    
    # 确保列索引在有效范围内
    if col_index < 0 or col_index >= len(POINTS):
        return None, None
    
    # 计算原始索引 (raw_index)
    raw_index = round((x - BEGIN_X) / (GRID * 0.5))
    
    return col_index, raw_index


def is_valid_formula(formula):
    """
    检测算式是否合法：
    1. 不能在没有左括号的时候出现右括号
    2. 加减乘除符号不能连续出现
    3. 数字不能连续出现（不能有两位数）
    4. 左括号后不能出现运算符
    5. 右括号前不能出现运算符
    6. 左右括号内必须有算式
    7. 数字后面不能直接接左括号
    """
    # 检查括号匹配
    left_bracket_count = 0
    
    # 记录前一个字符，用于检查连续性
    prev_char = None
    
    # 记录括号位置，用于检查括号内是否有算式
    bracket_positions = []

    if len(formula) == 0:
        return False, "算式不能为空"
    
    if formula[0] in '+-×÷':
        return False, "算式不能以运算符开头"
    
    for i, char in enumerate(formula):
        # 检查括号匹配
        if char == '(':
            left_bracket_count += 1
            bracket_positions.append(i)  # 记录左括号位置
            # 检查左括号后是否紧跟运算符
            if i + 1 < len(formula) and formula[i+1] in '+-×÷':
                return False, "左括号后不能直接跟运算符"
        elif char == ')':
            left_bracket_count -= 1
            # 如果右括号数量大于左括号，则不合法
            if left_bracket_count < 0:
                return False, "右括号数量大于左括号"
            # 检查右括号前是否是运算符
            if prev_char in '+-×÷':
                return False, "右括号前不能是运算符"
            
            # 检查左右括号内是否有算式
            if bracket_positions and i - bracket_positions[-1] <= 1:
                return False, "左右括号内必须有算式"
            bracket_positions.pop()  # 移除匹配的左括号位置
        
        # 检查运算符是否连续
        if char in '+-×÷':
            if prev_char in '+-×÷':
                return False, "运算符不能连续出现"
        
        # 检查数字是否连续
        if char.isdigit() and prev_char is not None and prev_char.isdigit():
            return False, "数字不能连续出现"
        
        # 检查数字后面是否直接接左括号
        if char == '(' and prev_char is not None and prev_char.isdigit():
            return False, "数字后面不能直接接左括号"
        
        # 更新前一个字符
        prev_char = char
    
    return True, "算式合法"


def get_point_color(x, y, col_index, point_index, point_map):
    """根据点的位置确定颜色"""
    # Get the number of points in this column
    col_length = point_map  # This is actually POINTS[col_index][0] from the calling code
    
    # 前四列为蓝色
    if col_index < 4:
        return RED
    # 最后四列为红色
    elif col_index >= 11:
        return BLUE
    # 第五列最上方和最下方为蓝色
    elif col_index == 4 and (point_index == 0 or point_index == col_length - 1):
        return RED
    # 倒数第五列最上方和最下方为红色
    elif col_index == 10 and (point_index == 0 or point_index == col_length - 1):
        return BLUE
    # 第八列最上和最下为特殊处理（双色）
    elif col_index == 7 and (point_index == 0 or point_index == col_length - 1):
        return "DUAL"  # 返回特殊标记，表示这是双色点
    # 其他区域为黄色
    else:
        return YELLOW


def get_neighbors(x, y, all_points):
    """获取一个点的所有相邻点"""
    neighbors = []
    # 检查六个方向
    for dx, dy in DIRECTIONS:
        neighbor_x = x + dx
        neighbor_y = y + dy
        # 检查是否在所有点列表中
        for point in all_points:
            if abs(point[0] - neighbor_x) < 5 and abs(point[1] - neighbor_y) < 5:
                neighbors.append(point)
                break
    return neighbors


def get_numbers(start, end, point_map):
    """
    使用col,row坐标方式获取start和end之间的棋子数字
    调用get_line_coordinates函数读取中间坐标存在的数据
    """
    numbers = []
    start_col, start_row = start
    end_col, end_row = end
    
    # 使用get_line_coordinates获取start点所在的三个方向的坐标
    left_diagonal, right_diagonal, horizontal_line = get_line_coordinates(start_col, start_row, point_map)
    
    # 检查end点在哪个方向上
    line_coords = None
    if (end_col, end_row) in horizontal_line:
        line_coords = horizontal_line
    elif (end_col, end_row) in left_diagonal:
        line_coords = left_diagonal
    elif (end_col, end_row) in right_diagonal:
        line_coords = right_diagonal
    
    if line_coords is None:
        return numbers  # start和end不在同一条线上
    
    # 找到start和end在line_coords中的索引
    try:
        start_idx = line_coords.index((start_col, start_row))
        end_idx = line_coords.index((end_col, end_row))
    except ValueError:
        return numbers  # start或end不在线上
    
    # 确保start_idx < end_idx
    if start_idx > end_idx:
        start_idx, end_idx = end_idx, start_idx
    
    # 获取start和end之间的中间坐标（不包括start和end本身）
    middle_coords = line_coords[start_idx + 1:end_idx]
    
    # 按照路径顺序检查中间坐标是否有棋子
    for coord in middle_coords:
        # 检查蓝色棋子
        for piece_num, piece_pos in BLUE_PIECES.items():
            if tuple(piece_pos) == coord:
                numbers.append(piece_num)
                break
        else:
            # 检查红色棋子
            for piece_num, piece_pos in RED_PIECES.items():
                if tuple(piece_pos) == coord:
                    numbers.append(piece_num)
                    break
    
    #if game_mode == 'practice' and numbers:
    #    print(f"跨越路径: {start} -> {end}, 跨越的数字: {numbers}")
    
    return numbers


def draw_dashed_line(surface, color, start_pos, end_pos, width=3, dash_length=10, gap_length=10):
    """绘制虚线"""
    x1, y1 = start_pos
    x2, y2 = end_pos
    dx = x2 - x1
    dy = y2 - y1
    distance = math.sqrt(dx * dx + dy * dy)
    dashes = int(distance / (dash_length + gap_length))
    
    if dashes == 0:  # 距离太短，画一条实线
        pygame.draw.line(surface, color, start_pos, end_pos, width)
        return
    
    unit_dx = dx / distance
    unit_dy = dy / distance
    
    for i in range(dashes):
        start = i * (dash_length + gap_length)
        end = start + dash_length
        
        start_x = x1 + start * unit_dx
        start_y = y1 + start * unit_dy
        end_x = x1 + end * unit_dx
        end_y = y1 + end * unit_dy
        
        pygame.draw.line(surface, color, (start_x, start_y), (end_x, end_y), width)


def draw_dual_color_circle(surface, center, radius):
    """绘制双色圆点（左蓝右红）"""
    x, y = center
    # 绘制左半圆（蓝色）
    pygame.draw.circle(surface, BLUE, center, radius)
    # 绘制右半圆（红色）
    points = [(x, y)]
    for angle in range(-180, 1):
        rad = math.radians(angle)
        points.append((x + (radius - 1) * math.cos(rad), y + (radius - 1) * math.sin(rad)))
    pygame.draw.polygon(surface, RED, points)
    # 绘制黑色边框
    pygame.draw.circle(surface, BLACK, center, radius, 2)


def draw_piece_with_number(surface, center, radius, color, number, is_selected=False):
    """绘制带数字的棋子"""
    # 绘制棋子（白色背景，彩色数字）
    pygame.draw.circle(surface, WHITE, center, radius)
    
    # 如果被选中，绘制高亮边框
    if is_selected:
        pygame.draw.circle(surface, SELECT, center, radius + 3, 3)
    
    # 绘制黑色边框
    pygame.draw.circle(surface, BLACK, center, radius, 2)
    
    # 绘制数字（使用对应颜色）
    font = pygame.font.SysFont('Arial', int(radius * 1.2))
    text = font.render(str(number), True, color)
    text_rect = text.get_rect(center=center)
    surface.blit(text, text_rect)


def highlight_valid_moves(surface, valid_move):
    """高亮显示有效移动位置"""
    for pos in valid_move:
        x, y = pos
        pygame.draw.circle(surface, HIGHLIGHT, (int(x), int(y)), RADIUS + 3, 3)


def is_point_in_circle(point, center, radius):
    """检查点是否在圆内"""
    return math.sqrt((point[0] - center[0])**2 + (point[1] - center[1])**2) <= radius


def get_piece_at_position(pos, point_map, blue_pieces, red_pieces):
    """获取指定位置的棋子"""
    global current_player, game_mode
    # 反向查找坐标对应的棋盘索引
    for (col, row), (x, y) in point_map.items():
        if is_point_in_circle(pos, (x, y), RADIUS):
            # 检查是否有蓝色棋子
            for num, (c, r) in blue_pieces.items():
                if (c, r) == (col, row):
                    # 在practice模式下检查是否可以移动该棋子
                    if game_mode == 'practice':
                        if can_move_piece('blue', num):
                            return ('blue', num, (col, row), (x, y))
                        return None
                    elif current_player == 'blue':
                        return ('blue', num, (col, row), (x, y))
                    return None
            # 检查是否有红色棋子
            for num, (c, r) in red_pieces.items():
                if (c, r) == (col, row):
                    # 在practice模式下检查是否可以移动该棋子
                    if game_mode == 'practice':
                        if can_move_piece('red', num):
                            return ('red', num, (col, row), (x, y))
                        return None
                    elif current_player == 'red':
                        return ('red', num, (col, row), (x, y))
                    return None
    return None


def get_empty_positions(point_map, blue_pieces, red_pieces):
    """获取所有空位置"""
    occupied = []
    # 修改：使用字典的实际键而不是假设0-9的连续索引
    for idx_blue in blue_pieces.keys():
        occupied.append((blue_pieces[idx_blue][0], blue_pieces[idx_blue][1]))
    for idx_red in red_pieces.keys():
        occupied.append((red_pieces[idx_red][0], red_pieces[idx_red][1]))
    
    empty = []
    for pos, (x, y) in point_map.items():
        if pos not in occupied:
            empty.append((pos, (x, y)))
    return empty


def get_all_piece_positions(blue_pieces, red_pieces):
    all_piece_positions = []
    # 修改：使用字典的实际键而不是假设0-9的连续索引
    for idx_blue in blue_pieces.keys():
        piece_pos = (blue_pieces[idx_blue][0], blue_pieces[idx_blue][1])
        all_piece_positions.append(piece_pos)
    for idx_red in red_pieces.keys():
        piece_pos = (red_pieces[idx_red][0], red_pieces[idx_red][1])
        all_piece_positions.append(piece_pos)
    return all_piece_positions


def get_potential_jump_positions(piece_pos, point_map, blue_pieces, red_pieces, all_points, start_from=1):
    """
    获取棋子的备选跨越点
    使用get_line_coordinates函数，基于col和row坐标进行计算
    返回棋盘坐标(col, row)而不是屏幕坐标(x, y)
    """
    col, row = piece_pos
    
    # 获取所有棋子的位置
    all_piece_positions = get_all_piece_positions(blue_pieces, red_pieces)
    
    # 获取所有空位置
    empty_positions = get_empty_positions(point_map, blue_pieces, red_pieces)
    empty_pos_list = [pos for pos, _ in empty_positions]
    
    potential_jumps = []
    
    # 使用get_line_coordinates获取三个方向的所有点
    left_diagonal, right_diagonal, horizontal_line = get_line_coordinates(col, row, point_map)
    
    # 处理三个方向的线：左斜行、右斜行、横行
    all_lines = [left_diagonal, right_diagonal, horizontal_line]
    
    for line_coords in all_lines:
        # 找到当前棋子在该线上的位置索引
        current_index = -1
        for i, (line_col, line_row) in enumerate(line_coords):
            if line_col == col and line_row == row:
                current_index = i
                break
        
        if current_index == -1:
            continue  # 当前棋子不在这条线上，跳过
        
        # 检查两个方向：向前和向后
        directions = [1, -1]  # 1表示向前，-1表示向后
        
        for direction in directions:
            # 从当前位置开始，沿着方向查找棋子
            piece_count = 0
            i = current_index + direction
            
            while 0 <= i < len(line_coords):
                check_col, check_row = line_coords[i]
                
                # 检查该位置是否有棋子
                if (check_col, check_row) in all_piece_positions:
                    piece_count += 1
                    
                    # 如果达到了start_from要求的棋子数量，检查下一个位置
                    if piece_count >= start_from:
                        next_index = i + direction
                        if 0 <= next_index < len(line_coords):
                            next_col, next_row = line_coords[next_index]
                            
                            # 检查后继位置是否是空位
                            if (next_col, next_row) in empty_pos_list:
                                # 计算方向值（用于兼容性）
                                if (next_col, next_row) in point_map and (col, row) in point_map:
                                    current_x, current_y = point_map[(col, row)]
                                    next_x, next_y = point_map[(next_col, next_row)]
                                    direction_value = get_direction((current_x, current_y), (next_x, next_y))
                                    # 返回棋盘坐标而不是屏幕坐标
                                    potential_jumps.append((next_col, next_row, direction_value))
                
                i += direction
    
    return potential_jumps


def not_in_pieces(x, y, pieces):
    for (pos_x, pos_y, _) in pieces:
        if pos_x == x and pos_y == y:
            return False
    return True

# 添加前进一步函数
def forward_try_move():
    """在试下模式中前进一步"""
    global try_mode, try_move_stack, BLUE_PIECES, RED_PIECES, try_current_player, try_current_index, current_player

    # 必须在试下模式，且存在可前进的步
    if not try_mode:
        return
    if try_current_index >= len(try_move_stack):
        return

    move_to_apply = try_move_stack[try_current_index]

    piece_color = move_to_apply["piece"][0]
    piece_num = move_to_apply["piece"][1]
    to_pos = move_to_apply["to"]

    # 应用移动到棋盘
    if piece_color == 'blue':
        BLUE_PIECES[piece_num] = list(to_pos)
    else:
        RED_PIECES[piece_num] = list(to_pos)

    # 更新索引与当前玩家（与正常走子逻辑保持一致）
    try_current_index += 1
    try_current_player = 'red' if piece_color == 'blue' else 'blue'
    current_player = try_current_player


def get_level_button_at_pos(pos):
    """获取点击位置对应的关卡ID"""
    for button_name, rect in draw_menu.button_rects.items():
        if rect.collidepoint(pos) and button_name.startswith("level_"):
            return int(button_name.split("_")[1])
    return None


def not_in_pieces_board_coords(col, row, pieces_list):
    """检查棋盘坐标是否不在pieces_list中（支持混合格式）"""
    for piece in pieces_list:
        if len(piece) >= 2:
            piece_col, piece_row = piece[0], piece[1]
            if piece_col == col and piece_row == row:
                return False
    return True


def get_potential_jump_recursion(point_map, blue_pieces, red_pieces, all_points, initial_jumps, potential_jumps, potential_jumps2):
    for (col, row, prev_direction) in potential_jumps:
        additional_iterms = get_potential_jump_positions((col, row), point_map, blue_pieces, red_pieces, all_points, 0)
        for i in range(len(additional_iterms) - 1, -1, -1):
            next_col, next_row, direction = additional_iterms[i]
            # 使用新的检查函数，统一处理棋盘坐标
            if (not_in_pieces_board_coords(next_col, next_row, potential_jumps2) and 
                not_in_pieces_board_coords(next_col, next_row, potential_jumps) and 
                not_in_pieces_board_coords(next_col, next_row, initial_jumps) and 
                not in_opposite_direction(prev_direction, direction, True)):
                # 统一存储棋盘坐标
                potential_jumps2.append((next_col, next_row, direction))
            else:
                additional_iterms.pop(i)
        potential_jumps2 = get_potential_jump_recursion(point_map, blue_pieces, red_pieces, all_points, initial_jumps, additional_iterms, potential_jumps2)
    return potential_jumps2


def get_paths(start, end, point_map, blue_pieces, red_pieces, all_points, current_jumps=None, path=None):
    """返回所有可行路径的数组，不修改全局变量"""
    if current_jumps is None:
        current_jumps = []
    if path is None:
        path = []
    res_paths = []
    start_col, start_row = start[0], start[1]
    end_col, end_row = end[0], end[1]
    first_check = True
    if start_col == end_col and start_row == end_row:
        if first_check:
            res_num = -1
            for node in path:
                if len(node) == 1:
                    if res_num == -1:
                        res_num = node[0]
                    elif res_num != node[0]:
                        return []
        res_paths.append(path)
        return res_paths

    new_pos = get_potential_jump_positions((start[0], start[1]), point_map, blue_pieces, red_pieces, all_points, 0)
    current_jumps.append((start_col, start_row))
    prev_direction = start[2]
    for (next_col, next_row, direction) in new_pos:
        # 修复：统一使用棋盘坐标进行重复检查
        if (next_col, next_row) not in current_jumps and not in_opposite_direction(prev_direction, direction, True):
            res = []
            for node in path:
                res.append(node)
            res.append(get_numbers((start_col, start_row), (next_col, next_row), point_map))
            child_paths = get_paths((next_col, next_row, direction), end, point_map, blue_pieces, red_pieces, all_points, current_jumps, res)
            if child_paths:
                res_paths.extend(child_paths)
    current_jumps.pop()
    return res_paths


def get_valid_moves(piece_pos, point_map, blue_pieces, red_pieces, all_points):
    """获取棋子的有效移动位置"""
    col, row = piece_pos
    x, y = point_map[(col, row)]
    
    # 获取相邻点
    neighbors = get_neighbors(x, y, [[p[0], p[1]] for p in all_points])
    
    # 获取所有空位置
    empty_positions = get_empty_positions(point_map, blue_pieces, red_pieces)
    empty_coords = [(pos, coords) for pos, coords in empty_positions]
    
    # 获取所有棋子的位置 - 修改：使用字典的实际键
    all_pieces = []
    for idx_blue in blue_pieces.keys():
        piece_pos = (blue_pieces[idx_blue][0], blue_pieces[idx_blue][1])
        piece_coords = point_map[piece_pos]
        all_pieces.append(piece_coords)
    for idx_red in red_pieces.keys():
        piece_pos = (red_pieces[idx_red][0], red_pieces[idx_red][1])
        piece_coords = point_map[piece_pos]
        all_pieces.append(piece_coords)
    
    valid_moves = []
    
    # 检查每个相邻点
    for neighbor in neighbors:
        # 1. 检查普通移动（相邻空位）
        for (pos, coords) in empty_coords:
            if abs(neighbor[0] - coords[0]) < 5 and abs(neighbor[1] - coords[1]) < 5:
                direction = get_direction((x, y), (coords[0], coords[1]))
                valid_moves.append((coords[0], coords[1], pos, direction))
        
        # 2. 检查跳跃移动
        # 如果相邻点有棋子，检查是否可以跳过
        for piece_coords in all_pieces:
            if abs(neighbor[0] - piece_coords[0]) < 5 and abs(neighbor[1] - piece_coords[1]) < 5:
                # 计算跳跃后的位置（在相同方向上延伸一格）
                jump_x = piece_coords[0] + (piece_coords[0] - x)
                jump_y = piece_coords[1] + (piece_coords[1] - y)
                
                # 检查跳跃位置是否是空位
                for (pos, coords) in empty_coords:
                    if abs(jump_x - coords[0]) < 5 and abs(jump_y - coords[1]) < 5:
                        direction = get_direction((x, y), (coords[0], coords[1]))
                        valid_moves.append((coords[0], coords[1], pos, direction))
    
    return valid_moves


def move_piece(piece_info, target_pos, blue_pieces, red_pieces, move_type="normal", formula=None, res=None):
    """移动棋子到目标位置"""
    global current_player, color_locked, level_move_count, try_mode, try_move_stack, try_step, try_current_index, try_current_player
    global net_session, local_side, processing_remote_move
    color, num, start_pos, _ = piece_info
    
    # 在练习模式下检查是否允许移动该棋子
    if game_mode == 'practice' and allowed_piece and not can_move_piece(color, num):
        return False  # 不允许移动，直接返回
    
    # 记录移动前的位置
    if color == 'blue':
        old_pos = (blue_pieces[num][0], blue_pieces[num][1])
        blue_pieces[num][0] = target_pos[0]
        blue_pieces[num][1] = target_pos[1]
        # 如果颜色没有锁定，则切换当前玩家
        if not color_locked:
            current_player = 'red'  # 切换到红方
    else:
        old_pos = (red_pieces[num][0], red_pieces[num][1])
        red_pieces[num][0] = target_pos[0]
        red_pieces[num][1] = target_pos[1]
        # 如果颜色没有锁定，则切换当前玩家
        if not color_locked:
            current_player = 'blue'  # 切换到蓝方
    
    # 在练习模式下增加移动计数
    if game_mode == 'practice':
        level_move_count += 1

    # 若处于试下模式，并且用户从中间步继续走子，先截断未来步
    if try_mode:
        if try_current_index < len(try_move_stack):
            try_move_stack = try_move_stack[:try_current_index]
            try_step = try_current_index

    # 记录这步棋（试下模式下也写入记谱，用于撤回与分析）
    record_move(piece_info, old_pos, target_pos, move_type, formula, res)

    # 在 LAN 模式下，将本地走子同步到对方
    if game_mode == 'lan' and net_session and not processing_remote_move:
        try:
            color, num, _, _ = piece_info
            net_session.send({
                'type': 'move',
                'piece': {'color': color, 'num': num},
                'from': list(old_pos),
                'to': list(target_pos),
                'move_type': move_type,
                'formula': formula,
                'res': res,
            })
        except Exception:
            pass

    # 在试下模式下，推入试下移动栈并更新步数与索引
    if try_mode:
        try_move_stack.append({
            "piece": (color, num),
            "from": old_pos,
            "to": target_pos
        })
        try_step = len(try_move_stack)
        try_current_index = try_step
        # 切换试下当前玩家用于下一步
        try_current_player = 'red' if color == 'blue' else 'blue'
    
    # 在练习模式下检查关卡胜利条件
    if game_mode == 'practice' and current_level and check_level_victory():
        complete_level()
        # 这里可以添加胜利提示逻辑
    
    return True  # 移动成功


def draw_replay_controls():
    """绘制回放控制面板"""
    global replay_step, replay_playing, replay_speed, try_mode, try_step, try_current_index, hovered_button
    
    # 控制面板背景
    control_panel_rect = pygame.Rect(CALC_AREA_X, CALC_AREA_Y + CALC_AREA_HEIGHT - 150, CALC_AREA_WIDTH, 150)
    pygame.draw.rect(window, LIGHT_GRAY, control_panel_rect)
    pygame.draw.rect(window, BLACK, control_panel_rect, 2)
    
    font = pygame.font.Font(None, 24)
    
    # 添加试下功能区域 - 独立显示在控制面板顶部
    try_section_y = CALC_AREA_Y + CALC_AREA_HEIGHT - 180
    try_section_height = 25
    button_width = 30
    button_height = 20
    
    # 添加试下按钮 - 独立显示在顶部
    if not try_mode:
        try_button = pygame.Rect(CALC_AREA_X + 10, try_section_y, button_width, button_height)
        if hovered_button == "replay_button_try_button":
            pygame.draw.rect(window, LIGHT_YELLOW, try_button)
        else:
            pygame.draw.rect(window, WHITE, try_button)
        pygame.draw.rect(window, BLACK, try_button, 2)
        try_text = font.render("T", True, BLACK)
        try_text_rect = try_text.get_rect(center=try_button.center)
        window.blit(try_text, try_text_rect)
        button_areas = {'try_button': try_button}
        
        # 只有在非试下模式下才显示复盘控制按钮
        # 步数显示
        step_text = font.render(f"Step: {replay_step}/{replay_max_steps}", True, BLACK)
        window.blit(step_text, (CALC_AREA_X + 10, CALC_AREA_Y + CALC_AREA_HEIGHT - 140))
        
        # 进度条
        progress_rect = pygame.Rect(CALC_AREA_X + 10, CALC_AREA_Y + CALC_AREA_HEIGHT - 110, CALC_AREA_WIDTH - 20, 20)
        pygame.draw.rect(window, WHITE, progress_rect)
        pygame.draw.rect(window, BLACK, progress_rect, 2)
        
        if replay_max_steps > 0:
            progress_width = int((replay_step / replay_max_steps) * (CALC_AREA_WIDTH - 24))
            progress_fill_rect = pygame.Rect(CALC_AREA_X + 12, CALC_AREA_Y + CALC_AREA_HEIGHT - 108, progress_width, 16)
            pygame.draw.rect(window, BLUE, progress_fill_rect)
        
        # 控制按钮 - 向上移动20像素
        button_y = CALC_AREA_Y + CALC_AREA_HEIGHT - 80
        button_width = 35
        button_height = 25
        button_spacing = 40
        
        # 上一步按钮
        prev_button = pygame.Rect(CALC_AREA_X + 10, button_y, button_width, button_height)
        if hovered_button == "replay_button_prev_button":
            pygame.draw.rect(window, LIGHT_YELLOW, prev_button)
        else:
            pygame.draw.rect(window, WHITE, prev_button)
        pygame.draw.rect(window, BLACK, prev_button, 2)
        prev_text = font.render("<<", True, BLACK)
        prev_text_rect = prev_text.get_rect(center=prev_button.center)
        window.blit(prev_text, prev_text_rect)
        
        # 播放/暂停按钮
        play_button = pygame.Rect(CALC_AREA_X + 10 + button_spacing, button_y , button_width, button_height)
        if hovered_button == "replay_button_play_button":
            pygame.draw.rect(window, LIGHT_YELLOW, play_button)
        else:
            pygame.draw.rect(window, WHITE, play_button)
        pygame.draw.rect(window, BLACK, play_button, 2)
        play_text = font.render("||" if replay_playing else ">", True, BLACK)
        play_text_rect = play_text.get_rect(center=play_button.center)
        window.blit(play_text, play_text_rect)
        
        # 下一步按钮
        next_button = pygame.Rect(CALC_AREA_X + 10 + button_spacing * 2, button_y, button_width, button_height)
        if hovered_button == "replay_button_next_button":
            pygame.draw.rect(window, LIGHT_YELLOW, next_button)
        else:
            pygame.draw.rect(window, WHITE, next_button)
        pygame.draw.rect(window, BLACK, next_button, 2)
        next_text = font.render(">>", True, BLACK)
        next_text_rect = next_text.get_rect(center=next_button.center)
        window.blit(next_text, next_text_rect)
        
        # 重置按钮
        reset_button = pygame.Rect(CALC_AREA_X + 10 + button_spacing * 3, button_y, button_width, button_height)
        if hovered_button == "replay_button_reset_button":
            pygame.draw.rect(window, LIGHT_YELLOW, reset_button)
        else:
            pygame.draw.rect(window, WHITE, reset_button)
        pygame.draw.rect(window, BLACK, reset_button, 2)
        reset_text = font.render("R", True, BLACK)
        reset_text_rect = reset_text.get_rect(center=reset_button.center)
        window.blit(reset_text, reset_text_rect)
        
        # 速度控制
        speed_text = font.render(f"Speed: {replay_speed:.1f}x", True, BLACK)
        window.blit(speed_text, (CALC_AREA_X + 10, button_y + 30))
        
        # 返回按钮区域信息
        button_areas.update({
            'prev_button': prev_button,
            'play_button': play_button,
            'next_button': next_button,
            'reset_button': reset_button,
            'progress_rect': progress_rect
        })
    else:
        # 在试下模式下显示试下步数
        try_step_text = font.render(f"Try Step: {try_current_index}", True, BLACK)
        window.blit(try_step_text, (CALC_AREA_X + 10, CALC_AREA_Y + CALC_AREA_HEIGHT - 140))
        
        # 试下模式进度条
        if try_step > 0:
            try_progress_rect = pygame.Rect(CALC_AREA_X + 10, CALC_AREA_Y + CALC_AREA_HEIGHT - 110, CALC_AREA_WIDTH - 20, 20)
            pygame.draw.rect(window, WHITE, try_progress_rect)
            pygame.draw.rect(window, BLACK, try_progress_rect, 2)
            
            try_progress_width = int((try_current_index / try_step) * (CALC_AREA_WIDTH - 24))
            try_progress_fill_rect = pygame.Rect(CALC_AREA_X + 12, CALC_AREA_Y + CALC_AREA_HEIGHT - 108, try_progress_width, 16)
            pygame.draw.rect(window, GREEN, try_progress_fill_rect)
        
        # 试下模式控制按钮
        button_y = CALC_AREA_Y + CALC_AREA_HEIGHT - 80
        button_width = 35
        button_height = 25
        button_spacing = 40
        
        # 在试下模式下显示结束试下和撤销按钮
        try_section_y += 20
        
        # 上一步按钮
        prev_try_button = pygame.Rect(CALC_AREA_X + 10, button_y + 30, button_width, button_height)
        if hovered_button == "replay_button_prev_try_button":
            pygame.draw.rect(window, LIGHT_YELLOW, prev_try_button)
        else:
            pygame.draw.rect(window, WHITE, prev_try_button)
        pygame.draw.rect(window, BLACK, prev_try_button, 2)
        prev_try_text = font.render("<<", True, BLACK)
        prev_try_text_rect = prev_try_text.get_rect(center=prev_try_button.center)
        window.blit(prev_try_text, prev_try_text_rect)
        
        # 下一步按钮
        next_try_button = pygame.Rect(CALC_AREA_X + 10 + button_spacing, button_y + 30, button_width, button_height)
        if hovered_button == "replay_button_next_try_button":
            pygame.draw.rect(window, LIGHT_YELLOW, next_try_button)
        else:
            pygame.draw.rect(window, WHITE, next_try_button)
        pygame.draw.rect(window, BLACK, next_try_button, 2)
        next_try_text = font.render(">>", True, BLACK)
        next_try_text_rect = next_try_text.get_rect(center=next_try_button.center)
        window.blit(next_try_text, next_try_text_rect)
        
        # 结束试下按钮
        exit_try_button = pygame.Rect(CALC_AREA_X + 10, try_section_y + 75, button_width, button_height)
        if hovered_button == "replay_button_exit_try_button":
            pygame.draw.rect(window, LIGHT_YELLOW, exit_try_button)
        else:
            pygame.draw.rect(window, WHITE, exit_try_button)
        pygame.draw.rect(window, BLACK, exit_try_button, 2)
        exit_try_text = font.render("E", True, BLACK)
        exit_try_text_rect = exit_try_text.get_rect(center=exit_try_button.center)
        window.blit(exit_try_text, exit_try_text_rect)
        
        # 显示结束试下按钮提示
        exit_try_label = font.render("End Try", True, BLACK)
        window.blit(exit_try_label, (exit_try_button.x + 40, exit_try_button.y + 5))
        
        
        # 在试下模式下返回试下相关按钮
        button_areas = {
            'exit_try_button': exit_try_button,
            'prev_try_button': prev_try_button,
            'next_try_button': next_try_button
        }
        
        # 显示当前玩家
        # current_player_text = font.render(f"Current: {'Blue' if try_current_player == 'blue' else 'Red'}", True, 
        #                                  BLUE if try_current_player == 'blue' else RED)
        # window.blit(current_player_text, (CALC_AREA_X + 10 + button_spacing * 2, button_y + 5))
    
    return button_areas

def draw_calculation_area():

    """绘制右侧计算版区域和上方算式区域"""
    global hovered_button, expected_result, try_mode
    
    # 绘制上方算式区域背景
    pygame.draw.rect(window, LIGHT_BLUE, (FORMULA_AREA_X, FORMULA_AREA_Y, FORMULA_AREA_WIDTH, FORMULA_AREA_HEIGHT))
    
    # 绘制计算版背景
    pygame.draw.rect(window, LIGHT_GRAY, (CALC_AREA_X, CALC_AREA_Y, CALC_AREA_WIDTH, CALC_AREA_HEIGHT))
    pygame.draw.line(window, BLACK, (CALC_AREA_X, CALC_AREA_Y), (CALC_AREA_X, CALC_AREA_Y + CALC_AREA_HEIGHT), 2)
    
    # 绘制标题
    font_title = pygame.font.SysFont('SimHei', 24)
    title = font_title.render("Calculation", True, BLACK)
    title_rect = title.get_rect(center=(CALC_AREA_X + CALC_AREA_WIDTH // 2, CALC_AREA_Y + 30))
    window.blit(title, title_rect)
    
    # 绘制已选择的数字
    font_numbers = pygame.font.SysFont('Arial', 20)
    y_pos = CALC_AREA_Y + 50
    # 绘制操作按钮
    button_width = 40
    button_height = 40
    button_margin = 10
    operations = ["+", "-", "×", "÷", "(", ")"]
    ops = []
    for i, op in enumerate(operations):
        if i <= 3:
            button_x = CALC_AREA_X + 10 + i * (button_width + button_margin)
            button_rect = pygame.Rect(button_x, y_pos, button_width, button_height)
            ops.append((button_x, y_pos, button_width, button_height, op))
        else:
            button_x = CALC_AREA_X + 10 + (i - 3) * (button_width + button_margin)
            button_rect = pygame.Rect(button_x, y_pos + 60, button_width, button_height)
            ops.append((button_x, y_pos + 60, button_width, button_height, op))

        # 如果鼠标悬停在此按钮上，使用深色
        if hovered_button == f"op_{op}":
            # 使用更深的颜色
            pygame.draw.rect(window, (200, 200, 200), button_rect)
        else:
            pygame.draw.rect(window, WHITE, button_rect)
        
        pygame.draw.rect(window, BLACK, button_rect, 2)
        
        # 绘制操作符文本
        op_text = font_numbers.render(op, True, BLACK)
        if i <= 3:
            op_rect = op_text.get_rect(center=(button_x + button_width // 2, y_pos + button_height // 2))
        else:
            op_rect = op_text.get_rect(center=(button_x + button_width // 2, y_pos + 60 + button_height // 2))
        window.blit(op_text, op_rect)
    
    # 绘制数字按钮 
    number_y_pos = y_pos + 120  # 放在运算符下方
    number_width = 30
    number_height = 30
    number_margin = 10
    number_buttons = []
    
    if board_locked:
        numbers_text = font_numbers.render("Numbers:", True, RED)
        window.blit(numbers_text, (CALC_AREA_X + 10, number_y_pos))
    number_y_pos += 30
    
    for i in range(len(selected_numbers)):
        num = selected_numbers[i]
        
        if i in [0, 1, 2, 3, 4]:
            button_x = CALC_AREA_X + 10 + i * (number_width + number_margin)
            button_rect = pygame.Rect(button_x, number_y_pos, number_width, number_height)
        else:
            button_x = CALC_AREA_X + 10 + (i - 5) * (number_width + number_margin)
            button_rect = pygame.Rect(button_x, number_y_pos + 40, number_width, number_height)
            
        # 如果鼠标悬停在此按钮上，使用深色
        if hovered_button == f"red_{i}":
            pygame.draw.rect(window, LIGHT_YELLOW, button_rect)
        else:
            pygame.draw.rect(window, WHITE, button_rect)
        
        # 黄色边框
        pygame.draw.rect(window, YELLOW, button_rect, 2)
        
        # 绘制数字文本
        num_text = font_numbers.render(str(num), True, BLACK)
        if i in [0, 1, 2, 3, 4]:
            num_rect = num_text.get_rect(center=(button_x + number_width // 2, number_y_pos + number_height // 2))
        else:
            num_rect = num_text.get_rect(center=(button_x + number_width // 2, number_y_pos + 40 + number_height // 2))
        window.blit(num_text, num_rect)
        
        # 添加到按钮列表
        if i in [0, 1, 2, 3, 4]:
            number_buttons.append((button_x, number_y_pos, number_width, number_height, "red", i, num))
        else:
            number_buttons.append((button_x, number_y_pos + 40, number_width, number_height, "red", i, num))

    continuous_span_area = {"paths": [], "numbers": []}
    if board_locked and continuous_span and len(paths) >= 1:
        button_y = number_y_pos
        for idx, path in enumerate(paths):
            button_x = CALC_AREA_X + 10 
            width = 35
            paths_rect = pygame.Rect(button_x, button_y, 180, width * (len(path) + 1))
            continuous_span_area["paths"].append(paths_rect)
            if hovered_button == f"continuous_span_{idx}" and len(paths) > 1:
                pygame.draw.rect(window, (200, 200, 60), paths_rect) 
            else:
                pygame.draw.rect(window, (240, 240, 100), paths_rect) 
            pygame.draw.rect(window, (240, 220, 0), paths_rect, 5)
            
            # 添加路径标题显示实际跨越的数字
            # path_title = f"Path {idx + 1}: {sum([len(group) for group in path])} numbers"
            # title_font = pygame.font.Font(None, 20)
            # title_text = title_font.render(path_title, True, BLACK)
            # window.blit(title_text, (button_x + 5, button_y + 5))
            button_y += 20
            
            for idx_x, group in enumerate(path):
                button_y += width
                continuous_span_area["numbers"].append([])
                
                # 显示这一段跨越的实际数字
                # group_title = f"Segment {idx_x + 1}: {group}"
                # segment_font = pygame.font.Font(None, 18)
                # segment_text = segment_font.render(group_title, True, BLACK)
                # window.blit(segment_text, (button_x + 10, button_y - width + 5))
                
                for t, num in enumerate(group):
                    font_goal = pygame.font.Font(None, 30)
                    text = font_goal.render(str(num), True, BLACK) 
                    button_rect = pygame.Rect(button_x + (t + 0.5) * width, button_y - width, number_width, number_height)
                    if len(paths) == 1:
                        continuous_span_area["numbers"][-1].append(button_rect)
                    if hovered_button == f"continuous_span_number_{idx_x}_{t}" and len(paths) == 1:
                        pygame.draw.rect(window, LIGHT_YELLOW, button_rect)
                    else:
                        pygame.draw.rect(window, WHITE, button_rect)
                    pygame.draw.rect(window, YELLOW, button_rect, 2)
                    rect = text.get_rect(center=(button_x + (t + 0.5) * width + 15, button_y - width // 2))  # 居中显示
                    window.blit(text, rect)           
            button_y += width * 1.5

    # 绘制上方算式输入区域 
    formula_font = pygame.font.SysFont('Arial', 24)
    formula_label = formula_font.render("Formula:", True, BLACK)
    window.blit(formula_label, (20, 20))
    
    # 绘制算式文本框
    formula_rect = pygame.Rect(120, 15, 400, 30)
    pygame.draw.rect(window, WHITE, formula_rect)
    pygame.draw.rect(window, BLACK, formula_rect, 2)
    
    # 显示算式文本
    if formula_text:
        formula_display = formula_font.render(formula_text, True, BLACK)
        window.blit(formula_display, (125, 20))
    
    # 绘制删除最后一个符号的按钮
    delete_button_rect = pygame.Rect(550, 15, 100, 30)
    clear_button_rect = pygame.Rect(550, 55, 100, 30)
    calc_button_rect = pygame.Rect(660, 15, 120, 70)  # 放大按钮并移到右边
    if game_mode != 'replay' or try_mode:
        if hovered_button == "delete_button":
            pygame.draw.rect(window, (100, 100, 200), delete_button_rect)  # 深蓝紫色
        else:
            pygame.draw.rect(window, (150, 150, 255), delete_button_rect)  # 蓝紫色
        pygame.draw.rect(window, BLACK, delete_button_rect, 2)
        
        delete_text = font_numbers.render("Delete", True, WHITE)
        delete_rect = delete_text.get_rect(center=(600, 30))
        window.blit(delete_text, delete_rect)

        if hovered_button == "clear_button":
            pygame.draw.rect(window, (200, 0, 0), clear_button_rect)  # 深红色
        else:
            pygame.draw.rect(window, RED, clear_button_rect)
        pygame.draw.rect(window, BLACK, clear_button_rect, 2)
        
        clear_text = font_numbers.render("Clear", True, WHITE)
        clear_rect = clear_text.get_rect(center=(600, 70))
        window.blit(clear_text, clear_rect)
 
        if hovered_button == "calc_button":
            pygame.draw.rect(window, (0, 70, 200), calc_button_rect)  # 深蓝色
        else:
            pygame.draw.rect(window, BLUE, calc_button_rect)
        pygame.draw.rect(window, BLACK, calc_button_rect, 2)
        
        calc_text = font_title.render("Calculate", True, WHITE)  # 使用更大的字体
        calc_rect = calc_text.get_rect(center=(720, 50))  # 居中显示
        window.blit(calc_text, calc_rect)

    if board_locked and expected_result is not None:
        display_goal_rect = pygame.Rect(790, 15, 70, 70)
        pygame.draw.rect(window, LIGHT_YELLOW, display_goal_rect) 
        pygame.draw.rect(window, YELLOW, display_goal_rect, 2)
        pygame.draw.circle(window, (255, 255, 255), (825, 50), 25)
        font_goal = pygame.font.Font(None, 50)
        calc_text = font_goal.render(str(expected_result), True, RED) 
        calc_rect = calc_text.get_rect(center=(825, 50))  # 居中显示
        window.blit(calc_text, calc_rect)
    
    # 绘制计算结果
    if calculation_result is not None:
        y_pos = CALC_AREA_Y + 300
        result_text = font_title.render("Result:", True, BLACK)
        window.blit(result_text, (CALC_AREA_X + 10, y_pos))
        
        result_value = font_title.render(str(calculation_result), True, BLUE)
        window.blit(result_value, (CALC_AREA_X + 10, y_pos + 40))
    
    # 绘制取消按钮（用于解除棋盘锁定状态）- 移到棋盘右上角
    cancel_button_rect = pygame.Rect(window_size - 80, OFFSET_Y + 10, 70, 30)
    if board_locked:
        # 如果鼠标悬停在取消按钮上，使用深色 
        if hovered_button == "cancel_button":
            pygame.draw.rect(window, (100, 100, 100), cancel_button_rect)  # 深灰色
        else:
            pygame.draw.rect(window, GRAY, cancel_button_rect)
        pygame.draw.rect(window, BLACK, cancel_button_rect, 2)
        cancel_text = font_numbers.render("Cancel", True, WHITE)
        cancel_rect = cancel_text.get_rect(center=(window_size - 45, OFFSET_Y + 25))
        window.blit(cancel_text, cancel_rect)
    
    # 添加锁定颜色按钮（右下角）
    lock_color_rect = pygame.Rect(window_size - 150, window_size + OFFSET_Y - 40, 140, 30)
    # 根据锁定状态使用不同颜色
    if color_locked:
        if hovered_button == "lock_color_button":
            pygame.draw.rect(window, (180, 0, 0), lock_color_rect)  # 深红色（锁定状态）
        else:
            pygame.draw.rect(window, (220, 0, 0), lock_color_rect)  # 红色（锁定状态）
        lock_text = font_numbers.render("Cancel Lock", True, WHITE)
    else:
        if hovered_button == "lock_color_button":
            pygame.draw.rect(window, (0, 100, 180), lock_color_rect)  # 深蓝色（未锁定状态）
        else:
            pygame.draw.rect(window, (0, 120, 220), lock_color_rect)  # 蓝色（未锁定状态）
        lock_text = font_numbers.render("Color Locked", True, WHITE)
    
    pygame.draw.rect(window, BLACK, lock_color_rect, 2)
    lock_rect = lock_text.get_rect(center=(window_size - 80, window_size + OFFSET_Y - 25))
    window.blit(lock_text, lock_rect)

    replay_button = []
    if game_mode == 'replay':
        replay_button = draw_replay_controls()
    
    # 返回按钮区域，用于事件处理
    return {
        "operations": ops,
        "calc_button": calc_button_rect,
        "clear_button": clear_button_rect,
        "delete_button": delete_button_rect,  # 添加删除按钮
        "cancel_button": cancel_button_rect,
        "lock_color_button": lock_color_rect,  # 添加锁定颜色按钮
        "formula_rect": formula_rect,  # 算式文本框区域
        "number_buttons": number_buttons,  # 数字按钮区域
        "continuous_span_area": continuous_span_area,
        "replay_button": replay_button
    }

def calculate_result():
    """根据选择的数字和操作计算结果"""
    global calculation_result
    
    if len(selected_numbers) != 2 or operation is None:
        return
    
    a, b = selected_numbers
    
    if operation == "+":
        calculation_result = a + b
    elif operation == "-":
        calculation_result = a - b
    elif operation == "×":
        calculation_result = a * b
    elif operation == "÷":
        if b != 0:
            calculation_result = a / b
        else:
            calculation_result = "ERROR"


def draw_custom_setup():
    """绘制自定义摆棋界面"""
    global dragging_piece, drag_offset, hovered_button
    
    window.fill(WHITE)
    
    # 绘制棋盘（复用draw_board的棋盘绘制逻辑）
    all_points = []
    point_map = {}  # 用于存储每个点的坐标和索引
    
    # 生成所有点的坐标
    for col_index, [num, offset] in enumerate(POINTS):
        y = BEGIN_Y + col_index * GRID * math.sqrt(3) / 2
        col_points = []
        for i in range(num):
            raw_index = offset + i * 2
            x = BEGIN_X + raw_index * GRID * 0.5
            col_points.append([x, y, col_index, i])
            point_map[(col_index, raw_index)] = (x, y)
        all_points.extend(col_points)
    
    # 先画连线（虚线）
    for point in all_points:
        x, y, col_index, point_index = point
        neighbors = get_neighbors(x, y, [[p[0], p[1]] for p in all_points])
        for neighbor in neighbors:
            draw_dashed_line(window, BLACK, 
                            (int(x), int(y)), 
                            (int(neighbor[0]), int(neighbor[1])), 3, 5, 5)
    
    # 再画圆点
    for point in all_points:
        x, y, col_index, point_index = point
        color = get_point_color(x, y, col_index, point_index, POINTS[col_index][0])
        if color == "DUAL":
            draw_dual_color_circle(window, (int(x), int(y)), RADIUS)
        else:
            pygame.draw.circle(window, color, (int(x), int(y)), RADIUS)
            pygame.draw.circle(surface=window, color=BLACK, center=(int(x), int(y)), radius=RADIUS, width=2)
    
    # 绘制已放置的棋子
    for pos, (color, num) in custom_setup_pieces.items():
        if pos in point_map:
            x, y = point_map[pos]
            piece_color = BLUE if color == 'blue' else RED
            draw_piece_with_number(window, (int(x), int(y)), RADIUS, piece_color, num)
    
    # 绘制右侧可用棋子区域
    piece_area_x_offset = 20
    piece_area_y_offset = 20
    piece_area_x = window_size + 20
    piece_area_y = OFFSET_Y + 70
    piece_spacing = 40
    
    # 绘制背景
    pygame.draw.rect(window, LIGHT_GRAY, (piece_area_x - 10, piece_area_y - 30, 160, 620))
    pygame.draw.rect(window, BLACK, (piece_area_x - 10, piece_area_y - 30, 160, 620), 2)
    
    # 标题
    title_font = pygame.font.Font(None, 24)
    title_text = title_font.render("Available Pieces", True, BLACK)
    window.blit(title_text, (piece_area_x, piece_area_y - 20))
    
    # 绘制蓝色棋子
    blue_label = title_font.render("Blue:", True, BLUE)
    window.blit(blue_label, (piece_area_x, piece_area_y + 10))
    
    for i in range(10):
        if available_pieces['blue'][i]:  # 只显示可用的棋子
            x = piece_area_x + (i % 2) * 70 + piece_area_x_offset
            y = piece_area_y + 40 + (i // 2) * piece_spacing + piece_area_y_offset
            
            # 如果正在拖拽这个棋子，则半透明显示
            if dragging_piece and dragging_piece == ('blue', i):
                # 创建半透明表面
                transparent_surface = pygame.Surface((RADIUS * 2, RADIUS * 2), pygame.SRCALPHA)
                pygame.draw.circle(transparent_surface, WHITE, (RADIUS, RADIUS), RADIUS)
                pygame.draw.circle(transparent_surface, BLACK, (RADIUS, RADIUS), RADIUS, 2)
                # 设置透明度
                transparent_surface.set_alpha(128)
                window.blit(transparent_surface, (x - RADIUS, y - RADIUS))
                
                # 绘制半透明数字
                font = pygame.font.SysFont('Arial', int(RADIUS * 1.2))
                text_surface = pygame.Surface((RADIUS * 2, RADIUS * 2), pygame.SRCALPHA)
                text = font.render(str(i), True, BLUE)
                text_rect = text.get_rect(center=(RADIUS, RADIUS))
                text_surface.blit(text, text_rect)
                text_surface.set_alpha(128)
                window.blit(text_surface, (x - RADIUS, y - RADIUS))
            else:
                # 使用标准的棋子绘制函数
                draw_piece_with_number(window, (x, y), RADIUS, BLUE, i)
    
    # 绘制红色棋子
    red_label = title_font.render("Red:", True, RED)
    window.blit(red_label, (piece_area_x, piece_area_y + 250))
    
    for i in range(10):
        if available_pieces['red'][i]:  # 只显示可用的棋子
            x = piece_area_x + (i % 2) * 70 + piece_area_x_offset
            y = piece_area_y + 280 + (i // 2) * piece_spacing + piece_area_y_offset
            
            # 如果正在拖拽这个棋子，则半透明显示
            if dragging_piece and dragging_piece == ('red', i):
                # 创建半透明表面
                transparent_surface = pygame.Surface((RADIUS * 2, RADIUS * 2), pygame.SRCALPHA)
                pygame.draw.circle(transparent_surface, WHITE, (RADIUS, RADIUS), RADIUS)
                pygame.draw.circle(transparent_surface, BLACK, (RADIUS, RADIUS), RADIUS, 2)
                # 设置透明度
                transparent_surface.set_alpha(128)
                window.blit(transparent_surface, (x - RADIUS, y - RADIUS))
                
                # 绘制半透明数字
                font = pygame.font.SysFont('Arial', int(RADIUS * 1.2))
                text_surface = pygame.Surface((RADIUS * 2, RADIUS * 2), pygame.SRCALPHA)
                text = font.render(str(i), True, RED)
                text_rect = text.get_rect(center=(RADIUS, RADIUS))
                text_surface.blit(text, text_rect)
                text_surface.set_alpha(128)
                window.blit(text_surface, (x - RADIUS, y - RADIUS))
            else:
                # 使用标准的棋子绘制函数
                draw_piece_with_number(window, (x, y), RADIUS, RED, i)
    
    # 如果正在拖拽棋子，在鼠标位置绘制棋子
    if dragging_piece:
        mouse_pos = pygame.mouse.get_pos()
        color, num = dragging_piece
        piece_color = BLUE if color == 'blue' else RED
        drag_x = mouse_pos[0] + drag_offset[0]
        drag_y = mouse_pos[1] + drag_offset[1]
        
        # 使用标准的棋子绘制函数
        draw_piece_with_number(window, (drag_x, drag_y), RADIUS, piece_color, num)
    
    # 绘制控制按钮
    button_y = piece_area_y + 500
    
    # 清空按钮
    clear_button = pygame.Rect(piece_area_x, button_y, 70, 30)
    # 根据悬停状态改变颜色
    if hovered_button == "clear":
        pygame.draw.rect(window, LIGHT_YELLOW, clear_button)
    else:
        pygame.draw.rect(window, WHITE, clear_button)
    pygame.draw.rect(window, BLACK, clear_button, 2)
    clear_text = title_font.render("Clear", True, BLACK)
    clear_text_rect = clear_text.get_rect(center=clear_button.center)
    window.blit(clear_text, clear_text_rect)
    
    # 保存按钮
    save_button = pygame.Rect(piece_area_x, button_y + 40, 70, 30)
    # 根据悬停状态改变颜色
    if hovered_button == "save":
        pygame.draw.rect(window, LIGHT_YELLOW, save_button)
    else:
        pygame.draw.rect(window, WHITE, save_button)
    pygame.draw.rect(window, BLACK, save_button, 2)
    save_text = title_font.render("Save", True, BLACK)
    save_text_rect = save_text.get_rect(center=save_button.center)
    window.blit(save_text, save_text_rect)
    
    # 返回按钮
    back_button = pygame.Rect(50, 50, 100, 40)
    # 根据悬停状态改变颜色
    if hovered_button == "back":
        pygame.draw.rect(window, LIGHT_YELLOW, back_button)
    else:
        pygame.draw.rect(window, WHITE, back_button)
    pygame.draw.rect(window, BLACK, back_button, 2)
    back_text = title_font.render("Back", True, BLACK)
    back_text_rect = back_text.get_rect(center=back_button.center)
    window.blit(back_text, back_text_rect)
    
    # 存储按钮区域用于点击检测
    if not hasattr(draw_custom_setup, 'button_rects'):
        draw_custom_setup.button_rects = {}
    draw_custom_setup.button_rects["clear"] = clear_button
    draw_custom_setup.button_rects["save"] = save_button
    draw_custom_setup.button_rects["back"] = back_button
    
    return all_points, point_map


def draw_level_complete():
    """Draw level completion interface"""
    window.fill(WHITE)
    
    # Draw completion information
    font = pygame.font.Font(None, 48)
    title_text = font.render("Level Complete!", True, BLACK)
    title_rect = title_text.get_rect(center=(window.get_width() // 2, 200))
    window.blit(title_text, title_rect)
    
    # Show statistics
    if current_level and practice_progress:
        record = practice_progress['level_records'][str(current_level)]
        stats_font = pygame.font.Font(None, 24)
        
        moves_text = stats_font.render(f"Moves this time: {level_move_count}", True, BLACK)
        best_text = stats_font.render(f"Best record: {record['best_moves']} moves", True, BLACK)
        
        moves_rect = moves_text.get_rect(center=(window.get_width() // 2, 300))
        best_rect = best_text.get_rect(center=(window.get_width() // 2, 330))
        
        window.blit(moves_text, moves_rect)
        window.blit(best_text, best_rect)
    
    # Hint information
    hint_font = pygame.font.Font(None, 24)
    hint_text = hint_font.render("Press SPACE to return to level selection", True, BLACK)
    hint_rect = hint_text.get_rect(center=(window.get_width() // 2, 400))
    window.blit(hint_text, hint_rect)
    
    # Back button
    button_font = pygame.font.Font(None, 32)
    back_button_rect = pygame.Rect(50, 50, 100, 40)
    # 根据鼠标悬停状态改变颜色
    if menu_hovered == "back":
        pygame.draw.rect(window, LIGHT_YELLOW, back_button_rect)
    else:
        pygame.draw.rect(window, WHITE, back_button_rect)
    pygame.draw.rect(window, BLACK, back_button_rect, 2)
    back_text = button_font.render("Back", True, BLACK)
    back_text_rect = back_text.get_rect(center=back_button_rect.center)
    window.blit(back_text, back_text_rect)
    
    # 存储按钮区域用于点击检测
    if not hasattr(draw_level_complete, 'button_rects'):
        draw_level_complete.button_rects = {}
    draw_level_complete.button_rects["back"] = back_button_rect


def draw_star(surface, center_x, center_y, size, color):
    """绘制五角星"""
    import math
    points = []
    for i in range(10):
        angle = math.pi * i / 5
        if i % 2 == 0:
            # 外顶点
            radius = size
        else:
            # 内顶点
            radius = size * 0.4
        x = center_x + radius * math.cos(angle - math.pi/2)
        y = center_y + radius * math.sin(angle - math.pi/2)
        points.append((x, y))
    pygame.draw.polygon(surface, color, points)


def draw_practice_levels():
    """Draw practice level selection interface"""
    if not levels_config or not practice_progress:
        return
    
    # Clear button records
    draw_menu.button_rects.clear()
    
    # Draw title
    title_font = pygame.font.Font(None, 48)
    title_text = title_font.render("Practice Levels", True, BLACK)
    title_rect = title_text.get_rect(center=(window.get_width() // 2, 100))
    window.blit(title_text, title_rect)
    
    # Draw level buttons
    levels = levels_config['levels']
    current_unlocked = practice_progress['player_progress']['current_level']
    
    button_width = 350
    button_height = 60
    start_y = 200
    spacing = 80
    
    for i, level in enumerate(levels):
        level_id = i + 1
        y = start_y + i * spacing
        x = (window.get_width() - button_width) // 2
        
        # Determine button state
        is_unlocked = level_id <= current_unlocked
        is_completed = level_id in practice_progress['player_progress']['completed_levels']
        
        # Draw button background
        if is_unlocked:
            color = (100, 150, 200)  # Blue - playable
        else:
            color = (150, 150, 150)  # Gray - locked
        
        button_rect = pygame.Rect(x, y, button_width, button_height)
        pygame.draw.rect(window, color, button_rect)
        pygame.draw.rect(window, BLACK, button_rect, 2)
        
        # Draw level name (centered)
        font = pygame.font.Font(None, 28)
        title_text = font.render(f"Level {level_id}: {level['name']}", True, BLACK)
        title_rect = title_text.get_rect(center=(x + button_width // 2, y + button_height // 2))
        window.blit(title_text, title_rect)
        
        # Draw completion status - draw star directly instead of using character
        if is_completed:
            star_center_x = x + button_width - 30
            star_center_y = y + button_height // 2
            draw_star(window, star_center_x, star_center_y, 12, (255, 215, 0))  # Yellow star
        # Remove lock icon display - no longer needed
        
        # Record clickable buttons
        if is_unlocked:
            draw_menu.button_rects[f"level_{level_id}"] = button_rect
    
    # Reset progress button
    reset_button_rect = pygame.Rect(window.get_width() - 200, 50, 150, 40)
    pygame.draw.rect(window, (255, 100, 100), reset_button_rect)  # Light red background
    pygame.draw.rect(window, BLACK, reset_button_rect, 2)
    button_font = pygame.font.Font(None, 24)
    reset_text = button_font.render("Reset Progress", True, BLACK)
    reset_text_rect = reset_text.get_rect(center=reset_button_rect.center)
    window.blit(reset_text, reset_text_rect)
    
    draw_menu.button_rects["reset_progress"] = reset_button_rect
    
    # Back button
    back_button_rect = pygame.Rect(50, 50, 100, 40)
    # 根据鼠标悬停状态改变颜色
    if menu_hovered == "back":
        pygame.draw.rect(window, LIGHT_YELLOW, back_button_rect)
    else:
        pygame.draw.rect(window, WHITE, back_button_rect)
    pygame.draw.rect(window, BLACK, back_button_rect, 2)
    button_font = pygame.font.Font(None, 32)
    back_text = button_font.render("Back", True, BLACK)
    back_text_rect = back_text.get_rect(center=back_button_rect.center)
    window.blit(back_text, back_text_rect)
    
    draw_menu.button_rects["back"] = back_button_rect


def draw_menu():
    """绘制主菜单界面"""
    global replay_files, renaming_file, rename_input
    window.fill(BACKGROUND)
    
    # 确保button_rects字典存在并清空之前的记录
    if not hasattr(draw_menu, 'button_rects'):
        draw_menu.button_rects = {}
    else:
        draw_menu.button_rects.clear()
    
    # 如果选择了practice模式且有关卡配置，显示关卡选择界面
    if game_mode == 'practice' and levels_config:
        draw_practice_levels()
        return
    
    # 如果选择了replay模式，显示文件选择界面
    if game_mode == 'replay':
        # 绘制标题
        title_font = pygame.font.Font(None, 48)
        title_text = title_font.render("Select Game Record", True, BLACK)
        title_rect = title_text.get_rect(center=(window.get_width()//2, 100))
        window.blit(title_text, title_rect)
        
        # 获取游戏记录文件列表
        if not replay_files:
            try:
                # 使用绝对路径以防工作目录问题
                base_dir = os.path.dirname(os.path.abspath(__file__))
                records_dir = os.path.join(base_dir, 'game_records')
                
                if not os.path.exists(records_dir):
                    os.makedirs(records_dir)
                    
                files = os.listdir(records_dir)
                json_files = [f for f in files if f.endswith('.json') and f != 'custom_names.json']
                # 按文件名（时间）倒序排序，最新的在前
                json_files.sort(reverse=True)
                replay_files.extend(json_files)
                # 加载自定义名称
                custom_names = custom_setup.load_custom_names()
                print(f"Loaded {len(replay_files)} game records from {records_dir}")
            except Exception as e:
                print(f"Error loading game records: {e}")
                import traceback
                traceback.print_exc()
                replay_files = []
        
        # 显示文件列表
        button_font = pygame.font.Font(None, 32)
        small_font = pygame.font.Font(None, 24)
        button_width = 500
        button_height = 50
        button_spacing = 60
        start_y = 150
        
        # 分页逻辑
        ITEMS_PER_PAGE = 8
        total_pages = (len(replay_files) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
        if total_pages == 0: total_pages = 1
        
        global replay_page
        if replay_page >= total_pages: replay_page = total_pages - 1
        if replay_page < 0: replay_page = 0
        
        start_idx = replay_page * ITEMS_PER_PAGE
        end_idx = min(start_idx + ITEMS_PER_PAGE, len(replay_files))
        
        if not replay_files:
            no_files_text = button_font.render("No game records found", True, BLACK)
            no_files_rect = no_files_text.get_rect(center=(window.get_width()//2, 300))
            window.blit(no_files_text, no_files_rect)
        else:
            for i, filename in enumerate(replay_files[start_idx:end_idx]):
                real_index = start_idx + i
                y = start_y + i * button_spacing
                button_rect = pygame.Rect(
                    window.get_width()//2 - button_width//2,
                    y,
                    button_width,
                    button_height
                )
                
                # 根据鼠标悬停状态改变颜色
                if menu_hovered == f"file_{i}":
                    button_color = LIGHT_YELLOW
                    text_color = BLACK
                else:
                    button_color = WHITE
                    text_color = BLACK
                    
                # 绘制按钮
                pygame.draw.rect(window, button_color, button_rect)
                pygame.draw.rect(window, BLACK, button_rect, 2)
                
                # 如果正在重命名这个文件
                if renaming_file == filename:
                    # 显示输入框
                    input_rect = pygame.Rect(button_rect.x + 10, button_rect.y + 10, button_width - 120, 30)
                    pygame.draw.rect(window, WHITE, input_rect)
                    pygame.draw.rect(window, BLUE, input_rect, 2)
                    
                    # 显示输入文本
                    input_text = button_font.render(rename_input, True, BLACK)
                    window.blit(input_text, (input_rect.x + 5, input_rect.y + 5))
                    
                    # 确认按钮
                    confirm_rect = pygame.Rect(button_rect.x + button_width - 100, button_rect.y + 10, 40, 30)
                    pygame.draw.rect(window, (0, 255, 0), confirm_rect)
                    pygame.draw.rect(window, BLACK, confirm_rect, 2)
                    confirm_text = small_font.render("OK", True, WHITE)
                    confirm_text_rect = confirm_text.get_rect(center=confirm_rect.center)
                    window.blit(confirm_text, confirm_text_rect)
                    
                    # 取消按钮
                    cancel_rect = pygame.Rect(button_rect.x + button_width - 50, button_rect.y + 10, 40, 30)
                    pygame.draw.rect(window, RED, cancel_rect)
                    pygame.draw.rect(window, BLACK, cancel_rect, 2)
                    cancel_text = small_font.render("X", True, WHITE)
                    cancel_text_rect = cancel_text.get_rect(center=cancel_rect.center)
                    window.blit(cancel_text, cancel_text_rect)
                    
                    # 存储按钮区域
                    draw_menu.button_rects[f"confirm_{i}"] = confirm_rect
                    draw_menu.button_rects[f"cancel_{i}"] = cancel_rect
                elif deleting_file == filename:
                    # 确认删除界面
                    # 提示文本
                    msg_font = pygame.font.Font(None, 24)
                    msg_text = msg_font.render("Sure?", True, RED)
                    msg_rect = msg_text.get_rect(right=button_rect.x + button_width - 110, centery=button_rect.centery)
                    window.blit(msg_text, msg_rect)

                    # Yes/Confirm
                    yes_rect = pygame.Rect(button_rect.x + button_width - 100, button_rect.y + 10, 40, 30)
                    pygame.draw.rect(window, RED, yes_rect)
                    pygame.draw.rect(window, BLACK, yes_rect, 2)
                    yes_text = small_font.render("Yes", True, WHITE)
                    yes_text_rect = yes_text.get_rect(center=yes_rect.center)
                    window.blit(yes_text, yes_text_rect)

                    # No/Cancel
                    no_rect = pygame.Rect(button_rect.x + button_width - 50, button_rect.y + 10, 40, 30)
                    pygame.draw.rect(window, WHITE, no_rect)
                    pygame.draw.rect(window, BLACK, no_rect, 2)
                    no_text = small_font.render("No", True, BLACK)
                    no_text_rect = no_text.get_rect(center=no_rect.center)
                    window.blit(no_text, no_text_rect)

                    draw_menu.button_rects[f"confirm_delete_{i}"] = yes_rect
                    draw_menu.button_rects[f"cancel_delete_{i}"] = no_rect
                else:
                    # 显示棋谱名称
                    display_name = get_display_name(filename, real_index)
                    total_moves, date_str = get_game_info(filename)
                    
                    # 主要棋谱名称
                    text = button_font.render(display_name, True, text_color)
                    text_rect = text.get_rect(left=button_rect.x + 10, centery=button_rect.centery)
                    window.blit(text, text_rect)
                    
                    # 右边显示步数和时间（较小字体）
                    info_font = pygame.font.Font(None, 20)  # 稍微缩小的字体
                    info_text = f"{date_str}  St: {total_moves}"
                    info_surface = info_font.render(info_text, True, (100, 100, 100))  # 灰色文字
                    info_rect = info_surface.get_rect(right=button_rect.right - 160, centery=button_rect.centery)
                    window.blit(info_surface, info_rect)
                    
                    # 重命名按钮
                    rename_rect = pygame.Rect(button_rect.x + button_width - 150, button_rect.y + 10, 80, 30)
                    pygame.draw.rect(window, LIGHT_BLUE, rename_rect)
                    pygame.draw.rect(window, BLACK, rename_rect, 2)
                    rename_text = small_font.render("Rename", True, BLACK)
                    rename_text_rect = rename_text.get_rect(center=rename_rect.center)
                    window.blit(rename_text, rename_text_rect)

                    # 删除按钮
                    delete_rect = pygame.Rect(button_rect.x + button_width - 60, button_rect.y + 10, 50, 30)
                    pygame.draw.rect(window, (255, 100, 100), delete_rect)
                    pygame.draw.rect(window, BLACK, delete_rect, 2)
                    delete_text = small_font.render("Del", True, BLACK)
                    delete_text_rect = delete_text.get_rect(center=delete_rect.center)
                    window.blit(delete_text, delete_text_rect)
                    
                    # 存储按钮区域用于点击检测
                    draw_menu.button_rects[f"file_{i}"] = pygame.Rect(button_rect.x, button_rect.y, button_width - 160, button_height)
                    draw_menu.button_rects[f"rename_{i}"] = rename_rect
                    draw_menu.button_rects[f"delete_{i}"] = delete_rect
        
        # 绘制翻页控件
        control_y = start_y + ITEMS_PER_PAGE * button_spacing + 10
        
        # Prev 按钮
        if replay_page > 0:
            prev_rect = pygame.Rect(window.get_width()//2 - 140, control_y, 80, 40)
            if menu_hovered == 'replay_prev':
                pygame.draw.rect(window, LIGHT_YELLOW, prev_rect)
            else:
                pygame.draw.rect(window, WHITE, prev_rect)
            pygame.draw.rect(window, BLACK, prev_rect, 2)
            prev_text = button_font.render("Prev", True, BLACK)
            prev_text_rect = prev_text.get_rect(center=prev_rect.center)
            window.blit(prev_text, prev_text_rect)
            draw_menu.button_rects['replay_prev'] = prev_rect
            
        # Next 按钮
        if replay_page < total_pages - 1:
            next_rect = pygame.Rect(window.get_width()//2 + 60, control_y, 80, 40)
            if menu_hovered == 'replay_next':
                pygame.draw.rect(window, LIGHT_YELLOW, next_rect)
            else:
                pygame.draw.rect(window, WHITE, next_rect)
            pygame.draw.rect(window, BLACK, next_rect, 2)
            next_text = button_font.render("Next", True, BLACK)
            next_text_rect = next_text.get_rect(center=next_rect.center)
            window.blit(next_text, next_text_rect)
            draw_menu.button_rects['replay_next'] = next_rect
            
        # 页码
        page_info = f"{replay_page + 1} / {total_pages}"
        page_text = button_font.render(page_info, True, BLACK)
        page_rect = page_text.get_rect(center=(window.get_width()//2, control_y + 20))
        window.blit(page_text, page_rect)
        
        # 返回按钮
        back_button_rect = pygame.Rect(50, 50, 100, 40)
        # 根据鼠标悬停状态改变颜色
        if menu_hovered == "back":
            pygame.draw.rect(window, LIGHT_YELLOW, back_button_rect)
        else:
            pygame.draw.rect(window, WHITE, back_button_rect)
        pygame.draw.rect(window, BLACK, back_button_rect, 2)
        back_text = button_font.render("Back", True, BLACK)
        back_text_rect = back_text.get_rect(center=back_button_rect.center)
        window.blit(back_text, back_text_rect)
        
        draw_menu.button_rects["back"] = back_button_rect
        
    # 如果选择了practice模式，显示自定义棋谱选择界面
    elif game_mode == 'practice':
        # 绘制标题
        title_font = pygame.font.Font(None, 48)
        title_text = title_font.render("Select Custom Setup", True, BLACK)
        title_rect = title_text.get_rect(center=(window.get_width()//2, 100))
        window.blit(title_text, title_rect)
        
        # 获取自定义棋谱文件列表
        custom_files = custom_setup.load_custom_setup_files()
        
        # 显示文件列表
        button_font = pygame.font.Font(None, 32)
        button_width = 500
        button_height = 50
        button_spacing = 60
        start_y = 150
        
        if not custom_files:
            no_files_text = button_font.render("No custom setups found", True, BLACK)
            no_files_rect = no_files_text.get_rect(center=(window.get_width()//2, 300))
            window.blit(no_files_text, no_files_rect)
        else:
            for i, filename in enumerate(custom_files[:8]):  # 最多显示8个文件
                y = start_y + i * button_spacing
                button_rect = pygame.Rect(
                    window.get_width()//2 - button_width//2,
                    y,
                    button_width,
                    button_height
                )
                
                # 根据鼠标悬停状态改变颜色
                if menu_hovered == f"custom_{i}":
                    button_color = LIGHT_YELLOW
                    text_color = BLACK
                else:
                    button_color = WHITE
                    text_color = BLACK
                    
                # 绘制按钮
                pygame.draw.rect(window, button_color, button_rect)
                pygame.draw.rect(window, BLACK, button_rect, 2)
                
                # 显示棋谱信息
                pieces_info, date_str = custom_setup.get_custom_setup_info(filename)
                display_text = f"Setup {i+1} - {pieces_info} - {date_str}"
                
                text = button_font.render(display_text, True, text_color)
                text_rect = text.get_rect(center=button_rect.center)
                window.blit(text, text_rect)
                
                # 存储按钮区域用于点击检测
                draw_menu.button_rects[f"custom_{i}"] = button_rect
        
        # 返回按钮
        back_button_rect = pygame.Rect(50, 50, 100, 40)
        pygame.draw.rect(window, WHITE, back_button_rect)
        pygame.draw.rect(window, BLACK, back_button_rect, 2)
        back_text = button_font.render("Back", True, BLACK)
        back_text_rect = back_text.get_rect(center=back_button_rect.center)
        window.blit(back_text, back_text_rect)
        
        draw_menu.button_rects["back"] = back_button_rect
        
    elif game_mode == 'lan':
        # LAN 房间创建/加入界面
        title_font = pygame.font.Font(None, 48)
        title_text = title_font.render("LAN - Host / Join", True, BLACK)
        title_rect = title_text.get_rect(center=(window.get_width()//2, 100))
        window.blit(title_text, title_rect)

        button_font = pygame.font.Font(None, 32)

        # Host as Blue
        host_blue_rect = pygame.Rect(window.get_width()//2 - 260, 180, 220, 50)
        pygame.draw.rect(window, LIGHT_BLUE if menu_hovered == 'host_blue' else WHITE, host_blue_rect)
        pygame.draw.rect(window, BLACK, host_blue_rect, 2)
        window.blit(button_font.render("Host as Blue", True, BLACK), host_blue_rect.move(20, 10))
        draw_menu.button_rects['host_blue'] = host_blue_rect

        # Host as Red
        host_red_rect = pygame.Rect(window.get_width()//2 + 40, 180, 220, 50)
        pygame.draw.rect(window, LIGHT_YELLOW if menu_hovered == 'host_red' else WHITE, host_red_rect)
        pygame.draw.rect(window, BLACK, host_red_rect, 2)
        window.blit(button_font.render("Host as Red", True, BLACK), host_red_rect.move(30, 10))
        draw_menu.button_rects['host_red'] = host_red_rect

        # Rooms list
        refresh_rect = pygame.Rect(window.get_width()//2 - 120, 250, 240, 40)
        pygame.draw.rect(window, WHITE, refresh_rect)
        pygame.draw.rect(window, BLACK, refresh_rect, 2)
        window.blit(button_font.render("Refresh Rooms", True, BLACK), refresh_rect.move(20, 8))
        draw_menu.button_rects['lan_refresh'] = refresh_rect

        # Hosting 状态提示（如果当前正在作为主机）
        small_font = pygame.font.Font(None, 24)
        if hasattr(draw_menu, 'hosting_info') and draw_menu.hosting_info:
            hi = draw_menu.hosting_info
            host_text = f"Hosting: {hi.get('room_name','room')} @ {hi.get('ip','?')}:{hi.get('port','?')} ({hi.get('host_side','blue')} host)"
            host_rect = pygame.Rect(window.get_width()//2 - 250, 300, 500, 30)
            pygame.draw.rect(window, LIGHT_BLUE, host_rect)
            pygame.draw.rect(window, BLACK, host_rect, 2)
            window.blit(small_font.render(host_text, True, BLACK), host_rect.move(10, 6))
            start_y = 340
        else:
            start_y = 310

        # Display rooms
        if not hasattr(draw_menu, 'lan_rooms'):
            draw_menu.lan_rooms = []
        small_font = pygame.font.Font(None, 24)
        for i, info in enumerate(draw_menu.lan_rooms[:6]):
            y = start_y + i * 55
            item_rect = pygame.Rect(window.get_width()//2 - 250, y, 500, 45)
            pygame.draw.rect(window, LIGHT_BLUE if menu_hovered == f'lan_room_{i}' else WHITE, item_rect)
            pygame.draw.rect(window, BLACK, item_rect, 2)
            text = f"{info.get('room_name','room')} @ {info.get('ip',info.get('addr','?'))}:{info.get('port','?')} ({info.get('host_side','blue')} host)"
            window.blit(small_font.render(text, True, BLACK), item_rect.move(10, 12))
            draw_menu.button_rects[f'lan_room_{i}'] = item_rect

        # 返回按钮
        back_button_rect = pygame.Rect(50, 50, 100, 40)
        pygame.draw.rect(window, WHITE, back_button_rect)
        pygame.draw.rect(window, BLACK, back_button_rect, 2)
        back_text = button_font.render("Back", True, BLACK)
        back_text_rect = back_text.get_rect(center=back_button_rect.center)
        window.blit(back_text, back_text_rect)
        draw_menu.button_rects['back'] = back_button_rect

    else:
        # 原有的主菜单界面
        # 绘制标题
        title_font = pygame.font.Font(None, 72)
        title_text = title_font.render("International Number Chess", True, BLACK)
        title_rect = title_text.get_rect(center=(window.get_width()//2, 150))
        window.blit(title_text, title_rect)
        
        # 菜单选项
        menu_options = ["Play", "Replay", "Practice", "Custom Setup", "LAN"]
        button_font = pygame.font.Font(None, 48)
        button_width = 250  # 从200增加到250
        button_height = 60
        button_spacing = 80
        start_y = 280  # 稍微上移以容纳第四个选项
        
        for i, option in enumerate(menu_options):
            y = start_y + i * button_spacing
            button_rect = pygame.Rect(
                window.get_width()//2 - button_width//2,
                y,
                button_width,
                button_height
            )
            
            # 根据鼠标悬停状态改变颜色
            if menu_hovered == option:
                button_color = LIGHT_YELLOW
                text_color = BLACK
            else:
                button_color = WHITE
                text_color = BLACK
                
            # 绘制按钮
            pygame.draw.rect(window, button_color, button_rect)
            pygame.draw.rect(window, BLACK, button_rect, 2)
            
            # 绘制文字
            text = button_font.render(option, True, text_color)
            text_rect = text.get_rect(center=button_rect.center)
            window.blit(text, text_rect)
            
            # 存储按钮区域用于点击检测
            draw_menu.button_rects[option] = button_rect


def get_menu_button_at_pos(pos):
    """获取指定位置的菜单按钮"""
    if hasattr(draw_menu, 'button_rects') and draw_menu.button_rects:
        for option, rect in draw_menu.button_rects.items():
            if rect.collidepoint(pos):
                return option
    return None


def draw_level_hint(screen):
    """Draw level hint information in the top right corner of the game interface"""
    global hint_box_pos, hint_box_dragging, hint_box_offset
    
    if game_mode != 'practice' or not current_level or not levels_config:
        return
    
    level_info = levels_config['levels'][current_level - 1]
    
    # Dynamic calculation of hint box size
    base_width = 240
    base_height = 90
    
    # Adjust height based on text length
    desc_font = pygame.font.Font(None, 18)
    objective_text = level_info['objective']
    
    def wrap_text(text, font, max_width):
        words = text.split(' ')
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    text_width = base_width - 20
    objective_lines = wrap_text(objective_text, desc_font, text_width)
    
    # Adjust height based on number of lines
    line_count = len(objective_lines)
    hint_height = base_height + max(0, (line_count - 2) * 18)
    hint_width = base_width
    
    # Initialize hint box position if not set
    if hint_box_pos[0] is None:
        hint_box_pos = (window_size + OFFSET_X - hint_width - 20, 20)
    
    hint_x, hint_y = hint_box_pos
    
    # Create transparent surface
    hint_surface = pygame.Surface((hint_width, hint_height), pygame.SRCALPHA)
    
    # Draw hint box background with 70% transparency (alpha = 255 * 0.3 = 76)
    hint_rect = pygame.Rect(0, 0, hint_width, hint_height)
    pygame.draw.rect(hint_surface, (255, 255, 240, 220), hint_rect)  # Light yellow background with transparency
    pygame.draw.rect(hint_surface, (0, 0, 0, 220), hint_rect, 2)  # Black border with some transparency
    
    # Draw level title
    title_font = pygame.font.Font(None, 22)
    title_text = title_font.render(f"Level {current_level}: {level_info['name']}", True, BLACK)
    title_rect = title_text.get_rect(center=(hint_width // 2, 15))
    hint_surface.blit(title_text, title_rect)
    
    # Draw objective description text
    start_y = 35
    for i, line in enumerate(objective_lines):
        desc_text = desc_font.render(line, True, BLACK)
        desc_rect = desc_text.get_rect(center=(hint_width // 2, start_y + i * 18))
        hint_surface.blit(desc_text, desc_rect)
    
    # Show allowed piece to move
    if allowed_piece:
        color_name = "Blue" if allowed_piece[0] == "blue" else "Red"
        target_y = start_y + len(objective_lines) * 18 + 5
        target_text = desc_font.render(f"Only move: {color_name} piece {allowed_piece[1]}", True, (200, 0, 0))
        target_rect = target_text.get_rect(center=(hint_width // 2, target_y))
        hint_surface.blit(target_text, target_rect)
    
    # Blit the transparent surface to the main screen
    screen.blit(hint_surface, (hint_x, hint_y))
    
    # Store the hint box rect for drag detection
    global hint_box_rect
    hint_box_rect = pygame.Rect(hint_x, hint_y, hint_width, hint_height)


def draw_board():
    global formula_text
    window.fill(WHITE)
    all_points = []
    point_map = {}  # 用于存储每个点的坐标和索引
    
    # 绘制当前玩家指示灯
    indicator_radius = 30
    indicator_pos = (50, 150)  # 左上角位置
    indicator_color = BLUE if current_player == 'blue' else RED
    pygame.draw.circle(window, indicator_color, indicator_pos, indicator_radius)
    pygame.draw.circle(window, BLACK, indicator_pos, indicator_radius, 2)  # 黑色边框
    
    # 生成所有点的坐标
    for col_index, [num, offset] in enumerate(POINTS):
        y = BEGIN_Y + col_index * GRID * math.sqrt(3) / 2
        col_points = []
        for i in range(num):
            raw_index = offset + i * 2
            x = BEGIN_X + raw_index * GRID * 0.5
            col_points.append([x, y, col_index, i])
            point_map[(col_index, raw_index)] = (x, y)
        all_points.extend(col_points)
    
    # 先画连线（虚线）
    for point in all_points:
        x, y, col_index, point_index = point
        neighbors = get_neighbors(x, y, [[p[0], p[1]] for p in all_points])
        for neighbor in neighbors:
            draw_dashed_line(window, BLACK, 
                            (int(x), int(y)), 
                            (int(neighbor[0]), int(neighbor[1])), 3, 5, 5)
    
    # 再画圆点（这样圆点会覆盖在线上）
    for point in all_points:
        x, y, col_index, point_index = point
        color = get_point_color(x, y, col_index, point_index, POINTS[col_index][0])
        if color == "DUAL":
            # 绘制双色圆点
            draw_dual_color_circle(window, (int(x), int(y)), RADIUS)
        else:
            # 绘制普通圆点
            pygame.draw.circle(window, color, (int(x), int(y)), RADIUS)
            pygame.draw.circle(surface=window, color=BLACK, center=(int(x), int(y)), radius=RADIUS, width=2)
            # 在蓝/红阵营的圆点中心绘制初始编号（使用深蓝/深红）
            raw_index = POINTS[col_index][1] + point_index * 2
            pos_key = (col_index, raw_index)
            num_text = None
            num_color = None
            # 左侧 0-3 列为蓝阵营编号
            if col_index < 4 and pos_key in SCORING_MAP['blue']:
                num_text = SCORING_MAP['blue'][pos_key]
                num_color = (100, 0, 0)    # 深蓝
            # 右侧 11-14 列为红阵营编号
            elif col_index >= 11 and pos_key in SCORING_MAP['red']:
                num_text = SCORING_MAP['red'][pos_key]
                num_color = (0, 50, 150)# 深红
            # 其他区域不绘制编号
            if num_text is not None:
                font = pygame.font.SysFont('Arial', int(RADIUS * 0.9))
                text_surf = font.render(str(num_text), True, num_color)
                text_rect = text_surf.get_rect(center=(int(x), int(y)))
                window.blit(text_surf, text_rect)
    
    # 如果有选中的棋子，显示备选跨越点（在回放但非试下模式下不显示灰/紫点）
    potential_jumps = []
    potential_jumps2 = []
    if selected_piece and not board_locked and not (game_mode == 'replay' and not try_mode):
        potential_jumps = get_potential_jump_positions(selected_piece[2], point_map, BLUE_PIECES, RED_PIECES, all_points, 2)
                
        if potential_jumps:
            for col, row, _ in potential_jumps:  # 修改：现在返回col,row坐标
                # 使用point_map将col,row转换为x,y坐标用于绘制
                x, y = point_map[(col, row)]
                pygame.draw.circle(window, GRAY, (int(x), int(y)), RADIUS + 3, 3)  # 灰色圆环标记备选跨越点
        
        initial_moves = []
        res = []
        # print(valid_moves)
        if valid_moves:
            for pos_x, pos_y, target_pos, direction in valid_moves:
                piece_x, piece_y = selected_piece[3]
                if (pos_x - piece_x)**2 + (pos_y - piece_y)**2 > GRID ** 2 * 1.5:
                    # 转换为棋盘坐标以保持一致性
                    col, row = xy_to_pos(pos_x, pos_y)
                    initial_moves.append((col, row, direction))
                # 同样转换res中的坐标
                col, row = xy_to_pos(pos_x, pos_y)
                res.append((col, row, direction))
        # potential_jumps已经是棋盘坐标格式，直接扩展
        initial_moves.extend(potential_jumps)
        res.extend(potential_jumps)
        potential_jumps2 = get_potential_jump_recursion(point_map, BLUE_PIECES, RED_PIECES, all_points, res, initial_moves, [])
        if potential_jumps2:
            # print("1:" + str(potential_jumps))
            # print("2:" + str(potential_jumps2))
            for i in range(len(potential_jumps2) - 1, -1, -1):  # 修改：现在获取col, row坐标
                # 使用point_map将col,row转换为x,y坐标
                col, row, _ = potential_jumps2[i]
                start = (selected_piece[2][0], selected_piece[2][1], (2, 2))
                temp_paths = get_paths(start, (col, row), point_map, BLUE_PIECES, RED_PIECES, all_points, [], [])
                if not temp_paths:
                    potential_jumps2.pop(i)
            for col, row, _ in potential_jumps2:  # 现在统一使用棋盘坐标
                # 使用point_map转换为屏幕坐标进行绘制
                x, y = point_map[(col, row)]
                pygame.draw.circle(window, PURPLE, (int(x), int(y)), RADIUS + 3, 3)  # 紫色圆环标记备选跨越点

    # 高亮显示有效移动位置（最后绘制，确保显示在最上层）
    if selected_piece and valid_moves and not board_locked and not (game_mode == 'replay' and not try_mode):
        highlight_valid_moves(window, [(x, y) for x, y, _, _ in valid_moves])
    # 如果有选中的灰色点，高亮显示
    if selected_gray_point and board_locked and not (game_mode == 'replay' and not try_mode):
        x, y = selected_gray_point
        pygame.draw.circle(window, SELECT, (int(x), int(y)), RADIUS + 5, 4)  # 红色高亮选中的灰色点
    
    # 始终使用正常棋子位置以保持一致
    blue_pieces = BLUE_PIECES
    red_pieces = RED_PIECES
    
    # 绘制蓝色棋子
    for number, (col, row) in blue_pieces.items():
        if (col, row) in point_map:
            x, y = point_map[(col, row)]
            # 在回放模式下也保持选中棋子高亮（禁用灰/紫点但允许高亮）
            is_selected = (selected_piece and selected_piece[0] == 'blue' and selected_piece[1] == number and not board_locked)
            draw_piece_with_number(window, (int(x), int(y)), RADIUS, BLUE, number, is_selected)
    
    # 绘制红色棋子
    for number, (col, row) in red_pieces.items():
        if (col, row) in point_map:
            x, y = point_map[(col, row)]
            # 在回放模式下也保持选中棋子高亮（禁用灰/紫点但允许高亮）
            is_selected = (selected_piece and selected_piece[0] == 'red' and selected_piece[1] == number and not board_locked)
            draw_piece_with_number(window, (int(x), int(y)), RADIUS, RED, number, is_selected)
    
    # 在practice模式下绘制目标点标注
    if game_mode == 'practice' and current_level and levels_config:
        level_info = levels_config['levels'][current_level - 1]
        if 'win_condition' in level_info and 'target_position' in level_info['win_condition']:
            target_pos = level_info['win_condition']['target_position']
            target_col, target_row = target_pos[0], target_pos[1]
            
            if (target_col, target_row) in point_map:
                x, y = point_map[(target_col, target_row)]
                # 创建半透明红色表面
                transparent_surface = pygame.Surface((RADIUS * 2 + 20, RADIUS * 2 + 20), pygame.SRCALPHA)
                red_transparent = (255, 0, 0, 100)  # 红色，透明度100
                pygame.draw.circle(transparent_surface, red_transparent, (RADIUS + 10, RADIUS + 10), RADIUS + 10)
                window.blit(transparent_surface, (int(x) - RADIUS - 10, int(y) - RADIUS - 10))
    button_areas = draw_calculation_area()
    # 在replay模式下绘制控制面板，否则绘制计算版区域
    if game_mode == 'replay' and replay_data:
        # replay_button_areas = draw_replay_controls()
        if replay_step > 0 and replay_step <= len(replay_data.get('moves', [])):
            current_move = replay_data['moves'][replay_step - 1]
            if 'formula' in current_move and current_move['formula']:
                # 处理新的formula数组格式
                formula_list = current_move['formula']
                if isinstance(formula_list, list) and len(formula_list) > 0:
                    # 将多组formula合并显示，用=连接
                    formula_text_content = f"Formula: {' = '.join(formula_list)}"
                else:
                    formula_text_content = "No formula for this move"
            else:
                formula_text_content = "No formula for this move"
        else:
            formula_text_content = "No move selected"
        
        if not try_mode:
            formula_text = formula_text_content
        
    # 新增：左上角显示上帝模式提示
    if god_mode:
        font_god = pygame.font.Font(None, 28)
        god_text = font_god.render('God Mode', True, (255,0,0))
        window.blit(god_text, (20, 50))
    
    # Back button for REPLAY state
    if state == "REPLAY":
        button_font = pygame.font.Font(None, 32)
        back_button_rect = pygame.Rect(50, 50, 100, 40)
        # 根据鼠标悬停状态改变颜色
        if menu_hovered == "back":
            pygame.draw.rect(window, LIGHT_YELLOW, back_button_rect)
        else:
            pygame.draw.rect(window, WHITE, back_button_rect)
        pygame.draw.rect(window, BLACK, back_button_rect, 2)
        back_text = button_font.render("Back", True, BLACK)
        back_text_rect = back_text.get_rect(center=back_button_rect.center)
        window.blit(back_text, back_text_rect)
        
        # 存储按钮区域用于点击检测
        if not hasattr(draw_board, 'replay_button_rects'):
            draw_board.replay_button_rects = {}
        draw_board.replay_button_rects["back"] = back_button_rect
    
    # 新增：END状态下显示分数和胜负
    if state == "END":
        blue_score, red_score = calculate_point()
        font_end = pygame.font.Font(None, 36)
        font_small = pygame.font.Font(None, 28)
        result = ""
        if blue_score > red_score:
            result = "BLUE"
        elif red_score > blue_score:
            result = "RED"
        else:
            result = "DRAW"
        text1 = font_end.render(f"BLUE SCORE: {blue_score}", True, BLUE)
        text2 = font_end.render(f"RED SCORE: {red_score}", True, RED)
        text3 = font_end.render(f"{result} WINS", True, (0,0,0))
        window.blit(text1, (window_size//2-100, window_size//2-60))
        window.blit(text2, (window_size//2-100, window_size//2))
        window.blit(text3, (window_size//2-100, window_size//2+60))
        
        # Back button for END state
        button_font = pygame.font.Font(None, 32)
        back_button_rect = pygame.Rect(50, 50, 100, 40)
        # 根据鼠标悬停状态改变颜色
        if menu_hovered == "back":
            pygame.draw.rect(window, LIGHT_YELLOW, back_button_rect)
        else:
            pygame.draw.rect(window, WHITE, back_button_rect)
        pygame.draw.rect(window, BLACK, back_button_rect, 2)
        back_text = button_font.render("Back", True, BLACK)
        back_text_rect = back_text.get_rect(center=back_button_rect.center)
        window.blit(back_text, back_text_rect)
        
        # 存储按钮区域用于点击检测
        if not hasattr(draw_board, 'end_button_rects'):
            draw_board.end_button_rects = {}
        draw_board.end_button_rects["back"] = back_button_rect

    # 绘制关卡提示信息（仅在practice模式下）
    if game_mode == 'practice':
        draw_level_hint(window)

    # print(get_line_coordinates(14, 10, point_map))

    return all_points, point_map, button_areas, potential_jumps, potential_jumps2


def main():
    global selected_piece, valid_moves, current_player, selected_numbers, operation, calculation_result, board_locked, selected_gray_point, formula_text, hovered_button, number_res, color_locked, continuous_span, paths, expected_result, continuous_span_line, state, winner, god_mode, menu_hovered, game_mode, replay_playing, replay_step, formula_res, renaming_file, rename_input, dragging_piece, available_pieces, custom_setup_pieces, BLUE_PIECES, RED_PIECES, hint_box_pos, hint_box_dragging, hint_box_offset, hint_box_rect, replay_last_update
    global net_session, local_side, replay_page, deleting_file
    
    pygame.init()
    clock = pygame.time.Clock()
    
    # 初始化游戏记录
    init_game_record()
    
    # 初始化关卡系统
    load_levels_config()
    load_practice_progress()
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # 游戏退出时保存记录（仅在正式对局且非试下模式下）
                if game_record and game_mode == 'play' and not try_mode:
                    save_game_record()
                pygame.quit()
                sys.exit()
            
            if state == "MENU":
                # 处理菜单界面的鼠标移动
                if event.type == pygame.MOUSEMOTION:
                    menu_hovered = get_menu_button_at_pos(event.pos)
                
                # 处理键盘输入（用于重命名）
                elif event.type == pygame.KEYDOWN:
                    if renaming_file:
                        if event.key == pygame.K_RETURN:  # 回车确认
                            if rename_input.strip():
                                custom_names[renaming_file] = rename_input.strip()
                                custom_setup.save_custom_names(custom_names)
                            renaming_file = None
                            rename_input = ""
                        elif event.key == pygame.K_ESCAPE:  # ESC取消
                            renaming_file = None
                            rename_input = ""
                        elif event.key == pygame.K_BACKSPACE:  # 退格删除
                            rename_input = rename_input[:-1]
                        else:
                            # 只允许英文字母、数字、空格和常用符号
                            if event.unicode and (event.unicode.isalnum() or event.unicode in " -_()[]{}.,!?"):
                                if len(rename_input) < 30:  # 限制长度
                                    rename_input += event.unicode
                
                # 处理菜单界面的点击
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # 左键点击
                        clicked_button = get_menu_button_at_pos(event.pos)
                        
                        if clicked_button:
                            if clicked_button == "back":
                                game_mode = None
                                replay_files.clear()
                                renaming_file = None
                                rename_input = ""
                                # 清理 LAN 会话
                                if 'net_session' in globals() and net_session:
                                    try:
                                        net_session.close()
                                    except Exception:
                                        pass
                                    net_session = None
                                    local_side = None
                            elif clicked_button.startswith("level_"):
                                if game_mode == 'practice':
                                    level_id = get_level_button_at_pos(event.pos)
                                    if level_id and start_level(level_id):
                                        state = "GAME"
                                        # 重置游戏状态
                                        selected_piece = None
                                        valid_moves = []
                                        current_player = 'blue'
                                        board_locked = False
                                        color_locked = False
                                        calculation_result = None
                                        continuous_span_line = -1
                                        init_game_record()
                            elif clicked_button.startswith("custom_"):
                                if game_mode == 'practice':
                                    file_index = int(clicked_button.split("_")[1])
                                    custom_files = custom_setup.load_custom_setup_files()
                                    if file_index < len(custom_files):
                                        filename = custom_files[file_index]
                                        loaded_positions = custom_setup.load_custom_setup_file(filename)
                                        if loaded_positions:
                                            BLUE_PIECES, RED_PIECES = loaded_positions
                                            state = "GAME"
                                            game_mode = 'practice'
                                            # 重置游戏状态
                                            selected_piece = None
                                            valid_moves = []
                                            current_player = 'blue'
                                            board_locked = False
                                            color_locked = False  # 修改：允许正常的棋子交互
                                            init_game_record()
                            elif clicked_button.startswith("file_"):
                                if not renaming_file:  # 只有在不重命名时才能选择文件
                                    file_index = int(clicked_button.split("_")[1])
                                    ITEMS_PER_PAGE = 8
                                    real_index = replay_page * ITEMS_PER_PAGE + file_index
                                    if real_index < len(replay_files):
                                        selected_replay_file = replay_files[real_index]
                                        if load_replay_file(selected_replay_file):
                                            state = "REPLAY"
                                            update_replay_positions()
                            elif clicked_button.startswith("rename_"):
                                file_index = int(clicked_button.split("_")[1])
                                ITEMS_PER_PAGE = 8
                                real_index = replay_page * ITEMS_PER_PAGE + file_index
                                if real_index < len(replay_files):
                                    renaming_file = replay_files[real_index]
                                    deleting_file = None  # Clear delete state
                                    # 设置当前名称作为初始输入
                                    current_name = custom_names.get(renaming_file, "")
                                    rename_input = current_name
                            elif clicked_button.startswith("delete_"):
                                file_index = int(clicked_button.split("_")[1])
                                ITEMS_PER_PAGE = 8
                                real_index = replay_page * ITEMS_PER_PAGE + file_index
                                if real_index < len(replay_files):
                                    deleting_file = replay_files[real_index]
                                    renaming_file = None  # Clear rename state
                            elif clicked_button.startswith("confirm_delete_"):
                                file_index = int(clicked_button.split("_")[2])
                                ITEMS_PER_PAGE = 8
                                real_index = replay_page * ITEMS_PER_PAGE + file_index
                                if real_index < len(replay_files):
                                    filename_to_delete = replay_files[real_index]
                                    if filename_to_delete == deleting_file:
                                        try:
                                            # 获取绝对路径
                                            base_dir = os.path.dirname(os.path.abspath(__file__))
                                            file_path = os.path.join(base_dir, 'game_records', filename_to_delete)
                                            if os.path.exists(file_path):
                                                os.remove(file_path)
                                                print(f"Deleted file: {file_path}")
                                            
                                            # 从列表中移除
                                            replay_files.pop(real_index)
                                            
                                            # 从自定义名称中移除
                                            if filename_to_delete in custom_names:
                                                del custom_names[filename_to_delete]
                                                custom_setup.save_custom_names(custom_names)
                                                
                                            # 处理分页：如果当前页变为空且不是第一页，则回到上一页
                                            total_pages = (len(replay_files) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
                                            if replay_page >= total_pages and replay_page > 0:
                                                replay_page -= 1
                                                
                                            deleting_file = None
                                                
                                        except Exception as e:
                                            print(f"Error deleting file: {e}")
                            elif clicked_button.startswith("cancel_delete_"):
                                deleting_file = None
                            elif clicked_button == "replay_prev":
                                if replay_page > 0:
                                    replay_page -= 1
                            elif clicked_button == "replay_next":
                                ITEMS_PER_PAGE = 8
                                total_pages = (len(replay_files) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
                                if replay_page < total_pages - 1:
                                    replay_page += 1
                            elif clicked_button.startswith("confirm_"):
                                file_index = int(clicked_button.split("_")[1])
                                if renaming_file and rename_input.strip():
                                    custom_names[renaming_file] = rename_input.strip()
                                    custom_setup.save_custom_names(custom_names)
                                renaming_file = None
                                rename_input = ""
                            elif clicked_button.startswith("cancel_"):
                                renaming_file = None
                                rename_input = ""
                            elif clicked_button == "reset_progress":
                                # 确认重置对话框（可选）
                                reset_practice_progress()
                            elif game_mode is None:
                                chosen = clicked_button.lower()
                                if chosen == 'play':
                                    # 重置棋子位置到初始状态
                                    BLUE_PIECES = {
                                        0: [14, 10],    # 第15列第1个点
                                        1: [11, 13],    # 第12列第4个点
                                        2: [11, 9],     # 第12列第2个点
                                        3: [11, 11],    # 第12列第3个点
                                        4: [11, 7],     # 第12列第1个点
                                        5: [12, 8],     # 第13列第1个点
                                        6: [12, 10],    # 第13列第2个点
                                        7: [12, 12],    # 第13列第3个点
                                        8: [13, 11],    # 第14列第2个点
                                        9: [13, 9]      # 第14列第1个点
                                    }
                                    RED_PIECES = {
                                        0: [0, 10],     # 第1列第1个点
                                        1: [3, 7],      # 第4列第1个点
                                        2: [3, 11],     # 第4列第3个点
                                        3: [3, 9],      # 第4列第2个点
                                        4: [3, 13],     # 第4列第4个点
                                        5: [2, 12],     # 第3列第3个点
                                        6: [2, 10],     # 第3列第2个点
                                        7: [2, 8],      # 第3列第1个点
                                        8: [1, 9],      # 第2列第1个点
                                        9: [1, 11]      # 第2列第2个点
                                    }
                                    state = "GAME"
                                    init_game_record()
                                    game_mode = 'play'
                                elif chosen == 'replay':
                                    # 保持在菜单状态，显示文件选择
                                    game_mode = 'replay'
                                    replay_page = 0
                                elif chosen == 'practice':
                                    # 修改：保持在菜单状态，显示自定义棋谱选择
                                    game_mode = 'practice'
                                elif chosen == 'custom setup':
                                    state = "CUSTOM_SETUP"
                                    game_mode = 'custom setup'
                                elif chosen == 'lan':
                                    # 进入 LAN 菜单页
                                    game_mode = 'lan'
                            # 处理 LAN 菜单点击
                            if game_mode == 'lan':
                                if clicked_button == 'lan_refresh':
                                    try:
                                        rooms = netplay.discover_rooms(timeout=1.0)
                                        # 如果当前是主机，确保本机房间优先显示且不被刷掉
                                        if hasattr(draw_menu, 'hosting_info') and draw_menu.hosting_info:
                                            hi = draw_menu.hosting_info
                                            rooms = [hi] + [r for r in rooms
                                                            if (r.get('ip', r.get('addr')) != hi.get('ip')
                                                                or r.get('port') != hi.get('port'))]
                                        draw_menu.lan_rooms = rooms
                                    except Exception:
                                        # 刷新失败时保留已有列表；若有 hosting_info，确保其存在于顶部
                                        if hasattr(draw_menu, 'hosting_info') and draw_menu.hosting_info:
                                            hi = draw_menu.hosting_info
                                            prev = getattr(draw_menu, 'lan_rooms', []) or []
                                            draw_menu.lan_rooms = [hi] + [r for r in prev
                                                                          if (r.get('ip', r.get('addr')) != hi.get('ip')
                                                                              or r.get('port') != hi.get('port'))]
                                        else:
                                            # 不覆盖现有列表
                                            pass
                                elif clicked_button == 'host_blue' or clicked_button == 'host_red':
                                    host_side = 'blue' if clicked_button == 'host_blue' else 'red'
                                    # 异步启动并等待连接（阻塞在后台线程）
                                    import threading
                                    def host_thread():
                                        global net_session, local_side, state
                                        try:
                                            # 使用房间名为本机 IP 简化
                                            room_name = f"Room-{netplay.get_local_ip()}"
                                            # 在界面上展示 Hosting 信息，并加入列表
                                            try:
                                                info = {
                                                    'type': 'room_info',
                                                    'room_name': room_name,
                                                    'ip': netplay.get_local_ip(),
                                                    'port': netplay.TCP_PORT,
                                                    'host_side': host_side,
                                                }
                                                draw_menu.hosting_info = info
                                                if not hasattr(draw_menu, 'lan_rooms'):
                                                    draw_menu.lan_rooms = []
                                                # 将本机房间显示在顶部
                                                draw_menu.lan_rooms = [info] + [r for r in draw_menu.lan_rooms if r.get('ip') != info['ip'] or r.get('port') != info['port']]
                                            except Exception:
                                                pass
                                            net_session, _ = netplay.start_host(room_name, host_side)
                                            local_side = host_side
                                            # 切入游戏
                                            state = 'GAME'
                                            # 初始化棋子到标准开局
                                            # 与 Play 相同布局
                                            set_default_positions()
                                            init_game_record()
                                        except Exception:
                                            net_session = None
                                            local_side = None
                                    threading.Thread(target=host_thread, daemon=True).start()
                                elif clicked_button.startswith('lan_room_'):
                                    try:
                                        idx = int(clicked_button.split('_')[-1])
                                        info = draw_menu.lan_rooms[idx]
                                        ip = info.get('ip', info.get('addr'))
                                        port = info.get('port')
                                        session = netplay.join_room(ip, port)
                                        if session:
                                            net_session = session
                                            local_side = session.side
                                            # 切入游戏
                                            state = 'GAME'
                                            set_default_positions()
                                            init_game_record()
                                    except Exception:
                                        pass
                continue
            
            elif state == "CUSTOM_SETUP":
                # 处理鼠标移动事件（悬停检测）
                if event.type == pygame.MOUSEMOTION:
                    mouse_pos = pygame.mouse.get_pos()
                    hovered_button = None
                    
                    # 检查按钮悬停
                    if hasattr(draw_custom_setup, 'button_rects'):
                        for button_name, rect in draw_custom_setup.button_rects.items():
                            if rect.collidepoint(mouse_pos):
                                hovered_button = button_name
                                break
                
                # 处理自定义摆棋模式的事件
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # 左键点击
                        mouse_pos = pygame.mouse.get_pos()
                        
                        # 检查是否点击了控制按钮
                        if hasattr(draw_custom_setup, 'button_rects'):
                            for button_name, rect in draw_custom_setup.button_rects.items():
                                if rect.collidepoint(mouse_pos):
                                    if button_name == "back":
                                        state = "MENU"
                                        game_mode = None
                                    elif button_name == "clear":
                                        # 清空所有棋子
                                        custom_setup_pieces = {}
                                        available_pieces = {
                                            'blue': {i: True for i in range(10)},
                                            'red': {i: True for i in range(10)}
                                        }
                                    elif button_name == "save":
                                        # 保存自定义棋谱
                                        save_custom_setup()
                                    break
                        
                        # 检查是否点击了右侧的棋子（开始拖拽）
                        if not dragging_piece:
                            piece_area_x = window_size + 20
                            piece_area_y = OFFSET_Y + 70
                            piece_spacing = 40
                            piece_area_x_offset = 20  # 添加偏移量定义
                            piece_area_y_offset = 20  # 添加偏移量定义
                            
                            # 检查蓝色棋子
                            for i in range(10):
                                if available_pieces['blue'][i]:
                                    x = piece_area_x + (i % 2) * 70 + piece_area_x_offset  # 添加偏移量
                                    y = piece_area_y + 40 + (i // 2) * piece_spacing + piece_area_y_offset  # 添加偏移量
                                    # 修复：使用RADIUS而不是piece_size-2
                                    if (mouse_pos[0] - x) ** 2 + (mouse_pos[1] - y) ** 2 <= RADIUS ** 2:
                                        dragging_piece = ('blue', i)
                                        drag_offset = (x - mouse_pos[0], y - mouse_pos[1])
                                        break
                            
                            # 检查红色棋子
                            if not dragging_piece:
                                for i in range(10):
                                    if available_pieces['red'][i]:
                                        x = piece_area_x + (i % 2) * 70 + piece_area_x_offset  # 添加偏移量
                                        y = piece_area_y + 280 + (i // 2) * piece_spacing + piece_area_y_offset  # 添加偏移量
                                        # 修复：使用RADIUS而不是piece_size-2
                                        if (mouse_pos[0] - x) ** 2 + (mouse_pos[1] - y) ** 2 <= RADIUS ** 2:
                                            dragging_piece = ('red', i)
                                            drag_offset = (x - mouse_pos[0], y - mouse_pos[1])
                                            break
                
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1 and dragging_piece:  # 左键释放且正在拖拽
                        mouse_pos = pygame.mouse.get_pos()
                        all_points, point_map = draw_custom_setup()
                        
                        # 找到最近的棋盘点
                        min_dist = float('inf')
                        target_pos = None
                        for pos, (x, y) in point_map.items():
                            dist = (mouse_pos[0] - x) ** 2 + (mouse_pos[1] - y) ** 2
                            if dist < min_dist and dist <= (RADIUS + 10) ** 2:  # 在合理范围内
                                min_dist = dist
                                target_pos = pos
                        
                        # 如果找到了有效位置且该位置未被占用
                        if target_pos and target_pos not in custom_setup_pieces:
                            color, num = dragging_piece
                            custom_setup_pieces[target_pos] = (color, num)
                            available_pieces[color][num] = False  # 标记为已使用
                        
                        dragging_piece = None
                        drag_offset = (0, 0)
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        state = "MENU"
                        game_mode = None
                
                continue
            
            elif state == "REPLAY":
                # 处理鼠标移动事件（悬停检测）
                if event.type == pygame.MOUSEMOTION:
                    mouse_pos = pygame.mouse.get_pos()
                    menu_hovered = None
                    
                    # 检查back按钮悬停
                    if hasattr(draw_board, 'replay_button_rects') and 'back' in draw_board.replay_button_rects:
                        if draw_board.replay_button_rects['back'].collidepoint(mouse_pos):
                            menu_hovered = "back"
                # 处理回放模式的事件   
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        mouse_pos = pygame.mouse.get_pos()
                        all_points, point_map, button_areas, _, _ = draw_board()
                        # 检查back按钮点击
                        if hasattr(draw_board, 'replay_button_rects') and 'back' in draw_board.replay_button_rects:
                            if draw_board.replay_button_rects['back'].collidepoint(mouse_pos):
                                # 如果在试下模式，先退出试下模式
                                if try_mode:
                                    exit_try_mode()
                                state = "MENU"
                                game_mode = None
                                continue
                        # 检查控制按钮点击
                        if 'prev_button' in button_areas['replay_button'] and button_areas['replay_button']['prev_button'].collidepoint(mouse_pos):
                            if replay_step > 0:
                                replay_step -= 1
                                update_replay_positions()
                        elif 'next_button' in button_areas['replay_button'] and button_areas['replay_button']['next_button'].collidepoint(mouse_pos):
                            if replay_step < replay_max_steps:
                                replay_step += 1
                                update_replay_positions()
                        elif 'reset_button' in button_areas['replay_button'] and button_areas['replay_button']['reset_button'].collidepoint(mouse_pos):
                            replay_step = 0
                            update_replay_positions()
                        elif 'progress_rect' in button_areas['replay_button'] and button_areas['replay_button']['progress_rect'].collidepoint(mouse_pos):
                            # 点击进度条跳转
                            progress_rect = button_areas['replay_button']['progress_rect']
                            click_x = mouse_pos[0] - progress_rect.x
                            progress_ratio = click_x / progress_rect.width
                            replay_step = int(progress_ratio * replay_max_steps)
                            replay_step = max(0, min(replay_step, replay_max_steps))
                            update_replay_positions()
                        # 添加试下按钮点击处理
                        elif 'try_button' in button_areas['replay_button'] and button_areas['replay_button']['try_button'].collidepoint(mouse_pos):
                            enter_try_mode()
                        # 添加结束试下按钮点击处理
                        elif 'exit_try_button' in button_areas['replay_button'] and button_areas['replay_button']['exit_try_button'].collidepoint(mouse_pos):
                            exit_try_mode()
                        # 添加撤销按钮点击处理
                        elif 'undo_button' in button_areas['replay_button'] and button_areas['replay_button']['undo_button'].collidepoint(mouse_pos):
                            if try_mode and try_move_stack:
                                undo_try_move()
                        # 添加前后调整按钮点击处理
                        elif 'prev_try_button' in button_areas['replay_button'] and button_areas['replay_button']['prev_try_button'].collidepoint(mouse_pos):
                            if try_mode and try_current_index > 0:
                                undo_try_move()
                        elif 'next_try_button' in button_areas['replay_button'] and button_areas['replay_button']['next_try_button'].collidepoint(mouse_pos):
                            if try_mode and try_current_index < try_step:
                                forward_try_move()
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        # 如果在试下模式，先退出试下模式
                        if try_mode:
                            exit_try_mode()
                        else:
                            state = "MENU"
                            game_mode = None
                    elif event.key == pygame.K_LEFT:
                        if try_mode:
                            if try_move_stack:
                                undo_try_move()
                        elif replay_step > 0:
                            replay_step -= 1
                            update_replay_positions()
                    elif event.key == pygame.K_RIGHT:
                        if try_mode:
                            if try_current_index < try_step:
                                forward_try_move()
                        elif replay_step < replay_max_steps:
                            replay_step += 1
                            update_replay_positions()
                        elif replay_step < replay_max_steps:
                            replay_step += 1
                            update_replay_positions()
            
            elif state == "END":
                # 处理鼠标移动事件（悬停检测）
                if event.type == pygame.MOUSEMOTION:
                    mouse_pos = pygame.mouse.get_pos()
                    menu_hovered = None
                    
                    # 检查back按钮悬停
                    if hasattr(draw_board, 'end_button_rects') and 'back' in draw_board.end_button_rects:
                        if draw_board.end_button_rects['back'].collidepoint(mouse_pos):
                            menu_hovered = "back"
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        mouse_pos = pygame.mouse.get_pos()
                        # 检查back按钮点击
                        if hasattr(draw_board, 'end_button_rects') and 'back' in draw_board.end_button_rects:
                            if draw_board.end_button_rects['back'].collidepoint(mouse_pos):
                                # 游戏结束时保存记录（仅在正式对局且非试下模式下）
                                if game_record and game_mode == 'play' and not try_mode:
                                    save_game_record()
                                state = "MENU"
                                continue
                elif event.type == pygame.KEYDOWN:
                    # 游戏结束时保存记录（仅在正式对局且非试下模式下）
                    if game_record and game_mode == 'play' and not try_mode:
                        save_game_record()
                    if game_mode == 'lan' and event.key == pygame.K_r:
                        # LAN 模式：按 R 重置棋盘并交换红蓝
                        if net_session:
                            try:
                                net_session.send({'type': 'reset_swap'})
                            except Exception:
                                pass
                        if local_side:
                            local_side = 'red' if local_side == 'blue' else 'blue'
                        set_default_positions()
                        init_game_record()
                        winner = None
                        board_locked = False
                        selected_piece = None
                        state = 'GAME'
                    else:
                        # 返回主菜单
                        state = "MENU"
                continue
            
            elif state == "LEVEL_COMPLETE":
                # 处理鼠标移动事件（悬停检测）
                if event.type == pygame.MOUSEMOTION:
                    mouse_pos = pygame.mouse.get_pos()
                    menu_hovered = None
                    
                    # 检查back按钮悬停
                    if hasattr(draw_level_complete, 'button_rects') and 'back' in draw_level_complete.button_rects:
                        if draw_level_complete.button_rects['back'].collidepoint(mouse_pos):
                            menu_hovered = "back"
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        mouse_pos = pygame.mouse.get_pos()
                        # 检查back按钮点击
                        if hasattr(draw_level_complete, 'button_rects') and 'back' in draw_level_complete.button_rects:
                            if draw_level_complete.button_rects['back'].collidepoint(mouse_pos):
                                state = "MENU"
                                game_mode = "practice"
                                current_level = None
                                continue
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        state = "MENU"
                        game_mode = "practice"
                        current_level = None
                continue
            
            elif state == "GAME":
                # 只在非练习模式下进行胜负判定
                if game_mode != 'practice':
                    if check_win() == "blue":
                        winner = "blue"
                        state = "END"
                    elif check_win() == "red":
                        winner = "red"
                        state = "END"

                # LAN 模式下轮询网络消息
                if game_mode == 'lan' and net_session:
                    for msg in net_session.poll():
                        if msg.get('type') == 'move':
                            piece = msg.get('piece', {})
                            color = piece.get('color')
                            num = piece.get('num')
                            frm = tuple(msg.get('from'))
                            to = tuple(msg.get('to'))
                            mv_type = msg.get('move_type', 'normal')
                            formula = msg.get('formula')
                            res = msg.get('res')
                            # 仅应用对方的走子
                            if color and num is not None and local_side and color != local_side:
                                # 构造 piece_info
                                piece_info = (color, num, frm, None)
                                processing_remote_move = True
                                move_piece(piece_info, to, BLUE_PIECES, RED_PIECES, mv_type, formula, res)
                                processing_remote_move = False
                        elif msg.get('type') == 'reset_swap':
                            # 交换执子颜色并重置棋盘
                            if local_side:
                                local_side = 'red' if local_side == 'blue' else 'blue'
                            set_default_positions()
                            init_game_record()
                            winner = None
                            board_locked = False
                            selected_piece = None
                            state = 'GAME'

            # 处理鼠标移动事件
            if event.type == pygame.MOUSEMOTION:
                mouse_pos = pygame.mouse.get_pos()
                
                # Handle hint box dragging
                if hint_box_dragging:
                    new_x = mouse_pos[0] - hint_box_offset[0]
                    new_y = mouse_pos[1] - hint_box_offset[1]
                    # Keep hint box within screen bounds
                    new_x = max(0, min(new_x, window.get_width() - (320 if 'hint_box_rect' in globals() else 320)))
                    new_y = max(0, min(new_y, window.get_height() - (120 if 'hint_box_rect' in globals() else 120)))
                    hint_box_pos = (new_x, new_y)
                    continue
                
                # 重置悬停状态
                hovered_button = None
                # 获取按钮区域
                _, _, button_areas, _, _ = draw_board()
                
                # 检查是否悬停在操作按钮上
                if "operations" in button_areas:
                    for x, y, width, height, op in button_areas["operations"]:
                        if x <= mouse_pos[0] <= x + width and y <= mouse_pos[1] <= y + height:
                            hovered_button = f"op_{op}"
                            break
                
                # 检查是否悬停在数字按钮上
                if "number_buttons" in button_areas:
                    for x, y, width, height, color, num, val in button_areas["number_buttons"]:
                        if x <= mouse_pos[0] <= x + width and y <= mouse_pos[1] <= y + height:
                            hovered_button = f"{color}_{num}"
                            break
                
                # 检查是否悬停在计算按钮上
                if "calc_button" in button_areas and button_areas["calc_button"].collidepoint(mouse_pos):
                    hovered_button = "calc_button"
                
                # 回放/试下控制按钮悬停（不要阻断其他按钮）
                if "replay_button" in button_areas and len(button_areas["replay_button"]) != 0:
                    for key, rect in button_areas["replay_button"].items():
                        if rect.collidepoint(mouse_pos):
                            hovered_button = f"replay_button_{key}"
                            break
                # 检查是否悬停在清除按钮上（与回放控件并行检测）
                if hovered_button is None and "clear_button" in button_areas and button_areas["clear_button"].collidepoint(mouse_pos):
                    hovered_button = "clear_button"
                
                # 检查是否悬停在删除按钮上（与回放控件并行检测）
                if hovered_button is None and "delete_button" in button_areas and button_areas["delete_button"].collidepoint(mouse_pos):
                    hovered_button = "delete_button"
                
                # 检查是否悬停在取消按钮上（与回放控件并行检测）
                if hovered_button is None and "cancel_button" in button_areas and button_areas["cancel_button"].collidepoint(mouse_pos):
                    hovered_button = "cancel_button"
                
                # 检查是否悬停在锁定颜色按钮上（与回放控件并行检测）
                if hovered_button is None and "lock_color_button" in button_areas and button_areas["lock_color_button"].collidepoint(mouse_pos):
                    hovered_button = "lock_color_button"
                
                elif "continuous_span_area" in button_areas:
                    if len(button_areas["continuous_span_area"]["paths"]) > 1:
                        for num, rect in enumerate[Any](button_areas["continuous_span_area"]["paths"]):
                            if rect.collidepoint(mouse_pos):
                                hovered_button = f"continuous_span_{str(num)}"
                                break
                    else:
                        for idx_x, list in enumerate(button_areas["continuous_span_area"]["numbers"]):
                            for idx_y, rect in enumerate(list):
                                if rect.collidepoint(mouse_pos):
                                    # print(selected_path)
                                    hovered_button = f"continuous_span_number_{str(idx_x)}_{str(idx_y)}"
                                    break
                # 检查是否悬停在棋盘上
  
            # 处理键盘事件
            elif event.type == pygame.KEYDOWN:
                # 如果正在重命名，处理重命名输入
                if state == "MENU" and renaming_file:
                    if event.key == pygame.K_BACKSPACE:
                        rename_input = rename_input[:-1]
                    elif event.key == pygame.K_RETURN:
                        # 确认重命名
                        if rename_input.strip():
                            custom_names[renaming_file] = rename_input.strip()
                            custom_setup.save_custom_names(custom_names)
                        renaming_file = None
                        rename_input = ""
                    elif event.key == pygame.K_ESCAPE:
                        # 取消重命名
                        renaming_file = None
                        rename_input = ""
                    elif event.unicode.isprintable() and len(rename_input) < 20:
                        rename_input += event.unicode
                    continue
                
                # 在GAME状态下按ESC键退出到主界面
                if state == "GAME" and event.key == pygame.K_ESCAPE:
                    # 保存当前游戏记录（仅在正式对局且非试下模式下）
                    if game_record and game_mode == 'play' and not try_mode:
                        save_game_record()
                    # 重置游戏状态
                    state = "MENU"
                    game_mode = None
                    # 重置游戏相关变量
                    selected_piece = None
                    valid_moves = []
                    selected_numbers = []
                    operation = None
                    calculation_result = None
                    board_locked = False
                    selected_gray_point = None
                    formula_text = ""
                    number_res = []
                    color_locked = True
                    continuous_span = False
                    paths = []
                    expected_result = None
                    continuous_span_line = -1
                    winner = None
                    continue
                
                # 处理算式输入
                if event.key == pygame.K_BACKSPACE:
                    formula_text = formula_text[:-1]
                elif event.key == pygame.K_RETURN:
                    # 计算算式结果
                    pass
                elif event.key == pygame.K_ESCAPE:
                    formula_text = ""
                elif not board_locked:  # 棋盘锁定时仍可输入算式，但不响应棋盘操作键
                    # 数字键0-9选择对应编号的棋子
                    if event.key >= pygame.K_0 and event.key <= pygame.K_9:
                        number = event.key - pygame.K_0  # 将按键转换为数字
                        # 根据当前玩家选择对应颜色的棋子
                        pieces = BLUE_PIECES if current_player == 'blue' else RED_PIECES
                        if number in pieces:
                            col, row = pieces[number]
                            x, y = point_map[(col, row)]
                            selected_piece = (current_player, number, (col, row), (x, y))
                            valid_moves = get_valid_moves((col, row), point_map, BLUE_PIECES, RED_PIECES, all_points)
                    
                    # 左右箭头切换棋子
                    elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                        if selected_piece:
                            current_num = selected_piece[1]
                            pieces = BLUE_PIECES if current_player == 'blue' else RED_PIECES
                            # 获取所有可用的棋子编号并排序
                            numbers = sorted(pieces.keys())
                            current_index = numbers.index(current_num)
                            
                            # 计算新的索引
                            if event.key == pygame.K_LEFT:
                                new_index = (current_index - 1) % len(numbers)
                            else:
                                new_index = (current_index + 1) % len(numbers)
                            
                            # 选择新的棋子
                            new_num = numbers[new_index]
                            col, row = pieces[new_num]
                            x, y = point_map[(col, row)]
                            selected_piece = (current_player, new_num, (col, row), (x, y))
                            valid_moves = get_valid_moves((col, row), point_map, BLUE_PIECES, RED_PIECES, all_points)
                    
                    # 上帝模式开关
                    elif event.key == pygame.K_g:
                        god_mode = not god_mode
                    
                    # 回放模式下的键盘控制
                    elif game_mode == 'replay':
                        if event.key == pygame.K_LEFT:
                            # 上一步
                            if replay_step > 0:
                                replay_step -= 1
                                update_replay_positions()
                        elif event.key == pygame.K_RIGHT:
                            # 下一步
                            if replay_step < replay_max_steps:
                                replay_step += 1
                                update_replay_positions()
                        elif event.key == pygame.K_SPACE:
                            # 播放/暂停
                            replay_playing = not replay_playing
                        elif event.key == pygame.K_r:
                            # 重置
                            replay_step = 0
                            replay_playing = False
                            update_replay_positions()
                        elif event.key == pygame.K_ESCAPE:
                            # 退出回放模式
                            # 如果在试下模式，先退出试下模式
                            if try_mode:
                                exit_try_mode()
                            state = "MENU"
                            game_mode = None
                            replay_data = None
            
            # 处理鼠标点击事件
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键点击
                    mouse_pos = pygame.mouse.get_pos()
                    
                    # Check if clicking on hint box for dragging
                    if (game_mode == 'practice' and 'hint_box_rect' in globals() and 
                        hint_box_rect.collidepoint(mouse_pos)):
                        hint_box_dragging = True
                        hint_box_offset = (mouse_pos[0] - hint_box_pos[0], mouse_pos[1] - hint_box_pos[1])
                        continue
                    
                    all_points, point_map, button_areas, potential_jumps, potential_jumps2 = draw_board()
                    
                    # 回放模式下不允许棋盘操作（试下模式除外）
                    if game_mode == 'replay' and not try_mode:
                        continue

                    # LAN 模式下，轮到对方时禁用本地操作
                    if game_mode == 'lan' and local_side and current_player != local_side:
                        continue
                    
                    # 上帝模式：点击棋子后再点击任意点即可移动
                    if god_mode:
                        # 第一步：点击棋子，选中
                        if not selected_piece:
                            piece = get_piece_at_position(mouse_pos, point_map, BLUE_PIECES, RED_PIECES)
                            if piece:
                                selected_piece = piece
                        # 第二步：已选中棋子，点击任意棋盘点移动
                        else:
                            # 找到最近的棋盘点
                            min_dist = float('inf')
                            target_pos = None
                            for pos, (x, y) in point_map.items():
                                dist = (mouse_pos[0] - x) ** 2 + (mouse_pos[1] - y) ** 2
                                if dist < min_dist:
                                    min_dist = dist
                                    target_pos = pos
                            # 移动棋子到该点
                            color, num, _, _ = selected_piece
                            if color == 'blue':
                                BLUE_PIECES[num][0], BLUE_PIECES[num][1] = target_pos
                                current_player = 'red'
                            else:
                                RED_PIECES[num][0], RED_PIECES[num][1] = target_pos
                                current_player = 'blue'
                            selected_piece = None
                            red_points, blue_points = calculate_point()
                            print(f"red_points: {red_points}, blue_points: {blue_points}")
                        continue  # 上帝模式下不处理其他点击
                    
                    # 检查是否点击了算式输入框
                    if "formula_rect" in button_areas and button_areas["formula_rect"].collidepoint(mouse_pos):
                        # 激活算式输入
                        pass  # 这里可以添加一个标志来表示当前正在输入算式
                    
                    # 检查是否点击了计算版区域的按钮
                    elif mouse_pos[0] > CALC_AREA_X or mouse_pos[1] < OFFSET_Y:  # 右侧计算版或上方算式区域
                        # 检查是否点击了操作按钮
                        for x, y, width, height, op in button_areas["operations"]:
                            if x <= mouse_pos[0] <= x + width and y <= mouse_pos[1] <= y + height:
                                operation = op
                                is_valid, error_msg = is_valid_formula(formula_text + op)
                                if is_valid:
                                    formula_text += op  # 将操作符添加到算式
                                else:
                                    print(error_msg)
                                break
                        
                        # 检查是否点击了计算按钮
                        if button_areas["calc_button"].collidepoint(mouse_pos):
                            if formula_text:  # 如果有算式文本，计算它
                                try:
                                    # 替换乘除符号为Python可识别的符号
                                    calc_formula = formula_text.replace('×', '*').replace('÷', '/')
                                    calculation_result = eval(calc_formula)
                                except:
                                    calculation_result = "ERROR"
                            else:  # 否则使用选择的数字和操作
                                calculate_result()
                            
                            # 添加判断：如果计算结果等于选择的棋子上的数字，则判断这一步有效
                            if board_locked and selected_piece and selected_gray_point and calculation_result != "ERROR":
                                move_made = False
                                if continuous_span:
                                    if  -114514 < number_res[-1][0] < 0 and expected_result is None:
                                        expected_result = int(calculation_result)
                                        formula_res.append(formula_text)
                                        formula_text = ""
                                        number_res[-1][0] = -114514
                                    elif -114514 < number_res[-1][0] < 0 and expected_result == calculation_result:
                                        if len(paths[0]) == 0:
                                            formula_res.append(formula_text)
                                            move_made = True
                                        else:
                                            formula_res.append(formula_text)
                                            formula_text = ""
                                            number_res[-1][0] = -114514                                       
                                elif not continuous_span:
                                    if selected_piece[1] == calculation_result:  # selected_piece[1]是棋子上的数字
                                        # 获取目标位置的棋盘坐标
                                        move_made = True
                                if move_made:
                                    # 修复：selected_gray_point已经是棋盘坐标(col, row)，直接使用
                                    target_pos = selected_gray_point
                                    
                                    if target_pos:
                                        # 构建算式字符串
                                        if len(formula_res) == 0:
                                            formula_res.append(formula_text)
                                        # 移动棋子到锁定的位置
                                        if move_piece(selected_piece, target_pos, BLUE_PIECES, RED_PIECES, "calculation", formula_res, number_res):
                                            # 退出锁定状态
                                            board_locked = False
                                            selected_gray_point = None
                                            # 清空selected_number
                                            selected_numbers = []
                                            formula_res = []
                                            number_res = []
                                            paths = []
                                            # 清空其他状态
                                            selected_piece = None
                                            valid_moves = []
                                            operation = None
                                            calculation_result = None
                                            expected_result = None
                                            formula_text = ""
                        
                        # 检查是否点击了删除按钮
                        elif button_areas["delete_button"].collidepoint(mouse_pos):
                            if formula_text:  # 如果有算式文本，删除最后一个字符
                                if formula_text[-1].isdigit():
                                    if continuous_span:
                                        if number_res[-1][0] < 0:  #当这一行满了
                                            number_res[-1][0] = abs(number_res[-1][0])
                                            paths[0].insert(number_res[-1][0] - 1, [])
                                        paths[0][number_res[-1][0] - 1].append(number_res[-1][-1])
                                        number_res[-1].pop(-1)
                                        if len(number_res[-1]) == 1:
                                            number_res.pop(-1)
                                    else:
                                        selected_numbers.append(number_res[-1])
                                        number_res.pop(-1)
                                formula_text = formula_text[:-1]
                        
                        # 检查是否点击了清除按钮
                        elif button_areas["clear_button"].collidepoint(mouse_pos):
                            if len(number_res) != 0:
                                if not continuous_span:
                                    for i in range(len(number_res)):
                                        selected_numbers.append(number_res[i])
                                else:
                                    for i in range(len(number_res)):
                                        if number_res[i][0] < 0:  # 当行索小于0时，加入整行
                                            paths[0].append(number_res[i][1:])
                                        else:
                                            for num in number_res[i][1:]:  # 否则在对应行加入数字
                                                paths[0][number_res[i][0] - 1].append(num)
                                number_res = []
                            operation = None
                            calculation_result = None
                            expected_result = None
                            formula_text = ""
                        
                        for rect in button_areas["number_buttons"]:
                            x, y, width, height, color, num, val = rect
                            if x <= mouse_pos[0] <= x + width and y <= mouse_pos[1] <= y + height:
                                is_valid, error_msg = is_valid_formula(formula_text + str(val))
                                if is_valid:
                                    formula_text += str(val)
                                    number_res.append(val)
                                    selected_numbers.pop(num)
                                else:
                                    print(error_msg)  # 打印错误信息
                                break
                        # 检查是否点击了取消按钮
                    
                        if "continuous_span_area" in button_areas:
                            if len(button_areas["continuous_span_area"]["paths"]) > 1:
                                selected_path = -1
                                for num, rect in enumerate(button_areas["continuous_span_area"]["paths"]):
                                    if rect.collidepoint(mouse_pos):
                                        selected_path = num
                                        # print(selected_path)
                                        break
                                if selected_path > -1:
                                    for i in range(len(button_areas["continuous_span_area"]["paths"]) - 1, -1, -1):
                                        if i != selected_path:
                                            paths.pop(i)
                                    # 检查选择的路径是否只有一组数据
                                    if len(paths) == 1 and len(paths[0]) == 1:
                                        # 改为灰色点判定方式
                                        continuous_span = False
                                        expected_result = selected_piece[1]  # 预期结果改为棋子点数
                                        selected_numbers = paths[0][0]  # 使用路径中的数据作为选中数字
                                        paths = []  # 清空路径
                            else:
                                # 原有的单路径数字选择逻辑
                                for idx_x in range(len(button_areas["continuous_span_area"]["numbers"]) - 1, -1, -1):
                                    list = button_areas["continuous_span_area"]["numbers"][idx_x]
                                    if continuous_span_line != -1 and idx_x != continuous_span_line:
                                        continue
                                    
                                    # 检查是否跨行选择：如果当前正在进行某行的计算，则只能选择该行的数字
                                    if len(number_res) > 0:
                                        last_row_idx = number_res[-1][0]
                                        if last_row_idx != -114514:
                                            active_row = abs(last_row_idx) - 1
                                            if idx_x != active_row:
                                                continue

                                    for idx_y in range(len(list) - 1, -1, -1):
                                        rect = button_areas["continuous_span_area"]["numbers"][idx_x][idx_y]
                                        if rect.collidepoint(mouse_pos):
                                            val = paths[0][idx_x][idx_y]
                                            is_valid, error_msg = is_valid_formula(formula_text + str(val))
                                            if is_valid:
                                                if len(number_res) == 0: # 若缓存为空，新增数组
                                                    number_res.append([idx_x + 1])
                                                elif number_res[-1][0] == -114514: # 当行没有数字时，缓存新增一行
                                                    number_res.append([idx_x + 1])
                                                elif number_res[-1][0] < 0: # 小于0时，无法进行数组选择
                                                    break
                                                formula_text += str(val) 
                                                paths[0][idx_x].pop(idx_y)
                                                number_res[-1].append(val) # 将计算数字加入缓存
                                                if len(paths[0][idx_x]) == 0:  # 当行没有数字时，索引改为负
                                                    paths[0].pop(idx_x)
                                                    number_res[-1][0] = -abs(number_res[-1][0])
                                                # 检查是否只剩一组数据
                                                if len(paths[0]) == 1 and len(paths[0][0]) == 0:
                                                    # 改为灰色点判定方式
                                                    continuous_span = False
                                                    expected_result = selected_piece[1]  # 预期结果改为棋子点数
                                                    # 将已选择的数字转换为selected_numbers格式
                                                    temp_numbers = []
                                                    for res in number_res:
                                                        temp_numbers.extend(res[1:])  # 跳过索引，只取数字
                                                    selected_numbers = temp_numbers
                                                    number_res = []  # 清空缓存
                                                    paths = []  # 清空路径
                                                # print(number_res)
                                            else:
                                                print(error_msg)  # 打印错误信息
                                            break
                                
                        continue

                    if "cancel_button" in button_areas and button_areas["cancel_button"].collidepoint(mouse_pos):
                        # 解除棋盘锁定状态
                        board_locked = False
                        continuous_span = False
                        selected_gray_point = None
                        selected_numbers = []
                        number_res = []
                        paths = []
                        formula_text = ""
                        operation = None
                        calculation_result = None
                        expected_result = None

                    # 检查是否点击了锁定颜色按钮
                    elif "lock_color_button" in button_areas and button_areas["lock_color_button"].collidepoint(mouse_pos):
                        # 切换颜色锁定状态
                        color_locked = not color_locked
                    
                    # 处理回放控制按钮点击（仅在命中控件时中断后续棋盘处理）
                    if game_mode == 'replay' and 'replay_button' in button_areas:
                        controls = button_areas['replay_button']
                        handled_control_click = False
                        if not try_mode:
                            # 非试下模式下，处理复盘控制按钮
                            if 'prev_button' in controls and controls['prev_button'].collidepoint(mouse_pos):
                                if replay_step > 0:
                                    replay_step -= 1
                                    update_replay_positions()
                                handled_control_click = True
                            elif 'next_button' in controls and controls['next_button'].collidepoint(mouse_pos):
                                if replay_step < replay_max_steps:
                                    replay_step += 1
                                    update_replay_positions()
                                handled_control_click = True
                            elif 'play_button' in controls and controls['play_button'].collidepoint(mouse_pos):
                                replay_playing = not replay_playing
                                handled_control_click = True
                            elif 'reset_button' in controls and controls['reset_button'].collidepoint(mouse_pos):
                                replay_step = 0
                                replay_playing = False
                                update_replay_positions()
                                handled_control_click = True
                            elif 'progress_rect' in controls and controls['progress_rect'].collidepoint(mouse_pos):
                                progress_x = mouse_pos[0] - controls['progress_rect'].x
                                progress_ratio = progress_x / controls['progress_rect'].width
                                replay_step = int(progress_ratio * replay_max_steps)
                                replay_step = max(0, min(replay_step, replay_max_steps))
                                update_replay_positions()
                                handled_control_click = True
                        else:
                            # 试下模式下，处理试下相关按钮
                            if 'exit_try_button' in controls and controls['exit_try_button'].collidepoint(mouse_pos):
                                exit_try_mode()
                                handled_control_click = True
                            elif 'undo_button' in controls and controls['undo_button'].collidepoint(mouse_pos):
                                if try_move_stack:
                                    undo_try_move()
                                    handled_control_click = True
                            elif 'prev_try_button' in controls and controls['prev_try_button'].collidepoint(mouse_pos):
                                if try_current_index > 0 and try_move_stack:
                                    undo_try_move()
                                    handled_control_click = True
                            elif 'next_try_button' in controls and controls['next_try_button'].collidepoint(mouse_pos):
                                if try_current_index < try_step:
                                    forward_try_move()
                                    handled_control_click = True
                        if handled_control_click:
                            continue
                    
                    # 如果棋盘已锁定或在回放模式，不允许进行棋盘操作
                    if board_locked:
                        continue
                    
                    # 优先检查绿圈点击（有效移动位置）
                    if selected_piece and valid_moves:
                        move_made = False
                        for x, y, target_pos, _ in valid_moves:
                            if is_point_in_circle(mouse_pos, (x, y), RADIUS):
                                # 移动棋子
                                if move_piece(selected_piece, target_pos, BLUE_PIECES, RED_PIECES, "normal"):
                                    selected_piece = None
                                    valid_moves = []
                                    move_made = True
                                break
                        
                        if move_made:
                            continue
                    
                    # 然后检查灰色点（备选跨越点）
                    clicked_gray_point = False
                    for col, row, _ in potential_jumps:  # 修改：现在获取col, row坐标
                        # 使用point_map将col,row转换为x,y坐标
                        x, y = point_map[(col, row)]
                        if is_point_in_circle(mouse_pos, (x, y), RADIUS):
                            # 选中灰色点，锁定棋盘状态
                            board_locked = True
                            selected_gray_point = (col, row)
                            clicked_gray_point = True
                            
                            # 进行路径搜索
                            start = (selected_piece[2][0], selected_piece[2][1], (2, 2))
                            paths = get_paths(start, selected_gray_point, point_map, BLUE_PIECES, RED_PIECES, all_points, [], [])
                            
                            # 清理空路径
                            for path in paths[:]:
                                if path == []:
                                    paths.remove(path)
                            
                            # 根据路径数量决定处理方式
                            if len(paths) <= 1:
                                # 只有一条路径或无路径，使用之前的判定规则
                                continuous_span = False
                                expected_result = selected_piece[1]  # 预期结果设置为棋子本身的数值
                                selected_numbers = get_numbers(selected_piece[2], selected_gray_point, point_map)
                            else:
                                # 有多条路径，采用紫色判定逻辑并重置参数
                                continuous_span = True
                                # 重置判断参数
                                expected_result = None  # 重置期望结果
                                selected_numbers = []   # 重置选中数字
                                number_res = []         # 重置数字结果
                                formula_text = ""       # 重置算式文本
                                operation = None        # 重置运算符
                                calculation_result = None  # 重置计算结果
                                # print(f"找到 {len(paths)} 条路径，采用紫色判定模式")
                                # print(selected_piece, selected_gray_point)
                            
                            break
                    
                    # 检查是否点击紫色点（备选跨越点2）
                    for col, row, _ in potential_jumps2:  # 修改：现在获取col, row坐标
                        # 使用point_map将col,row转换为x,y坐标
                        x, y = point_map[(col, row)]
                        if is_point_in_circle(mouse_pos, (x, y), RADIUS):
                            board_locked = True
                            selected_gray_point = (col, row)
                            clicked_gray_point = True
                            continuous_span = True
                            print(selected_piece, selected_gray_point)
                            start = (selected_piece[2][0], selected_piece[2][1], (2, 2))
                            paths = get_paths(start, selected_gray_point, point_map, BLUE_PIECES, RED_PIECES, all_points, [], [])
                            # print(paths)
                            for path in paths:
                                if path == []:
                                    paths.remove(path)
                            break

                    if clicked_gray_point:
                        continue
                    
                    # 检查是否点击了棋子
                    piece = get_piece_at_position(mouse_pos, point_map, BLUE_PIECES, RED_PIECES)
                    if piece:
                        piece_color, piece_number = piece[0], piece[1]
                        # 在练习模式下检查是否可以移动该棋子
                        if game_mode == "practice" and not can_move_piece(piece_color, piece_number):
                            # 可以添加一个临时的错误提示或者忽略点击
                            # 这里可以设置一个全局变量来显示错误信息
                            pass  # 忽略无效的棋子选择
                        else:
                            # 正常的棋子选择逻辑
                            # 如果点击的是棋子，同时更新选中棋子和计算版数字
                            selected_piece = piece
                            # 获取有效移动位置
                            valid_moves = get_valid_moves(piece[2], point_map, BLUE_PIECES, RED_PIECES, all_points)
                    else:
                        selected_piece = None
                        valid_moves = []
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left click release
                    hint_box_dragging = False
        
        # 根据状态绘制不同界面
        if state == "MENU":
            draw_menu()
        elif state == "CUSTOM_SETUP":
            draw_custom_setup()
        elif state == "GAME":
            all_points, point_map, button_areas, potential_jumps, potential_jumps2 = draw_board()
        elif state == "REPLAY":
            all_points, point_map, button_areas, potential_jumps, potential_jumps2 = draw_board()
        elif state == "END":
            all_points, point_map, button_areas, potential_jumps, potential_jumps2 = draw_board()
        elif state == "LEVEL_COMPLETE":
            draw_level_complete()
            
        pygame.display.flip()
        clock.tick(60)


if __name__ == '__main__':
    main()
