"""
地图瓦片
"""
import pygame
from settings import TILE_SIZE, TILE_SIZE as TS
from src.engine.resource import get_resources


class Tile:
    """单个瓦片"""

    def __init__(self, tile_type='floor'):
        self.tile_type = tile_type
        self.is_solid = tile_type in ('wall', 'wall_top', 'water', 'lava', 'pit')
        self.is_room = False
        self.room_id = -1
        self.sprite = None
        # 瓦片属性
        self.damage_per_tick = 0  # 踩上去每帧伤害
        self.slow_factor = 1.0  # 减速因子
        self.animated = False
        self.anim_offset = 0

        if tile_type == 'lava':
            self.damage_per_tick = 1
        elif tile_type == 'water':
            self.slow_factor = 0.5
            self.damage_per_tick = 0
        elif tile_type == 'pit':
            self.damage_per_tick = 999  # 即死

    def get_sprite(self):
        if self.sprite is None:
            res = get_resources()
            if self.tile_type == 'floor':
                key = 'floor' if (id(self) % 3) != 0 else 'floor_alt'
            elif self.tile_type in ('water', 'lava'):
                key = f'tile_{self.tile_type}'
            else:
                key = f'tile_{self.tile_type}'
            self.sprite = res.get_tile(key)
        return self.sprite


class TileMap:
    """瓦片地图"""

    def __init__(self, map_width, map_height):
        self.width = map_width
        self.height = map_height
        self.tiles = [[Tile('wall') for _ in range(map_height)] for _ in range(map_width)]
        self.room_tiles = {}  # room_id -> [(tx, ty), ...]

    def set_tile(self, x, y, tile_type):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.tiles[x][y] = Tile(tile_type)

    def get_tile(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[x][y]
        return Tile('wall')  # 边界为墙

    def fill_rect(self, x, y, w, h, tile_type):
        """用 tile_type 填充矩形区域"""
        for dx in range(w):
            for dy in range(h):
                self.set_tile(x + dx, y + dy, tile_type)

    def mark_room(self, x, y, w, h, room_id):
        """标记一个区域属于某个房间"""
        if room_id not in self.room_tiles:
            self.room_tiles[room_id] = []
        for dx in range(w):
            for dy in range(h):
                tx, ty = x + dx, y + dy
                if 0 <= tx < self.width and 0 <= ty < self.height:
                    self.tiles[tx][ty].is_room = True
                    self.tiles[tx][ty].room_id = room_id
                    self.room_tiles[room_id].append((tx, ty))

    def get_room_tiles(self, room_id):
        """获取指定房间的所有瓦片坐标"""
        return self.room_tiles.get(room_id, [])

    def is_solid(self, x, y):
        return self.get_tile(x, y).is_solid

    def is_walkable(self, x, y):
        return not self.is_solid(x, y)

    def draw(self, screen, camera):
        """绘制可见区域的瓦片"""
        cx = int(camera.x // TILE_SIZE)
        cy = int(camera.y // TILE_SIZE)
        tw = (camera.world_width or screen.get_width()) // TILE_SIZE + 2
        th = (camera.world_height or screen.get_height()) // TILE_SIZE + 2

        for dx in range(max(0, cx - 1), min(self.width, cx + tw + 2)):
            for dy in range(max(0, cy - 1), min(self.height, cy + th + 2)):
                tile = self.tiles[dx][dy]
                sprite = tile.get_sprite()
                sx, sy = camera.apply_point(dx * TILE_SIZE, dy * TILE_SIZE)
                if sprite:
                    screen.blit(sprite, (sx, sy))
                else:
                    if tile.is_solid:
                        pygame.draw.rect(screen, (80, 80, 90), (sx, sy, TILE_SIZE, TILE_SIZE))
                    else:
                        pygame.draw.rect(screen, (60, 50, 40), (sx, sy, TILE_SIZE, TILE_SIZE))

    def check_collision(self, rect):
        """检查矩形是否与固体瓦片碰撞"""
        left = max(0, int(rect.left // TILE_SIZE))
        right = min(self.width - 1, int(rect.right // TILE_SIZE))
        top = max(0, int(rect.top // TILE_SIZE))
        bottom = min(self.height - 1, int(rect.bottom // TILE_SIZE))

        for tx in range(left, right + 1):
            for ty in range(top, bottom + 1):
                if self.is_solid(tx, ty):
                    tile_rect = pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    if rect.colliderect(tile_rect):
                        return True
        return False
