"""
小地图系统 - 显示房间布局、玩家位置、敌人标记、出口位置
"""
import math
import pygame
from settings import WINDOW_WIDTH, WHITE, YELLOW, GREEN, RED, GRAY, CYAN, ORANGE, TILE_SIZE


class Minimap:
    """小地图 - 在屏幕右上角显示缩略地图"""

    def __init__(self, dungeon, camera):
        self.dungeon = dungeon
        self.camera = camera
        self.enabled = True
        self.x = WINDOW_WIDTH - 165   # 右侧
        self.y = 145                    # 在武器栏 + 信息栏下方
        self.size = 140
        self.margin = 8
        self.alpha = 180

        # 缩放
        self.scale = 1.0
        self._calc_scale()

        # 标记
        self.visited_rooms = set()
        self.player_marker_pulse = 0

        # 地图动画
        self.reveal_queue = []  # 待揭示的房间
        self.reveal_progress = {}  # 房间揭示动画进度

    def _calc_scale(self):
        """计算缩放比例"""
        if self.dungeon:
            dungeon_w = self.dungeon.pixel_width
            dungeon_h = self.dungeon.pixel_height
            self.scale = min(self.size / max(dungeon_w, dungeon_h, 1), 1.0)

    def mark_visited(self, room):
        """标记已访问房间"""
        if room not in self.visited_rooms:
            self.visited_rooms.add(room)
            self.reveal_queue.append(room)
            self.reveal_progress[room] = 0

    def mark_enemy_spawn(self, enemy):
        """标记敌人出生点（确保其所在房间在小地图中可见）"""
        if not self.dungeon:
            return
        ex, ey = enemy.x, enemy.y
        for room in self.dungeon.rooms:
            if room.contains_point(ex, ey):
                if room not in self.visited_rooms:
                    self.mark_visited(room)
                break

    def update(self):
        """更新动画"""
        self.player_marker_pulse += 0.08
        # 揭示动画
        for room in list(self.reveal_progress.keys()):
            self.reveal_progress[room] = min(100, self.reveal_progress[room] + 5)
            if self.reveal_progress[room] >= 100:
                del self.reveal_progress[room]

    def toggle(self):
        """开关小地图"""
        self.enabled = not self.enabled

    def _world_to_minimap(self, wx, wy):
        """世界坐标（像素）转小地图坐标"""
        if not self.dungeon:
            return 0, 0

        map_w = self.dungeon.pixel_width
        map_h = self.dungeon.pixel_height
        mx = self.x + self.margin + int((wx / max(map_w, 1)) * (self.size - self.margin * 2))
        my = self.y + self.margin + int((wy / max(map_h, 1)) * (self.size - self.margin * 2))
        return mx, my

    def _room_to_minimap_rect(self, room):
        """房间矩形（像素坐标）转小地图矩形"""
        if not room:
            return None
        rx = room.x * TILE_SIZE
        ry = room.y * TILE_SIZE
        rw = room.width * TILE_SIZE
        rh = room.height * TILE_SIZE
        rx1, ry1 = self._world_to_minimap(rx, ry)
        rx2, ry2 = self._world_to_minimap(rx + rw, ry + rh)
        return pygame.Rect(rx1, ry1, max(2, rx2 - rx1), max(2, ry2 - ry1))

    def draw(self, screen, player=None, enemies=None, exit_room=None, shop_room=None, boss_room=None):
        """绘制小地图"""
        if not self.enabled or not self.dungeon:
            return

        # 背景面板
        panel_rect = pygame.Rect(self.x, self.y, self.size, self.size)
        panel = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        panel.fill((10, 10, 20, self.alpha))
        screen.blit(panel, (self.x, self.y))
        pygame.draw.rect(screen, (60, 60, 80), panel_rect, 1)

        # 标题
        try:
            from src.engine.font_helper import get_chinese_font
            font = get_chinese_font(12)
            title = font.render('地图', True, GRAY)
            screen.blit(title, (self.x + 4, self.y + 2))
        except:
            pass

        # 绘制已访问的房间
        for room in self.visited_rooms:
            rect = self._room_to_minimap_rect(room)
            if not rect:
                continue

            # 揭示动画
            reveal_pct = 1.0
            if room in self.reveal_progress:
                reveal_pct = self.reveal_progress[room] / 100.0

            # 房间颜色
            color = (60, 60, 80)
            if room == shop_room:
                color = (80, 80, 30)
            elif room == boss_room:
                color = (80, 30, 30)
            elif room == exit_room:
                color = (30, 80, 30)

            alpha = int(200 * reveal_pct)
            rsurf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            rsurf.fill((*color, min(255, alpha)))
            screen.blit(rsurf, (rect.x, rect.y))
            pygame.draw.rect(screen, (*color, alpha), rect, 1)

            # 连接通道标记（connections 是房间ID列表）
            if hasattr(room, 'entrances') and room.entrances:
                for ex_tile, ey_tile in room.entrances:
                    # 入口在小地图边缘位置画小点
                    ex_px = ex_tile * TILE_SIZE
                    ey_px = ey_tile * TILE_SIZE
                    emx, emy = self._world_to_minimap(ex_px, ey_px)
                    pygame.draw.circle(screen, (255, 255, 255, alpha),
                                       (emx, emy), 2)

        # 特殊房间标记
        if shop_room and shop_room in self.visited_rooms:
            srect = self._room_to_minimap_rect(shop_room)
            if srect:
                self._draw_icon(screen, srect.centerx, srect.centery, 'S', YELLOW)

        if boss_room and boss_room in self.visited_rooms:
            brect = self._room_to_minimap_rect(boss_room)
            if brect:
                self._draw_icon(screen, brect.centerx, brect.centery, 'B', RED)

        if exit_room and exit_room in self.visited_rooms:
            erect = self._room_to_minimap_rect(exit_room)
            if erect:
                self._draw_icon(screen, erect.centerx, erect.centery, '→', GREEN)

        # 敌人标记
        if enemies:
            enemy_counts = {}
            for enemy in enemies:
                if not enemy.alive:
                    continue
                # 确定敌人所在房间
                ex, ey = enemy.x, enemy.y
                found_room = None
                for room in self.visited_rooms:
                    if room.contains_point(ex, ey):
                        found_room = room
                        break
                if found_room:
                    rid = id(found_room)
                    enemy_counts[rid] = enemy_counts.get(rid, 0) + 1

            for rid, count in enemy_counts.items():
                for room in self.visited_rooms:
                    if id(room) == rid:
                        rect = self._room_to_minimap_rect(room)
                        if rect:
                            self._draw_enemy_dot(screen, rect.centerx, rect.centery, count)
                        break

        # 玩家标记（闪烁脉冲）
        if player and (hasattr(player, 'is_alive') and player.is_alive()):
            px, py = self._world_to_minimap(player.x, player.y)
            pulse = 1 + 0.3 * math.sin(self.player_marker_pulse * 3)
            r = int(4 * pulse)
            # 外发光
            glow = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
            pygame.draw.circle(glow, (255, 255, 255, 60), (r * 2, r * 2), r * 2)
            screen.blit(glow, (px - r * 2, py - r * 2))
            # 玩家点
            pygame.draw.circle(screen, GREEN, (px, py), max(2, r))

    def _draw_icon(self, screen, x, y, text, color):
        """绘制图标文字"""
        try:
            from src.engine.font_helper import get_chinese_font
            font = get_chinese_font(10)
            surf = font.render(text, True, color)
            screen.blit(surf, (x - surf.get_width() // 2, y - surf.get_height() // 2))
        except:
            pygame.draw.circle(screen, color, (x, y), 4)

    def _draw_enemy_dot(self, screen, x, y, count):
        """绘制敌人标记"""
        dot_color = RED if count > 1 else ORANGE
        size = 2 if count == 1 else 3
        pygame.draw.circle(screen, dot_color, (x, y + 6), size)
        if count > 1:
            try:
                from src.engine.font_helper import get_chinese_font
                font = get_chinese_font(8)
                surf = font.render(str(count), True, RED)
                screen.blit(surf, (x + 3, y + 3))
            except:
                pass
