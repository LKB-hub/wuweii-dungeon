"""
敌人系统 - AI 行为、寻路、攻击
"""
import math
import random
import pygame
from settings import TILE_SIZE
from src.entities.character import ENEMY_TYPES, BOSS_TYPES
from src.entities.bullet import Bullet
from src.engine.resource import get_resources


class Enemy:
    """敌人基类"""

    def __init__(self, x, y, enemy_type='soldier', is_boss=False):
        data = BOSS_TYPES.get(enemy_type) if is_boss else ENEMY_TYPES.get(enemy_type, ENEMY_TYPES['soldier'])
        self.enemy_type = enemy_type
        self.is_boss = is_boss

        self.x = x
        self.y = y
        size = TILE_SIZE * data.get('size_mult', 1.0)
        self.width = int(size)
        self.height = int(size)
        self.vx = 0
        self.vy = 0

        # 属性
        self.max_hp = data.get('hp', 30)
        self.hp = self.max_hp
        self.speed = data.get('speed', 2.0)
        self.damage = data.get('damage', 10)
        self.attack_range = data.get('attack_range', 40)
        self.attack_cooldown = data.get('attack_cooldown', 45)
        self.ai_type = data.get('ai', 'chase')
        self.score = data.get('score', 50)
        self.color = data.get('color', (180, 40, 40))
        self.explodes = data.get('explodes', False)
        # 从数据中复制更多特有属性
        self.bullet_type = data.get('bullet_type', 'normal')
        self.summons_minions = data.get('summons_minions', False)
        self.block_front = data.get('block_front', False)
        self.dash_attack = data.get('dash_attack', False)
        self.charge_attack = data.get('charge_attack', False)
        self.disguised = data.get('disguised', False)
        self.phasing = data.get('phasing', False)
        self.steals_gold = data.get('steals_gold', False)
        self.burn_effect = data.get('burn_effect', False)
        self.slow_effect = data.get('slow_effect', False)
        self.burst_fire = data.get('burst_fire', 0)
        self.boss_phases = data.get('phases', [])

        # 状态
        self.alive = True
        self.attack_timer = random.randint(0, self.attack_cooldown)
        self.stun_timer = 0
        self.slow_timer = 0
        self.burn_timer = 0
        self.burn_damage_timer = 0

        # 寻路
        self.patrol_angle = random.uniform(0, math.pi * 2)
        self.patrol_timer = random.randint(60, 180)

        # 碰撞体
        self.hitbox = pygame.Rect(x, y, self.width, self.height)

        # 精灵
        self.sprites = get_resources().get_enemy_frames(enemy_type)
        self.current_frame = 0
        self.anim_timer = 0

        # 受伤闪烁
        self.flash_timer = 0

        # 精英属性
        self.is_elite = False

        # AI 行为状态
        self.ai_state = 'idle'
        self.ai_state_timer = 0
        self.aggro_range = self.attack_range * 3
        self.last_known_player_pos = None
        self.patrol_waypoints = []
        self.current_waypoint = 0

    def apply_status(self, status_type, duration=60, damage=0):
        """施加状态效果"""
        if status_type == 'burn':
            self.burn_timer = max(self.burn_timer, duration)
            self.burn_damage_timer = 30
        elif status_type == 'slow':
            self.slow_timer = max(self.slow_timer, duration)
        elif status_type == 'stun':
            self.stun_timer = max(self.stun_timer, duration)
        elif status_type == 'freeze':
            self.stun_timer = max(self.stun_timer, duration * 2)
            self.slow_timer = max(self.slow_timer, duration)

    def is_status_immune(self, status_type):
        """检查状态免疫"""
        return self.is_boss and status_type in ('stun', 'freeze')

    def get_ai_state_name(self):
        """获取AI状态名"""
        states = {
            'idle': '待机', 'patrol': '巡逻', 'chase': '追击',
            'attack': '攻击', 'flee': '逃跑', 'guard': '防守',
        }
        return states.get(self.ai_state, '未知')

    def set_ai_state(self, state, duration=60):
        """设置AI状态"""
        self.ai_state = state
        self.ai_state_timer = duration

    def update(self, player, world):
        """AI 更新"""
        if not self.alive:
            return

        # 计时器
        if self.attack_timer > 0:
            self.attack_timer -= 1
        if self.stun_timer > 0:
            self.stun_timer -= 1
        if self.slow_timer > 0:
            self.slow_timer -= 1
        if self.burn_timer > 0:
            self.burn_timer -= 1
            self.burn_damage_timer -= 1
            if self.burn_damage_timer <= 0:
                self.take_damage(3)
                self.burn_damage_timer = 30
        if self.flash_timer > 0:
            self.flash_timer -= 1

        # 动画
        self.anim_timer += 1
        if self.anim_timer > 20:
            self.anim_timer = 0
            self.current_frame = (self.current_frame + 1) % 4

        # 被眩晕时不行动
        if self.stun_timer > 0:
            return

        # 计算与玩家的距离
        dx_p = player.x - self.x
        dy_p = player.y - self.y
        dist = math.sqrt(dx_p * dx_p + dy_p * dy_p)
        self.vx = 0
        self.vy = 0

        effective_speed = self.speed * 0.4 if self.slow_timer > 0 else self.speed

        # AI 行为
        if self.ai_type == 'chase':
            self._ai_chase(player, dist, dx_p, dy_p, effective_speed, world)
        elif self.ai_type == 'keep_distance':
            self._ai_keep_distance(player, dist, dx_p, dy_p, effective_speed, world)
        elif self.ai_type == 'shield_wall':
            self._ai_shield_wall(player, dist, dx_p, dy_p, effective_speed, world)
        elif self.ai_type == 'flank':
            self._ai_flank(player, dist, dx_p, dy_p, effective_speed, world)
        elif self.ai_type == 'flee':
            self._ai_flee(player, dist, dx_p, dy_p, effective_speed, world)
        elif self.ai_type == 'turret':
            self._ai_turret(player, dist, dx_p, dy_p, effective_speed, world)
        elif self.ai_type == 'ambush':
            self._ai_ambush(player, dist, dx_p, dy_p, effective_speed, world)
        elif self.ai_type == 'phase':
            self._ai_phase(player, dist, dx_p, dy_p, effective_speed, world)
        elif self.ai_type == 'hit_and_run':
            self._ai_hit_and_run(player, dist, dx_p, dy_p, effective_speed, world)
        elif self.ai_type == 'boss_chase':
            self._ai_boss(player, dist, dx_p, dy_p, effective_speed, world)
        elif self.ai_type == 'boss_ranged':
            self._ai_boss_ranged(player, dist, dx_p, dy_p, effective_speed, world)
        elif self.ai_type == 'boss_dragon':
            self._ai_boss_dragon(player, dist, dx_p, dy_p, effective_speed, world)
        elif self.ai_type == 'boss_turret':
            self._ai_boss_turret(player, dist, dx_p, dy_p, effective_speed, world)

        # 移动碰撞
        self._move_with_collision(world, effective_speed)

        # 碰触伤害（近战型）
        if self.ai_type == 'chase' and dist < self.attack_range:
            player.take_damage(self.damage)

        # 边界
        self.x = max(10, min(self.x, world.pixel_width - self.width - 10))
        self.y = max(10, min(self.y, world.pixel_height - self.height - 10))
        self.hitbox.x = self.x
        self.hitbox.y = self.y

    def _ai_chase(self, player, dist, dx, dy, speed, world):
        """追踪AI：直接冲向玩家"""
        if dist > 0:
            self.vx = (dx / dist) * speed
            self.vy = (dy / dist) * speed

    def _ai_keep_distance(self, player, dist, dx, dy, speed, world):
        """保持距离AI：与玩家保持攻击距离"""
        ideal_dist = self.attack_range * 0.7
        if dist < ideal_dist * 0.6:
            if dist > 0:
                self.vx = -(dx / dist) * speed
                self.vy = -(dy / dist) * speed
        elif dist > self.attack_range * 1.2:
            if dist > 0:
                self.vx = (dx / dist) * speed
                self.vy = (dy / dist) * speed
        # 在范围内时横向移动
        else:
            self.patrol_timer -= 1
            if self.patrol_timer <= 0:
                self.patrol_angle = random.uniform(0, math.pi * 2)
                self.patrol_timer = random.randint(60, 120)
            self.vx = math.cos(self.patrol_angle) * speed * 0.5
            self.vy = math.sin(self.patrol_angle) * speed * 0.5

    def _ai_boss(self, player, dist, dx, dy, speed, world):
        """Boss AI：追踪 + 偶尔冲刺"""
        if dist > 0:
            self.vx = (dx / dist) * speed
            self.vy = (dy / dist) * speed
            if self.hp < self.max_hp * 0.5 and random.random() < 0.02:
                self.vx *= 3
                self.vy *= 3

    def _ai_shield_wall(self, player, dist, dx, dy, speed, world):
        """盾墙AI：缓慢推进，正面格挡"""
        if dist > 0:
            self.vx = (dx / dist) * speed * 0.6
            self.vy = (dy / dist) * speed * 0.6
        angle_to_player = math.atan2(-dy, -dx) if dist > 0 else 0
        diff = abs((angle_to_player + math.pi) % (2 * math.pi) - math.pi)
        self._blocking = diff < math.radians(60)

    def _ai_flank(self, player, dist, dx, dy, speed, world):
        """侧翼AI：绕到玩家侧面或背后攻击"""
        if not hasattr(self, 'flank_timer'):
            self.flank_timer = random.randint(60, 120)
            self.flank_direction = random.choice([-1, 1])
        self.flank_timer -= 1
        if self.flank_timer <= 0:
            self.flank_timer = random.randint(60, 120)
            self.flank_direction *= -1
        if dist > 0:
            angle = math.atan2(dy, dx)
            perp_angle = angle + (math.pi / 2) * self.flank_direction
            self.vx = math.cos(perp_angle) * speed
            self.vy = math.sin(perp_angle) * speed
            if dist > 150:
                self.vx += (dx / dist) * speed * 0.5
                self.vy += (dy / dist) * speed * 0.5

    def _ai_flee(self, player, dist, dx, dy, speed, world):
        """逃跑AI：远离玩家，偶尔召唤"""
        if dist < 300 and dist > 0:
            self.vx = -(dx / dist) * speed * 1.3
            self.vy = -(dy / dist) * speed * 1.3
        else:
            self.patrol_timer -= 1
            if self.patrol_timer <= 0:
                self.patrol_angle = random.uniform(0, math.pi * 2)
                self.patrol_timer = random.randint(60, 120)
            self.vx = math.cos(self.patrol_angle) * speed * 0.3
            self.vy = math.sin(self.patrol_angle) * speed * 0.3
        if dist > 250 and self.summons_minions:
            if not hasattr(self, 'summon_timer'):
                self.summon_timer = 180
            self.summon_timer -= 1
            if self.summon_timer <= 0:
                self.summon_timer = 200
                self._trying_to_summon = True

    def _ai_turret(self, player, dist, dx, dy, speed, world):
        """炮台AI：不动，高速射击"""
        self.vx = 0
        self.vy = 0

    def _ai_ambush(self, player, dist, dx, dy, speed, world):
        """伏击AI：静止伪装直到玩家靠近"""
        if not hasattr(self, 'revealed'):
            self.revealed = False
            self.disguised_timer = 0
        if not self.revealed:
            self.disguised_timer += 1
            if dist < 80 or self.disguised_timer > 300:
                self.revealed = True
            self.vx = 0
            self.vy = 0
        else:
            if dist > 0:
                self.vx = (dx / dist) * speed * 1.5
                self.vy = (dy / dist) * speed * 1.5

    def _ai_phase(self, player, dist, dx, dy, speed, world):
        """相位AI：间歇性隐身"""
        if not hasattr(self, 'phase_timer'):
            self.phase_timer = random.randint(40, 100)
            self.is_phased = False
        self.phase_timer -= 1
        if self.phase_timer <= 0:
            self.is_phased = not self.is_phased
            self.phase_timer = random.randint(40, 100) if self.is_phased else random.randint(80, 160)
        if self.is_phased:
            if dist > 0:
                self.vx = (dx / dist) * speed * 0.8
                self.vy = (dy / dist) * speed * 0.8
        else:
            if dist > 0:
                self.vx = (dx / dist) * speed * 1.2
                self.vy = (dy / dist) * speed * 1.2

    def _ai_hit_and_run(self, player, dist, dx, dy, speed, world):
        """打了就跑AI：快速接近攻击后逃跑"""
        if not hasattr(self, 'run_state'):
            self.run_state = 'approach'
            self.state_timer = random.randint(30, 60)
        self.state_timer -= 1
        if self.state_timer <= 0:
            if self.run_state == 'approach':
                self.run_state = 'retreat'
                self.state_timer = random.randint(20, 45)
            else:
                self.run_state = 'approach'
                self.state_timer = random.randint(40, 70)
        if self.run_state == 'approach':
            if dist > 0:
                self.vx = (dx / dist) * speed * 1.5
                self.vy = (dy / dist) * speed * 1.5
        else:
            if dist > 0:
                self.vx = -(dx / dist) * speed * 1.2
                self.vy = -(dy / dist) * speed * 1.2

    def _ai_boss_ranged(self, player, dist, dx, dy, speed, world):
        """远程Boss AI：保持距离、瞬移、多阶段"""
        if not hasattr(self, 'boss_phase'):
            self.boss_phase = 0
            self.phase_timer = 300
            self.teleport_cooldown = 100
        self.phase_timer -= 1
        self.teleport_cooldown -= 1
        hp_pct = self.hp / self.max_hp
        if hp_pct < 0.3:
            self.boss_phase = 2
        elif hp_pct < 0.6:
            self.boss_phase = 1
        ideal = self.attack_range * 0.7
        if dist < ideal * 0.5 and dist > 0:
            self.vx = -(dx / dist) * speed
            self.vy = -(dy / dist) * speed
        elif dist > ideal * 1.3 and dist > 0:
            self.vx = (dx / dist) * speed
            self.vy = (dy / dist) * speed
        else:
            self.patrol_timer -= 1
            if self.patrol_timer <= 0:
                self.patrol_angle = random.uniform(0, math.pi * 2)
                self.patrol_timer = random.randint(40, 80)
            self.vx = math.cos(self.patrol_angle) * speed * 0.5
            self.vy = math.sin(self.patrol_angle) * speed * 0.5
        if self.teleport_cooldown <= 0 and dist < 150:
            self._do_teleport(player, world)
            self.teleport_cooldown = 80 if self.boss_phase < 2 else 50

    def _do_teleport(self, player, world):
        """Boss瞬移到玩家远处"""
        for _ in range(20):
            angle = random.uniform(0, math.pi * 2)
            d = random.uniform(200, 350)
            tx = player.x + math.cos(angle) * d
            ty = player.y + math.sin(angle) * d
            test = pygame.Rect(tx, ty, self.width, self.height)
            if not world.check_wall_collision(test):
                self.x = tx
                self.y = ty
                self.hitbox.x = self.x
                self.hitbox.y = self.y
                return

    def _ai_boss_dragon(self, player, dist, dx, dy, speed, world):
        """龙Boss AI：盘旋、俯冲、甩尾"""
        if not hasattr(self, 'dragon_phase'):
            self.dragon_phase = 'circle'
            self.dragon_timer = 180
            self.dragon_angle = 0
        self.dragon_timer -= 1
        hp_pct = self.hp / self.max_hp
        if self.dragon_timer <= 0:
            choices = ['circle']
            if hp_pct < 0.7:
                choices.append('dive')
            if hp_pct < 0.4:
                choices.append('sweep')
            self.dragon_phase = random.choice(choices)
            self.dragon_timer = 120 if self.dragon_phase == 'dive' else 200
        if self.dragon_phase == 'circle':
            self.dragon_angle += 0.02
            orbit_r = 180
            self.x = player.x + math.cos(self.dragon_angle) * orbit_r - self.width / 2
            self.y = player.y + math.sin(self.dragon_angle) * orbit_r - self.height / 2
        elif self.dragon_phase == 'dive':
            if dist > 0:
                self.vx = (dx / dist) * speed * 4
                self.vy = (dy / dist) * speed * 4
        elif self.dragon_phase == 'sweep':
            if dist > 0:
                self.vx = (dx / dist) * speed * 2
                self.vy = (dy / dist) * speed * 2

    def _ai_boss_turret(self, player, dist, dx, dy, speed, world):
        """机甲Boss AI：炮台模式切换"""
        if not hasattr(self, 'weapon_mode'):
            self.weapon_mode = 'machine_gun'
            self.mode_timer = 240
        self.mode_timer -= 1
        if self.mode_timer <= 0:
            modes = ['machine_gun', 'missiles', 'laser']
            self.weapon_mode = random.choice(modes)
            self.mode_timer = 180
        if dist > 0:
            if self.weapon_mode == 'machine_gun':
                self.vx = (dx / dist) * speed * 0.3
                self.vy = (dy / dist) * speed * 0.3
            elif self.weapon_mode == 'missiles':
                self.vx = -(dx / dist) * speed * 0.5
                self.vy = -(dy / dist) * speed * 0.5
            else:
                self.vx = 0
                self.vy = 0

    def _move_with_collision(self, world, speed):
        new_x = self.x + self.vx
        test = pygame.Rect(new_x, self.y, self.width, self.height)
        if not world.check_wall_collision(test):
            self.x = new_x
        else:
            self.vx = 0

        new_y = self.y + self.vy
        test = pygame.Rect(self.x, new_y, self.width, self.height)
        if not world.check_wall_collision(test):
            self.y = new_y
        else:
            self.vy = 0

    def try_attack(self):
        """尝试远程攻击，返回子弹列表（瞄准玩家方向）"""
        if self.attack_timer > 0:
            return []

        # 计算瞄准玩家的角度
        tx = getattr(self, '_target_x', self.x + 100)
        ty = getattr(self, '_target_y', self.y)
        base_angle = math.atan2(ty - self.y, tx - self.x)

        bullets = []
        if self.bullet_type == 'normal':
            b = Bullet(self.x, self.y, base_angle,
                       {'bullet_speed': 5, 'damage': self.damage, 'bullet_type': 'normal'},
                       source_is_player=False)
            bullets.append(b)
        elif self.bullet_type == 'spread':
            for i in range(3):
                angle_offset = (i - 1) * 0.3
                b = Bullet(self.x, self.y, base_angle + angle_offset,
                           {'bullet_speed': 4, 'damage': self.damage // 2, 'bullet_type': 'normal'},
                           source_is_player=False)
                bullets.append(b)
        elif self.bullet_type == 'fire':
            b = Bullet(self.x, self.y, base_angle,
                       {'bullet_speed': 4, 'damage': self.damage, 'bullet_type': 'fire', 'burn_effect': True},
                       source_is_player=False)
            bullets.append(b)
        elif self.bullet_type == 'ice':
            b = Bullet(self.x, self.y, base_angle,
                       {'bullet_speed': 3, 'damage': self.damage, 'bullet_type': 'ice', 'slow_effect': True},
                       source_is_player=False)
            bullets.append(b)
        elif self.bullet_type == 'lightning':
            b = Bullet(self.x, self.y, base_angle,
                       {'bullet_speed': 8, 'damage': self.damage * 2, 'bullet_type': 'lightning'},
                       source_is_player=False)
            bullets.append(b)
        elif self.bullet_type == 'homing':
            b = Bullet(self.x, self.y, base_angle,
                       {'bullet_speed': 3, 'damage': self.damage, 'bullet_type': 'homing', 'homing': True},
                       source_is_player=False)
            if hasattr(self, '_target_x'):
                b.set_target(tx, ty)
            bullets.append(b)
        elif self.bullet_type == 'burst':
            for i in range(5):
                angle = base_angle + (i - 2) * 0.25
                b = Bullet(self.x, self.y, angle,
                           {'bullet_speed': 4, 'damage': self.damage // 3, 'bullet_type': 'normal'},
                           source_is_player=False)
                bullets.append(b)

        self.attack_timer = self.attack_cooldown
        return bullets

    def perform_special_attack(self, player):
        """特殊攻击（Boss和精英用），均以玩家为中心"""
        bullets = []
        cx, cy = self.x, self.y
        base_angle = math.atan2(player.y - cy, player.x - cx) if player else 0

        if self.enemy_type == 'boss_mage':
            for i in range(12):
                angle = base_angle + (math.pi * 2 * i) / 12
                b = Bullet(cx, cy, angle,
                           {'bullet_speed': 3, 'damage': self.damage // 2, 'bullet_type': 'energy'},
                           source_is_player=False)
                bullets.append(b)
        elif self.enemy_type == 'boss_dragon':
            for i in range(7):
                angle = base_angle + (i - 3) * 0.2
                b = Bullet(cx, cy, angle,
                           {'bullet_speed': 4, 'damage': self.damage, 'bullet_type': 'fire', 'burn_effect': True},
                           source_is_player=False)
                bullets.append(b)
        elif self.enemy_type == 'boss_knight':
            dx = player.x - cx
            dy = player.y - cy
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 0:
                self.vx = (dx / dist) * self.speed * 5
                self.vy = (dy / dist) * self.speed * 5
                self.stun_timer = 10
        elif self.enemy_type == 'summoner':
            pass
        elif self.enemy_type == 'fire_mage':
            b = Bullet(cx, cy, base_angle,
                       {'bullet_speed': 2, 'damage': self.damage * 2, 'bullet_type': 'homing',
                        'homing': True, 'burn_effect': True},
                       source_is_player=False)
            if player:
                b.set_target(player.x, player.y)
            bullets.append(b)
        elif self.enemy_type == 'ice_witch':
            for i in range(5):
                angle = base_angle + (i - 2) * 0.35
                b = Bullet(cx, cy, angle,
                           {'bullet_speed': 3, 'damage': self.damage, 'bullet_type': 'ice', 'slow_effect': True},
                           source_is_player=False)
                bullets.append(b)
        elif self.enemy_type == 'necromancer':
            for i in range(8):
                angle = random.uniform(0, math.pi * 2)
                b = Bullet(cx, cy, angle,
                           {'bullet_speed': 2, 'damage': self.damage // 2, 'bullet_type': 'dark'},
                           source_is_player=False)
                bullets.append(b)
        elif self.enemy_type == 'heavy_gunner':
            b = Bullet(self.x, self.y, 0,
                       {'bullet_speed': 3, 'damage': self.damage * 3, 'bullet_type': 'rocket', 'explosive': True},
                       source_is_player=False)
            bullets.append(b)

        return bullets

    def get_drop_table(self):
        """获取掉落表"""
        if self.is_boss:
            return {'gold': (50, 150), 'exp': (100, 200), 'weapon_chance': 0.5}
        elif self.is_elite:
            return {'gold': (20, 60), 'exp': (40, 80), 'weapon_chance': 0.15}
        else:
            return {'gold': (3, 15), 'exp': (10, 30), 'weapon_chance': 0.03}

    def attempt_attack(self, player):
        """记录目标后尝试攻击"""
        self._target_x = player.x
        self._target_y = player.y
        return self.try_attack()

    def take_damage(self, amount):
        """受到伤害"""
        if not self.alive:
            return False
        self.hp -= amount
        self.flash_timer = 6
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            return True
        return True

    def apply_effect(self, effect_type):
        """应用状态效果"""
        if effect_type == 'slow':
            self.slow_timer = 60
        elif effect_type == 'burn':
            self.burn_timer = 90
            self.burn_damage_timer = 30
        elif effect_type == 'stun':
            self.stun_timer = 20

    def draw(self, screen, camera):
        """绘制敌人"""
        if not self.alive:
            return
        sx, sy = camera.apply_point(self.x, self.y)

        # 闪烁
        if self.flash_timer > 0 and self.flash_timer % 2 == 0:
            color_override = (255, 255, 255)
            r = pygame.Rect(sx, sy, self.width, self.height)
            pygame.draw.rect(screen, color_override, r)
            return

        if self.sprites and 0 <= self.current_frame < len(self.sprites):
            sprite = self.sprites[self.current_frame]
            if sprite:
                if self.is_boss:
                    scaled = pygame.transform.scale(sprite, (self.width, self.height))
                    screen.blit(scaled, (sx, sy))
                else:
                    screen.blit(sprite, (sx, sy))
        else:
            pygame.draw.rect(screen, self.color, (sx, sy, self.width, self.height))

        # 生命值条
        bar_w = self.width
        bar_h = 3
        bar_y = sy - 6
        pygame.draw.rect(screen, (60, 60, 60), (sx, bar_y, bar_w, bar_h))
        hp_pct = self.hp / self.max_hp
        pygame.draw.rect(screen, (200, 50, 50), (sx, bar_y, int(bar_w * hp_pct), bar_h))

        # Boss 特殊标记
        if self.is_boss:
            pygame.draw.rect(screen, (255, 200, 0), (sx - 2, bar_y - 1, bar_w + 4, bar_h + 2), 1)

        # 减速效果
        if self.slow_timer > 0:
            pygame.draw.circle(screen, (150, 220, 255), (int(sx + self.width // 2), int(sy + self.height // 2)),
                               self.width // 2 + 2, 1)

        # 燃烧效果
        if self.burn_timer > 0:
            for _ in range(3):
                fx = sx + random.randint(0, self.width)
                fy = sy + random.randint(0, self.height)
                pygame.draw.circle(screen, (255, 100, 20), (int(fx), int(fy)), 3)


def spawn_enemy_for_room(room, difficulty=1):
    """为一个房间生成敌人 - 根据难度选择敌人池"""
    enemies = []
    cx, cy = room.center()
    w, h = room.width, room.height

    num_enemies = max(1, min(difficulty + random.randint(1, 3), 8))

    # 按难度分级敌人池
    low_tier = ['soldier', 'goblin']
    mid_tier = ['archer', 'mage_enemy', 'bomber', 'assassin_enemy', 'ghost']
    high_tier = ['shield_guard', 'fire_mage', 'ice_witch', 'summoner', 'heavy_gunner']
    elite_tier = ['necromancer', 'elite_knight', 'mimic']

    enemy_pool = low_tier[:]
    if difficulty >= 2:
        enemy_pool.extend(mid_tier)
    if difficulty >= 3:
        enemy_pool.extend(high_tier)
    if difficulty >= 4:
        enemy_pool.extend(elite_tier)
        # 更高难度减少敌人数量但更强
        num_enemies = max(2, num_enemies - 1)

    # 可能生成阵型编队
    if num_enemies >= 3 and random.random() < 0.3:
        formation = _create_formation(cx, cy, enemy_pool, num_enemies, w, h, difficulty)
        return formation

    for _ in range(num_enemies):
        ex = cx + random.randint(-int(w * TILE_SIZE // 3), int(w * TILE_SIZE // 3))
        ey = cy + random.randint(-int(h * TILE_SIZE // 3), int(h * TILE_SIZE // 3))
        etype = random.choice(enemy_pool)
        enemy = Enemy(ex, ey, etype)
        _apply_difficulty_scaling(enemy, difficulty)
        enemies.append(enemy)

    return enemies


def _create_formation(cx, cy, enemy_pool, count, room_w, room_h, difficulty):
    """创建敌人阵型编队"""
    enemies = []
    formation_type = random.choice(['v_shape', 'line', 'circle', 'square'])

    if formation_type == 'v_shape':
        for i in range(count):
            offset_x = (i - count // 2) * 40
            offset_y = abs(i - count // 2) * 30
            ex = cx + offset_x
            ey = cy + offset_y - 30
            etype = random.choice(enemy_pool)
            enemy = Enemy(ex, ey, etype)
            _apply_difficulty_scaling(enemy, difficulty)
            enemies.append(enemy)

    elif formation_type == 'line':
        for i in range(count):
            offset_x = (i - count // 2) * 50
            ex = cx + offset_x
            ey = cy
            etype = random.choice(enemy_pool)
            enemy = Enemy(ex, ey, etype)
            _apply_difficulty_scaling(enemy, difficulty)
            enemies.append(enemy)

    elif formation_type == 'circle':
        for i in range(count):
            angle = (2 * math.pi / count) * i
            r = 60
            ex = cx + math.cos(angle) * r
            ey = cy + math.sin(angle) * r
            etype = 'shield_guard' if i == 0 else random.choice(enemy_pool)
            enemy = Enemy(ex, ey, etype)
            _apply_difficulty_scaling(enemy, difficulty)
            enemies.append(enemy)

    elif formation_type == 'square':
        side = int(count ** 0.5) + 1
        for i in range(count):
            row = i // side
            col = i % side
            offset_x = (col - side // 2) * 50
            offset_y = (row - side // 2) * 45
            ex = cx + offset_x
            ey = cy + offset_y
            etype = random.choice(enemy_pool)
            enemy = Enemy(ex, ey, etype)
            _apply_difficulty_scaling(enemy, difficulty)
            enemies.append(enemy)

    return enemies


def _apply_difficulty_scaling(enemy, difficulty):
    """根据难度缩放敌人属性"""
    mult = 0.8 + difficulty * 0.2
    enemy.max_hp = int(enemy.max_hp * mult)
    enemy.hp = enemy.max_hp
    enemy.damage = max(1, int(enemy.damage * (0.9 + difficulty * 0.1)))
    if difficulty >= 4:
        enemy.speed *= 1.1
    if difficulty >= 5:
        enemy.speed *= 1.15
        enemy.attack_cooldown = max(10, int(enemy.attack_cooldown * 0.8))


def spawn_boss(room, boss_type=None):
    """为 Boss 房间生成 Boss - 根据楼层随机选择"""
    cx, cy = room.center()
    if boss_type is None:
        boss_type = random.choice(['boss_knight', 'boss_mage', 'boss_dragon', 'boss_mech'])
    boss = Enemy(cx, cy, boss_type, is_boss=True)
    return boss


def spawn_minions(boss, difficulty):
    """Boss召唤的小兵"""
    minions = []
    count = random.randint(2, 3 + difficulty)
    minion_types = ['soldier', 'archer', 'goblin']
    if difficulty >= 3:
        minion_types.append('bomber')
    for _ in range(count):
        angle = random.uniform(0, math.pi * 2)
        dist = random.uniform(60, 120)
        mx = boss.x + math.cos(angle) * dist
        my = boss.y + math.sin(angle) * dist
        mtype = random.choice(minion_types)
        minion = Enemy(mx, my, mtype)
        minion.max_hp = int(minion.max_hp * 0.6)
        minion.hp = minion.max_hp
        minions.append(minion)
    return minions


def spawn_elite(room, elite_type='elite_knight', difficulty=1):
    """生成精英敌人（小Boss）"""
    cx, cy = room.center()
    enemy = Enemy(cx, cy, elite_type)
    enemy.max_hp = int(enemy.max_hp * (1.0 + difficulty * 0.3))
    enemy.hp = enemy.max_hp
    enemy.damage = int(enemy.damage * 1.2)
    enemy.is_elite = True
    enemy.score = int(enemy.score * 2)
    return enemy
