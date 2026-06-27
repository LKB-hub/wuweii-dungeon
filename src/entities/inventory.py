"""
背包/仓库系统 - 可存放道具、装备、消耗品，战斗中随时使用
"""
import math
import random
import pygame


# ============ 道具模板 ============
ITEM_DEFS = {
    'health_potion_s':  {'name': '小型生命药水',  'desc': '恢复 25 HP',      'type': 'consumable', 'effect': {'heal': 25},      'icon_color': (255, 80, 80),   'stack': 5, 'cost': 15},
    'health_potion_m':  {'name': '中型生命药水',  'desc': '恢复 60 HP',      'type': 'consumable', 'effect': {'heal': 60},      'icon_color': (255, 50, 50),   'stack': 3, 'cost': 30},
    'health_potion_l':  {'name': '大型生命药水',  'desc': '恢复 150 HP',     'type': 'consumable', 'effect': {'heal': 150},     'icon_color': (255, 20, 20),   'stack': 2, 'cost': 60},
    'energy_potion':    {'name': '能量药水',      'desc': '恢复 80 能量',    'type': 'consumable', 'effect': {'energy': 80},    'icon_color': (100, 150, 255), 'stack': 3, 'cost': 25},
    'shield_potion':    {'name': '护盾药水',      'desc': '+40 护盾',        'type': 'consumable', 'effect': {'shield': 40},    'icon_color': (80, 180, 255),  'stack': 3, 'cost': 35},
    'speed_potion':     {'name': '速度药剂',      'desc': '加速 8秒',        'type': 'consumable', 'effect': {'speed_boost': 480}, 'icon_color': (255, 255, 100), 'stack': 3, 'cost': 20},
    'damage_potion':    {'name': '狂暴药剂',      'desc': '伤害+50% 8秒',   'type': 'consumable', 'effect': {'damage_boost': 480}, 'icon_color': (255, 100, 50), 'stack': 2, 'cost': 40},
    'regen_potion':     {'name': '再生药水',      'desc': '持续回血 15秒',   'type': 'consumable', 'effect': {'regen': 900},   'icon_color': (100, 255, 100), 'stack': 2, 'cost': 45},
    'bomb':             {'name': '炸弹',          'desc': '范围伤害 80',     'type': 'consumable', 'effect': {'bomb': 80},      'icon_color': (60, 60, 60),    'stack': 3, 'cost': 30},
    'key':              {'name': '地牢钥匙',      'desc': '开启特殊的门',     'type': 'key',        'effect': {},              'icon_color': (200, 180, 100), 'stack': 9, 'cost': 50},
    'scroll_identify':  {'name': '鉴定卷轴',      'desc': '鉴定未知装备',     'type': 'scroll',     'effect': {},              'icon_color': (200, 180, 220), 'stack': 3, 'cost': 20},
    'scroll_teleport':  {'name': '传送卷轴',      'desc': '随机传送',        'type': 'scroll',     'effect': {'teleport': True}, 'icon_color': (150, 100, 200), 'stack': 2, 'cost': 40},
}


class InventoryItem:
    """背包中的一个道具实例"""

    def __init__(self, item_id, quantity=1):
        self.item_id = item_id
        self.defn = ITEM_DEFS.get(item_id, {})
        self.quantity = quantity
        self.max_stack = self.defn.get('stack', 1)

    @property
    def name(self):
        return self.defn.get('name', self.item_id)

    @property
    def item_type(self):
        return self.defn.get('type', 'misc')

    def can_stack(self, other):
        """能否与另一个道具合并堆叠"""
        return (self.item_id == other.item_id and
                self.quantity < self.max_stack and
                other.quantity > 0)

    def use(self, player):
        """使用道具，返回 True 表示消耗成功"""
        eff = self.defn.get('effect', {})
        if 'heal' in eff:
            old = player.hp
            player.hp = min(player.max_hp, player.hp + eff['heal'])
            return player.hp > old
        elif 'energy' in eff:
            player.energy = min(player.max_energy, player.energy + eff['energy'])
            return True
        elif 'shield' in eff:
            player.shield = min(100, player.shield + eff['shield'])
            return True
        elif 'speed_boost' in eff:
            player.apply_effect('speed_boost', eff['speed_boost'])
            return True
        elif 'damage_boost' in eff:
            player.apply_effect('damage_boost', eff['damage_boost'])
            return True
        elif 'regen' in eff:
            player.apply_effect('regen', eff['regen'])
            return True
        elif 'bomb' in eff:
            return '__bomb__'
        elif 'teleport' in eff:
            return '__teleport__'
        return False


class Inventory:
    """背包管理器"""

    def __init__(self, max_slots=24):
        self.items = []  # [InventoryItem, ...]
        self.max_slots = max_slots
        self.gold = 0

    def add_item(self, item_id, quantity=1):
        """添加道具，自动堆叠，返回实际添加数量"""
        added = 0
        defn = ITEM_DEFS.get(item_id, {})
        stack = defn.get('stack', 1)

        # 先尝试堆叠到已有格子
        for inv_item in self.items:
            if inv_item.item_id == item_id and inv_item.quantity < inv_item.max_stack:
                space = inv_item.max_stack - inv_item.quantity
                take = min(space, quantity)
                inv_item.quantity += take
                quantity -= take
                added += take
                if quantity <= 0:
                    return added

        # 开新格子
        while quantity > 0 and len(self.items) < self.max_slots:
            take = min(stack, quantity)
            self.items.append(InventoryItem(item_id, take))
            quantity -= take
            added += take

        return added

    def remove_item(self, index, quantity=1):
        """从背包移除道具"""
        if 0 <= index < len(self.items):
            item = self.items[index]
            item.quantity -= quantity
            if item.quantity <= 0:
                self.items.pop(index)
            return True
        return False

    def use_item(self, index, player):
        """使用指定格子道具"""
        if 0 <= index < len(self.items):
            item = self.items[index]
            result = item.use(player)
            if result == '__bomb__':
                self.remove_item(index)
                return '__bomb__'
            elif result == '__teleport__':
                self.remove_item(index)
                return '__teleport__'
            elif result:
                self.remove_item(index)
                return f'使用了 {item.name}'
        return None

    def has_item(self, item_id):
        """检查是否有某种道具"""
        return any(it.item_id == item_id for it in self.items)

    def count_item(self, item_id):
        """统计某种道具总数"""
        return sum(it.quantity for it in self.items if it.item_id == item_id)

    def to_dict(self):
        return [{'id': it.item_id, 'qty': it.quantity} for it in self.items]

    def from_dict(self, data):
        self.items = []
        if data:
            for d in data:
                self.items.append(InventoryItem(d['id'], d['qty']))


class InventoryUI:
    """背包界面 - 游戏中按 I 打开"""

    def __init__(self, game):
        self.game = game
        self.visible = False
        self.selected = 0
        self.scroll = 0
        self.max_visible = 10
        self.item_slots = []
        self.anim_timer = 0

    def toggle(self):
        self.visible = not self.visible
        if self.visible:
            self.selected = 0
            self.scroll = 0

    def handle_event(self, event, player, inventory):
        if not self.visible:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_i:
                self.toggle()
            return False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_i or event.key == pygame.K_ESCAPE:
                self.toggle()
                return True
            elif event.key == pygame.K_UP:
                self.selected = max(0, self.selected - 1)
                if self.selected < self.scroll:
                    self.scroll = self.selected
            elif event.key == pygame.K_DOWN:
                self.selected = min(len(inventory.items) - 1, self.selected + 1)
                if self.selected >= self.scroll + self.max_visible:
                    self.scroll = self.selected - self.max_visible + 1
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                if inventory.items:
                    msg = inventory.use_item(self.selected, player)
                    if msg:
                        return msg
            elif event.key == pygame.K_q:
                if inventory.items:
                    inventory.remove_item(self.selected)
                    if self.selected >= len(inventory.items):
                        self.selected = max(0, len(inventory.items) - 1)
            elif event.key == pygame.K_TAB:
                self.toggle()
                return True
        return True  # 吞掉事件

    def update(self):
        self.anim_timer += 0.05

    def draw(self, screen, inventory, player):
        if not self.visible:
            return

        from src.engine.font_helper import get_chinese_font

        # 半透明背景遮罩
        overlay = pygame.Surface((self.game.screen.get_width(), self.game.screen.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # 面板
        pw, ph = 560, 450
        px = (1280 - pw) // 2
        py = (720 - ph) // 2
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((20, 20, 35, 230))
        screen.blit(panel, (px, py))
        pygame.draw.rect(screen, (100, 100, 140), (px, py, pw, ph), 2)

        # 标题
        title = get_chinese_font(24).render(f'背 包 ({len(inventory.items)}/{inventory.max_slots})', True, (255, 215, 0))
        screen.blit(title, (px + pw // 2 - title.get_width() // 2, py + 15))

        # 统计信息
        gold_text = get_chinese_font(14).render(f'金币: {player.gold}', True, (255, 200, 50))
        screen.blit(gold_text, (px + pw - 120, py + 18))

        # 道具列表
        start_y = py + 55
        slot_h = 38
        inv = inventory.items

        for i in range(self.scroll, min(len(inv), self.scroll + self.max_visible)):
            item = inv[i]
            sy = start_y + (i - self.scroll) * slot_h
            is_sel = (i == self.selected)

            # 背景
            bg = (50, 50, 65) if is_sel else (30, 30, 45)
            alpha = 200 if is_sel else 140
            rect = pygame.Rect(px + 20, sy, pw - 40, slot_h - 2)
            s = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            s.fill((*bg, alpha))
            screen.blit(s, (rect.x, rect.y))
            if is_sel:
                pygame.draw.rect(screen, (255, 215, 0), rect, 2)

            # 图标色块
            icon_color = item.defn.get('icon_color', (200, 200, 200))
            pygame.draw.rect(screen, icon_color, (rect.x + 5, rect.y + 5, 26, 26))
            pygame.draw.rect(screen, (255, 255, 255), (rect.x + 5, rect.y + 5, 26, 26), 1)

            # 名字
            name_color = {
                'consumable': (200, 230, 255),
                'key': (255, 220, 150),
                'scroll': (200, 180, 255),
            }.get(item.item_type, (200, 200, 200))
            name_surf = get_chinese_font(16).render(item.name, True, name_color)
            screen.blit(name_surf, (rect.x + 40, rect.y + 5))

            # 数量
            if item.quantity > 1:
                qty_surf = get_chinese_font(14).render(f'x{item.quantity}', True, (180, 180, 180))
                screen.blit(qty_surf, (rect.x + 40 + name_surf.get_width() + 10, rect.y + 6))

            # 描述
            desc_surf = get_chinese_font(12).render(item.defn.get('desc', ''), True, (140, 140, 160))
            screen.blit(desc_surf, (rect.x + 40, rect.y + 22))

            # 使用提示（选中时）
            if is_sel:
                hint = get_chinese_font(12).render('回车使用 | Q丢弃 | TAB/ESC关闭', True, (140, 140, 160))
                screen.blit(hint, (rect.right - hint.get_width() - 5, rect.y + 18))

        # 底部提示
        hint = get_chinese_font(13).render('I / ESC 关闭  |  ↑↓ 选择  |  回车 使用  |  Q 丢弃', True, (120, 120, 120))
        screen.blit(hint, (px + pw // 2 - hint.get_width() // 2, py + ph - 28))

        # 滚动指示
        if self.scroll > 0:
            pygame.draw.polygon(screen, (150, 150, 150),
                                [(px + pw // 2, py + 48), (px + pw // 2 - 8, py + 42), (px + pw // 2 + 8, py + 42)])
        if self.scroll + self.max_visible < len(inv):
            pygame.draw.polygon(screen, (150, 150, 150),
                                [(px + pw // 2, py + ph - 35), (px + pw // 2 - 8, py + ph - 29), (px + pw // 2 + 8, py + ph - 29)])
