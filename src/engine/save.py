"""
存档系统 - 多存档位、预览、自动保存、游戏进度保存和加载
"""
import os
import json
import time
import glob
from datetime import datetime


SAVE_DIR = "saves"
SAVE_FILE = os.path.join(SAVE_DIR, "savegame.json")
STATS_FILE = os.path.join(SAVE_DIR, "stats.json")
SETTINGS_FILE = os.path.join(SAVE_DIR, "settings.json")
MAX_SAVE_SLOTS = 5


def ensure_save_dir():
    """确保存档目录存在"""
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)


class SaveManager:
    """存档管理器"""

    def __init__(self):
        ensure_save_dir()
        self.stats = self._load_stats()
        self.settings = self._load_settings()

    # ============ 游戏存档 ============
    def save_game(self, game_state, slot=0):
        """保存游戏状态到指定存档位"""
        filename = self._get_slot_path(slot)
        data = {
            'timestamp': datetime.now().isoformat(),
            'version': '1.0',
            'character_id': game_state.get('character_id', 'knight'),
            'difficulty': game_state.get('difficulty', 1),
            'current_hp': game_state.get('current_hp', 100),
            'max_hp': game_state.get('max_hp', 100),
            'gold': game_state.get('gold', 0),
            'kills': game_state.get('kills', 0),
            'score': game_state.get('score', 0),
            'floor': game_state.get('floor', 1),
            'level': game_state.get('level', 1),
            'weapons': game_state.get('weapons', []),
            'dungeon_seed': game_state.get('dungeon_seed', 0),
            'room_progress': game_state.get('room_progress', {}),
        }
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存失败: {e}")
            return False

    def load_game(self, slot=0):
        """加载指定存档位的游戏状态"""
        filename = self._get_slot_path(slot)
        if not os.path.exists(filename):
            return None
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载失败: {e}")
            return None

    def has_save(self, slot=None):
        """检查是否有存档"""
        if slot is not None:
            return os.path.exists(self._get_slot_path(slot))
        # 检查所有存档位
        for s in range(MAX_SAVE_SLOTS):
            if os.path.exists(self._get_slot_path(s)):
                return True
        return os.path.exists(SAVE_FILE)

    def get_save_preview(self, slot=0):
        """获取存档预览信息"""
        data = self.load_game(slot)
        if not data:
            return None
        return {
            'character': data.get('character_id', '?'),
            'floor': data.get('floor', 1),
            'level': data.get('level', 1),
            'gold': data.get('gold', 0),
            'score': data.get('score', 0),
            'time': data.get('timestamp', ''),
        }

    def list_saves(self):
        """列出所有存档位"""
        saves = []
        for s in range(MAX_SAVE_SLOTS):
            preview = self.get_save_preview(s)
            if preview:
                preview['slot'] = s
                saves.append(preview)
        return saves

    def delete_save(self, slot=0):
        """删除指定存档"""
        filename = self._get_slot_path(slot)
        if os.path.exists(filename):
            os.remove(filename)
            return True
        if slot == 0 and os.path.exists(SAVE_FILE):
            os.remove(SAVE_FILE)
            return True
        return False

    def _get_slot_path(self, slot):
        """获取存档位文件路径"""
        if slot == 0:
            return SAVE_FILE
        slot_file = os.path.join(SAVE_DIR, f"savegame_{slot}.json")
        return slot_file

    # ============ 统计数据 ============
    def _load_stats(self):
        """加载统计数据"""
        default = {
            'total_kills': 0,
            'total_gold': 0,
            'total_games': 0,
            'total_wins': 0,
            'best_score': 0,
            'best_time': 0,
            'bosses_defeated': {},
            'weapons_used': [],
            'achievements': {},
            'highest_difficulty': 1,
        }
        if not os.path.exists(STATS_FILE):
            return default
        try:
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                default.update(loaded)
                return default
        except:
            return default

    def save_stats(self):
        """保存统计数据"""
        try:
            with open(STATS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"统计保存失败: {e}")

    def record_game(self, victory, score, kills, gold, character_id, difficulty, game_time):
        """记录一局游戏"""
        self.stats['total_games'] += 1
        self.stats['total_kills'] += kills
        self.stats['total_gold'] += gold
        if victory:
            self.stats['total_wins'] += 1
        if score > self.stats['best_score']:
            self.stats['best_score'] = score
        if game_time < self.stats['best_time'] or self.stats['best_time'] == 0:
            self.stats['best_time'] = game_time
        if difficulty > self.stats['highest_difficulty']:
            self.stats['highest_difficulty'] = difficulty
        self.save_stats()

    def record_achievement(self, achievement_id):
        """记录成就"""
        if achievement_id not in self.stats['achievements']:
            from src.entities.character import ACHIEVEMENTS
            ach = ACHIEVEMENTS.get(achievement_id, {})
            self.stats['achievements'][achievement_id] = {
                'unlocked': True,
                'time': datetime.now().isoformat(),
                'name': ach.get('name', achievement_id),
            }
            self.save_stats()
            return True
        return False

    def record_weapon_used(self, weapon_id):
        """记录使用的武器"""
        if weapon_id not in self.stats['weapons_used']:
            self.stats['weapons_used'].append(weapon_id)
            self.save_stats()

    def record_boss_kill(self, boss_type):
        """记录Boss击杀"""
        self.stats['bosses_defeated'][boss_type] = self.stats['bosses_defeated'].get(boss_type, 0) + 1
        self.save_stats()

    # ============ 设置 ============
    def _load_settings(self):
        """加载设置"""
        default = {
            'sound_enabled': True,
            'music_enabled': True,
            'sound_volume': 0.3,
            'fullscreen': False,
            'show_fps': False,
            'language': 'zh',
            'screen_shake': True,
        }
        if not os.path.exists(SETTINGS_FILE):
            return default
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                default.update(loaded)
                return default
        except:
            return default

    def save_settings(self):
        """保存设置"""
        try:
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"设置保存失败: {e}")

    def get_setting(self, key, default=None):
        return self.settings.get(key, default)

    def set_setting(self, key, value):
        self.settings[key] = value
        self.save_settings()

    # ============ 成就检查 ============
    def check_achievements(self, game_state):
        """检查并解锁成就"""
        unlocked = []
        checks = {
            'first_kill': lambda: game_state.get('kills', 0) >= 1,
            'kill_100': lambda: self.stats['total_kills'] >= 100,
            'kill_500': lambda: self.stats['total_kills'] >= 500,
            'boss_slayer': lambda: len(self.stats['bosses_defeated']) > 0,
            'all_bosses': lambda: len(self.stats['bosses_defeated']) >= 4,
            'gold_1000': lambda: self.stats['total_gold'] >= 1000,
            'gold_5000': lambda: self.stats['total_gold'] >= 5000,
            'weapon_master': lambda: len(self.stats['weapons_used']) >= 15,
        }
        for aid, check in checks.items():
            try:
                if check() and aid not in self.stats['achievements']:
                    if self.record_achievement(aid):
                        unlocked.append(aid)
            except:
                pass
        return unlocked


# 全局存档管理器
_save_manager = None


def get_save_manager():
    global _save_manager
    if _save_manager is None:
        _save_manager = SaveManager()
    return _save_manager
