"""
技能系统 - 主动技能释放、被动技能效果
"""
import math
import random
import pygame
from src.entities.bullet import Bullet
from src.entities.character import SKILL_DATA


class SkillManager:
    """管理玩家技能（主动+被动）"""

    def __init__(self, player):
        self.player = player
        self.active_skill_id = None
        self.passive_skill_id = None
        self.cooldown_remaining = 0
        self.passive_timer = 0

        # 技能等级
        self.active_level = 1
        self.passive_level = 1

        # 额外被动加成
        self.passives = {}

    def set_skills(self, character_data):
        """根据角色数据设置技能"""
        self.active_skill_id = character_data.get('skill')
        self.passive_skill_id = character_data.get('passive')
        self.cooldown_remaining = 0
        self.passive_timer = 0
        self.active_level = 1
        self.passive_level = 1
        # 初始化被动数据
        if self.passive_skill_id:
            self.passives[self.passive_skill_id] = SKILL_DATA.get(self.passive_skill_id, {})
        if character_data.get('passive') == 'backstab':
            self.passives['backstab'] = SKILL_DATA.get('backstab', {})

    def upgrade_active(self):
        """升级主动技能"""
        if self.active_skill_id:
            self.active_level += 1
            return True
        return False

    def upgrade_passive(self):
        """升级被动技能"""
        if self.passive_skill_id:
            self.passive_level += 1
            return True
        return False

    def get_active_data(self):
        """获取主动技能数据（含等级加成）"""
        data = SKILL_DATA.get(self.active_skill_id, {}).copy()
        if self.active_level > 1:
            data['damage'] = data.get('damage', 0) + (self.active_level - 1) * 5
            data['cooldown'] = max(30, data.get('cooldown', 180) - (self.active_level - 1) * 10)
            if 'heal' in data:
                data['heal'] = data['heal'] + (self.active_level - 1) * 5
            if 'arrow_count' in data:
                data['arrow_count'] = data['arrow_count'] + (self.active_level - 1) * 2
            if 'strike_count' in data:
                data['strike_count'] = data['strike_count'] + (self.active_level - 1)
        return data

    def can_use_active(self):
        """是否可以释放主动技能"""
        if not self.active_skill_id:
            return False
        data = SKILL_DATA.get(self.active_skill_id, {})
        if self.cooldown_remaining > 0:
            return False
        if self.player.energy < data.get('energy_cost', 50):
            return False
        return True

    def use_active(self, target_x=None, target_y=None):
        """释放主动技能，返回效果信息"""
        if not self.can_use_active():
            return None

        data = SKILL_DATA[self.active_skill_id]
        self.player.energy -= data.get('energy_cost', 50)
        self.cooldown_remaining = data.get('cooldown', 180)

        skill_id = self.active_skill_id
        result = {
            'type': skill_id,
            'player_x': self.player.x,
            'player_y': self.player.y,
            'target_x': target_x,
            'target_y': target_y,
            'data': data,
        }

        if skill_id == 'shield_bash':
            result['dash'] = self._calc_dash(data)
        elif skill_id == 'arrow_rain':
            result['arrows'] = self._calc_arrow_rain(data)
        elif skill_id == 'thunder_storm':
            result['strikes'] = self._calc_thunder_storm(data)
        elif skill_id == 'shadow_step':
            result['teleport'] = self._calc_shadow_step(data, target_x, target_y)
        elif skill_id == 'holy_light':
            result['heal'] = data.get('heal', 30)
        elif skill_id == 'deploy_turret':
            result['turret'] = True

        return result

    def _calc_dash(self, data):
        """计算盾击冲刺方向"""
        angle = self.player.facing_angle
        dist = data.get('dash_distance', 120)
        return {
            'vx': math.cos(angle) * dist,
            'vy': math.sin(angle) * dist,
            'damage': data.get('damage', 20),
            'stun_duration': data.get('stun_duration', 40),
        }

    def _calc_arrow_rain(self, data):
        """计算箭雨方向"""
        count = data.get('arrow_count', 12)
        arrows = []
        for i in range(count):
            angle = (2 * math.pi / count) * i
            arrows.append({
                'angle': angle,
                'speed': 7,
                'damage': data.get('damage', 8),
                'bullet_type': 'arrow',
            })
        return arrows

    def _calc_thunder_storm(self, data):
        """计算雷暴位置"""
        count = data.get('strike_count', 8)
        radius = data.get('radius', 200)
        strikes = []
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            dist = random.uniform(0, radius)
            sx = self.player.x + math.cos(angle) * dist
            sy = self.player.y + math.sin(angle) * dist
            strikes.append({
                'x': sx,
                'y': sy,
                'damage': data.get('damage', 30),
                'delay': random.randint(0, 30),  # 延迟帧
            })
        return strikes

    def _calc_shadow_step(self, data, target_x, target_y):
        """计算暗影步目标位置"""
        if target_x is None:
            target_x = self.player.x
            target_y = self.player.y
        max_range = data.get('teleport_range', 200)
        dx = target_x - self.player.x
        dy = target_y - self.player.y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > max_range:
            scale = max_range / dist
            dx *= scale
            dy *= scale
        return {
            'target_x': self.player.x + dx,
            'target_y': self.player.y + dy,
            'damage': data.get('damage', 40),
        }

    def update(self):
        """每帧更新"""
        if self.cooldown_remaining > 0:
            self.cooldown_remaining -= 1

        # 被动技能
        self.passive_timer += 1
        if self.passive_skill_id:
            self._update_passive()

    def _update_passive(self):
        """更新被动技能效果"""
        pid = self.passive_skill_id
        data = SKILL_DATA.get(pid, {})

        if pid == 'iron_wall':
            interval = data.get('tick_interval', 600)
            if self.passive_timer % interval == 0:
                self.player.shield = min(50, self.player.shield + data.get('shield_per_tick', 5))

        elif pid == 'mana_flow':
            if self.passive_timer % 60 == 0:
                bonus = int(2 * data.get('energy_regen_bonus', 0.5))
                self.player.energy = min(self.player.max_energy, self.player.energy + 1 + bonus)

        elif pid == 'healing_aura':
            if self.passive_timer % 60 == 0:
                self.player.hp = min(self.player.max_hp, self.player.hp + data.get('heal_per_second', 1))

    def get_cooldown_pct(self):
        """获取冷却进度(0~1)"""
        if not self.active_skill_id:
            return 1.0
        data = SKILL_DATA.get(self.active_skill_id, {})
        total = data.get('cooldown', 180)
        if total == 0:
            return 1.0
        return 1.0 - (self.cooldown_remaining / total)

    def get_crit_chance(self):
        """获取暴击率加成"""
        if self.passive_skill_id == 'eagle_eye':
            data = SKILL_DATA['eagle_eye']
            return data.get('crit_chance_bonus', 0.15)
        return 0.0

    def get_backstab_multiplier(self, enemy_angle, player_angle):
        """计算背刺伤害倍率"""
        if self.passive_skill_id != 'backstab':
            return 1.0
        # 简化：检查玩家是否在敌人背后
        diff = abs((enemy_angle - player_angle + math.pi) % (2 * math.pi) - math.pi)
        if diff < math.radians(45):  # 背后45度内
            data = SKILL_DATA['backstab']
            return data.get('backstab_multiplier', 2.0)
        return 1.0

    def get_bonus_gold(self):
        """获取额外金币奖励"""
        if self.passive_skill_id == 'scrap_collect':
            data = SKILL_DATA['scrap_collect']
            lo, hi = data.get('bonus_gold', (3, 8))
            return random.randint(lo, hi)
        return 0


class Turret:
    """工程师的炮台"""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.damage = 8
        self.fire_rate = 20
        self.fire_timer = 0
        self.duration = 900  # 15秒
        self.alive = True
        self.width = 24
        self.height = 24
        self.angle = 0
        self.hitbox = pygame.Rect(x - 12, y - 12, 24, 24)

    def update(self, enemies, player_bullets):
        """更新炮台，自动瞄准并射击"""
        self.duration -= 1
        if self.duration <= 0:
            self.alive = False
            return

        self.fire_timer -= 1
        if self.fire_timer > 0:
            return

        # 找最近的敌人
        nearest = None
        nearest_dist = float('inf')
        for enemy in enemies:
            if not enemy.alive:
                continue
            dx = enemy.x - self.x
            dy = enemy.y - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < 350 and dist < nearest_dist:
                nearest_dist = dist
                nearest = enemy

        if nearest:
            self.angle = math.atan2(nearest.y - self.y, nearest.x - self.x)
            bullet = Bullet(
                self.x, self.y, self.angle,
                {'bullet_speed': 8, 'damage': self.damage, 'bullet_type': 'normal'},
                source_is_player=True
            )
            player_bullets.append(bullet)
            self.fire_timer = self.fire_rate

    def draw(self, screen, camera):
        sx, sy = camera.apply_point(self.x, self.y)
        import pygame as pg
        pg.draw.rect(screen, (100, 120, 140), (sx - 10, sy - 10, 20, 20))
        pg.draw.rect(screen, (150, 170, 200), (sx - 6, sy - 6, 12, 12))
        # 炮管
        end_x = sx + int(math.cos(self.angle) * 16)
        end_y = sy + int(math.sin(self.angle) * 16)
        pg.draw.line(screen, (200, 200, 200), (sx, sy), (end_x, end_y), 3)
        # 剩余时间指示
        pct = self.duration / 900
        pg.draw.rect(screen, (60, 60, 60), (sx - 12, sy - 16, 24, 3))
        pg.draw.rect(screen, (100, 200, 100), (sx - 12, sy - 16, int(24 * pct), 3))
