"""
房间类 - 地牢中的房间和走廊，含特殊房间类型和效果
"""
import random
import math
import pygame
from settings import TILE_SIZE


class Room:
    """地牢中的一个房间"""

    def __init__(self, x, y, w, h):
        self.x = x  # 瓦片坐标 (左上角)
        self.y = y
        self.width = w
        self.height = h
        self.id = -1
        self.room_type = 'normal'  # normal, chest, shop, boss, start, secret, treasure, trap_room
        self.enemies = []
        self.items = []
        self.traps = []
        self.decorations = []
        self.cleared = False
        self.visited = False
        self.opened = False
        self.connections = []  # 连接的房间ID列表
        self.entrances = []  # 入口位置 (tile_x, tile_y)
        # 特殊房间属性
        self.door_locked = False
        self.enemy_wave_index = 0
        self.max_waves = 1
        self.active_event = None
        self.ambient_sound_timer = random.randint(180, 600)
        self.portal_active = False
        self.portal_target = None

    def center(self):
        """返回房间中心的像素坐标"""
        cx = (self.x + self.width // 2) * TILE_SIZE
        cy = (self.y + self.height // 2) * TILE_SIZE
        return (cx, cy)

    def center_tile(self):
        """返回房间中心的瓦片坐标"""
        return (self.x + self.width // 2, self.y + self.height // 2)

    def random_position(self, margin=2):
        """返回房间内随机像素坐标"""
        px = (self.x + random.randint(margin, self.width - margin)) * TILE_SIZE
        py = (self.y + random.randint(margin, self.height - margin)) * TILE_SIZE
        return (px, py)

    def edge_midpoints(self):
        """返回四条边中点(瓦片坐标): 上/下/左/右"""
        mx = self.x + self.width // 2
        my = self.y + self.height // 2
        return [
            (mx, self.y),                     # 上
            (mx, self.y + self.height - 1),   # 下
            (self.x, my),                     # 左
            (self.x + self.width - 1, my),    # 右
        ]

    def overlaps(self, other, padding=1):
        """检查是否与另一个房间重叠"""
        return (self.x - padding < other.x + other.width and
                self.x + self.width + padding > other.x and
                self.y - padding < other.y + other.height and
                self.y + self.height + padding > other.y)

    def contains_point(self, px, py):
        """检查像素坐标是否在房间内"""
        rw = self.width * TILE_SIZE
        rh = self.height * TILE_SIZE
        return (self.x * TILE_SIZE <= px < self.x * TILE_SIZE + rw and
                self.y * TILE_SIZE <= py < self.y * TILE_SIZE + rh)

    def contains_tile(self, tx, ty):
        """检查瓦片坐标是否在房间内"""
        return self.x <= tx < self.x + self.width and self.y <= ty < self.y + self.height

    def is_on_border(self, tx, ty):
        """检查瓦片是否在房间边界上"""
        on_x = tx == self.x or tx == self.x + self.width - 1
        on_y = ty == self.y or ty == self.y + self.height - 1
        inside = self.contains_tile(tx, ty)
        return inside and (on_x or on_y)

    def perimeter_tiles(self):
        """返回房间边界瓦片列表"""
        tiles = []
        for dx in range(self.width):
            tiles.append((self.x + dx, self.y))
            tiles.append((self.x + dx, self.y + self.height - 1))
        for dy in range(1, self.height - 1):
            tiles.append((self.x, self.y + dy))
            tiles.append((self.x + self.width - 1, self.y + dy))
        return tiles

    def has_enemies(self):
        """房间内还有存活的敌人"""
        return any(e.alive for e in self.enemies)

    def lock_doors(self):
        """锁定房门（Boss战/事件）"""
        self.door_locked = True

    def unlock_doors(self):
        """解锁房门"""
        self.door_locked = False

    def get_pixel_rect(self):
        """获取房间的像素矩形"""
        return pygame.Rect(
            self.x * TILE_SIZE, self.y * TILE_SIZE,
            self.width * TILE_SIZE, self.height * TILE_SIZE
        )

    def get_inner_rect(self, margin=2):
        """获取房间内部像素矩形（有边距）"""
        return pygame.Rect(
            (self.x + margin) * TILE_SIZE,
            (self.y + margin) * TILE_SIZE,
            (self.width - margin * 2) * TILE_SIZE,
            (self.height - margin * 2) * TILE_SIZE
        )

    def distance_to(self, other):
        """计算到另一个房间中心的曼哈顿距离"""
        cx1, cy1 = self.center_tile()
        cx2, cy2 = other.center_tile()
        return abs(cx1 - cx2) + abs(cy1 - cy2)

    def is_adjacent(self, other):
        """检查是否与另一个房间相邻"""
        return other.id in self.connections

    def __repr__(self):
        return f"Room({self.x},{self.y},{self.width}x{self.height},{self.room_type})"


class Corridor:
    """走廊连接两个房间 - 强化版：正确打通房间入口"""

    def __init__(self, room_a, room_b):
        self.room_a = room_a
        self.room_b = room_b
        self.tiles = []  # (x, y) 瓦片坐标列表
        self.entry_a = None  # 进入房间A的入口坐标
        self.entry_b = None  # 进入房间B的入口坐标

    def generate(self, tile_map):
        """在 tile_map 上生成走廊"""
        # 选择最佳的边缘中点作为连接点
        ax, ay = self._best_entry(self.room_a, self.room_b)
        bx, by = self._best_entry(self.room_b, self.room_a)
        self.entry_a = (ax, ay)
        self.entry_b = (bx, by)

        # 先打通房间入口（房间墙壁变地板）
        self._open_entrance(tile_map, self.room_a, ax, ay)
        self._open_entrance(tile_map, self.room_b, bx, by)

        # L形走廊
        if random.random() < 0.5:
            self._dig_horizontal(tile_map, ax, bx, ay)
            self._dig_vertical(tile_map, bx, ay, by)
        else:
            self._dig_vertical(tile_map, ax, ay, by)
            self._dig_horizontal(tile_map, ax, bx, by)

        # 记录连接
        self.room_a.connections.append(self.room_b.id)
        self.room_b.connections.append(self.room_a.id)
        self.room_a.entrances.append((ax, ay))
        self.room_b.entrances.append((bx, by))

    def _best_entry(self, room, target):
        """选择room到target的最佳入口点（最近的边缘中点）"""
        points = room.edge_midpoints()
        tx, ty = target.center_tile()
        best = points[0]
        best_dist = float('inf')
        for px, py in points:
            dist = abs(px - tx) + abs(py - ty)
            if dist < best_dist:
                best_dist = dist
                best = (px, py)
        return best

    def _open_entrance(self, tile_map, room, ex, ey):
        """打通房间入口：将入口及周围墙壁改为地板"""
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                tx, ty = ex + dx, ey + dy
                if room.contains_tile(tx, ty):
                    tile_map.set_tile(tx, ty, 'floor')
                    self.tiles.append((tx, ty))

    def _try_set_floor(self, tile_map, x, y):
        """安全地设置地板（不覆盖房间边界外的墙）"""
        if 0 <= x < tile_map.width and 0 <= y < tile_map.height:
            current = tile_map.get_tile(x, y)
            if not current.is_room:
                tile_map.set_tile(x, y, 'floor')
                self.tiles.append((x, y))

    def _try_set_wall(self, tile_map, x, y):
        """安全地设置墙壁（不覆盖房间或走廊地板）"""
        if 0 <= x < tile_map.width and 0 <= y < tile_map.height:
            current = tile_map.get_tile(x, y)
            if current.is_solid and not current.is_room:
                tile_map.set_tile(x, y, 'wall')

    def _dig_horizontal(self, tile_map, x1, x2, y):
        """水平挖掘走廊"""
        step = 1 if x2 > x1 else -1
        for x in range(x1, x2 + step, step):
            # 中央通道 (3格宽)
            for dy in range(-1, 2):
                self._try_set_floor(tile_map, x, y + dy)
            # 两侧墙壁
            self._try_set_wall(tile_map, x, y - 2)
            self._try_set_wall(tile_map, x, y + 2)

    def _dig_vertical(self, tile_map, x, y1, y2):
        """垂直挖掘走廊"""
        step = 1 if y2 > y1 else -1
        for y in range(y1, y2 + step, step):
            # 中央通道 (3格宽)
            for dx in range(-1, 2):
                self._try_set_floor(tile_map, x + dx, y)
            # 两侧墙壁
            self._try_set_wall(tile_map, x - 2, y)
            self._try_set_wall(tile_map, x + 2, y)
