"""
武器系统
"""
import math
import random
from src.entities.bullet import Bullet, MeleeAttack
from src.entities.character import WEAPON_DATA, WEAPON_RARITY, WEAPON_RARITY_ORDER


class Weapon:
    """武器基类"""

    def __init__(self, weapon_id, owner=None):
        self.weapon_id = weapon_id
        self.data = WEAPON_DATA.get(weapon_id, {}).copy()
        self.name = self.data.get('name', weapon_id)
        self.weapon_type = self.data.get('type', 'ranged')
        self.damage = self.data.get('damage', 10)
        self.fire_rate = self.data.get('fire_rate', 30)
        self.owner = owner
        self.ammo = self.data.get('mag_size', 12)
        self.max_ammo = self.data.get('mag_size', 12)
        self.fire_cooldown = 0
        self.reloading = False
        self.reload_time = 60
        self.reload_timer = 0
        self.level = 1
        self.crit_chance = 0.05
        self.crit_multiplier = 2.0

        # 稀有度
        self.rarity = 'common'
        self.rarity_mult = 1.0

        # 特殊属性
        self.has_lifesteal = self.data.get('lifesteal', 0) > 0
        self.lifesteal_pct = self.data.get('lifesteal', 0)

    def can_fire(self):
        """是否可以开火"""
        if self.reloading:
            return False
        if self.fire_cooldown > 0:
            return False
        if self.weapon_type == 'ranged' and self.ammo <= 0:
            self.start_reload()
            return False
        return True

    def fire(self, x, y, target_x, target_y):
        """开火，返回子弹或近战攻击列表"""
        if not self.can_fire():
            return []

        self.fire_cooldown = self.fire_rate
        results = []

        if self.weapon_type == 'melee':
            angle = math.atan2(target_y - y, target_x - x)
            attack = MeleeAttack(x, y, angle, self.data)
            attack.damage = self._apply_crit(attack.damage)
            results.append(attack)
        else:
            self.ammo -= 1
            base_angle = math.atan2(target_y - y, target_x - x)
            spread = self.data.get('spread', 5)
            bullets = self.data.get('bullets_per_shot', 1)

            for i in range(bullets):
                angle = base_angle
                if bullets > 1:
                    offset = (i - (bullets - 1) / 2) * math.radians(spread)
                    angle += offset + math.radians(self._rand(-spread * 0.3, spread * 0.3))
                else:
                    angle += math.radians(self._rand(-spread, spread))
                bullet = Bullet(x, y, angle, self.data, source_is_player=True)
                bullet.damage = self._apply_crit(bullet.damage)
                results.append(bullet)

        return results

    def _apply_crit(self, damage):
        """应用暴击"""
        import random as _rnd
        if _rnd.random() < self.crit_chance:
            return int(damage * self.crit_multiplier)
        return damage

    def upgrade(self):
        """升级武器"""
        self.level += 1
        self.damage = int(self.damage * 1.15)
        if self.weapon_type == 'ranged':
            self.max_ammo = int(self.max_ammo * 1.1)
            self.ammo = self.max_ammo
        self.crit_chance = min(0.3, self.crit_chance + 0.02)
        self.crit_multiplier = min(3.5, self.crit_multiplier + 0.1)
        if self.level % 3 == 0:
            self.fire_rate = max(2, int(self.fire_rate * 0.85))

    def roll_rarity(self):
        """随机生成稀有度"""
        total_weight = sum(r['drop_weight'] for r in WEAPON_RARITY.values())
        roll = random.randint(1, total_weight)
        cumulative = 0
        for rarity_name in WEAPON_RARITY_ORDER:
            cumulative += WEAPON_RARITY[rarity_name]['drop_weight']
            if roll <= cumulative:
                self.rarity = rarity_name
                self.rarity_mult = WEAPON_RARITY[rarity_name]['mult']
                self.damage = int(self.damage * self.rarity_mult)
                return rarity_name
        return 'common'

    def get_rarity_color(self):
        """获取稀有度颜色"""
        return WEAPON_RARITY.get(self.rarity, {}).get('color', (150, 150, 150))

    def get_rarity_name(self):
        """获取稀有度名称"""
        rarity_name = WEAPON_RARITY.get(self.rarity, {}).get('name', '普通')
        if self.rarity == 'common':
            return ''
        return f'[{rarity_name}]'

    def start_reload(self):
        if not self.reloading and self.ammo < self.max_ammo:
            self.reloading = True
            self.reload_timer = self.reload_time

    def update(self):
        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1
        if self.reloading:
            self.reload_timer -= 1
            if self.reload_timer <= 0:
                self.reloading = False
                self.ammo = self.max_ammo

    def get_reload_progress(self):
        if not self.reloading:
            return 1.0
        return 1.0 - (self.reload_timer / self.reload_time)

    @staticmethod
    def _rand(lo, hi):
        return random.uniform(lo, hi)


class WeaponManager:
    """管理玩家的武器栏（2格）"""

    def __init__(self):
        self.slots = [None, None]
        self.current_slot = 0

    def equip(self, weapon_id, slot=None):
        """装备武器到指定插槽，返回(插槽索引, 被替换的武器ID或None)"""
        weapon = Weapon(weapon_id)
        old_id = None
        if slot is not None:
            if self.slots[slot] is not None:
                old_id = self.slots[slot].weapon_id
            self.slots[slot] = weapon
        else:
            # 自动选择空插槽
            for i in range(2):
                if self.slots[i] is None:
                    self.slots[i] = weapon
                    return i, None
            # 替换当前插槽
            current = self.slots[self.current_slot]
            if current is not None:
                old_id = current.weapon_id
            self.slots[self.current_slot] = weapon
        return self.current_slot, old_id

    def get_current(self):
        return self.slots[self.current_slot]

    def switch_weapon(self):
        """切换到另一个武器"""
        for i in range(1, 3):
            idx = (self.current_slot + i) % 2
            if self.slots[idx] is not None:
                self.current_slot = idx
                break

    def switch_to_slot(self, index):
        if 0 <= index < 2 and self.slots[index] is not None:
            self.current_slot = index

    def update(self):
        for slot in self.slots:
            if slot:
                slot.update()


def generate_random_weapon(min_tier=1, max_tier=3):
    """生成一把随机稀有度武器"""
    candidates = [wid for wid, wd in WEAPON_DATA.items()
                  if min_tier <= wd.get('tier', 1) <= max_tier
                  and wd.get('cost', 0) > 0]
    if not candidates:
        candidates = [wid for wid in WEAPON_DATA]

    weapon_id = random.choice(candidates)
    weapon = Weapon(weapon_id)
    weapon.roll_rarity()
    return weapon


def get_weapon_display_name(weapon):
    """获取武器的完整显示名称（含稀有度）"""
    if weapon is None:
        return '空'
    rarity_name = weapon.get_rarity_name()
    base_name = weapon.name
    level_suffix = f' Lv.{weapon.level}' if weapon.level > 1 else ''
    if rarity_name:
        return f'{rarity_name} {base_name}{level_suffix}'
    return f'{base_name}{level_suffix}'
