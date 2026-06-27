"""
成就系统 - 解锁追踪、通知弹窗、进度持久化
"""
import math
import random
import pygame
from src.entities.character import ACHIEVEMENTS
from settings import WINDOW_WIDTH, WINDOW_HEIGHT


class AchievementTracker:
    """成就追踪器 - 运行时检测成就解锁"""

    def __init__(self):
        # 成就解锁状态 {achievement_id: True/False}
        self.unlocked = {}
        # 成就进度 {achievement_id: current_value}
        self.progress = {}
        # 待显示的通知
        self.pending_notifications = []
        # 初始化所有成就为未解锁
        for aid in ACHIEVEMENTS:
            self.unlocked[aid] = False
        # 初始化进度
        self.progress['total_kills'] = 0
        self.progress['total_gold'] = 0
        self.progress['bosses_defeated'] = set()
        self.progress['weapons_used'] = set()
        self.progress['no_damage_rooms'] = 0
        self.progress['damage_taken_this_room'] = 0
        self.progress['kills_this_run'] = 0
        self.progress['damage_taken_boss'] = 0

    def reset_run_stats(self):
        """重置本局统计"""
        self.progress['no_damage_rooms'] = 0
        self.progress['damage_taken_this_room'] = 0
        self.progress['kills_this_run'] = 0
        self.progress['damage_taken_boss'] = 0

    def on_enemy_killed(self, is_boss=False, boss_type=None):
        """击杀敌人时调用"""
        self.progress['total_kills'] += 1
        self.progress['kills_this_run'] += 1

        # 初次击杀
        if self.progress['total_kills'] >= 1 and not self.unlocked['first_kill']:
            self._unlock('first_kill')
        # 百人斩
        if self.progress['total_kills'] >= 100 and not self.unlocked['kill_100']:
            self._unlock('kill_100')
        # 屠夫
        if self.progress['total_kills'] >= 500 and not self.unlocked['kill_500']:
            self._unlock('kill_500')
        # Boss杀手
        if is_boss and not self.unlocked['boss_slayer']:
            self._unlock('boss_slayer')
        if is_boss and boss_type:
            self.progress['bosses_defeated'].add(boss_type)
            if len(self.progress['bosses_defeated']) >= 4 and not self.unlocked['all_bosses']:
                self._unlock('all_bosses')

    def on_gold_collected(self, amount):
        """拾取金币时调用"""
        self.progress['total_gold'] += amount
        if self.progress['total_gold'] >= 1000 and not self.unlocked['gold_1000']:
            self._unlock('gold_1000')
        if self.progress['total_gold'] >= 5000 and not self.unlocked['gold_5000']:
            self._unlock('gold_5000')

    def on_damage_taken(self, amount, is_boss_room=False):
        """受到伤害时调用"""
        self.progress['damage_taken_this_room'] += amount
        if is_boss_room:
            self.progress['damage_taken_boss'] += amount

    def on_room_cleared(self, is_boss_room=False):
        """房间清空时调用"""
        if self.progress['damage_taken_this_room'] == 0:
            self.progress['no_damage_rooms'] += 1
            if is_boss_room and not self.unlocked['no_damage_boss']:
                self._unlock('no_damage_boss')
            if not self.unlocked['no_damage_room']:
                self._unlock('no_damage_room')
        self.progress['damage_taken_this_room'] = 0

    def on_weapon_used(self, weapon_id):
        """使用武器时调用"""
        self.progress['weapons_used'].add(weapon_id)
        if len(self.progress['weapons_used']) >= 15 and not self.unlocked['weapon_master']:
            self._unlock('weapon_master')

    def on_game_end(self, victory, time_elapsed, hp_pct, kills):
        """游戏结束时检测通关成就"""
        if victory:
            # 速通
            if time_elapsed <= 180 and not self.unlocked['speed_run']:
                self._unlock('speed_run')
            # 幸存者
            if hp_pct <= 0.1 and not self.unlocked['survivor']:
                self._unlock('survivor')
            # 和平主义者
            if kills < 5 and not self.unlocked['pacifist']:
                self._unlock('pacifist')

    def _unlock(self, achievement_id):
        """解锁成就"""
        if self.unlocked.get(achievement_id, False):
            return
        self.unlocked[achievement_id] = True
        data = ACHIEVEMENTS.get(achievement_id, {})
        self.pending_notifications.append({
            'name': data.get('name', achievement_id),
            'desc': data.get('desc', ''),
            'timer': 180,  # 3秒显示
            'y_offset': 60 + len(self.pending_notifications) * 50,
        })

    def update(self):
        """更新通知计时器"""
        for notif in self.pending_notifications[:]:
            notif['timer'] -= 1
            if notif['timer'] <= 0:
                self.pending_notifications.remove(notif)

    def draw_notifications(self, screen):
        """绘制成就解锁通知"""
        for i, notif in enumerate(self.pending_notifications):
            progress = min(1.0, notif['timer'] / 180)
            # 从右侧滑入
            x_offset = int((1 - progress) * 300) if progress > 0.9 else 0
            x = WINDOW_WIDTH - 250 + x_offset
            y = 20 + i * 55

            # 背景
            alpha = int(200 * progress) if progress < 0.3 else 200
            bg = pygame.Surface((240, 48), pygame.SRCALPHA)
            bg.fill((40, 30, 20, alpha))
            screen.blit(bg, (x, y))

            # 边框
            border_color = (255, 215, 0, alpha)
            pygame.draw.rect(screen, border_color, (x, y, 240, 48), 2)

            # 图标
            pygame.draw.circle(screen, (255, 215, 0), (x + 20, y + 24), 10)
            pygame.draw.circle(screen, (255, 255, 100), (x + 20, y + 24), 3)

            # 文字
            font = pygame.font.Font(None, 18)
            name_text = font.render(f"成就解锁: {notif['name']}", True, (255, 215, 0))
            desc_text = font.render(notif['desc'], True, (200, 200, 200))
            screen.blit(name_text, (x + 38, y + 6))
            screen.blit(desc_text, (x + 38, y + 26))

    @staticmethod
    def get_achievement_icon(achievement_id):
        """获取成就图标的简单绘制"""
        icons = {
            'skull': lambda s, x, y, c: (pygame.draw.circle(s, c, (x, y), 8),
                                          pygame.draw.circle(s, (0, 0, 0), (x - 3, y - 1), 2),
                                          pygame.draw.circle(s, (0, 0, 0), (x + 3, y - 1), 2)),
            'swords': lambda s, x, y, c: (pygame.draw.line(s, c, (x - 8, y - 8), (x + 4, y + 4), 3),
                                           pygame.draw.line(s, c, (x - 8, y + 8), (x + 4, y - 4), 3)),
            'crown': lambda s, x, y, c: (pygame.draw.polygon(s, c, [(x - 8, y), (x - 5, y - 8),
                                                                      (x, y - 3), (x + 5, y - 8),
                                                                      (x + 8, y), (x, y + 4)])),
            'trophy': lambda s, x, y, c: (pygame.draw.rect(s, c, (x - 6, y - 6, 12, 10)),
                                          pygame.draw.rect(s, c, (x - 2, y + 4, 4, 4))),
            'shield': lambda s, x, y, c: pygame.draw.polygon(s, c, [(x, y - 8), (x + 7, y - 2),
                                                                     (x + 7, y + 4), (x, y + 8),
                                                                     (x - 7, y + 4), (x - 7, y - 2)]),
            'star': lambda s, x, y, c: pygame.draw.polygon(s, c, [(x, y - 8), (x + 2, y - 2),
                                                                   (x + 8, y - 2), (x + 3, y + 1),
                                                                   (x + 5, y + 7), (x, y + 3),
                                                                   (x - 5, y + 7), (x - 3, y + 1),
                                                                   (x - 8, y - 2), (x - 2, y - 2)]),
            'coin': lambda s, x, y, c: (pygame.draw.circle(s, c, (x, y), 7),
                                        pygame.draw.circle(s, (0, 0, 0), (x, y), 4)),
            'bolt': lambda s, x, y, c: pygame.draw.polygon(s, c, [(x, y - 8), (x + 4, y - 1),
                                                                   (x + 1, y - 1), (x + 5, y + 8),
                                                                   (x, y + 1), (x + 3, y + 1)]),
            'heart': lambda s, x, y, c: (pygame.draw.circle(s, c, (x - 3, y - 2), 4),
                                         pygame.draw.circle(s, c, (x + 3, y - 2), 4),
                                         pygame.draw.polygon(s, c, [(x - 6, y), (x + 6, y),
                                                                     (x, y + 7)])),
            'crosshair': lambda s, x, y, c: (pygame.draw.circle(s, c, (x, y), 7, 1),
                                             pygame.draw.line(s, c, (x - 7, y), (x + 7, y)),
                                             pygame.draw.line(s, c, (x, y - 7), (x, y + 7))),
        }
        return icons.get(achievement_id, lambda s, x, y, c: pygame.draw.circle(s, c, (x, y), 6))
