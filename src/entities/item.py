"""
道具/掉落物系统
"""
import math
import random
import pygame
from settings import TILE_SIZE
from src.engine.resource import get_resources


class Item:
    """可拾取道具基类"""

    def __init__(self, x, y, item_type):
        self.x = x
        self.y = y
        self.item_type = item_type
        self.alive = True
        self.lifetime = 600  # 10秒后消失
        self.pickup_range = 40
        self.bob_offset = 0
        self.bob_timer = 0

        # 碰撞体积
        self.radius = 10
        self.hitbox = pygame.Rect(x - self.radius, y - self.radius,
                                   self.radius * 2, self.radius * 2)

        self.sprite = get_resources().get_item_sprite(item_type)

    def update(self):
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.alive = False
        self.bob_timer += 0.05
        self.bob_offset = int(3 * math.sin(self.bob_timer))

    def apply(self, player):
        """应用效果到玩家"""
        pass

    def draw(self, screen, camera):
        sx, sy = camera.apply_point(self.x, self.y + self.bob_offset)
        if self.sprite:
            rect = self.sprite.get_rect(center=(sx, sy))
            screen.blit(self.sprite, rect)
        else:
            pygame.draw.circle(screen, (255, 255, 0), (int(sx), int(sy)), self.radius)


class GoldItem(Item):
    def __init__(self, x, y, amount=10):
        super().__init__(x, y, 'gold')
        self.amount = amount

    def apply(self, player):
        player.gold += self.amount
        return f"+{self.amount} 金币"


class HealthItem(Item):
    def __init__(self, x, y, amount=30):
        super().__init__(x, y, 'health')
        self.amount = amount

    def apply(self, player):
        old = player.hp
        player.hp = min(player.max_hp, player.hp + self.amount)
        return f"+{player.hp - old} HP"


class EnergyItem(Item):
    def __init__(self, x, y, amount=50):
        super().__init__(x, y, 'energy')
        self.amount = amount

    def apply(self, player):
        player.energy = min(player.max_energy, player.energy + self.amount)
        return f"+{self.amount} 能量"


class ShieldItem(Item):
    def __init__(self, x, y):
        super().__init__(x, y, 'shield')

    def apply(self, player):
        player.shield = min(100, player.shield + 40)
        return "+护盾"


class SpeedBoostItem(Item):
    def __init__(self, x, y):
        super().__init__(x, y, 'speed_boost')

    def apply(self, player):
        player.speed_boost_duration = 300
        return "加速!"


class DamageBoostItem(Item):
    def __init__(self, x, y):
        super().__init__(x, y, 'damage_boost')

    def apply(self, player):
        player.damage_boost_duration = 300
        return "伤害UP!"


class RegenerationItem(Item):
    """再生药水 - 持续回血"""
    def __init__(self, x, y):
        super().__init__(x, y, 'regen')

    def apply(self, player):
        player.apply_effect('regen', 600)
        return "再生药水! 持续回血30秒"


class BerserkItem(Item):
    """狂暴药水 - 伤害+速度提升"""
    def __init__(self, x, y):
        super().__init__(x, y, 'berserk')

    def apply(self, player):
        player.apply_effect('berserk', 300)
        return "狂暴! 伤害+速度提升!"


class MagnetItem(Item):
    """磁铁 - 自动吸取附近金币"""
    def __init__(self, x, y):
        super().__init__(x, y, 'magnet')

    def apply(self, player):
        for _ in range(10):
            player.gold += 5
        return "磁铁! +50金币"


class BombItem(Item):
    """炸弹 - 清屏伤害"""
    def __init__(self, x, y):
        super().__init__(x, y, 'bomb')
        self.damage = 80

    def apply(self, player):
        return "__bomb__"


class ExpOrb(Item):
    """经验球 - 给玩家提供经验值"""
    def __init__(self, x, y, exp_amount=20):
        super().__init__(x, y, 'exp')
        self.exp_amount = exp_amount
        self.radius = 6
        self.hitbox = pygame.Rect(x - self.radius, y - self.radius,
                                   self.radius * 2, self.radius * 2)

    def apply(self, player):
        leveled = player.add_exp(self.exp_amount)
        msg = f'+{self.exp_amount} EXP'
        if leveled:
            msg += f' 升到 Lv.{player.level}!'
        return msg

    def draw(self, screen, camera):
        sx, sy = camera.apply_point(self.x, self.y + self.bob_offset)
        # 绿色小光球
        alpha = int(128 + 127 * abs(math.sin(self.bob_timer)))
        color = (100, 255, 100, alpha)
        pygame.draw.circle(screen, (100, 255, 100), (int(sx), int(sy)), self.radius)
        pygame.draw.circle(screen, (200, 255, 200), (int(sx), int(sy)), self.radius // 2)


class WeaponDrop(Item):
    """武器掉落 - 掉落在房间地面"""
    def __init__(self, x, y, weapon_id):
        super().__init__(x, y, 'weapon_drop')
        self.weapon_id = weapon_id
        self.lifetime = 900  # 15秒后消失
        self.radius = 14
        self.hitbox = pygame.Rect(x - self.radius, y - self.radius,
                                   self.radius * 2, self.radius * 2)
        from src.entities.character import WEAPON_DATA, WEAPON_RARITY
        self.weapon_data = WEAPON_DATA.get(weapon_id, {})
        self._rarity = None

    def roll_rarity(self):
        """随机获取稀有度"""
        from src.entities.character import WEAPON_RARITY, WEAPON_RARITY_ORDER
        total = sum(r['drop_weight'] for r in WEAPON_RARITY.values())
        roll = random.randint(1, total)
        cumulative = 0
        for rn in WEAPON_RARITY_ORDER:
            cumulative += WEAPON_RARITY[rn]['drop_weight']
            if roll <= cumulative:
                self._rarity = rn
                break
        return self._rarity or 'common'

    def apply(self, player):
        rarity = self._rarity or 'common'
        slot, old_id = player.weapon_manager.equip(self.weapon_id)
        if slot is not None:
            weapon = player.weapon_manager.slots[slot]
            if weapon:
                weapon.rarity = rarity
                from src.entities.character import WEAPON_RARITY
                weapon.rarity_mult = WEAPON_RARITY[rarity]['mult']
                weapon.damage = int(weapon.damage * weapon.rarity_mult)
        wname = self.weapon_data.get('name', self.weapon_id)
        return f'获得 [{wname}]!'

    def draw(self, screen, camera):
        sx, sy = camera.apply_point(self.x, self.y + self.bob_offset)
        rarity = self._rarity or 'common'
        from src.entities.character import WEAPON_RARITY
        color = WEAPON_RARITY.get(rarity, {}).get('color', (200, 200, 200))

        # 旋转光环
        glow_alpha = int(100 + 80 * abs(math.sin(self.bob_timer * 1.5)))
        glow_surf = pygame.Surface((self.radius * 2 + 4, self.radius * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*color, glow_alpha),
                           (self.radius + 2, self.radius + 2), self.radius + 2)
        screen.blit(glow_surf, (sx - self.radius - 2, sy - self.radius - 2))

        # 武器图标
        pygame.draw.rect(screen, color, (sx - self.radius // 2, sy - self.radius // 2,
                                          self.radius, self.radius))
        # 十字准星
        pygame.draw.line(screen, (255, 255, 255), (sx - 6, sy), (sx + 6, sy), 1)
        pygame.draw.line(screen, (255, 255, 255), (sx, sy - 6), (sx, sy + 6), 1)


class CoinChest(Item):
    """金币宝箱 - 掉落大量金币"""
    def __init__(self, x, y):
        super().__init__(x, y, 'gold_chest')
        self.lifetime = 999999
        self.opened = False

    def apply(self, player):
        if self.opened:
            return None
        self.opened = True
        amount = random.randint(50, 120)
        player.gold += amount
        return f'金币宝箱! +{amount} 金币!'

    def draw(self, screen, camera):
        sx, sy = camera.apply_point(self.x, self.y + self.bob_offset)
        if self.opened:
            color = (120, 90, 40)
        else:
            color = (200, 170, 80)
        pygame.draw.rect(screen, color, (sx - 10, sy - 8, 20, 16))
        pygame.draw.rect(screen, (180, 150, 50), (sx - 8, sy - 3, 16, 4))
        if not self.opened:
            glow_alpha = int(128 + 64 * abs(math.sin(self.bob_timer)))
            pygame.draw.circle(screen, (255, 215, 0, glow_alpha),
                               (int(sx), int(sy - 12)), 6, 1)


class ChestItem(Item):
    def __init__(self, x, y):
        super().__init__(x, y, 'chest')
        self.lifetime = 999999  # 宝箱不会消失
        self.opened = False

    def apply(self, player):
        if self.opened:
            return None
        self.opened = True
        return "chest"


def generate_loot(x, y, is_boss=False):
    """生成随机掉落"""
    items = []
    if is_boss:
        items.append(GoldItem(x + random.randint(-30, 30), y + random.randint(-30, 30),
                              random.randint(50, 100)))
        items.append(HealthItem(x + random.randint(-30, 30), y + random.randint(-30, 30), 50))
        items.append(ExpOrb(x + random.randint(-20, 20), y + random.randint(-20, 20), 80))
        if random.random() < 0.5:
            items.append(EnergyItem(x + random.randint(-30, 30), y + random.randint(-30, 30), 80))
        if random.random() < 0.3:
            items.append(ShieldItem(x + random.randint(-20, 20), y + random.randint(-20, 20)))
        if random.random() < 0.15:
            items.append(BerserkItem(x + random.randint(-20, 20), y + random.randint(-20, 20)))
        # Boss有概率掉落武器
        if random.random() < 0.25:
            from src.entities.character import SHOP_WEAPONS
            wid = random.choice(SHOP_WEAPONS)
            drop = WeaponDrop(x + random.randint(-20, 20), y + random.randint(-20, 20), wid)
            drop.roll_rarity()
            items.append(drop)
    else:
        roll = random.random()
        if roll < 0.25:
            items.append(GoldItem(x + random.randint(-20, 20), y + random.randint(-20, 20),
                                  random.randint(5, 20)))
        elif roll < 0.40:
            items.append(HealthItem(x + random.randint(-10, 10), y + random.randint(-10, 10),
                                    random.randint(10, 25)))
        elif roll < 0.50:
            items.append(EnergyItem(x + random.randint(-10, 10), y + random.randint(-10, 10),
                                    random.randint(20, 40)))
        elif roll < 0.58:
            items.append(ExpOrb(x + random.randint(-10, 10), y + random.randint(-10, 10),
                                random.randint(10, 30)))
        elif roll < 0.64:
            items.append(ShieldItem(x, y))
        elif roll < 0.70:
            items.append(SpeedBoostItem(x, y))
        elif roll < 0.75:
            items.append(DamageBoostItem(x, y))
        elif roll < 0.79:
            items.append(RegenerationItem(x, y))
        elif roll < 0.82:
            items.append(MagnetItem(x, y))
        elif roll < 0.85:
            items.append(BombItem(x, y))
        elif roll < 0.88:
            items.append(BerserkItem(x, y))
        # 稀有武器掉落
        elif roll < 0.90:
            from src.entities.character import SHOP_WEAPONS
            wid = random.choice(SHOP_WEAPONS)
            drop = WeaponDrop(x, y, wid)
            drop.roll_rarity()
            items.append(drop)
    return items


def generate_chest(x, y):
    """生成宝箱"""
    return ChestItem(x, y)
