"""
Boss AI 系统 - 高级BOSS多阶段战斗逻辑
每个Boss有独特的阶段转换、攻击模式和特效
"""
import math
import random
import pygame
from src.entities.bullet import Bullet


class BossBrain:
    """Boss 智能控制器 - 为 Enemy 提供高级AI决策"""

    @staticmethod
    def get_phase_behavior(enemy, player, world):
        """根据Boss类型和血量百分比返回行为"""
        enemy_type = enemy.enemy_type
        hp_pct = enemy.hp / enemy.max_hp

        if enemy_type == 'boss_knight':
            return BossBrain._boss_knight_phase(enemy, player, world, hp_pct)
        elif enemy_type == 'boss_mage':
            return BossBrain._boss_mage_phase(enemy, player, world, hp_pct)
        elif enemy_type == 'boss_dragon':
            return BossBrain._boss_dragon_phase(enemy, player, world, hp_pct)
        elif enemy_type == 'boss_mech':
            return BossBrain._boss_mech_phase(enemy, player, world, hp_pct)
        return {}

    @staticmethod
    def _boss_knight_phase(enemy, player, world, hp_pct):
        """暗黑骑士 - 三阶段：斩击→冲锋→旋转"""
        result = {'phase': 0, 'special_attack': None}

        if hp_pct < 0.3:
            result['phase'] = 2  # 狂暴阶段：旋转攻击 + 频繁冲锋
            result['speed_mult'] = 1.4
            result['attack_cooldown_mult'] = 0.6
            result['energy_color'] = (255, 50, 50)
            if random.random() < 0.03:
                result['special_attack'] = {
                    'type': 'spin_attack',
                    'damage': 35,
                    'radius': 120,
                    'duration': 30
                }
            elif random.random() < 0.04:
                result['special_attack'] = {
                    'type': 'charge',
                    'damage': 40,
                    'speed_mult': 5,
                    'charge_distance': 250,
                }
        elif hp_pct < 0.6:
            result['phase'] = 1  # 强化阶段：剑气 + 冲锋
            result['speed_mult'] = 1.15
            result['attack_cooldown_mult'] = 0.8
            result['energy_color'] = (255, 150, 50)
            if random.random() < 0.02:
                result['special_attack'] = {
                    'type': 'slash_wave',
                    'damage': 25,
                    'wave_count': 5,
                    'spread': 30,
                    'speed': 6,
                }
            elif random.random() < 0.03:
                result['special_attack'] = {
                    'type': 'charge',
                    'damage': 30,
                    'speed_mult': 4,
                    'charge_distance': 200,
                }
        else:
            result['phase'] = 0  # 普通阶段
            result['speed_mult'] = 1.0
            result['attack_cooldown_mult'] = 1.0
            result['energy_color'] = None
            if random.random() < 0.015:
                result['special_attack'] = {
                    'type': 'slash_wave',
                    'damage': 20,
                    'wave_count': 3,
                    'spread': 25,
                    'speed': 5,
                }

        return result

    @staticmethod
    def _boss_mage_phase(enemy, player, world, hp_pct):
        """大法师 - 四阶段：火球→冰风暴→瞬移→召唤"""
        result = {'phase': 0, 'special_attack': None}

        if hp_pct < 0.25:
            result['phase'] = 3  # 召唤阶段
            result['speed_mult'] = 1.0
            result['attack_cooldown_mult'] = 0.5
            result['energy_color'] = (100, 50, 200)
            result['summon_minions'] = True
            if random.random() < 0.04:
                result['special_attack'] = {
                    'type': 'ice_storm',
                    'damage': 15,
                    'radius': 300,
                    'duration': 60,
                    'slow_amount': 0.5,
                }
            if random.random() < 0.03:
                result['special_attack'] = {
                    'type': 'teleport_nuke',
                    'damage': 40,
                    'nuke_radius': 100,
                }
        elif hp_pct < 0.5:
            result['phase'] = 2  # 冰风暴 + 瞬移
            result['speed_mult'] = 1.1
            result['attack_cooldown_mult'] = 0.7
            result['energy_color'] = (100, 180, 255)
            if random.random() < 0.025:
                result['special_attack'] = {
                    'type': 'ice_storm',
                    'damage': 12,
                    'radius': 250,
                    'duration': 45,
                    'slow_amount': 0.4,
                }
            if random.random() < 0.03:
                result['special_attack'] = {
                    'type': 'teleport_bolt',
                    'damage': 30,
                    'bolt_count': 8,
                }
        elif hp_pct < 0.75:
            result['phase'] = 1  # 火球射击
            result['speed_mult'] = 1.0
            result['attack_cooldown_mult'] = 0.85
            result['energy_color'] = (255, 100, 30)
            if random.random() < 0.02:
                result['special_attack'] = {
                    'type': 'fireball_volley',
                    'damage': 15,
                    'count': 6,
                    'spread': 45,
                }
        else:
            result['phase'] = 0
            result['speed_mult'] = 1.0
            result['attack_cooldown_mult'] = 1.0
            result['energy_color'] = None

        return result

    @staticmethod
    def _boss_dragon_phase(enemy, player, world, hp_pct):
        """远古巨龙 - 火焰吐息→尾扫→俯冲"""
        result = {'phase': 0, 'special_attack': None}

        if hp_pct < 0.3:
            result['phase'] = 2  # 狂暴
            result['speed_mult'] = 1.3
            result['attack_cooldown_mult'] = 0.5
            result['energy_color'] = (255, 60, 0)
            if random.random() < 0.03:
                result['special_attack'] = {
                    'type': 'fire_breath_cone',
                    'damage': 20,
                    'cone_angle': 60,
                    'cone_range': 200,
                    'tick_rate': 5,
                }
            if random.random() < 0.025:
                result['special_attack'] = {
                    'type': 'tail_sweep',
                    'damage': 35,
                    'sweep_radius': 150,
                    'knockback': 80,
                }
            if random.random() < 0.02:
                result['special_attack'] = {
                    'type': 'dive_bomb',
                    'damage': 45,
                    'landing_radius': 80,
                    'shockwave_radius': 200,
                }
        elif hp_pct < 0.6:
            result['phase'] = 1
            result['speed_mult'] = 1.15
            result['attack_cooldown_mult'] = 0.7
            result['energy_color'] = (255, 140, 30)
            if random.random() < 0.025:
                result['special_attack'] = {
                    'type': 'fire_breath_cone',
                    'damage': 15,
                    'cone_angle': 45,
                    'cone_range': 160,
                    'tick_rate': 8,
                }
            if random.random() < 0.02:
                result['special_attack'] = {
                    'type': 'tail_sweep',
                    'damage': 25,
                    'sweep_radius': 120,
                    'knockback': 60,
                }
        else:
            result['phase'] = 0
            result['speed_mult'] = 1.0
            result['attack_cooldown_mult'] = 1.0
            result['energy_color'] = None

        return result

    @staticmethod
    def _boss_mech_phase(enemy, player, world, hp_pct):
        """战争机甲 - 导弹弹幕→激光→地雷"""
        result = {'phase': 0, 'special_attack': None}

        if hp_pct < 0.3:
            result['phase'] = 2  # 全弹发射
            result['speed_mult'] = 0.5
            result['attack_cooldown_mult'] = 0.4
            result['energy_color'] = (255, 0, 0)
            if random.random() < 0.04:
                result['special_attack'] = {
                    'type': 'missile_barrage',
                    'damage': 12,
                    'missile_count': 16,
                    'spread': 60,
                    'homing': True,
                }
            if random.random() < 0.03:
                result['special_attack'] = {
                    'type': 'laser_beam',
                    'damage': 25,
                    'beam_width': 10,
                    'beam_length': 500,
                    'sweep_speed': 0.03,
                }
            if random.random() < 0.025:
                result['special_attack'] = {
                    'type': 'mine_field',
                    'damage': 30,
                    'mine_count': 12,
                    'field_radius': 250,
                    'mine_lifetime': 300,
                }
        elif hp_pct < 0.6:
            result['phase'] = 1
            result['speed_mult'] = 0.7
            result['attack_cooldown_mult'] = 0.6
            result['energy_color'] = (255, 120, 0)
            if random.random() < 0.03:
                result['special_attack'] = {
                    'type': 'missile_barrage',
                    'damage': 10,
                    'missile_count': 10,
                    'spread': 45,
                }
            if random.random() < 0.025:
                result['special_attack'] = {
                    'type': 'laser_beam',
                    'damage': 18,
                    'beam_width': 8,
                    'beam_length': 400,
                    'sweep_speed': 0.02,
                }
        else:
            result['phase'] = 0
            result['speed_mult'] = 1.0
            result['attack_cooldown_mult'] = 1.0
            result['energy_color'] = None

        return result

    @staticmethod
    def execute_special(enemy, player, world, special_data):
        """执行特殊攻击，返回产生的子弹列表"""
        bullets = []
        atype = special_data['type']
        cx = enemy.x + enemy.width // 2
        cy = enemy.y + enemy.height // 2

        if atype == 'slash_wave':
            count = special_data['wave_count']
            base_angle = math.atan2(player.y - cy, player.x - cx)
            for i in range(count):
                offset = (i - count // 2) * math.radians(special_data['spread'])
                angle = base_angle + offset
                b = Bullet(cx, cy, angle,
                           {'bullet_speed': special_data['speed'],
                            'damage': special_data['damage'],
                            'bullet_type': 'energy'},
                           source_is_player=False)
                bullets.append(b)

        elif atype == 'fireball_volley':
            count = special_data['count']
            base_angle = math.atan2(player.y - cy, player.x - cx)
            for i in range(count):
                offset = (i - count // 2) * math.radians(special_data['spread'])
                angle = base_angle + offset
                b = Bullet(cx, cy, angle,
                           {'bullet_speed': 5, 'damage': special_data['damage'],
                            'bullet_type': 'fire'},
                           source_is_player=False)
                bullets.append(b)

        elif atype == 'fire_breath_cone':
            cone_angle = math.atan2(player.y - cy, player.x - cx)
            for _ in range(8):
                spread = random.uniform(-math.radians(special_data['cone_angle'] // 2),
                                        math.radians(special_data['cone_angle'] // 2))
                angle = cone_angle + spread
                b = Bullet(cx, cy, angle,
                           {'bullet_speed': random.uniform(3, 7),
                            'damage': special_data['damage'],
                            'bullet_type': 'fire'},
                           source_is_player=False)
                bullets.append(b)

        elif atype == 'missile_barrage':
            count = special_data['missile_count']
            for i in range(count):
                angle = random.uniform(0, math.pi * 2)
                b = Bullet(cx, cy, angle,
                           {'bullet_speed': 4, 'damage': special_data['damage'],
                            'bullet_type': 'rocket', 'explosive': True,
                            'explosion_radius': 30},
                           source_is_player=False)
                bullets.append(b)

        elif atype == 'laser_beam':
            angle = math.atan2(player.y - cy, player.x - cx)
            b = Bullet(cx, cy, angle,
                       {'bullet_speed': 25, 'damage': special_data['damage'],
                        'bullet_type': 'laser', 'piercing': True},
                       source_is_player=False)
            bullets.append(b)

        elif atype == 'teleport_bolt':
            count = special_data['bolt_count']
            for i in range(count):
                angle = (2 * math.pi / count) * i
                b = Bullet(cx, cy, angle,
                           {'bullet_speed': 6, 'damage': special_data['damage'],
                            'bullet_type': 'energy'},
                           source_is_player=False)
                bullets.append(b)

        elif atype == 'mine_field':
            count = special_data['mine_count']
            radius = special_data['field_radius']
            for _ in range(count):
                mx = cx + random.randint(-radius, radius)
                my = cy + random.randint(-radius, radius)
                # 地雷：在玩家附近生成静止子弹，设定延迟引爆
                mine = Bullet(mx, my, 0,
                              {'bullet_speed': 0, 'damage': special_data['damage'],
                               'bullet_type': 'rocket', 'explosive': True,
                               'explosion_radius': 40},
                              source_is_player=False)
                mine._mine_lifetime = special_data['mine_lifetime']
                mine._mine_armed = False
                mine._mine_arm_time = 60
                bullets.append(mine)

        elif atype == 'ice_storm':
            for _ in range(20):
                ix = player.x + random.randint(-special_data['radius'], special_data['radius'])
                iy = player.y + random.randint(-special_data['radius'], special_data['radius'])
                b = Bullet(ix, iy + 60, -math.pi / 2,
                           {'bullet_speed': 3, 'damage': special_data['damage'],
                            'bullet_type': 'ice', 'slow_effect': True},
                           source_is_player=False)
                bullets.append(b)

        return bullets


def create_boss_bullet_pattern(pattern_name, cx, cy, target_x, target_y, damage=20,
                               count=8, bullet_type='energy'):
    """
    预设子弹模式生成器
    - 'circle': 圆形弹幕
    - 'spiral': 螺旋弹幕
    - 'wave': 波形弹幕
    - 'shotgun': 霰弹
    - 'aimed': 瞄准扩散
    - 'ring_expand': 扩展环
    """
    bullets = []
    base_angle = math.atan2(target_y - cy, target_x - cx)

    if pattern_name == 'circle':
        for i in range(count):
            angle = (2 * math.pi / count) * i
            b = Bullet(cx, cy, angle,
                       {'bullet_speed': 4, 'damage': damage, 'bullet_type': bullet_type},
                       source_is_player=False)
            bullets.append(b)

    elif pattern_name == 'spiral':
        for i in range(count):
            angle = base_angle + (2 * math.pi / count) * i + random.uniform(0, 0.3)
            b = Bullet(cx, cy, angle,
                       {'bullet_speed': 3 + i * 0.3, 'damage': damage,
                        'bullet_type': bullet_type},
                       source_is_player=False)
            bullets.append(b)

    elif pattern_name == 'wave':
        for i in range(count):
            angle = base_angle + math.sin(i * 0.5) * math.radians(40)
            b = Bullet(cx, cy, angle,
                       {'bullet_speed': 5, 'damage': damage, 'bullet_type': bullet_type},
                       source_is_player=False)
            bullets.append(b)

    elif pattern_name == 'shotgun':
        for i in range(count):
            spread = (i - count // 2) * math.radians(8)
            angle = base_angle + spread
            b = Bullet(cx, cy, angle,
                       {'bullet_speed': 6, 'damage': damage, 'bullet_type': bullet_type},
                       source_is_player=False)
            bullets.append(b)

    elif pattern_name == 'aimed':
        for i in range(count):
            spread = random.uniform(-0.3, 0.3)
            angle = base_angle + spread
            b = Bullet(cx, cy, angle,
                       {'bullet_speed': random.uniform(5, 8), 'damage': damage,
                        'bullet_type': bullet_type},
                       source_is_player=False)
            bullets.append(b)

    elif pattern_name == 'ring_expand':
        for ring in range(1, 4):
            ring_count = count * ring
            for i in range(ring_count):
                angle = (2 * math.pi / ring_count) * i
                b = Bullet(cx, cy, angle,
                           {'bullet_speed': 2 + ring * 1.5, 'damage': damage,
                            'bullet_type': bullet_type},
                           source_is_player=False)
                bullets.append(b)

    return bullets


def predict_player_movement(player):
    """预测玩家移动方向（用于预判射击）"""
    if abs(player.vx) < 0.1 and abs(player.vy) < 0.1:
        return player.x + player.width // 2, player.y + player.height // 2

    prediction_frames = 30
    predicted_x = player.x + player.vx * prediction_frames + player.width // 2
    predicted_y = player.y + player.vy * prediction_frames + player.height // 2
    return predicted_x, predicted_y


class BossPhaseManager:
    """Boss阶段管理 - 跟踪每个Boss的阶段状态和冷却"""

    def __init__(self):
        self.boss_states = {}  # boss_id -> state dict

    def get_state(self, boss):
        """获取或创建Boss状态"""
        bid = id(boss)
        if bid not in self.boss_states:
            self.boss_states[bid] = {
                'current_phase': 0,
                'phase_entered_frame': 0,
                'special_cooldown': 0,
                'attack_pattern_index': 0,
                'teleport_history': [],
                'summon_count': 0,
                'last_hp_check': boss.hp,
            }
        return self.boss_states[bid]

    def update(self, boss, player, world, frame_count):
        """更新Boss阶段和冷却"""
        state = self.get_state(boss)
        if state['special_cooldown'] > 0:
            state['special_cooldown'] -= 1
        hp_pct = boss.hp / boss.max_hp
        state['last_hp_check'] = boss.hp
        return state

    def cleanup(self, boss):
        """Boss死亡时清理状态"""
        bid = id(boss)
        if bid in self.boss_states:
            del self.boss_states[bid]
