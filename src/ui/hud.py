"""
游戏内 HUD - 血条、护盾、武器信息、金币等
"""
import pygame
import math
from settings import (WINDOW_WIDTH, WINDOW_HEIGHT, WHITE, YELLOW, GREEN, RED,
                      HEALTH_BAR_GREEN, HEALTH_BAR_RED, SHIELD_BAR_BLUE,
                      ENERGY_BAR_PURPLE, GRAY, DARK_GRAY, ORANGE)
from src.engine.resource import get_resources
from src.engine.font_helper import get_chinese_font


class DamageNumber:
    """飘字伤害数字"""
    def __init__(self, x, y, text, color, size=16, lifetime=40, rise_speed=1.5):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.size = size
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.rise_speed = rise_speed
        self.alive = True
        self.alpha = 255

    def update(self):
        self.lifetime -= 1
        self.y -= self.rise_speed
        self.alpha = int(255 * (self.lifetime / self.max_lifetime))
        if self.lifetime <= 0:
            self.alive = False

    def draw(self, screen, camera):
        if not self.alive:
            return
        try:
            from src.engine.font_helper import get_chinese_font
            font = get_chinese_font(self.size)
            alpha_color = (*self.color[:3], self.alpha) if len(self.color) == 3 else self.color
            surf = font.render(self.text, True, alpha_color)
            sx, sy = camera.apply_point(self.x, self.y)
            screen.blit(surf, (sx - surf.get_width() // 2, sy))
        except:
            pass


class HUD:
    """游戏内抬头显示器"""

    def __init__(self, screen):
        self.screen = screen
        self.resources = get_resources()
        self.messages = []
        self.message_timer = 0
        self.run_time = 0  # 由 gameplay 更新
        self.kill_count = 0
        self.dungeon_floor = 1

    def add_message(self, text, color=WHITE):
        self.messages.append({'text': text, 'color': color, 'timer': 120})

    def update(self):
        self.message_timer += 1
        self.messages = [m for m in self.messages if m['timer'] > 0]
        for m in self.messages:
            m['timer'] -= 1

    def draw(self, player):
        self._draw_health_bar(player)
        self._draw_energy_bar(player)
        self._draw_exp_bar(player)
        self._draw_skill_cooldown(player)
        self._draw_combo(player)
        self._draw_weapon_info(player)
        self._draw_gold(player)
        self._draw_buffs(player)
        self._draw_status_effects(player)
        self._draw_messages()
        self._draw_run_info(player)
        self._draw_minimap_info(player)

    def _draw_exp_bar(self, player):
        """绘制经验条"""
        bar_x = 20
        bar_y = 72
        bar_w = 180
        bar_h = 6

        pygame.draw.rect(self.screen, DARK_GRAY, (bar_x, bar_y, bar_w, bar_h))

        exp_pct = player.exp / player.exp_to_next if player.exp_to_next > 0 else 0
        e_w = int(bar_w * exp_pct)
        pygame.draw.rect(self.screen, (100, 255, 100), (bar_x, bar_y, e_w, bar_h))
        pygame.draw.rect(self.screen, WHITE, (bar_x, bar_y, bar_w, bar_h), 1)

        self._draw_text(f"Lv.{player.level}", bar_x + bar_w + 5, bar_y - 2, (100, 255, 100), 12)
        self._draw_text(f"EXP: {player.exp}/{player.exp_to_next}",
                        bar_x + bar_w + 5, bar_y + 5, WHITE, 10)

    def _draw_health_bar(self, player):
        bar_x = 20
        bar_y = 20
        bar_w = 250
        bar_h = 22

        # 背景
        surf = pygame.Surface((bar_w, bar_h), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 140))
        self.screen.blit(surf, (bar_x, bar_y))

        # 血量
        hp_pct = player.hp / player.max_hp
        hp_w = int(bar_w * hp_pct)
        hp_color = HEALTH_BAR_GREEN if hp_pct > 0.5 else YELLOW if hp_pct > 0.25 else HEALTH_BAR_RED
        pygame.draw.rect(self.screen, hp_color, (bar_x, bar_y, hp_w, bar_h))
        pygame.draw.rect(self.screen, WHITE, (bar_x, bar_y, bar_w, bar_h), 1)

        # 护盾
        if player.shield > 0:
            shield_pct = min(1.0, player.shield / 100)
            shield_w = int(bar_w * shield_pct)
            pygame.draw.rect(self.screen, SHIELD_BAR_BLUE, (bar_x, bar_y + bar_h + 3, shield_w, 6))
            pygame.draw.rect(self.screen, WHITE, (bar_x, bar_y + bar_h + 3, bar_w, 6), 1)

        # 文字
        hp_text = f"HP: {int(player.hp)}/{player.max_hp}"
        self._draw_text(hp_text, bar_x + bar_w + 10, bar_y + 2, WHITE, 16)

    def _draw_energy_bar(self, player):
        bar_x = 20
        bar_y = 52
        bar_w = 180
        bar_h = 12

        surf = pygame.Surface((bar_w, bar_h), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 140))
        self.screen.blit(surf, (bar_x, bar_y))

        energy_pct = player.energy / player.max_energy
        e_w = int(bar_w * energy_pct)
        pygame.draw.rect(self.screen, ENERGY_BAR_PURPLE, (bar_x, bar_y, e_w, bar_h))
        pygame.draw.rect(self.screen, WHITE, (bar_x, bar_y, bar_w, bar_h), 1)

        self._draw_text(f"EN: {int(player.energy)}/{player.max_energy}", bar_x + bar_w + 5, bar_y, WHITE, 12)

    def _draw_weapon_info(self, player):
        wm = player.weapon_manager
        box_size = 56
        start_x = WINDOW_WIDTH - 20 - box_size * 2 - 10
        box_y = 20

        for i in range(2):
            bx = start_x + i * (box_size + 10)
            is_current = (i == wm.current_slot)

            # 背景
            bg_alpha = 200 if is_current else 100
            surf = pygame.Surface((box_size, box_size), pygame.SRCALPHA)
            surf.fill((30, 30, 40, bg_alpha))
            self.screen.blit(surf, (bx, box_y))
            border_color = YELLOW if is_current else GRAY
            pygame.draw.rect(self.screen, border_color, (bx, box_y, box_size, box_size), 2)

            weapon = wm.slots[i]
            if weapon:
                # 武器图标
                icon = self.resources.get_weapon_icon(weapon.weapon_id)
                if icon:
                    icon_scaled = pygame.transform.scale(icon, (40, 40))
                    self.screen.blit(icon_scaled, (bx + 8, box_y + 4))

                # 装弹进度
                if weapon.reloading:
                    progress = weapon.get_reload_progress()
                    bar_y = box_y + box_size - 6
                    pygame.draw.rect(self.screen, DARK_GRAY, (bx, bar_y, box_size, 4))
                    pygame.draw.rect(self.screen, YELLOW, (bx, bar_y, int(box_size * progress), 4))
                elif weapon.weapon_type == 'ranged':
                    ammo_ratio = weapon.ammo / weapon.max_ammo
                    bar_y = box_y + box_size - 6
                    pygame.draw.rect(self.screen, DARK_GRAY, (bx, bar_y, box_size, 4))
                    color = WHITE if ammo_ratio > 0.3 else RED
                    pygame.draw.rect(self.screen, color, (bx, bar_y, int(box_size * ammo_ratio), 4))

            # 键位提示
            key_text = f"[{i + 1}]" if is_current else str(i + 1)
            self._draw_text(key_text, bx + box_size // 2, box_y - 12, WHITE if is_current else GRAY, 12, center=True)

    def _draw_gold(self, player):
        """金币已合并到 _draw_run_info"""
        pass

    def _draw_buffs(self, player):
        """绘制增益效果（右中位置）"""
        y_offset = 115
        x = WINDOW_WIDTH - 155
        if player.speed_boost_duration > 0:
            sec = player.speed_boost_duration // 60
            self._draw_text(f"{sec}s+", x, y_offset, GREEN, 11)
            y_offset += 14
        if player.damage_boost_duration > 0:
            sec = player.damage_boost_duration // 60
            self._draw_text(f"ATK+{sec}s", x, y_offset, ORANGE, 11)
            y_offset += 14
        if player.berserk_duration > 0:
            sec = player.berserk_duration // 60
            self._draw_text(f"RAGE{sec}s", x, y_offset, RED, 11)
            y_offset += 14

    def _draw_status_effects(self, player):
        """绘制状态效果"""
        y = 140
        x = 20
        if player.burn_duration > 0:
            self._draw_text(f"燃烧 {player.burn_duration // 60}s", x, y, RED, 14)
            y += 18
        if player.poison_duration > 0:
            self._draw_text(f"中毒 {player.poison_duration // 60}s", x, y, GREEN, 14)
            y += 18
        if player.slow_duration > 0:
            self._draw_text(f"减速 {player.slow_duration // 60}s", x, y, (150, 200, 255), 14)
            y += 18
        if player.regeneration_duration > 0:
            self._draw_text(f"再生 {player.regeneration_duration // 60}s", x, y, (100, 255, 100), 14)

    def _draw_skill_cooldown(self, player):
        """绘制技能冷却指示"""
        sm = getattr(player, 'skill_manager', None)
        if sm is None:
            return
        cd_pct = sm.get_cooldown_pct()
        cx = WINDOW_WIDTH - 35
        cy = 330
        r = 20
        pygame.draw.circle(self.screen, DARK_GRAY, (cx, cy), r)
        if cd_pct < 1.0:
            pygame.draw.circle(self.screen, (80, 80, 120), (cx, cy), r, 3)
            angle_end = -math.pi / 2 + 2 * math.pi * cd_pct
            points = [(cx, cy)]
            for i in range(30):
                a = -math.pi / 2 + (angle_end + math.pi / 2) * i / 30
                points.append((cx + math.cos(a) * (r - 1), cy + math.sin(a) * (r - 1)))
            if len(points) > 2:
                pygame.draw.polygon(self.screen, (100, 100, 180, 150), points)
        else:
            pygame.draw.circle(self.screen, (100, 200, 100), (cx, cy), r, 3)
        self._draw_text("E", cx, cy - 1, WHITE, 14, center=True)

    def _draw_combo(self, player):
        """绘制连击计数和连击特效"""
        if player.combo_count >= 5:
            combo_alpha = min(255, player.combo_timer * 4)
            size = 30 if player.combo_count < 25 else 40 if player.combo_count < 50 else 50
            color = WHITE if player.combo_count < 15 else YELLOW if player.combo_count < 30 else ORANGE if player.combo_count < 50 else RED
            self._draw_text(f"{player.combo_count} COMBO!", WINDOW_WIDTH // 2, 60,
                            (*color[:3], combo_alpha) if len(color) == 3 else color, size, center=True)
            # 连击里程碑提示
            milestones = {10: 'Great!', 25: 'Amazing!', 50: 'GODLIKE!', 75: 'UNSTOPPABLE!'}
            for m, label in milestones.items():
                if player.combo_count == m:
                    self._draw_text(label, WINDOW_WIDTH // 2, 90, YELLOW, 20, center=True)
                    break

    def _draw_floor_info(self, player):
        """绘制楼层信息"""
        if hasattr(player, '_current_room') and player._current_room:
            room = player._current_room
            enemies_alive = sum(1 for e in getattr(room, 'enemies', []) if e.alive)
            if room.room_type not in ('start', 'shop') and enemies_alive > 0:
                self._draw_text(f"剩余敌人: {enemies_alive}", WINDOW_WIDTH // 2, 45, RED, 14, center=True)

    def _draw_run_info(self, player):
        """绘制本局统计（击杀、时间、楼层、金币合并）"""
        # 右上角信息栏（武器栏下方、小地图上方）
        x = WINDOW_WIDTH - 155
        y = 82
        
        # 楼层 + 金币同一行
        floor_text = f'F{self.dungeon_floor}' if self.dungeon_floor > 0 else ''
        gold_text = f'\u2665{player.gold}'  # heart as gold icon
        self._draw_text(floor_text, x, y, YELLOW, 13)
        self._draw_text(gold_text, x + 55, y, (255, 200, 50), 13)
        
        # 击杀 + 时间
        mins = self.run_time // 60
        secs = self.run_time % 60
        self._draw_text(f'{self.kill_count}K', x, y + 17, (255, 180, 120), 12)
        self._draw_text(f'{mins:02d}:{secs:02d}', x + 55, y + 17, (200, 200, 230), 12)
        
        # 房间类型在武器栏下
        room = player._current_room if hasattr(player, '_current_room') else None
        if room and room.room_type not in ('start', 'normal'):
            room_labels = {'boss': 'BOSS', 'chest': 'CHEST', 'shop': 'SHOP',
                           'secret': 'SECRET', 'mini_boss': 'ELITE'}
            label = room_labels.get(room.room_type, '')
            if label:
                self._draw_text(f'[{label}]', x, y + 35, YELLOW, 10)
            enemies = sum(1 for e in getattr(room, 'enemies', []) if e.alive)
            if enemies > 0:
                self._draw_text(f'{enemies} enemy', x + 55, y + 35, RED, 10)

    def _draw_messages(self):
        y = WINDOW_HEIGHT - 100
        for msg in reversed(self.messages[-5:]):
            alpha = min(255, msg['timer'] * 2)
            color = (*msg['color'][:3], alpha) if len(msg['color']) == 3 else msg['color']
            self._draw_text(msg['text'], WINDOW_WIDTH // 2, y, color, 16, center=True)
            y -= 22

    def _draw_minimap_info(self, player):
        """在小地图旁显示补充信息"""
        room = player._current_room if hasattr(player, '_current_room') else None
        if room:
            room_type_text = {
                'normal': '',
                'start': '[初始房间]',
                'boss': '[BOSS房间]',
                'chest': '[宝箱房]',
                'shop': '[商店]',
                'secret': '[秘密房间]',
            }.get(room.room_type, '')
            if room_type_text:
                self._draw_text(room_type_text, WINDOW_WIDTH // 2, 20, YELLOW, 16, center=True)

            # 敌人数统计（小地图区域）
            if hasattr(player, 'rooms_cleared'):
                cleared = player.rooms_cleared
                self._draw_text(f'清理: {cleared} 房间', 20, WINDOW_HEIGHT - 20, GREEN, 12)

            # 房间事件提示
            if hasattr(room, 'active_event') and room.active_event:
                evt = room.active_event
                evt_names = {
                    'ambush': '⚠ 伏击中',
                    'treasure': '✦ 隐藏宝箱',
                    'healing': '♡ 治疗泉',
                    'trap_gauntlet': '☠ 陷阱挑战',
                    'time_rift': '↯ 时空裂隙',
                }
                evt_text = evt_names.get(evt, '')
                if evt_text:
                    self._draw_text(evt_text, WINDOW_WIDTH - 160, WINDOW_HEIGHT - 20, CYAN, 12)

    def _draw_text(self, text, x, y, color, size, center=False):
        try:
            font = get_chinese_font(size)
            surf = font.render(str(text), True, color)
            if center:
                rect = surf.get_rect(center=(x, y))
                self.screen.blit(surf, rect)
            else:
                self.screen.blit(surf, (x, y))
        except:
            pass


class Minimap:
    """小地图 - 代理到增强版"""

    def __init__(self):
        from src.ui.minimap import Minimap as EnhancedMinimap
        self._impl = None
        self._dungeon = None
        self._player = None
        self._enhanced = True

    def set_dungeon(self, dungeon):
        if self._enhanced:
            try:
                from src.ui.minimap import Minimap as EnhancedMinimap
                self._impl = EnhancedMinimap(dungeon, None)
                self._dungeon = dungeon
            except:
                self._enhanced = False

    def mark_visited(self, room):
        if self._impl and self._enhanced:
            self._impl.mark_visited(room)
        elif room:
            room.visited = True

    def mark_enemy_spawn(self, enemy):
        """标记敌人出生（用于小地图更新）"""
        if self._impl and self._enhanced:
            self._impl.mark_enemy_spawn(enemy)

    def toggle(self):
        """切换小地图开关"""
        if self._impl and self._enhanced:
            self._impl.toggle()

    def update(self):
        if self._impl and self._enhanced:
            self._impl.update()

    def draw(self, screen, dungeon, player):
        if self._impl and self._enhanced:
            self._impl.dungeon = dungeon
            self._impl.draw(screen, player, dungeon.enemies,
                           exit_room=getattr(dungeon, 'boss_room', None),
                           shop_room=getattr(dungeon, 'shop_room', None),
                           boss_room=getattr(dungeon, 'boss_room', None))
        else:
            self._draw_simple(screen, dungeon, player)

    def _draw_simple(self, screen, dungeon, player):
        map_surf = pygame.Surface((150, 150), pygame.SRCALPHA)
        map_surf.fill((0, 0, 0, 180))
        scale_x = 150 / dungeon.width
        scale_y = 150 / dungeon.height
        for room in dungeon.rooms:
            rx = int(room.x * scale_x)
            ry = int(room.y * scale_y)
            rw = max(2, int(room.width * scale_x))
            rh = max(2, int(room.height * scale_y))
            if room.visited:
                color = (100, 100, 100, 180)
                if room.room_type == 'boss':
                    color = (200, 80, 80, 200)
                elif room.room_type == 'chest':
                    color = (200, 200, 80, 180)
                elif room.room_type == 'shop':
                    color = (80, 200, 150, 180)
                pygame.draw.rect(map_surf, color, (rx, ry, rw, rh))
        px = int(player.x / TILE_SIZE * scale_x)
        py = int(player.y / TILE_SIZE * scale_y)
        pygame.draw.circle(map_surf, (255, 255, 255), (px, py), 3)
        for enemy in dungeon.enemies:
            if enemy.alive:
                ex = int(enemy.x / TILE_SIZE * scale_x)
                ey = int(enemy.y / TILE_SIZE * scale_y)
                pygame.draw.circle(map_surf, (255, 100, 100), (ex, ey), 1)
        screen.blit(map_surf, (10, WINDOW_HEIGHT - 160))
        pygame.draw.rect(screen, (80, 80, 100), (10, WINDOW_HEIGHT - 160, 150, 150), 1)


from settings import TILE_SIZE
