"""
宠物系统 - 跟随玩家作战，可升级进化
"""
import math
import random
import pygame
from settings import TILE_SIZE


# ============ 宠物类型 ============
PET_TYPES = {
    'fire_dragon': {
        'name': '火焰幼龙', 'desc': '喷吐火球攻击敌人',
        'max_hp': 80, 'attack': 12, 'speed': 3.0,
        'attack_range': 200, 'attack_cooldown': 40,
        'color': (255, 120, 30), 'bullet_type': 'fire',
        'follow_dist': 80, 'evolve_at': 3, 'evolves_to': 'fire_drake',
    },
    'healing_fairy': {
        'name': '治愈精灵', 'desc': '定期恢复主人生命',
        'max_hp': 40, 'attack': 0, 'speed': 4.0,
        'attack_range': 0, 'attack_cooldown': 0,
        'color': (100, 255, 150), 'bullet_type': 'none',
        'follow_dist': 50, 'evolve_at': 3, 'evolves_to': 'greater_fairy',
        'heal_interval': 120, 'heal_amount': 5,
    },
    'shadow_cat': {
        'name': '暗影猫', 'desc': '高速近战，拾取金币',
        'max_hp': 50, 'attack': 8, 'speed': 5.5,
        'attack_range': 40, 'attack_cooldown': 20,
        'color': (80, 60, 100), 'bullet_type': 'melee',
        'follow_dist': 60, 'evolve_at': 4, 'evolves_to': 'shadow_panther',
        'collect_gold': True,
    },
    'crystal_golem': {
        'name': '水晶魔像', 'desc': '高血量坦克，嘲讽敌人',
        'max_hp': 200, 'attack': 6, 'speed': 2.0,
        'attack_range': 35, 'attack_cooldown': 60,
        'color': (100, 180, 220), 'bullet_type': 'melee',
        'follow_dist': 100, 'evolve_at': 5, 'evolves_to': 'crystal_giant',
    },
}

EVOLVED_TYPES = {
    'fire_drake': {
        'name': '火焰翼龙', 'desc': '更强力的火焰吐息',
        'max_hp': 150, 'attack': 22, 'speed': 3.5,
        'attack_range': 250, 'attack_cooldown': 30,
        'color': (255, 80, 0), 'bullet_type': 'fire',
        'follow_dist': 80,
    },
    'greater_fairy': {
        'name': '大精灵', 'desc': '更强治愈效果',
        'max_hp': 60, 'attack': 5, 'speed': 4.5,
        'attack_range': 150, 'attack_cooldown': 50,
        'color': (150, 255, 200), 'bullet_type': 'energy',
        'follow_dist': 50,
        'heal_interval': 80, 'heal_amount': 10,
    },
    'shadow_panther': {
        'name': '暗影豹', 'desc': '高速收割，自动拾取',
        'max_hp': 90, 'attack': 16, 'speed': 6.0,
        'attack_range': 50, 'attack_cooldown': 15,
        'color': (60, 40, 80), 'bullet_type': 'melee',
        'follow_dist': 60,
        'collect_gold': True,
    },
    'crystal_giant': {
        'name': '水晶巨人', 'desc': '巨型坦克，范围震击',
        'max_hp': 350, 'attack': 15, 'speed': 2.5,
        'attack_range': 80, 'attack_cooldown': 45,
        'color': (80, 160, 200), 'bullet_type': 'melee',
        'follow_dist': 100,
    },
}


class Pet:
    """宠物 - 跟随玩家、作战、升级"""

    def __init__(self, pet_id='fire_dragon', level=1):
        self.pet_id = pet_id
        self.level = level
        self._update_stats()

        self.x = 0
        self.y = 0
        self.width = 20
        self.height = 20
        self.hp = self.max_hp
        self.alive = True
        self.exp = 0
        self.exp_to_next = 50

        # 战斗
        self.attack_timer = 0
        self.last_target = None

        # 移动
        self.vx = 0
        self.vy = 0
        self.bob_phase = random.uniform(0, math.pi * 2)

        # 动画
        self.anim_frame = 0
        self.anim_timer = 0

    def _update_stats(self):
        """根据类型和等级更新属性"""
        # 先检查是否是进化形态
        data = EVOLVED_TYPES.get(self.pet_id) or PET_TYPES.get(self.pet_id, PET_TYPES['fire_dragon'])
        lv_mult = 1 + (self.level - 1) * 0.25
        self.max_hp = int(data['max_hp'] * lv_mult)
        self.attack = int(data['attack'] * lv_mult) if data['attack'] > 0 else 0
        self.speed = data['speed']
        self.attack_range = data.get('attack_range', 80)
        self.attack_cooldown = data.get('attack_cooldown', 40)
        self.color = data['color']
        self.bullet_type = data.get('bullet_type', 'normal')
        self.follow_dist = data.get('follow_dist', 60)
        self.heal_interval = data.get('heal_interval', 0)
        self.heal_amount = data.get('heal_amount', 0)
        self.collect_gold = data.get('collect_gold', False)
        self.pet_name = data['name']

    def add_exp(self, amount):
        """获得经验，返回是否升级"""
        self.exp += amount
        if self.exp >= self.exp_to_next:
            self.exp -= self.exp_to_next
            self.level += 1
            self.exp_to_next = int(self.exp_to_next * 1.4)
            self._update_stats()
            self.hp = min(self.hp + 10, self.max_hp)
            return True
        return False

    def check_evolve(self):
        """检查是否满足进化条件，返回进化后的ID或None"""
        base_data = PET_TYPES.get(self.pet_id)
        if base_data and 'evolves_to' in base_data:
            need_lv = base_data['evolve_at']
            if self.level >= need_lv:
                evolved_id = base_data['evolves_to']
                self.pet_id = evolved_id
                self._update_stats()
                return evolved_id
        return None

    def update(self, player, world, enemies):
        """更新宠物AI"""
        if not self.alive:
            return None

        self.bob_phase += 0.08
        self.anim_timer += 1
        if self.anim_timer > 12:
            self.anim_timer = 0
            self.anim_frame = (self.anim_frame + 1) % 4

        # 计时器
        if self.attack_timer > 0:
            self.attack_timer -= 1

        # 跟随玩家
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        action_result = None

        # 治疗型宠物
        if self.heal_interval > 0 and self.attack_timer <= -self.heal_interval + self.attack_cooldown:
            if self.attack_timer <= -self.heal_interval:
                self.attack_timer = 0  # 重置以使用治疗

        if self.heal_interval > 0 and self.attack_timer == 0:
            if player.hp < player.max_hp:
                player.hp = min(player.max_hp, player.hp + self.heal_amount)
                self.attack_timer = self.heal_interval
                action_result = ('heal', self.heal_amount)

        # 攻击型宠物 - 找最近敌人
        if self.attack > 0 and self.attack_timer <= 0 and enemies:
            nearest = None
            nearest_dist = self.attack_range
            for enemy in enemies:
                if not enemy.alive:
                    continue
                ed = math.hypot(enemy.x - self.x, enemy.y - self.y)
                if ed < nearest_dist:
                    nearest_dist = ed
                    nearest = enemy

            if nearest:
                self.last_target = nearest
                self.attack_timer = self.attack_cooldown
                if self.bullet_type == 'fire':
                    from src.entities.bullet import Bullet
                    angle = math.atan2(nearest.y - self.y, nearest.x - self.x)
                    b = Bullet(self.x, self.y, angle,
                               {'bullet_speed': 6, 'damage': self.attack, 'bullet_type': 'fire', 'burn_effect': True},
                               source_is_player=True)
                    action_result = ('bullet', b)
                elif self.bullet_type != 'none':
                    from src.entities.bullet import Bullet
                    angle = math.atan2(nearest.y - self.y, nearest.x - self.x)
                    b = Bullet(self.x, self.y, angle,
                               {'bullet_speed': 7, 'damage': self.attack, 'bullet_type': 'normal'},
                               source_is_player=True)
                    action_result = ('bullet', b)
                else:
                    action_result = ('melee', nearest)

        # 拾取金币
        if self.collect_gold and hasattr(player, 'gold'):
            if hasattr(world, 'items'):
                for item in world.items:
                    if hasattr(item, 'item_type') and item.item_type == 'gold':
                        d = math.hypot(item.x - self.x, item.y - self.y)
                        if d < 60:
                            player.gold += item.amount if hasattr(item, 'amount') else 5
                            item.alive = False

        # 移动逻辑
        if dist > self.follow_dist:
            if dist > 0:
                speed = min(self.speed, dist * 0.05)
                target_x = player.x - math.cos(self.bob_phase) * self.follow_dist * 0.3
                target_y = player.y - math.sin(self.bob_phase * 0.7) * self.follow_dist * 0.3
                dx2 = target_x - self.x
                dy2 = target_y - self.y
                d2 = math.sqrt(dx2 * dx2 + dy2 * dy2)
                if d2 > 0:
                    self.vx = (dx2 / d2) * speed
                    self.vy = (dy2 / d2) * speed
                    self.x += self.vx
                    self.y += self.vy
        else:
            # 在跟随距离内，小幅度环绕
            self.vx *= 0.9
            self.vy *= 0.9
            self.x += math.cos(self.bob_phase * 0.5) * 0.3
            self.y += math.sin(self.bob_phase * 0.5) * 0.3

        # 墙壁碰撞
        pet_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        if world and hasattr(world, 'check_wall_collision') and world.check_wall_collision(pet_rect):
            self.x -= self.vx * 0.5
            self.y -= self.vy * 0.5

        # 边界
        if world:
            self.x = max(10, min(self.x, world.pixel_width - self.width - 10))
            self.y = max(10, min(self.y, world.pixel_height - self.height - 10))

        return action_result

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
        return not self.alive

    def draw(self, screen, camera):
        """绘制宠物"""
        if not self.alive:
            return
        sx, sy = camera.apply_point(self.x, self.y)
        sy += int(3 * math.sin(self.bob_phase))

        # 身体
        size = self.width
        body_color = self.color
        # 外围光晕
        glow = pygame.Surface((size + 8, size + 8), pygame.SRCALPHA)
        glow_alpha = int(60 + 30 * math.sin(self.bob_phase * 2))
        pygame.draw.circle(glow, (*body_color, glow_alpha), (size // 2 + 4, size // 2 + 4), size // 2 + 2)
        screen.blit(glow, (sx - 4, sy - 4))

        # 身体
        pygame.draw.circle(screen, body_color, (int(sx + size // 2), int(sy + size // 2)), size // 2)
        # 眼睛
        eye_color = (255, 255, 255) if 'shadow' not in self.pet_id else (255, 200, 50)
        ex1 = sx + size // 2 - 4
        ey1 = sy + size // 2 - 3
        ex2 = sx + size // 2 + 4
        pygame.draw.circle(screen, eye_color, (int(ex1), int(ey1)), 3)
        pygame.draw.circle(screen, eye_color, (int(ex2), int(ey1)), 3)
        pygame.draw.circle(screen, (0, 0, 0), (int(ex1), int(ey1)), 1)
        pygame.draw.circle(screen, (0, 0, 0), (int(ex2), int(ey1)), 1)

        # 名字
        try:
            from src.engine.font_helper import get_chinese_font
            font = get_chinese_font(10)
            name_surf = font.render(self.pet_name, True, self.color)
            screen.blit(name_surf, (sx + size // 2 - name_surf.get_width() // 2, sy - 10))
        except:
            pass

        # 等级
        lv_text = f'Lv.{self.level}'
        lv_surf = pygame.font.Font(None, 11).render(lv_text, True, (200, 200, 200))
        screen.blit(lv_surf, (sx + size // 2 - lv_surf.get_width() // 2, sy + size - 2))
