"""
商店系统 - 武器购买、道具交易、等级折扣、刷新机制
"""
import random
import math
import pygame
from settings import TILE_SIZE, WINDOW_WIDTH, WINDOW_HEIGHT, YELLOW, WHITE, GREEN, GRAY, RED, CYAN
from src.entities.character import SHOP_WEAPONS, WEAPON_DATA, ITEM_DATA, WEAPON_RARITY
from src.engine.resource import get_resources
from src.engine.font_helper import get_chinese_font


# 商店等级配置
SHOP_TIERS = {
    'basic': {
        'name': '普通商店', 'color': (100, 150, 100),
        'weapon_count': (2, 3), 'item_count': (2, 3),
        'discount_chance': 0.1, 'max_discount': 0.85,
        'reroll_cost': 15, 'haggle_chance': 0.3,
    },
    'advanced': {
        'name': '高级商店', 'color': (100, 100, 220),
        'weapon_count': (3, 4), 'item_count': (3, 4),
        'discount_chance': 0.25, 'max_discount': 0.75,
        'reroll_cost': 10, 'haggle_chance': 0.4,
    },
    'premium': {
        'name': '特级商店', 'color': (200, 150, 50),
        'weapon_count': (3, 5), 'item_count': (3, 5),
        'discount_chance': 0.4, 'max_discount': 0.6,
        'reroll_cost': 5, 'haggle_chance': 0.5,
    },
}

# 商店NPC对话
NPC_TALK = [
    "欢迎光临！", "来看看新货！", "今天可是好日子～",
    "勇士，你需要什么？", "物美价廉！", "只此一家！",
    "地牢深处的好东西！", "算你便宜点？",
]


class Shop:
    """商店 - 在商店房间中显示和交易"""

    def __init__(self, x, y, tier='basic', floor_number=1):
        self.x = x
        self.y = y
        self.tier = tier
        self.tier_config = SHOP_TIERS.get(tier, SHOP_TIERS['basic'])
        self.floor_number = floor_number
        self.items = []  # 待售物品列表
        self.rerolls_used = 0
        self.total_sales = 0
        self.talk_text = random.choice(NPC_TALK)
        self.talk_timer = random.randint(60, 180)
        self._generate_stock()

    def _generate_stock(self):
        """生成随机商品（根据商店等级）"""
        cfg = self.tier_config
        self.items = []

        # 生成武器
        num_weapons = random.randint(*cfg['weapon_count'])
        # 根据楼层过滤武器池
        available = []
        for wid in SHOP_WEAPONS:
            if wid in WEAPON_DATA:
                wdata = WEAPON_DATA[wid]
                # 高级武器只在高层出现
                min_floor = wdata.get('min_floor', 1)
                if self.floor_number >= min_floor:
                    available.append(wid)
        if not available:
            available = list(SHOP_WEAPONS)

        weapons = random.sample(available, min(num_weapons, len(available)))
        for wid in weapons:
            data = WEAPON_DATA[wid]
            base_cost = data.get('cost', 50)
            # 应用折扣
            cost, discount = self._apply_discount(base_cost)
            # 随机稀有度
            rarity = self._roll_shop_rarity()
            self.items.append({
                'type': 'weapon',
                'id': wid,
                'name': data['name'],
                'cost': cost,
                'base_cost': base_cost,
                'data': data,
                'discount': discount,
                'rarity': rarity,
            })

        # 生成道具
        num_items = random.randint(*cfg['item_count'])
        item_ids = random.sample(list(ITEM_DATA.keys()), min(num_items, len(ITEM_DATA)))
        for iid in item_ids:
            data = ITEM_DATA[iid]
            base_cost = data.get('cost', 10)
            cost, discount = self._apply_discount(base_cost)
            self.items.append({
                'type': 'item',
                'id': iid,
                'name': data['name'],
                'cost': cost,
                'base_cost': base_cost,
                'data': data,
                'discount': discount,
                'rarity': None,
            })

        self._layout_items()

    def _apply_discount(self, base_cost):
        """随机打折"""
        cfg = self.tier_config
        if random.random() < cfg['discount_chance']:
            discount = round(random.uniform(cfg['max_discount'], 0.95), 2)
            return int(base_cost * discount), discount
        return base_cost, 1.0

    def _roll_shop_rarity(self):
        """按商店等级随机稀有度"""
        tier_bonus = {'basic': 0, 'advanced': 5, 'premium': 10}
        bonus = tier_bonus.get(self.tier, 0)
        roll = random.randint(1, 100)
        if roll <= 1 + bonus:
            return 'legendary'
        elif roll <= 5 + bonus:
            return 'epic'
        elif roll <= 20 + bonus:
            return 'rare'
        elif roll <= 50 + bonus:
            return 'uncommon'
        return 'common'

    def _layout_items(self):
        """排列物品位置"""
        cols = 3
        spacing_x = 70
        spacing_y = 65
        start_x = self.x - ((min(len(self.items), cols) - 1) % cols) * spacing_x // 2
        start_y = self.y - 110
        for i, item in enumerate(self.items):
            col = i % cols
            row = i // cols
            item['px'] = start_x + col * spacing_x
            item['py'] = start_y + row * spacing_y
            item['rect'] = pygame.Rect(item['px'] - 28, item['py'] - 28, 56, 56)

    def reroll_stock(self):
        """刷新商品（消耗金币）"""
        self.rerolls_used += 1
        self._generate_stock()

    def get_reroll_cost(self):
        """获取刷新价格"""
        return self.tier_config['reroll_cost'] + self.rerolls_used * 5

    def get_item_at(self, mx, my):
        """获取鼠标点击的商品"""
        for item in self.items:
            if item['rect'].collidepoint(mx, my):
                return item
        return None

    def buy_item(self, item, player):
        """购买商品"""
        if player.gold < item['cost']:
            return False, '金币不足!'

        # 尝试砍价
        final_cost = item['cost']
        haggle_success = False
        if random.random() < self.tier_config['haggle_chance']:
            discount = random.uniform(0.7, 0.95)
            final_cost = int(final_cost * discount)
            haggle_success = True

        if player.gold < final_cost:
            final_cost = player.gold  # 不够就全花掉

        player.gold -= final_cost
        self.total_sales += 1

        if item['type'] == 'weapon':
            # 装备武器
            slot, old_id = player.weapon_manager.equip(item['id'])
            rarity_info = WEAPON_RARITY.get(item.get('rarity', 'common'), {})
            result_text = f'获得了 {rarity_info.get("name","")} {item["name"]}!'
        else:
            # 使用道具效果
            iid = item['id']
            if 'heal' in item['data']:
                old_hp = player.hp
                player.hp = min(player.max_hp, player.hp + item['data']['heal'])
                result_text = f'+{player.hp - old_hp} HP'
            elif 'energy' in item['data']:
                player.energy = min(player.max_energy, player.energy + item['data']['energy'])
                result_text = f'+{item["data"]["energy"]} 能量'
            elif 'shield' in item['data']:
                player.shield = min(100, player.shield + item['data']['shield'])
                result_text = f'+{item["data"]["shield"]} 护盾'
            else:
                result_text = f'获得了 {item["name"]}!'

        if haggle_success and final_cost < item['cost']:
            result_text += f' (砍价成功! -{item["cost"] - final_cost}金)'

        self.items.remove(item)
        self._layout_items()
        return True, result_text

    def update(self):
        """更新NPC对话气泡"""
        self.talk_timer -= 1
        if self.talk_timer <= 0:
            self.talk_text = random.choice(NPC_TALK)
            self.talk_timer = random.randint(120, 300)

    def get_item_tooltip(self, item):
        """获取物品提示文字"""
        lines = [item['name']]
        if item['type'] == 'weapon':
            wdata = item['data']
            lines.append(f"伤害: {wdata.get('damage', 0)}")
            lines.append(f"射速: {wdata.get('fire_rate', 0)}/s")
            if wdata.get('energy_cost', 0) > 0:
                lines.append(f"能耗: {wdata['energy_cost']}")
            if item.get('rarity'):
                rinfo = WEAPON_RARITY.get(item['rarity'], {})
                lines.append(f"品质: {rinfo.get('name', item['rarity'])}")
        else:
            d = item['data']
            if 'heal' in d:
                lines.append(f"恢复 {d['heal']} HP")
            if 'energy' in d:
                lines.append(f"恢复 {d['energy']} 能量")
            if 'shield' in d:
                lines.append(f"+{d['shield']} 护盾")
        if item.get('discount', 1.0) < 1.0:
            lines.append(f"折扣: {int((1 - item['discount']) * 100)}% OFF!")
        lines.append(f"价格: {item['cost']} 金币")
        return lines

    def draw(self, screen, camera):
        """绘制商店"""
        res = get_resources()
        font = get_chinese_font(14)
        font_small = get_chinese_font(11)
        font_title = get_chinese_font(22)

        # 商店标识
        shop_x, shop_y = camera.apply_point(self.x, self.y - 170)
        tier_color = self.tier_config['color']
        title = font_title.render(self.tier_config['name'], True, tier_color)
        screen.blit(title, (shop_x - title.get_width() // 2, shop_y))

        # NPC对话气泡
        bubble_y = shop_y + 30
        talk_surf = font_small.render(self.talk_text, True, (200, 200, 220))
        bw, bh = talk_surf.get_width() + 16, talk_surf.get_height() + 10
        bubble_rect = pygame.Rect(shop_x - bw // 2, bubble_y, bw, bh)
        bubble_bg = pygame.Surface((bw, bh), pygame.SRCALPHA)
        bubble_bg.fill((30, 30, 50, 180))
        screen.blit(bubble_bg, (bubble_rect.x, bubble_rect.y))
        pygame.draw.rect(screen, (80, 80, 100), bubble_rect, 1)
        screen.blit(talk_surf, (bubble_rect.x + 8, bubble_rect.y + 5))

        for item in self.items:
            sx, sy = camera.apply_point(item['px'], item['py'])

            # 背景卡片
            card_w, card_h = 60, 64
            card = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            card_color = (40, 40, 50, 200)
            card.fill(card_color)
            screen.blit(card, (sx - card_w // 2, sy - card_h // 2))

            border_color = (100, 100, 120)
            if item.get('rarity'):
                rinfo = WEAPON_RARITY.get(item['rarity'], {})
                border_color = rinfo.get('color', (100, 100, 120))
            pygame.draw.rect(screen, border_color,
                             (sx - card_w // 2, sy - card_h // 2, card_w, card_h), 2)

            # 折扣标记
            if item.get('discount', 1.0) < 1.0:
                off_pct = int((1 - item['discount']) * 100)
                off_surf = font_small.render(f'-{off_pct}%', True, (255, 80, 80))
                screen.blit(off_surf, (sx - off_surf.get_width() // 2, sy - card_h // 2 - 8))

            # 武器图标
            if item['type'] == 'weapon':
                icon = res.get_weapon_icon(item['id'])
                if icon:
                    icon_scaled = pygame.transform.scale(icon, (32, 32))
                    screen.blit(icon_scaled, (sx - 16, sy - 16))
            else:
                sprite = res.get_item_sprite(item['id'] if item['id'] in ['health_small', 'health_large'] else 'gold')
                if sprite:
                    screen.blit(sprite, (sx - 10, sy - 14))

            # 价格标签
            cost_color = YELLOW if item.get('discount', 1.0) >= 1.0 else (255, 150, 100)
            cost_text = f'${item["cost"]}'
            cost_surf = font_small.render(cost_text, True, cost_color)
            screen.blit(cost_surf, (sx - cost_surf.get_width() // 2, sy + 20))

            # 名字
            name_color = WHITE
            if item.get('rarity'):
                rinfo = WEAPON_RARITY.get(item['rarity'], {})
                name_color = rinfo.get('color', WHITE)
            name_surf = font.render(item['name'][:6], True, name_color)
            screen.blit(name_surf, (sx - name_surf.get_width() // 2, sy - 44))

        # 刷新提示
        if self.rerolls_used < 3:
            reroll_cost = self.get_reroll_cost()
            hint_y = shop_y + 55
            hint = font_small.render(f'按R刷新 ({reroll_cost}金)', True, (160, 160, 180))
            screen.blit(hint, (shop_x - hint.get_width() // 2, hint_y))

    def get_bounds(self):
        """返回商店的交互区域"""
        if not self.items:
            return pygame.Rect(0, 0, 0, 0)
        left = min(item['px'] for item in self.items) - 40
        right = max(item['px'] for item in self.items) + 40
        top = min(item['py'] for item in self.items) - 90
        bottom = max(item['py'] for item in self.items) + 40
        return pygame.Rect(left, top, right - left, bottom - top)
