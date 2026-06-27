"""
元气骑士风格 Roguelike 游戏 - 全局设置
"""

# 窗口设置
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
TITLE = "元气地牢"
FPS = 60

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (220, 40, 40)
GREEN = (40, 220, 40)
BLUE = (40, 40, 220)
YELLOW = (220, 220, 40)
ORANGE = (255, 140, 0)
PURPLE = (160, 40, 200)
CYAN = (40, 200, 200)
GRAY = (120, 120, 120)
DARK_GRAY = (40, 40, 40)
LIGHT_GRAY = (180, 180, 180)
BROWN = (139, 90, 43)
DARK_BROWN = (80, 50, 20)

# UI 颜色
UI_BG = (20, 20, 30, 180)
UI_BORDER = (80, 80, 100)
HEALTH_BAR_GREEN = (50, 200, 50)
HEALTH_BAR_RED = (200, 50, 50)
SHIELD_BAR_BLUE = (50, 120, 220)
ENERGY_BAR_PURPLE = (180, 100, 220)

# 世界设置
TILE_SIZE = 32
ROOM_MIN_SIZE = 10
ROOM_MAX_SIZE = 18
DUNGEON_WIDTH = 100
DUNGEON_HEIGHT = 80
MAX_ROOMS = 18

# 游戏平衡
PLAYER_SPEED = 4.0
PLAYER_MAX_HP = 100
PLAYER_DODGE_COOLDOWN = 60  # 帧
PLAYER_INVINCIBLE_TIME = 30  # 受伤后无敌帧

# 敌人设置
ENEMY_SPEED = 2.0
ENEMY_DETECTION_RANGE = 250

# 子弹设置
BULLET_SPEED = 8.0
BULLET_LIFETIME = 180  # 帧

# 武器插槽
MAX_WEAPON_SLOTS = 2

# ========== 输入配置 ==========
# 预设键位方案
KEY_PRESETS = {
    'default': {
        'name': '默认',
        'up': 'W',
        'down': 'S',
        'left': 'A',
        'right': 'D',
        'dodge': 'SPACE',
        'skill': 'E',
        'reload': 'R',
        'swap': 'Q',
        'pause': 'P',
        'minimap': 'TAB',
        'weapon1': '1',
        'weapon2': '2',
    },
    'arrows': {
        'name': '方向键',
        'up': 'UP',
        'down': 'DOWN',
        'left': 'LEFT',
        'right': 'RIGHT',
        'dodge': 'SPACE',
        'skill': 'E',
        'reload': 'R',
        'swap': 'Q',
        'pause': 'P',
        'minimap': 'TAB',
        'weapon1': '1',
        'weapon2': '2',
    },
}

# 当前使用的键位方案
CURRENT_KEY_PRESET = 'default'


def get_key_preset(name=None):
    """获取键位方案"""
    name = name or CURRENT_KEY_PRESET
    return KEY_PRESETS.get(name, KEY_PRESETS['default'])


# ========== 音效配置 ==========
SOUND_CONFIG = {
    'master_volume': 0.8,
    'music_volume': 0.6,
    'sfx_volume': 1.0,
    'ui_volume': 0.7,
    'muted': False,
}

# ========== 画面配置 ==========
DISPLAY_CONFIG = {
    'fullscreen': False,
    'vsync': True,
    'show_fps': False,
    'show_debug': False,
    'particle_quality': 'high',  # low, medium, high
    'screen_shake': True,
}

# ========== HUD 布局常量 ==========
HUD_HP_BAR = {'x': 20, 'y': 20, 'w': 250, 'h': 22}
HUD_ENERGY_BAR = {'x': 20, 'y': 52, 'w': 180, 'h': 12}
HUD_EXP_BAR = {'x': 20, 'y': 72, 'w': 180, 'h': 6}
HUD_WEAPON_BOX = {'size': 56, 'gap': 10, 'margin_right': 20}
HUD_RUN_INFO_X = WINDOW_WIDTH - 155
HUD_BUFF_X = WINDOW_WIDTH - 155
HUD_SKILL_CD = {'cx': WINDOW_WIDTH - 35, 'cy': 330, 'r': 20}
HUD_MSG_Y = WINDOW_HEIGHT - 100
HUD_MINIMAP = {'x': 10, 'y': WINDOW_HEIGHT - 160, 'size': 150}
