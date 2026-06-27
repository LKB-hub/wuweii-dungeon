"""
玩家类 - 移动、战斗、碰撞检测
"""
import math
import random
import pygame
from settings import (TILE_SIZE, PLAYER_SPEED, PLAYER_INVINCIBLE_TIME,
                      PLAYER_DODGE_COOLDOWN)
from src.entities.weapon import WeaponManager
from src.engine.resource import get_resources


class Player:
    """玩家角色"""

    def __init__(self, character_id='knight', x=0, y=0):
        self.character_id = character_id
        from src.entities.character import PLAYER_CHARACTERS
        data = PLAYER_CHARACTERS.get(character_id, PLAYER_CHARACTERS['knight'])

        self.x = x
        self.y = y
        self.width = 24
        self.height = 28
        self.vx = 0
        self.vy = 0

        # 属性
        self.max_hp = data['max_hp']
        self.hp = self.max_hp
        self.speed = data['speed']
        self.max_energy = data['max_energy']
        self.energy = self.max_energy
        self.shield = 0
        self.gold = 0

        # Buff/Debuff
        self.speed_boost_duration = 0
        self.damage_boost_duration = 0
        self.invincible_timer = 0
        self.dodge_timer = 0
        self.is_dodging = False
        self.slow_duration = 0
        self.burn_duration = 0
        self.burn_tick_timer = 0
        self.poison_duration = 0
        self.poison_tick_timer = 0
        self.regeneration_duration = 0
        self.berserk_duration = 0

        # 连击系统
        self.combo_count = 0
        self.combo_timer = 0
        self.max_combo = 0

        # 统计
        self.damage_dealt = 0
        self.damage_taken = 0
        self.enemies_killed = 0
        self.gold_collected = 0
        self.rooms_cleared = 0

        # 经验与升级
        self.level = 1
        self.exp = 0
        self.exp_to_next = 100
        self.skill_points = 0
        self.level_up_pending = False

        # 武器系统
        self.weapon_manager = WeaponManager()
        self.weapon_manager.equip(data['starting_weapon'], 0)

        # 朝向
        self.facing_angle = 0
        self.direction = 0

        # 碰撞体
        self.hitbox = pygame.Rect(x, y, self.width, self.height)
        self.attack_hitbox = pygame.Rect(x, y, self.width + 6, self.height + 6)

        # 精灵
        self.sprites = get_resources().get_player_frames(character_id)
        self.current_frame = 0
        self.anim_timer = 0

        # 输入
        self.move_input = (0, 0)
        self.aim_input = (0, 0)

    @property
    def active_speed(self):
        if self.is_dodging:
            return self.speed * 3
        base = self.speed
        if self.slow_duration > 0:
            base *= 0.4
        if self.speed_boost_duration > 0:
            base *= 1.6
        if self.berserk_duration > 0:
            base *= 1.3
        return base

    def get_damage_multiplier(self):
        mult = 1.0
        if self.damage_boost_duration > 0:
            mult *= 1.5
        if self.berserk_duration > 0:
            mult *= 1.3
        if self.combo_count >= 10:
            mult *= 1.1
        if self.combo_count >= 25:
            mult *= 1.15
        if self.combo_count >= 50:
            mult *= 1.2
        return mult

    def add_combo(self):
        """增加连击数"""
        self.combo_count += 1
        self.combo_timer = 60
        if self.combo_count > self.max_combo:
            self.max_combo = self.combo_count

    def update(self, keys, mouse_pos, world, camera):
        """更新玩家状态"""
        # 计时器
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
        if self.dodge_timer > 0:
            self.dodge_timer -= 1
        if self.speed_boost_duration > 0:
            self.speed_boost_duration -= 1
        if self.damage_boost_duration > 0:
            self.damage_boost_duration -= 1
        if self.slow_duration > 0:
            self.slow_duration -= 1
        if self.burn_duration > 0:
            self.burn_duration -= 1
            self.burn_tick_timer -= 1
            if self.burn_tick_timer <= 0:
                self.take_damage(2, ignore_invincible=True)
                self.burn_tick_timer = 30
        if self.poison_duration > 0:
            self.poison_duration -= 1
            self.poison_tick_timer -= 1
            if self.poison_tick_timer <= 0:
                self.take_damage(1, ignore_invincible=True)
                self.poison_tick_timer = 20
        if self.regeneration_duration > 0:
            self.regeneration_duration -= 1
            if self.regeneration_duration % 60 == 0:
                self.hp = min(self.max_hp, self.hp + 1)
        if self.berserk_duration > 0:
            self.berserk_duration -= 1

        # 连击衰减
        if self.combo_timer > 0:
            self.combo_timer -= 1
        else:
            self.combo_count = 0

        # 翻滚结束
        if self.is_dodging and self.dodge_timer <= 30:
            self.is_dodging = False

        # 能量自然回复
        if self.energy < self.max_energy:
            self.energy = min(self.max_energy, self.energy + 0.03)

        # 移动输入
        dx, dy = self.move_input
        if dx != 0 or dy != 0:
            mag = math.sqrt(dx * dx + dy * dy)
            dx /= mag
            dy /= mag

        self.vx = dx * self.active_speed
        self.vy = dy * self.active_speed

        # 更新朝向（用于瞄准，鼠标控制）
        mouse_wx = mouse_pos[0] + camera.x
        mouse_wy = mouse_pos[1] + camera.y
        self.facing_angle = math.atan2(mouse_wy - self.y, mouse_wx - self.x)
        self.aim_input = (mouse_wx, mouse_wy)

        # 更新方向帧（精灵朝向 + 攻击方向）
        # 优先使用移动方向（键盘），静止时回退到鼠标朝向
        if dx != 0 or dy != 0:
            move_angle = math.degrees(math.atan2(dy, dx)) % 360
        else:
            move_angle = math.degrees(self.facing_angle) % 360

        if 45 <= move_angle < 135:
            self.direction = 0        # 下
        elif 135 <= move_angle < 225:
            self.direction = 1        # 左
        elif 225 <= move_angle < 315:
            self.direction = 3        # 上
        else:
            self.direction = 2        # 右

        # 物理移动 + 碰撞
        self._move_with_collision(world)

        # 动画
        self.anim_timer += 1
        if self.anim_timer > 15:
            self.anim_timer = 0
            self.current_frame = (self.current_frame + 1) % 4

        # 更新武器
        self.weapon_manager.update()

    def _move_with_collision(self, world):
        """分轴移动并检测碰撞"""
        # X 轴
        new_x = self.x + self.vx
        test_rect = pygame.Rect(new_x, self.y, self.width, self.height)
        if not world.check_wall_collision(test_rect):
            self.x = new_x
        else:
            self.vx = 0

        # Y 轴
        new_y = self.y + self.vy
        test_rect = pygame.Rect(self.x, new_y, self.width, self.height)
        if not world.check_wall_collision(test_rect):
            self.y = new_y
        else:
            self.vy = 0

        # 边界
        self.x = max(10, min(self.x, world.pixel_width - self.width - 10))
        self.y = max(10, min(self.y, world.pixel_height - self.height - 10))

        self.hitbox.x = self.x
        self.hitbox.y = self.y
        self.attack_hitbox.x = self.x - 3
        self.attack_hitbox.y = self.y - 3

    def on_input_move(self, dx, dy):
        self.move_input = (dx, dy)

    def dodge(self):
        """闪避/翻滚"""
        if self.dodge_timer > 0:
            return
        self.dodge_timer = PLAYER_DODGE_COOLDOWN
        self.is_dodging = True
        self.invincible_timer = max(self.invincible_timer, 15)

    def fire(self):
        """开火"""
        weapon = self.weapon_manager.get_current()
        if weapon is None:
            return []
        return weapon.fire(self.x + self.width // 2, self.y + self.height // 2,
                           self.aim_input[0], self.aim_input[1])

    def reload(self):
        weapon = self.weapon_manager.get_current()
        if weapon:
            weapon.start_reload()

    def switch_weapon(self):
        self.weapon_manager.switch_weapon()

    def take_damage(self, amount, ignore_invincible=False):
        """受到伤害"""
        if not ignore_invincible and (self.invincible_timer > 0 or self.is_dodging):
            return False

        # 先扣护盾
        if self.shield > 0:
            if self.shield >= amount:
                self.shield -= amount
                self.damage_taken += amount
                return True
            amount -= self.shield
            self.damage_taken += self.shield
            self.shield = 0

        self.hp -= amount
        self.damage_taken += amount
        if not ignore_invincible:
            self.invincible_timer = PLAYER_INVINCIBLE_TIME
        # 受伤重置连击
        if amount > 3:
            self.combo_count = 0
        return True

    def add_exp(self, amount):
        """增加经验值，返回是否升级"""
        self.exp += amount
        if self.exp >= self.exp_to_next:
            self.exp -= self.exp_to_next
            self._level_up()
            return True
        return False

    def _level_up(self):
        """升级 - 随机提升属性"""
        self.level += 1
        self.exp_to_next = int(self.exp_to_next * 1.5)
        self.skill_points += 1
        self.level_up_pending = True

        # 随机属性提升
        boost = random.choice(['max_hp', 'speed', 'damage', 'energy'])
        if boost == 'max_hp':
            self.max_hp += 15
            self.hp = min(self.hp + 15, self.max_hp)
        elif boost == 'speed':
            self.speed += 0.15
        elif boost == 'energy':
            self.max_energy += 20
            self.energy = min(self.energy + 20, self.max_energy)
        elif boost == 'damage':
            self.damage_boost_duration += 600  # 10秒伤害提升

        # 全部属性微量提升
        self.max_hp += 5
        self.hp = min(self.hp + 5, self.max_hp)

    def get_level_stats(self):
        """获取升级后的统计信息"""
        return {
            'level': self.level,
            'max_hp': self.max_hp,
            'speed': self.speed,
            'max_energy': self.max_energy,
            'skill_points': self.skill_points,
        }

    def apply_effect(self, effect_type, duration=None):
        """应用状态效果"""
        if effect_type == 'burn':
            self.burn_duration = duration or 90
            self.burn_tick_timer = 30
        elif effect_type == 'poison':
            self.poison_duration = duration or 120
            self.poison_tick_timer = 20
        elif effect_type == 'slow':
            self.slow_duration = duration or 60
        elif effect_type == 'speed_boost':
            self.speed_boost_duration = duration or 180
        elif effect_type == 'damage_boost':
            self.damage_boost_duration = duration or 240
        elif effect_type == 'regen':
            self.regeneration_duration = duration or 300
        elif effect_type == 'berserk':
            self.berserk_duration = duration or 300

    def is_alive(self):
        return self.hp > 0

    def draw(self, screen, camera):
        """绘制玩家"""
        sx, sy = camera.apply_point(self.x, self.y)

        # 无敌闪烁
        if self.invincible_timer > 0 and (self.invincible_timer // 3) % 2 == 0:
            return

        # 绘制精灵
        if self.sprites and 0 <= self.direction < len(self.sprites):
            sprite = self.sprites[self.direction]
            if sprite:
                screen.blit(sprite, (sx, sy))
        else:
            # 备用：绘制彩色矩形
            color = (50, 100, 220)
            if self.character_id == 'ranger':
                color = (50, 180, 80)
            elif self.character_id == 'mage':
                color = (180, 60, 200)
            pygame.draw.rect(screen, color, (sx, sy, self.width, self.height))
            # 生命值条
            bar_w = self.width
            bar_h = 4
            bar_y = sy - 8
            pygame.draw.rect(screen, (60, 60, 60), (sx, bar_y, bar_w, bar_h))
            hp_pct = self.hp / self.max_hp
            hp_color = (50, 200, 50) if hp_pct > 0.5 else (200, 200, 50) if hp_pct > 0.25 else (200, 50, 50)
            pygame.draw.rect(screen, hp_color, (sx, bar_y, int(bar_w * hp_pct), bar_h))

        # 护盾效果
        if self.shield > 0:
            pygame.draw.circle(screen, (80, 180, 255), (int(sx + self.width // 2), int(sy + self.height // 2)),
                               self.width // 2 + 4, 2)

        # 加速效果
        if self.speed_boost_duration > 0:
            pygame.draw.circle(screen, (255, 255, 100), (int(sx + self.width // 2), int(sy + self.height // 2)),
                               self.width // 2 + 6, 1)

    def draw_weapon_effect(self, screen, camera):
        """绘制武器枪口指示"""
        sx = int(camera.apply_point(self.x + self.width // 2, self.y + self.height // 2)[0])
        sy = int(camera.apply_point(self.x + self.width // 2, self.y + self.height // 2)[1])
        # 简单瞄准线
        weapon = self.weapon_manager.get_current()
        if weapon and weapon.weapon_type == 'ranged':
            ex = sx + math.cos(self.facing_angle) * 30
            ey = sy + math.sin(self.facing_angle) * 30
            pygame.draw.line(screen, (255, 255, 255, 60), (sx, sy), (ex, ey), 2)
