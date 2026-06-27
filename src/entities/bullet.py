"""
子弹类
"""
import math
import random
import pygame
from settings import TILE_SIZE
from src.engine.resource import get_resources


class Bullet:
    """子弹实体"""

    def __init__(self, x, y, angle, weapon_data, source_is_player=True):
        self.x = x
        self.y = y
        self.angle = angle
        self.source_is_player = source_is_player
        self.speed = weapon_data.get('bullet_speed', 8)
        self.damage = weapon_data.get('damage', 10)
        self.bullet_type = weapon_data.get('bullet_type', 'normal')
        self.lifetime = 180
        self.alive = True
        self.is_explosive = weapon_data.get('explosive', False)
        self.explosion_radius = weapon_data.get('explosion_radius', 40)
        self.slow_effect = weapon_data.get('slow_effect', False)
        self.burn_effect = weapon_data.get('burn_effect', False)
        self.is_piercing = weapon_data.get('piercing', False)
        self.is_homing = weapon_data.get('homing', False)
        self.homing_strength = weapon_data.get('homing_strength', 0.05)
        self.is_bouncing = weapon_data.get('bouncing', False)
        self.bounces_left = weapon_data.get('max_bounces', 2)
        self.chain_lightning = weapon_data.get('chain_lightning', False)
        self.chain_range = weapon_data.get('chain_range', 100)
        self.chain_count = weapon_data.get('chain_count', 3)
        self.pierced_enemies = set()

        self.vx = math.cos(angle) * self.speed
        self.vy = math.sin(angle) * self.speed

        self.radius = 4
        if self.bullet_type == 'rocket':
            self.radius = 7
        elif self.bullet_type == 'laser':
            self.radius = 3
        elif self.bullet_type == 'arrow':
            self.radius = 5
        self.hitbox = pygame.Rect(x - self.radius, y - self.radius,
                                   self.radius * 2, self.radius * 2)

        self.sprite = get_resources().get_bullet_sprite(self.bullet_type)
        self.trail_positions = []

    def update(self, world):
        """更新子弹位置"""
        # 追踪
        if self.is_homing and hasattr(self, '_target'):
            tx, ty = self._target
            dx = tx - self.x
            dy = ty - self.y
            target_angle = math.atan2(dy, dx)
            current_angle = math.atan2(self.vy, self.vx)
            angle_diff = target_angle - current_angle
            # 规范化角度差
            angle_diff = ((angle_diff + math.pi) % (2 * math.pi)) - math.pi
            new_angle = current_angle + angle_diff * self.homing_strength
            self.vx = math.cos(new_angle) * self.speed
            self.vy = math.sin(new_angle) * self.speed
            self.angle = new_angle

        # 火箭弹的尾迹烟雾
        if self.bullet_type == 'rocket':
            self.trail_positions.append((self.x + random.uniform(-2, 2),
                                         self.y + random.uniform(-2, 2)))

        # 尾迹
        self.trail_positions.append((self.x, self.y))
        if len(self.trail_positions) > 8:
            self.trail_positions.pop(0)

        self.x += self.vx
        self.y += self.vy
        self.hitbox.x = self.x - self.radius
        self.hitbox.y = self.y - self.radius

        self.lifetime -= 1
        if self.lifetime <= 0:
            self.alive = False

        # 墙壁碰撞
        if world and world.check_wall_collision(self.hitbox):
            if self.is_bouncing and self.bounces_left > 0:
                self.bounces_left -= 1
                test_x = pygame.Rect(self.x + self.vx, self.y, self.hitbox.width, self.hitbox.height)
                test_y = pygame.Rect(self.x, self.y - self.vy, self.hitbox.width, self.hitbox.height)
                if world.check_wall_collision(test_x):
                    self.vx *= -1
                    self.angle = math.atan2(self.vy, self.vx)
                if world.check_wall_collision(test_y):
                    self.vy *= -1
                    self.angle = math.atan2(self.vy, self.vx)
            else:
                self.alive = False

    def set_target(self, target_x, target_y):
        """设置追踪目标"""
        self._target = (target_x, target_y)

    def draw(self, screen, camera):
        """绘制子弹"""
        sx, sy = camera.apply_point(self.x, self.y)

        # 尾迹
        if len(self.trail_positions) > 1:
            for i, (tx, ty) in enumerate(self.trail_positions[:-1]):
                alpha = int(100 * (i + 1) / len(self.trail_positions))
                tsx, tsy = camera.apply_point(tx, ty)
                pygame.draw.circle(screen, (*self._bullet_color(), alpha),
                                   (int(tsx), int(tsy)), self.radius - 1)

        if self.sprite:
            rect = self.sprite.get_rect(center=(sx, sy))
            screen.blit(self.sprite, rect)
        else:
            color = self._bullet_color()
            pygame.draw.circle(screen, color, (int(sx), int(sy)), self.radius)
            # 追踪子弹有准星效果
            if self.is_homing:
                pygame.draw.circle(screen, color, (int(sx), int(sy)), self.radius + 2, 1)

    def _bullet_color(self):
        """根据类型返回颜色"""
        colors = {
            'normal': (255, 255, 200),
            'fire': (255, 80, 20),
            'ice': (150, 220, 255),
            'laser': (100, 200, 255),
            'energy': (200, 100, 255),
            'arrow': (160, 120, 60),
            'rocket': (255, 140, 40),
        }
        return colors.get(self.bullet_type, (255, 255, 200))


class MeleeAttack:
    """近战攻击判定"""

    def __init__(self, x, y, angle, weapon_data):
        self.x = x
        self.y = y
        self.angle = angle
        self.damage = weapon_data.get('damage', 25)
        self.range = weapon_data.get('range', 50)
        self.arc = weapon_data.get('arc', 120)  # 攻击弧度
        self.lifetime = 8  # 存在帧数
        self.alive = True
        self.hit_enemies = set()  # 防止重复命中

    def update(self):
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.alive = False

    def hits_target(self, target_x, target_y, target_radius=16):
        """检查是否命中目标"""
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > self.range + target_radius:
            return False
        if dist == 0:
            return True
        attack_angle = math.atan2(dy, dx)
        diff = abs((attack_angle - self.angle + math.pi) % (2 * math.pi) - math.pi)
        return diff < math.radians(self.arc / 2)

    def draw(self, screen, camera):
        """绘制近战攻击范围"""
        sx, sy = camera.apply_point(self.x, self.y)
        alpha = int(80 * (self.lifetime / 8))
        surf = pygame.Surface((self.range * 2, self.range * 2), pygame.SRCALPHA)
        start_angle = math.degrees(self.angle) - self.arc / 2
        pygame.draw.arc(surf, (255, 255, 255, alpha),
                        (0, 0, self.range * 2, self.range * 2),
                        math.radians(start_angle),
                        math.radians(start_angle + self.arc),
                        width=6)
        screen.blit(surf, (sx - self.range, sy - self.range))


class LaserBeam:
    """激光束 - 持续伤害的线状攻击"""

    def __init__(self, x, y, angle, damage, width=6, length=300, lifetime=30):
        self.x = x
        self.y = y
        self.angle = angle
        self.damage = damage
        self.width = width
        self.length = length
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.alive = True
        self.hit_enemies = set()

        self.ex = x + math.cos(angle) * length
        self.ey = y + math.sin(angle) * length

    def update(self):
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.alive = False

    def hits_target(self, target_x, target_y, target_radius=16):
        """检测点是否在激光束上"""
        # 线段到点的距离
        px = target_x - self.x
        py = target_y - self.y
        dx = self.ex - self.x
        dy = self.ey - self.y
        line_len_sq = dx * dx + dy * dy
        if line_len_sq == 0:
            return False
        t = max(0, min(1, (px * dx + py * dy) / line_len_sq))
        closest_x = self.x + t * dx
        closest_y = self.y + t * dy
        dist = math.hypot(target_x - closest_x, target_y - closest_y)
        return dist < target_radius + self.width // 2

    def draw(self, screen, camera):
        """绘制激光束"""
        sx, sy = camera.apply_point(self.x, self.y)
        sx2, sy2 = camera.apply_point(self.ex, self.ey)
        alpha = int(200 * (self.lifetime / self.max_lifetime))

        # 外光束
        color = (*self._beam_color(), alpha)
        if alpha > 0:
            pygame.draw.line(screen, color, (sx, sy), (sx2, sy2), self.width + 4)
            # 内光束（更亮）
            inner_color = tuple(min(255, c + 100) for c in color[:3]) + (min(255, alpha + 50),)
            pygame.draw.line(screen, inner_color, (sx, sy), (sx2, sy2), self.width)
            # 闪烁核心
            core_color = (255, 255, 255, alpha)
            pygame.draw.line(screen, core_color, (sx, sy), (sx2, sy2), max(1, self.width - 4))

    def _beam_color(self):
        colors = {
            'laser': (100, 200, 255),
            'fire': (255, 100, 20),
            'energy': (200, 100, 255),
            'ice': (150, 220, 255),
        }
        return colors.get(self.bullet_type if hasattr(self, 'bullet_type') else 'laser', (100, 200, 255))
