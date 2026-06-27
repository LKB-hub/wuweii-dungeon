"""
地牢生成器 - 使用 BSP 算法生成随机房间布局
"""
import math
import random
import pygame
from settings import (TILE_SIZE, DUNGEON_WIDTH, DUNGEON_HEIGHT, MAX_ROOMS,
                      ROOM_MIN_SIZE, ROOM_MAX_SIZE)
from src.world.tile import TileMap
from src.world.room import Room, Corridor
from src.entities.enemy import spawn_enemy_for_room, spawn_boss, spawn_elite
from src.entities.item import generate_loot, generate_chest, ChestItem
from src.entities.shop import Shop
from src.entities.character import TRAP_TYPES, DECORATIONS, ROOM_THEMES, ROOM_EVENTS, BUFF_TYPES


class Trap:
    """陷阱实体"""
    def __init__(self, x, y, trap_type):
        self.x = x
        self.y = y
        self.trap_type = trap_type
        data = TRAP_TYPES[trap_type]
        self.damage = data['damage']
        self.cooldown = 0
        self.max_cooldown = data['cooldown']
        self.trigger_radius = data['trigger_radius']
        self.visible = data['visible']
        self.triggered = False
        self.burn_duration = data.get('burn_duration', 0)
        self.poison_duration = data.get('poison_duration', 0)
        self.hitbox = pygame.Rect(x - self.trigger_radius, y - self.trigger_radius,
                                   self.trigger_radius * 2, self.trigger_radius * 2)

    def update(self):
        if self.cooldown > 0:
            self.cooldown -= 1
        if self.triggered and self.cooldown <= 0:
            self.triggered = False

    def try_trigger(self, player_x, player_y):
        if self.cooldown > 0:
            return None
        dist = ((player_x - self.x) ** 2 + (player_y - self.y) ** 2) ** 0.5
        if dist < self.trigger_radius:
            self.triggered = True
            self.cooldown = self.max_cooldown
            return {'damage': self.damage, 'burn': self.burn_duration, 'poison': self.poison_duration}
        return None

    def draw(self, screen, camera):
        if not self.visible and not self.triggered:
            return
        sx, sy = camera.apply_point(self.x, self.y)
        colors = {'spike': (180, 180, 180), 'fire_trap': (255, 100, 30),
                  'poison_gas': (100, 200, 50), 'arrow_trap': (150, 150, 100)}
        color = colors.get(self.trap_type, (200, 200, 200))
        if self.triggered:
            color = (255, 50, 50)
        r = self.trigger_radius
        pygame.draw.circle(screen, color, (int(sx), int(sy)), r // 2, 2)
        if self.cooldown > 0:
            pct = self.cooldown / self.max_cooldown
            pygame.draw.arc(screen, (100, 100, 100), (sx - r, sy - r, r * 2, r * 2),
                            0, 2 * 3.14159 * pct, 2)


class Dungeon:
    """地牢世界 - 包含所有房间、走廊和实体"""

    def __init__(self):
        self.width = DUNGEON_WIDTH
        self.height = DUNGEON_HEIGHT
        self.pixel_width = self.width * TILE_SIZE
        self.pixel_height = self.height * TILE_SIZE

        self.tile_map = TileMap(self.width, self.height)
        self.rooms = []
        self.corridors = []
        self.start_room = None
        self.boss_room = None
        self.shop_room = None
        self.enemies = []
        self.items = []
        self.traps = []
        self.shop = None
        self.score = 0
        self.difficulty = 1

        # 楼层系统
        self.floor_number = 1
        self.floor_theme = 'dungeon'
        self.max_floor = 12  # 通关所需楼层（快速通关约1小时）

        # 环境装饰帧
        self._deco_frame = 0
        self._deco_anim_speed = 30

        # 房间事件
        self.room_events = {}
        self.active_buffs = []

    def generate(self, difficulty=1):
        """生成整个地牢"""
        self.difficulty = difficulty
        self._generate_rooms()
        self._generate_corridors()
        self._assign_room_types()
        self._spawn_room_content(difficulty)
        self._spawn_traps(difficulty)
        self._spawn_decorations()
        self._generate_secret_room()
        self._spawn_mini_boss()
        self._setup_doors()

    def _generate_rooms(self):
        """使用 BSP 风格生成不重叠的房间"""
        for _ in range(200):
            w = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
            h = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
            x = random.randint(2, self.width - w - 2)
            y = random.randint(2, self.height - h - 2)
            new_room = Room(x, y, w, h)
            new_room.id = len(self.rooms)

            if not any(new_room.overlaps(r, padding=3) for r in self.rooms):
                self.rooms.append(new_room)
                self.tile_map.fill_rect(x, y, w, h, 'floor')
                self.tile_map.mark_room(x, y, w, h, new_room.id)
                for dx in range(-1, w + 1):
                    self.tile_map.set_tile(x + dx, y - 1, 'wall')
                    self.tile_map.set_tile(x + dx, y + h, 'wall')
                for dy in range(-1, h + 1):
                    self.tile_map.set_tile(x - 1, y + dy, 'wall')
                    self.tile_map.set_tile(x + w, y + dy, 'wall')

                if len(self.rooms) >= MAX_ROOMS:
                    break

    def _generate_corridors(self):
        """用最小生成树连接房间"""
        if len(self.rooms) < 2:
            return

        connected = {self.rooms[0]}
        unconnected = set(self.rooms[1:])

        while unconnected:
            best_dist = float('inf')
            best_pair = None

            for r1 in connected:
                for r2 in unconnected:
                    c1 = r1.center_tile()
                    c2 = r2.center_tile()
                    dist = abs(c1[0] - c2[0]) + abs(c1[1] - c2[1])
                    if dist < best_dist:
                        best_dist = dist
                        best_pair = (r1, r2)

            if best_pair:
                r1, r2 = best_pair
                corridor = Corridor(r1, r2)
                corridor.generate(self.tile_map)
                self.corridors.append(corridor)
                connected.add(r2)
                unconnected.remove(r2)

    def _assign_room_types(self):
        """分配房间类型"""
        if not self.rooms:
            return

        self.start_room = self.rooms[0]
        self.start_room.room_type = 'start'

        if len(self.rooms) >= 2:
            farthest = self.rooms[-1]
            max_dist = 0
            for r in self.rooms[1:]:
                c1 = self.start_room.center_tile()
                c2 = r.center_tile()
                dist = abs(c1[0] - c2[0]) + abs(c1[1] - c2[1])
                if dist > max_dist:
                    max_dist = dist
                    farthest = r
            self.boss_room = farthest
            self.boss_room.room_type = 'boss'
            self.tile_map.fill_rect(farthest.x, farthest.y,
                                    farthest.width, farthest.height, 'boss_room_floor')

        candidates = [r for r in self.rooms if r not in (self.start_room, self.boss_room)]
        random.shuffle(candidates)

        if len(candidates) >= 1:
            candidates[0].room_type = 'chest'
            self.tile_map.fill_rect(candidates[0].x, candidates[0].y,
                                    candidates[0].width, candidates[0].height,
                                    'chest_room_floor')

        if len(candidates) >= 2:
            candidates[1].room_type = 'shop'
            self.shop_room = candidates[1]
            self.tile_map.fill_rect(candidates[1].x, candidates[1].y,
                                    candidates[1].width, candidates[1].height,
                                    'shop_floor')

    def _spawn_room_content(self, difficulty):
        """在每个房间生成敌人和物品"""
        for room in self.rooms:
            if room.room_type == 'start':
                continue
            elif room.room_type == 'boss':
                boss_type = self._select_boss()
                boss = spawn_boss(room, boss_type)
                self.enemies.append(boss)
                room.enemies.append(boss)
            elif room.room_type == 'chest':
                cx, cy = room.center()
                chest = generate_chest(cx, cy)
                self.items.append(chest)
                room.items.append(chest)
            elif room.room_type == 'shop':
                cx, cy = room.center()
                self.shop = Shop(cx, cy)
            else:
                enemies = spawn_enemy_for_room(room, difficulty)
                self.enemies.extend(enemies)
                room.enemies.extend(enemies)

    def _spawn_traps(self, difficulty):
        """在走廊和普通房间生成陷阱"""
        num_traps = difficulty * 3
        trap_types = list(TRAP_TYPES.keys())
        for _ in range(num_traps):
            normal_rooms = [r for r in self.rooms if r.room_type == 'normal']
            if not normal_rooms:
                break
            room = random.choice(normal_rooms)
            tx, ty = room.random_position(margin=3)
            ttype = random.choice(trap_types)
            trap = Trap(tx, ty, ttype)
            self.traps.append(trap)
            room.traps.append(trap)

    def add_trap(self, tx, ty, trap_type):
        """在指定位置添加陷阱"""
        if trap_type not in TRAP_TYPES:
            return
        trap = Trap(tx, ty, trap_type)
        self.traps.append(trap)
        # 尝试找到所在房间并关联
        for room in self.rooms:
            if (room.x * TILE_SIZE <= tx <= (room.x + room.width) * TILE_SIZE and
                    room.y * TILE_SIZE <= ty <= (room.y + room.height) * TILE_SIZE):
                room.traps.append(trap)
                break

    def get_tile(self, tile_x, tile_y):
        """获取指定瓦片坐标的瓦片"""
        return self.tile_map.get_tile(tile_x, tile_y)

    def update_traps(self, player):
        """更新陷阱状态，检测触发"""
        effect = None
        for trap in self.traps:
            trap.update()
            result = trap.try_trigger(player.x + player.width // 2, player.y + player.height // 2)
            if result:
                effect = result
        return effect

    def _setup_doors(self):
        """在房间入口处标记门"""
        for room in self.rooms:
            for ex, ey in room.entrances:
                self.tile_map.set_tile(ex, ey, 'door')

    def _spawn_decorations(self):
        """在房间中生成装饰物"""
        for room in self.rooms:
            if room.room_type in ('start', 'shop'):
                continue
            num = random.randint(0, 3)
            for _ in range(num):
                dx, dy = room.random_position(margin=2)
                deco = random.choice(DECORATIONS)
                room.decorations.append({'x': dx, 'y': dy, **deco})

    def _generate_secret_room(self):
        """有概率生成秘密房间"""
        if random.random() < 0.3 + self.difficulty * 0.05:
            w = random.randint(4, 8)
            h = random.randint(4, 8)
            x = random.randint(5, self.width - w - 5)
            y = random.randint(5, self.height - h - 5)
            secret = Room(x, y, w, h)
            secret.id = len(self.rooms)
            secret.room_type = 'secret'
            if not any(secret.overlaps(r, padding=1) for r in self.rooms):
                self.rooms.append(secret)
                self.tile_map.fill_rect(x, y, w, h, 'secret_floor')
                self.tile_map.mark_room(x, y, w, h, secret.id)
                for dx in range(-1, w + 1):
                    self.tile_map.set_tile(x + dx, y - 1, 'hidden_wall')
                    self.tile_map.set_tile(x + dx, y + h, 'hidden_wall')
                for dy in range(-1, h + 1):
                    self.tile_map.set_tile(x - 1, y + dy, 'hidden_wall')
                    self.tile_map.set_tile(x + w, y + dy, 'hidden_wall')
                entry_side = random.randint(0, 3)
                if entry_side == 0:
                    ex, ey = x + w // 2, y - 1
                elif entry_side == 1:
                    ex, ey = x + w // 2, y + h
                elif entry_side == 2:
                    ex, ey = x - 1, y + h // 2
                else:
                    ex, ey = x + w, y + h // 2
                if 0 <= ex < self.width and 0 <= ey < self.height:
                    self.tile_map.set_tile(ex, ey, 'floor')

    def _spawn_mini_boss(self):
        """在普通房间随机刷新精英敌人"""
        if self.difficulty >= 3 and random.random() < 0.25 + self.difficulty * 0.05:
            candidates = [r for r in self.rooms if r.room_type == 'normal' and r != self.start_room]
            if candidates:
                room = random.choice(candidates)
                elite_types = ['elite_knight', 'necromancer', 'heavy_gunner', 'shield_guard']
                etype = random.choice(elite_types)
                mini_boss = spawn_elite(room, etype, self.difficulty)
                self.enemies.append(mini_boss)
                room.enemies.append(mini_boss)
                room.room_type = 'mini_boss'
                self.tile_map.fill_rect(room.x, room.y, room.width, room.height, 'mini_boss_floor')

    def get_floor_name(self):
        """获取当前楼层名称"""
        if not hasattr(self, 'floor_number'):
            self.floor_number = 1
        theme_names = {
            'dungeon': '幽暗地牢',
            'crypt': '地下墓地',
            'forge': '熔岩锻造场',
            'jungle': '剧毒丛林',
            'ice_cave': '寒冰洞穴',
        }
        total = self.max_floor
        suffix = f'第{self.floor_number}/{total}层'
        base = theme_names.get(self.floor_theme, '未知区域')
        name = f'{base} {suffix}'
        if self.floor_number == total:
            name = f'{base} 最终层 [{self.floor_number}/{total}]'
        return name

    def _select_floor_theme(self):
        """根据楼层选择主题（更多主题递增难度）"""
        themes = ['dungeon', 'crypt', 'forge', 'jungle', 'ice_cave',
                  'dungeon', 'crypt', 'forge', 'jungle', 'ice_cave',
                  'dungeon', 'crypt']
        idx = min(self.floor_number - 1, len(themes) - 1)
        self.floor_theme = themes[idx]

    def _select_boss(self):
        """根据楼层选择Boss类型（每3层换一个主题Boss）"""
        n = self.floor_number
        if n % 4 == 1:
            return 'boss_knight'
        elif n % 4 == 2:
            return random.choice(['boss_mage', 'boss_mech'])
        elif n % 4 == 3:
            return random.choice(['boss_dragon', 'boss_mage'])
        else:
            return random.choice(['boss_knight', 'boss_mech', 'boss_dragon'])

    def generate_next_floor(self):
        """生成下一层地牢（难度随楼层递增）"""
        self.floor_number = getattr(self, 'floor_number', 1) + 1
        self.rooms = []
        self.corridors = []
        self.enemies = []
        self.items = []
        self.traps = []
        self.shop = None
        self.active_buffs = []
        self.tile_map = TileMap(self.width, self.height)
        self._select_floor_theme()
        # 楼层越深难度越高
        floor_difficulty = min(self.difficulty + (self.floor_number - 1) // 2, 8)
        self.generate(difficulty=floor_difficulty)

    def update(self):
        """更新地牢状态 - 清理死亡敌人、环境动画"""
        # 环境帧
        self._deco_frame += 1

        for enemy in self.enemies:
            if not enemy.alive:
                room = self.get_room_at(enemy.x, enemy.y)
                if room:
                    room.enemies = [e for e in room.enemies if e.alive]
                    if len(room.enemies) == 0 and not room.cleared:
                        room.cleared = True
                        room.opened = True
                        loot = generate_loot(enemy.x, enemy.y, room.room_type == 'boss')
                        self.items.extend(loot)
                        room.items.extend(loot)
                        if room.room_type == 'boss':
                            self.score += 500
                        else:
                            self.score += 50

        self.enemies = [e for e in self.enemies if e.alive]
        self.items = [i for i in self.items if i.alive]

        for item in self.items[:]:
            item.update()
        self.items = [i for i in self.items if i.alive]

        # 更新陷阱
        for trap in self.traps:
            trap.update()

    def check_wall_collision(self, rect):
        """检查墙壁碰撞"""
        return self.tile_map.check_collision(rect)

    def get_room_at(self, px, py):
        """获取指定像素坐标所在的房间"""
        for room in self.rooms:
            if room.contains_point(px, py):
                return room
        return None

    def get_spawn_point(self):
        """返回玩家出生点"""
        if self.start_room:
            return self.start_room.center()
        elif self.rooms:
            return self.rooms[0].center()
        return (TILE_SIZE * 5, TILE_SIZE * 5)

    def is_all_cleared(self):
        """检查是否所有房间都被清理"""
        return all(room.cleared for room in self.rooms if room.room_type not in ('start', 'shop'))

    def trigger_room_event(self, room):
        """触发房间事件"""
        if id(room) in self.room_events:
            return None
        # 随机决定是否触发事件
        if random.random() < 0.3:
            weights = [ev['weight'] for ev in ROOM_EVENTS]
            event = random.choices(ROOM_EVENTS, weights=weights, k=1)[0]
            self.room_events[id(room)] = event
            return event
        return None

    def apply_room_event(self, room, player):
        """应用房间事件效果"""
        event = self.room_events.get(id(room))
        if not event:
            return None

        ename = event['name']
        if ename == 'enemy_ambush':
            # 在房间边缘生成额外敌人
            extra = spawn_enemy_for_room(room, self.difficulty)
            self.enemies.extend(extra)
        elif ename == 'treasure_room':
            cx, cy = room.center()
            chest = generate_chest(cx + random.randint(-30, 30), cy + random.randint(-30, 30))
            self.items.append(chest)
            if hasattr(room, 'items'):
                room.items.append(chest)
        elif ename == 'healing_fountain':
            if player:
                heal_amount = int(player.max_hp * 0.4)
                player.hp = min(player.max_hp, player.hp + heal_amount)
                player.energy = player.max_energy
        elif ename == 'trap_gauntlet':
            # 在房间中添加额外陷阱
            for _ in range(random.randint(3, 6)):
                tx = room.x + random.randint(2, max(3, room.width - 3))
                ty = room.y + random.randint(2, max(3, room.height - 3))
                ttype = random.choice(list(TRAP_TYPES.keys()))
                self.traps.append(Trap(tx, ty, ttype))
        elif ename == 'time_rift':
            # 减速所有敌人
            for enemy in self.enemies:
                enemy.slow_timer = max(enemy.slow_timer, 300)

        del self.room_events[id(room)]
        return event

    def add_buff(self, buff_type):
        """添加增益效果"""
        if buff_type in BUFF_TYPES:
            self.active_buffs.append({
                'type': buff_type,
                'duration': BUFF_TYPES[buff_type]['duration'],
                'data': BUFF_TYPES[buff_type],
            })

    def update_buffs(self):
        """更新增益效果"""
        for buff in self.active_buffs[:]:
            buff['duration'] -= 1
            if buff['duration'] <= 0:
                self.active_buffs.remove(buff)

    def get_buff_multiplier(self, stat_key):
        """获取增益属性的倍率"""
        mult = 1.0
        for buff in self.active_buffs:
            data = buff['data']
            if stat_key == 'attack' and 'atk_mult' in data:
                mult *= data['atk_mult']
            elif stat_key == 'speed' and 'spd_mult' in data:
                mult *= data['spd_mult']
            elif stat_key == 'damage_taken' and 'dmg_mult' in data:
                mult *= data['dmg_mult']
            elif stat_key == 'gold' and 'gold_mult' in data:
                mult *= data['gold_mult']
        return mult

    def has_buff(self, buff_type):
        """检查是否有指定增益"""
        return any(b['type'] == buff_type for b in self.active_buffs)

    def draw(self, screen, camera):
        """绘制地牢"""
        self.tile_map.draw(screen, camera)

        for item in self.items:
            if item.alive:
                item.draw(screen, camera)

        # 绘制房间装饰物（带动画）
        for room in self.rooms:
            for deco in room.decorations:
                sx, sy = camera.apply_point(deco['x'], deco['y'])
                color = deco.get('color', (150, 150, 150))
                sym = deco.get('symbol', 'o')
                size = 4
                animated = deco.get('animated', False)

                # 动画闪烁
                if animated and self._deco_frame % self._deco_anim_speed < self._deco_anim_speed // 2:
                    color = tuple(min(255, c + 40) for c in color)

                if sym == 'i':  # 蜡烛
                    pygame.draw.circle(screen, color, (int(sx), int(sy)), size)
                    if animated:
                        # 火焰光晕
                        flicker = random.randint(-3, 3)
                        r = size + 3 + flicker
                        pygame.draw.circle(screen, (255, 200, 50, 40),
                                           (int(sx), int(sy)), r, 1)
                elif sym == 'T':  # 火把
                    pygame.draw.rect(screen, color, (sx - 2, sy - size, 4, size * 2))
                    if animated:
                        flicker = random.randint(-4, 4)
                        pygame.draw.circle(screen, (255, 150, 30),
                                           (int(sx), int(sy - size - 2 + flicker)), 5)
                elif sym == '#':  # 木箱
                    pygame.draw.rect(screen, color, (sx - size, sy - size, size * 2, size * 2))
                    pygame.draw.line(screen, (80, 60, 30), (sx - size, sy), (sx + size, sy), 2)
                elif sym == 'x':  # 骷髅
                    pygame.draw.circle(screen, color, (int(sx), int(sy)), size + 1)
                    pygame.draw.circle(screen, (0, 0, 0), (int(sx) - 2, int(sy) - 1), 2)
                    pygame.draw.circle(screen, (0, 0, 0), (int(sx) + 2, int(sy) - 1), 2)
                elif sym == 'u':  # 蘑菇
                    pygame.draw.ellipse(screen, color, (sx - size, sy - size * 2, size * 2, size * 3))
                    pygame.draw.rect(screen, (180, 150, 120), (sx - 1, sy - size, 2, size))
                elif sym == '^':  # 石笋
                    pygame.draw.polygon(screen, color, [(sx, sy - size - 2), (sx - size, sy + 2),
                                                         (sx + size, sy + 2)])
                elif sym == ',':  # 血迹
                    pygame.draw.ellipse(screen, color, (sx - size, sy - size, size * 2, size * 3))
                elif sym == '~':  # 蜘蛛网
                    for _ in range(3):
                        angle = random.uniform(0, math.pi)
                        end_x = sx + math.cos(angle) * size * 2
                        end_y = sy + math.sin(angle) * size * 2
                        pygame.draw.line(screen, color, (sx, sy), (end_x, end_y), 1)
                else:
                    pygame.draw.circle(screen, color, (int(sx), int(sy)), size + 1)

                # 发光效果
                if deco.get('glowing'):
                    glow_r = size + 3 + int(math.sin(self._deco_frame * 0.05) * 2)
                    glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
                    pygame.draw.circle(glow_surf, (*color, 30), (glow_r, glow_r), glow_r)
                    screen.blit(glow_surf, (sx - glow_r, sy - glow_r))

        for trap in self.traps:
            trap.draw(screen, camera)

        if self.shop:
            self.shop.draw(screen, camera)
