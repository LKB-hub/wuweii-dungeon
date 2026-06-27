"""
城镇枢纽 - 出生点、商店、任务板、地牢入口、宠物屋
每次回到城镇时恢复满状态
"""
import math
import random
import pygame
from src.engine.scene import Scene
from src.engine.font_helper import get_chinese_font
from settings import WINDOW_WIDTH, WINDOW_HEIGHT, WHITE, YELLOW, GREEN, RED, GRAY, CYAN, ORANGE, PURPLE, BROWN


# 城镇各区域位置
ZONES = {
    'dungeon':    {'name': '地牢入口',   'rect': (460, 130, 360, 280),  'icon': '>>', 'color': (180, 80, 80)},
    'shop':       {'name': '商店',       'rect': (50,  80,  240, 220),  'icon': '[G]', 'color': (200, 180, 80)},
    'quest':      {'name': '任务告示板', 'rect': (50,  350, 240, 220),  'icon': '[Q]', 'color': (180, 160, 120)},
    'pet':        {'name': '宠物小屋',   'rect': (990, 80,  240, 220),  'icon': '[P]', 'color': (120, 180, 200)},
    'storage':    {'name': '仓库',       'rect': (990, 350, 240, 220),  'icon': '[B]', 'color': (160, 140, 100)},
}


class HubScene(Scene):
    """城镇枢纽场景"""

    def __init__(self, game, **kwargs):
        super().__init__(game)
        self.anim_timer = 0
        self.selected_zone = None
        self.selected_quest = 0
        self.quest_tab = 'main'
        self.selected_shop_item = 0
        self.hover_zone = None
        self.ui_mode = None  # None, 'quest_board', 'shop', 'pet_house', 'storage'
        self.flash_texts = []
        self.scroll_offset = 0
        self.hub_character_id = kwargs.get('character_id', 'knight')
        self.hub_difficulty = kwargs.get('difficulty', 1)

        # 导入重要组件
        from src.engine.save import get_save_manager
        self.save_mgr = get_save_manager()
        from src.entities.inventory import Inventory
        from src.entities.quest import QuestManager
        from src.entities.pet import Pet

        # 玩家虚拟状态（城镇里显示的）
        self.player_lv = self.save_mgr.stats.get('hub_player_level', 1)
        self.player_gold = self.save_mgr.stats.get('hub_gold', 0)

        # 背包（从存档恢复）
        self.inventory = Inventory(max_slots=30)
        inv_data = self.save_mgr.stats.get('hub_inventory', [])
        if inv_data:
            self.inventory.from_dict(inv_data)
        else:
            self.inventory.add_item('health_potion_s', 3)
            self.inventory.add_item('energy_potion', 2)

        # 任务系统
        self.quest_mgr = QuestManager()
        q_data = self.save_mgr.stats.get('hub_quests')
        if q_data:
            self.quest_mgr.from_dict(q_data)
        from datetime import date
        self.quest_mgr.refresh_daily(str(date.today()))

        # 宠物
        pet_info = self.save_mgr.stats.get('hub_pet', {})
        if pet_info:
            self.pet = Pet(pet_info.get('id', 'healing_fairy'), pet_info.get('level', 1))
            self.pet.exp = pet_info.get('exp', 0)
            self.pet.alive = pet_info.get('alive', True)
        else:
            self.pet = Pet('healing_fairy', 1)
            self.pet.alive = True

        # 已解锁区域
        self.unlocked_zones = list(ZONES.keys())
        self.unlocked_floors = self.save_mgr.stats.get('hub_max_floor', 1)

    def on_enter(self):
        self.selected_zone = None
        self.ui_mode = None
        self.flash_texts = []
        # 保存进入城镇的状态
        self._save_hub_state()

    def on_exit(self):
        self._save_hub_state()

    def _save_hub_state(self):
        """保存城镇状态到存档"""
        self.save_mgr.stats['hub_player_level'] = self.player_lv
        self.save_mgr.stats['hub_gold'] = self.player_gold
        self.save_mgr.stats['hub_inventory'] = self.inventory.to_dict()
        self.save_mgr.stats['hub_pet'] = {
            'id': self.pet.pet_id,
            'level': self.pet.level,
            'exp': self.pet.exp,
            'alive': self.pet.alive,
        }
        self.save_mgr.stats['hub_quests'] = self.quest_mgr.to_dict()
        self.save_mgr.stats['hub_max_floor'] = self.unlocked_floors
        self.save_mgr.save_stats()

    def _add_flash(self, text, color=YELLOW):
        self.flash_texts.append({'text': text, 'color': color, 'timer': 120})

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if self.ui_mode:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                        self.ui_mode = None
                        self.selected_quest = 0
                        self.selected_shop_item = 0
                        continue
                    self._handle_ui_key(event)
                else:
                    if event.key == pygame.K_ESCAPE:
                        self.switch_to('menu')
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        self._enter_zone()
                    elif event.key == pygame.K_1:
                        self.selected_zone = 'dungeon'
                        self._enter_zone()
                    elif event.key == pygame.K_2:
                        self.selected_zone = 'shop'
                        self._enter_zone()
                    elif event.key == pygame.K_3:
                        self.selected_zone = 'quest'
                        self._enter_zone()
                    elif event.key == pygame.K_4:
                        self.selected_zone = 'pet'
                        self._enter_zone()
                    elif event.key == pygame.K_5:
                        self.selected_zone = 'storage'
                        self._enter_zone()

            elif event.type == pygame.MOUSEMOTION and not self.ui_mode:
                mx, my = event.pos
                self.hover_zone = None
                for zid, zdata in ZONES.items():
                    rx, ry, rw, rh = zdata['rect']
                    if rx <= mx <= rx + rw and ry <= my <= ry + rh:
                        self.hover_zone = zid
                        break

            elif event.type == pygame.MOUSEBUTTONDOWN and not self.ui_mode:
                mx, my = event.pos
                for zid, zdata in ZONES.items():
                    rx, ry, rw, rh = zdata['rect']
                    if rx <= mx <= rx + rw and ry <= my <= ry + rh:
                        self.selected_zone = zid
                        self._enter_zone()
                        break

    def _handle_ui_key(self, event):
        if self.ui_mode == 'quest_board':
            if event.key == pygame.K_TAB:
                tabs = ['main', 'side', 'dungeon', 'daily']
                idx = tabs.index(self.quest_tab) if self.quest_tab in tabs else 0
                self.quest_tab = tabs[(idx + 1) % len(tabs)]
                self.selected_quest = 0
            elif event.key == pygame.K_UP:
                self.selected_quest = max(0, self.selected_quest - 1)
            elif event.key == pygame.K_DOWN:
                max_q = self._get_quest_list_count()
                self.selected_quest = min(max_q - 1, self.selected_quest + 1)
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                self._accept_or_claim_quest()

    def _get_quest_list_count(self):
        if self.quest_tab == 'main':
            return 1
        elif self.quest_tab == 'side':
            return len(self.quest_mgr.get_available_side_quests()) + len([q for q in self.quest_mgr.quests if q.category == 'side' and q.completed and not q.claimed])
        elif self.quest_tab == 'dungeon':
            return len(self.quest_mgr.get_available_dungeon_quests()) + len([q for q in self.quest_mgr.quests if q.category == 'dungeon' and q.completed and not q.claimed])
        elif self.quest_tab == 'daily':
            return len(self.quest_mgr.daily_quests)

        elif self.ui_mode == 'shop':
            if event.key == pygame.K_UP:
                self.selected_shop_item = max(0, self.selected_shop_item - 1)
            elif event.key == pygame.K_DOWN:
                self.selected_shop_item = min(self._get_shop_items_count() - 1, self.selected_shop_item + 1)
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                self._buy_shop_item()

        elif self.ui_mode == 'pet_house':
            if event.key == pygame.K_r:
                if not self.pet.alive:
                    self.pet.alive = True
                    self.pet.hp = self.pet.max_hp
                    self._add_flash(f'{self.pet.pet_name} 已复活!', GREEN)
            elif event.key == pygame.K_f and self.pet.level < 10:
                cost = 100 * self.pet.level
                if self.player_gold >= cost:
                    self.player_gold -= cost
                    self.pet.add_exp(100)
                    self._add_flash(f'{self.pet.pet_name} 获得经验!', CYAN)
                    evolved = self.pet.check_evolve()
                    if evolved:
                        self._add_flash(f'{self.pet.pet_name} 进化了!', (255, 215, 0))

    def _enter_zone(self):
        zid = self.selected_zone
        if zid == 'dungeon':
            self._enter_dungeon()
        elif zid == 'shop':
            self.ui_mode = 'shop'
            self.selected_shop_item = 0
        elif zid == 'quest':
            self.ui_mode = 'quest_board'
            self.selected_quest = 0
        elif zid == 'pet':
            self.ui_mode = 'pet_house'
        elif zid == 'storage':
            self.ui_mode = 'storage'

    def _enter_dungeon(self):
        """进入地牢"""
        self._save_hub_state()
        from src.entities.character import DIFFICULTY_LEVELS
        diff = min(self.unlocked_floors, 5)
        self.switch_to('gameplay', character_id=self.hub_character_id, difficulty=diff)

    def _get_shop_items_count(self):
        return 6

    def _buy_shop_item(self):
        items = [
            {'id': 'health_potion_m', 'name': '中型生命药水', 'cost': 30,  'desc': '恢复 60 HP'},
            {'id': 'energy_potion',   'name': '能量药水',     'cost': 25,  'desc': '恢复 80 能量'},
            {'id': 'shield_potion',   'name': '护盾药水',     'cost': 35,  'desc': '+40 护盾'},
            {'id': 'bomb',            'name': '炸弹',          'cost': 30,  'desc': '范围伤害 80'},
            {'id': 'speed_potion',    'name': '速度药剂',      'cost': 20,  'desc': '加速 8秒'},
            {'id': 'damage_potion',   'name': '狂暴药剂',      'cost': 40,  'desc': '伤害+50% 8秒'},
        ]
        if 0 <= self.selected_shop_item < len(items):
            item = items[self.selected_shop_item]
            if self.player_gold >= item['cost']:
                added = self.inventory.add_item(item['id'], 1)
                if added > 0:
                    self.player_gold -= item['cost']
                    self._add_flash(f'购买 {item["name"]} 成功!', GREEN)
                else:
                    self._add_flash('背包已满!', RED)
            else:
                self._add_flash('金币不足!', RED)

    def _accept_or_claim_quest(self):
        tab = self.quest_tab

        if tab == 'main':
            # 主线：接取/领取
            mq = self.quest_mgr.get_main_quest()
            if mq is None:
                return
            # 判断是否是Quest实例还是模板dict
            from src.entities.quest import Quest
            if not isinstance(mq, Quest):
                # 未接取，接取
                if self.quest_mgr.add_quest(mq['id']):
                    self._add_flash(f'接取主线: {mq["name"]}', YELLOW)
            else:
                if mq.completed and not mq.claimed:
                    gold, exp, item = self.quest_mgr.claim_quest(mq.template_id)
                    self.player_gold += gold
                    self._add_flash(f'{mq.name} 完成! +{gold}G +{exp}EXP', GREEN)
                    if item and self.inventory:
                        self.inventory.add_item(item, 1)
                    if hasattr(self, 'pet') and self.pet.alive:
                        self.pet.add_exp(exp // 2)
        elif tab == 'side':
            available = self.quest_mgr.get_available_side_quests()
            claimable = [q for q in self.quest_mgr.quests if q.category == 'side' and q.completed and not q.claimed]
            if self.selected_quest < len(available):
                tpl = available[self.selected_quest]
                if self.quest_mgr.add_quest(tpl['id']):
                    self._add_flash(f'接取支线: {tpl["name"]}', YELLOW)
            else:
                ci = self.selected_quest - len(available)
                if 0 <= ci < len(claimable):
                    q = claimable[ci]
                    gold, exp, item = self.quest_mgr.claim_quest(q.template_id)
                    self.player_gold += gold
                    self._add_flash(f'{q.name} 完成! +{gold}G +{exp}EXP', GREEN)
                    if item and self.inventory:
                        self.inventory.add_item(item, 1)
                    if hasattr(self, 'pet') and self.pet.alive:
                        self.pet.add_exp(exp // 2)
        elif tab == 'dungeon':
            available = self.quest_mgr.get_available_dungeon_quests()
            claimable = [q for q in self.quest_mgr.quests if q.category == 'dungeon' and q.completed and not q.claimed]
            if self.selected_quest < len(available):
                tpl = available[self.selected_quest]
                if self.quest_mgr.add_quest(tpl['id']):
                    self._add_flash(f'接取副本: {tpl["name"]}', YELLOW)
            else:
                ci = self.selected_quest - len(available)
                if 0 <= ci < len(claimable):
                    q = claimable[ci]
                    gold, exp, item = self.quest_mgr.claim_quest(q.template_id)
                    self.player_gold += gold
                    self._add_flash(f'{q.name} 完成! +{gold}G +{exp}EXP', GREEN)
                    if item and self.inventory:
                        self.inventory.add_item(item, 1)
        elif tab == 'daily':
            claimable = [q for q in self.quest_mgr.daily_quests if q.completed and not q.claimed]
            if 0 <= self.selected_quest < len(claimable):
                q = claimable[self.selected_quest]
                gold, exp, item = self.quest_mgr.claim_quest(q.template_id)
                self.player_gold += gold
                self._add_flash(f'{q.name} +{gold}G +{exp}EXP', GREEN)

    def update(self):
        self.anim_timer += 0.04
        # 闪烁文本
        for ft in self.flash_texts[:]:
            ft['timer'] -= 1
            if ft['timer'] <= 0:
                self.flash_texts.remove(ft)

    def draw(self):
        self.screen.fill((25, 20, 35))

        # 背景装饰（地板、柱子）
        self._draw_background()

        # 各区域
        for zid, zdata in ZONES.items():
            self._draw_zone_card(zid, zdata)

        # 玩家角色（中心偏下）
        self._draw_player()

        # 底部状态栏
        self._draw_status_bar()

        # 浮动提示
        self._draw_flash_texts()

        # 如果进入子界面
        if self.ui_mode == 'quest_board':
            self._draw_quest_board()
        elif self.ui_mode == 'shop':
            self._draw_shop()
        elif self.ui_mode == 'pet_house':
            self._draw_pet_house()
        elif self.ui_mode == 'storage':
            self._draw_storage()

    def _draw_flash_texts(self):
        """显示浮动提示文本"""
        y = 100
        for ft in self.flash_texts:
            alpha = min(255, ft['timer'] * 3)
            color = (*ft['color'][:3], alpha) if len(ft['color']) == 3 else ft['color']
            self.game.draw_text(ft['text'], WINDOW_WIDTH // 2, y, color, size=18, center=True)
            y += 28

    def _draw_shop(self):
        """商店界面"""
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        pw, ph = 520, 440
        px, py = (WINDOW_WIDTH - pw) // 2, (WINDOW_HEIGHT - ph) // 2
        pygame.draw.rect(self.screen, (30, 25, 35), (px, py, pw, ph))
        pygame.draw.rect(self.screen, (180, 160, 100), (px, py, pw, ph), 2)

        self.game.draw_text('\u5546 \u5e97', px + pw // 2, py + 15, (255, 215, 0), size=28, center=True)
        self.game.draw_text(f'\u91d1\u5e01: {self.player_gold}', px + pw - 100, py + 20, (255, 200, 50), size=16)

        items = [
            {'id': 'health_potion_m', 'name': '\u4e2d\u578b\u751f\u547d\u836f\u6c34', 'cost': 30,  'desc': '\u6062\u590d 60 HP',       'color': (255, 80, 80)},
            {'id': 'energy_potion',   'name': '\u80fd\u91cf\u836f\u6c34',     'cost': 25,  'desc': '\u6062\u590d 80 \u80fd\u91cf',    'color': (100, 150, 255)},
            {'id': 'shield_potion',   'name': '\u62a4\u76fe\u836f\u6c34',     'cost': 35,  'desc': '+40 \u62a4\u76fe',       'color': (80, 180, 255)},
            {'id': 'bomb',            'name': '\u70b8\u5f39',          'cost': 30,  'desc': '\u8303\u56f4\u4f24\u5bb3 80',     'color': (60, 60, 60)},
            {'id': 'speed_potion',    'name': '\u901f\u5ea6\u836f\u5242',      'cost': 20,  'desc': '\u52a0\u901f 8\u79d2',       'color': (255, 255, 100)},
        ]

        y = py + 60
        for i, item in enumerate(items):
            is_sel = (i == self.selected_shop_item)
            bg = (50, 50, 65) if is_sel else None
            if bg:
                pygame.draw.rect(self.screen, bg, (px + 30, y, pw - 60, 42))
            if is_sel:
                pygame.draw.rect(self.screen, (255, 215, 0), (px + 30, y, pw - 60, 42), 1)
            pygame.draw.rect(self.screen, item['color'], (px + 40, y + 6, 28, 28))
            pygame.draw.rect(self.screen, (255, 255, 255), (px + 40, y + 6, 28, 28), 1)
            self.game.draw_text(item['name'], px + 80, y + 5, (255, 255, 255), size=16)
            self.game.draw_text(item['desc'], px + 80, y + 25, (140, 140, 140), size=12)
            can_afford = self.player_gold >= item['cost']
            cost_color = (255, 255, 255) if can_afford else (255, 50, 50)
            self.game.draw_text(f'{item["cost"]}G', px + pw - 70, y + 8, cost_color, size=16)
            if is_sel:
                self.game.draw_text('[\u56de\u8f66\u8d2d\u4e70]' if can_afford else '[\u91d1\u5e01\u4e0d\u8db3]',
                                    px + pw - 80, y + 26, (100, 200, 100) if can_afford else (255, 80, 80), size=11)
            y += 48

        self.game.draw_text('\u2191\u2193 \u9009\u62e9  |  \u56de\u8f66\u8d2d\u4e70  |  ESC/Q \u8fd4\u56de',
                            px + pw // 2, py + ph - 18, (120, 120, 120), size=13, center=True)

    def _draw_pet_house(self):
        """宠物小屋界面"""
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        pw, ph = 500, 400
        px, py = (WINDOW_WIDTH - pw) // 2, (WINDOW_HEIGHT - ph) // 2
        pygame.draw.rect(self.screen, (25, 30, 40), (px, py, pw, ph))
        pygame.draw.rect(self.screen, (120, 180, 200), (px, py, pw, ph), 2)

        self.game.draw_text('\u5ba0 \u7269 \u5c0f \u5c4b', px + pw // 2, py + 20, (100, 200, 255), size=26, center=True)

        pet = self.pet
        alive_text = '\u5b58\u6d3b' if pet.alive else '\u9635\u4ea1'
        alive_color = (100, 255, 100) if pet.alive else (255, 50, 50)
        self.game.draw_text(f'{pet.pet_name}  Lv.{pet.level}', px + pw // 2, py + 60,
                            pet.color if pet.alive else (255, 50, 50), size=22, center=True)
        self.game.draw_text(alive_text, px + pw // 2, py + 82, alive_color, size=16, center=True)

        if pet.alive:
            hp_pct = pet.hp / pet.max_hp if pet.max_hp > 0 else 0
            bar_x, bar_y, bar_w = px + 100, py + 100, 300
            pygame.draw.rect(self.screen, (40, 40, 50), (bar_x, bar_y, bar_w, 12))
            pygame.draw.rect(self.screen, (100, 220, 100), (bar_x, bar_y, int(bar_w * hp_pct), 12))
            self.game.draw_text(f'HP: {pet.hp}/{pet.max_hp}', bar_x + bar_w // 2, bar_y + 18,
                                (255, 255, 255), size=12, center=True)

            exp_pct = pet.exp / pet.exp_to_next if pet.exp_to_next > 0 else 0
            self.game.draw_text(f'\u7ecf\u9a8c: {pet.exp}/{pet.exp_to_next}',
                                px + pw // 2, bar_y + 36, (150, 200, 255), size=13, center=True)
            pygame.draw.rect(self.screen, (40, 40, 50), (bar_x, bar_y + 50, bar_w, 8))
            pygame.draw.rect(self.screen, (100, 180, 255), (bar_x, bar_y + 50, int(bar_w * exp_pct), 8))

        feed_cost = 100 * pet.level
        y = py + 200
        self.game.draw_text(f'[R] \u590d\u6d3b\u5ba0\u7269' if not pet.alive else '',
                            px + pw // 2, y, (100, 255, 100), size=16, center=True)
        self.game.draw_text(f'[F] \u5582\u98df\u8bad\u7ec3  ({feed_cost}G  +100\u7ecf\u9a8c)',
                            px + pw // 2, y + 25, (100, 200, 255), size=15, center=True)
        self.game.draw_text(f'\u653b\u51fb\u529b: {pet.attack}  |  \u901f\u5ea6: {pet.speed}',
                            px + pw // 2, y + 50, (200, 200, 200), size=14, center=True)

        self.game.draw_text('ESC/Q \u8fd4\u56de', px + pw // 2, py + ph - 18, (120, 120, 120), size=13, center=True)

    def _draw_storage(self):
        """仓库/背包界面"""
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        pw, ph = 550, 460
        px, py = (WINDOW_WIDTH - pw) // 2, (WINDOW_HEIGHT - ph) // 2
        pygame.draw.rect(self.screen, (30, 28, 35), (px, py, pw, ph))
        pygame.draw.rect(self.screen, (160, 140, 100), (px, py, pw, ph), 2)

        self.game.draw_text('\u4ed3 \u5e93', px + pw // 2, py + 18, (255, 215, 0), size=26, center=True)
        self.game.draw_text(f'\u7269\u54c1: {len(self.inventory.items)}/{self.inventory.max_slots}',
                            px + pw - 100, py + 22, (140, 140, 140), size=14)

        y = py + 55
        if not self.inventory.items:
            self.game.draw_text('\u80cc\u5305\u662f\u7a7a\u7684', px + pw // 2, y + 30, (100, 100, 100), size=18, center=True)
        else:
            for i, item in enumerate(self.inventory.items):
                if y > py + ph - 50:
                    break
                icon_color = item.defn.get('icon_color', (200, 200, 200))
                pygame.draw.rect(self.screen, icon_color, (px + 30, y, 22, 22))
                pygame.draw.rect(self.screen, (255, 255, 255), (px + 30, y, 22, 22), 1)
                self.game.draw_text(item.name, px + 60, y + 1, (255, 255, 255), size=15)
                if item.quantity > 1:
                    self.game.draw_text(f'x{item.quantity}', px + 60 + 100, y + 1, (140, 140, 140), size=14)
                self.game.draw_text(item.defn.get('desc', ''), px + 60, y + 18, (140, 140, 140), size=11)
                y += 34

        self.game.draw_text('ESC/Q \u8fd4\u56de', px + pw // 2, py + ph - 18, (120, 120, 120), size=13, center=True)

    def _draw_background(self):
        """绘制城镇背景"""
        # 地面
        self.game.draw_rect(0, 300, WINDOW_WIDTH, 420, (35, 30, 45))
        # 地板网格
        for x in range(0, WINDOW_WIDTH, 60):
            for y in range(300, 720, 40):
                alpha = 10 if (x + y) % 120 == 0 else 5
                self.game.draw_rect(x, y, 60, 40, (50, 45, 60), alpha=alpha)
        # 装饰柱子
        for px in [100, 1180]:
            self.game.draw_rect(px, 280, 16, 200, (60, 55, 70))
            self.game.draw_rect(px - 4, 270, 24, 16, (80, 75, 90))
        # 顶部光效
        self.game.draw_rect(0, 0, WINDOW_WIDTH, 3, (100, 120, 160), alpha=40)

    def _draw_zone_card(self, zid, zdata):
        """绘制可交互区域卡片"""
        rx, ry, rw, rh = zdata['rect']
        is_hover = (self.hover_zone == zid)
        is_selected = (self.selected_zone == zid and not self.ui_mode)

        # 卡片背景
        alpha = 40 if not is_hover else 70
        border_color = zdata['color'] if is_hover else (60, 60, 80)
        border_w = 2 if is_hover else 1
        self.game.draw_rect(rx, ry, rw, rh, (20, 20, 35), alpha=alpha)
        pygame.draw.rect(self.screen, border_color, (rx, ry, rw, rh), border_w)

        # 悬停光效
        if is_hover:
            glow_alpha = int(30 + 20 * math.sin(self.anim_timer * 2))
            pygame.draw.rect(self.screen, (*zdata['color'], glow_alpha),
                             (rx - 1, ry - 1, rw + 2, rh + 2), 1)

        # 图标
        icon_size = int(50 + 5 * math.sin(self.anim_timer * 0.5 + hash(zid) % 10))
        self.game.draw_text(zdata['icon'], rx + rw // 2, ry + rh // 2 - 15,
                            zdata['color'], size=icon_size, center=True)

        # 名字
        self.game.draw_text(zdata['name'], rx + rw // 2, ry + rh // 2 + 30,
                            WHITE if is_hover else GRAY, size=18, center=True)

        # 下标快捷键
        shortcut_map = {'dungeon': '1', 'shop': '2', 'quest': '3', 'pet': '4', 'storage': '5'}
        if zid in shortcut_map:
            self.game.draw_text(shortcut_map[zid], rx + rw - 20, ry + 8,
                                (80, 80, 100), size=12, center=True)

    def _draw_player(self):
        """绘制城镇中的玩家"""
        px, py = WINDOW_WIDTH // 2, 330

        # 角色光效
        glow_r = 30 + int(5 * math.sin(self.anim_timer * 1.5))
        pygame.draw.circle(self.screen, (80, 100, 160, 40),
                           (px, py + 15), glow_r, 2)

        # 身体（简单绘制）
        body_color = (50, 100, 220)
        body_rect = (px - 12, py - 14, 24, 28)
        pygame.draw.rect(self.screen, body_color, body_rect)
        # 头
        pygame.draw.circle(self.screen, (255, 220, 180),
                          (px, py - 18), 10)
        # 等级
        self.game.draw_text(f'Lv.{self.player_lv}', px + 20, py - 10, (100, 255, 100), size=12)

        # 宠物
        if hasattr(self, 'pet') and self.pet.alive:
            pet_x = px + 35 + int(8 * math.sin(self.anim_timer))
            pet_y = py + 5 + int(3 * math.sin(self.anim_timer * 0.7))
            pygame.draw.circle(self.screen, self.pet.color,
                              (pet_x, pet_y), 10)
            pygame.draw.circle(self.screen, (255, 255, 255),
                              (pet_x - 3, pet_y - 3), 2)
            pygame.draw.circle(self.screen, (255, 255, 255),
                              (pet_x + 3, pet_y - 3), 2)

    def _draw_status_bar(self):
        """底部状态栏"""
        bar_y = WINDOW_HEIGHT - 50
        self.game.draw_rect(0, bar_y, WINDOW_WIDTH, 50, (15, 15, 30), alpha=200)

        # 金币
        self.game.draw_text(f'💰 {self.player_gold}', 30, bar_y + 14, (255, 200, 50), size=20)
        # 楼层进度
        self.game.draw_text(f'[MAP] 已探索 {self.unlocked_floors}/{ZONES.get("dungeon", {}).get("max_floor", 12)} 层',
                            250, bar_y + 14, CYAN, size=16)
        # 背包容量
        self.game.draw_text(f'[BAG] {len(self.inventory.items)}/{self.inventory.max_slots}',
                            600, bar_y + 14, (180, 160, 120), size=16)
        # 宠物状态
        if self.pet.alive:
            self.game.draw_text(f'🐾 {self.pet.pet_name} Lv.{self.pet.level}',
                                800, bar_y + 14, self.pet.color, size=16)
        else:
            self.game.draw_text('🐾 宠物已阵亡', 800, bar_y + 14, RED, size=16)
        # 快捷键提示
        self.game.draw_text('ESC 返回菜单  |  1~5 快捷键  |  点击交互', WINDOW_WIDTH // 2, bar_y + 34,
                            GRAY, size=12, center=True)

    def _draw_quest_board(self):
        """任务告示板 - 主线/支线/副本分类"""
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        pw, ph = 700, 520
        px, py = (WINDOW_WIDTH - pw) // 2, (WINDOW_HEIGHT - ph) // 2
        pygame.draw.rect(self.screen, (28, 25, 38), (px, py, pw, ph))
        pygame.draw.rect(self.screen, (100, 90, 70), (px, py, pw, ph), 2)

        self.game.draw_text('\u8d23\u4efb\u544a\u793a\u677f', px + pw // 2, py + 18, (255, 215, 0), size=26, center=True)

        # Tab 切换
        tabs = [('\u4e3b\u7ebf\u6545\u4e8b', 'main'), ('\u652f\u7ebf\u4efb\u52a1', 'side'),
                ('\u526f\u672c\u6311\u6218', 'dungeon'), ('\u6bcf\u65e5\u4efb\u52a1', 'daily')]
        tab_w = 150
        tab_y = py + 48
        tab_h = 28
        current_tab = getattr(self, 'quest_tab', 'main')

        for i, (tname, tid) in enumerate(tabs):
            tx = px + 30 + i * (tab_w + 5)
            is_sel = (tid == current_tab)
            bg = (50, 45, 60) if is_sel else (35, 32, 45)
            self.game.draw_rect(tx, tab_y, tab_w, tab_h, bg)
            pygame.draw.rect(self.screen, (180, 170, 120) if is_sel else (70, 65, 80), (tx, tab_y, tab_w, tab_h), 1 if not is_sel else 2)
            self.game.draw_text(tname, tx + tab_w // 2, tab_y + tab_h // 2,
                                (255, 215, 0) if is_sel else (180, 180, 180), size=14, center=True)

        self.quest_tab = current_tab
        y = tab_y + tab_h + 12

        # 根据tab显示不同内容
        if current_tab == 'main':
            self._draw_main_quest_board(px, py, pw, ph, y)
        elif current_tab == 'side':
            self._draw_side_quest_board(px, py, pw, ph, y)
        elif current_tab == 'dungeon':
            self._draw_dungeon_quest_board(px, py, pw, ph, y)
        elif current_tab == 'daily':
            self._draw_daily_quest_board(px, py, pw, ph, y)

        self.game.draw_text('\u2194 Tab \u5207\u6362 | \u2191\u2193 \u9009\u62e9 | \u56de\u8f66\u63a5\u53d6 | ESC/Q \u8fd4\u56de',
                            px + pw // 2, py + ph - 18, (120, 120, 120), size=12, center=True)

    def _draw_main_quest_board(self, px, py, pw, ph, start_y):
        """主线任务面板"""
        main_q = self.quest_mgr.get_main_quest()
        if main_q is None:
            self.game.draw_text('* 主线故事已全部完成 *', px + pw // 2, start_y + 40,
                                (255, 215, 0), size=20, center=True)
            self.game.draw_text('你已成功封印了深渊，艾尔迪亚大陆恢复了平静...',
                                px + pw // 2, start_y + 80, (180, 180, 180), size=14, center=True)
            return

        # 判断是 Quest 实例还是模板字典
        is_quest = hasattr(main_q, 'data') and hasattr(main_q, 'template_id')

        if is_quest:
            q = main_q
            data = q.data
            ch = data.get('chapter', '?')
            self.game.draw_text(f'第 {ch} 章：{q.name}', px + 30, start_y, (255, 215, 0), size=20)
            self.game.draw_text(q.desc, px + 30, start_y + 28, (200, 200, 200), size=13)
            self.game.draw_text(f'奖励: 金币+{q.reward_gold}  经验+{q.reward_exp}',
                                px + 30, start_y + 50, (150, 200, 150), size=13)

            # 目标进度
            y = start_y + 75
            objs = q.objectives
            obj_names = {'reach_floor': '到达层数', 'kill_boss': '击败 Boss',
                         'kill': '击杀', 'collect': '收集', 'explore': '探索'}
            for i, obj in enumerate(objs):
                oname = obj_names.get(obj['type'], obj['type'])
                text = f'{i+1}. {oname}: {obj.get("count", 1)}'
                self.game.draw_text(text, px + 50, y, (180, 180, 220), size=13)
                y += 22

            # 故事文本
            if q.story_text:
                y += 5
                lines = []
                s = q.story_text
                while len(s) > 50:
                    idx = s.rfind('，', 0, 50)
                    if idx == -1: idx = s.rfind('。', 0, 50)
                    if idx == -1: idx = 50
                    lines.append(s[:idx+1])
                    s = s[idx+1:]
                if s: lines.append(s)
                for line in lines:
                    self.game.draw_text(line.strip(), px + 50, y, (140, 140, 160), size=11)
                    y += 16

            if q.completed:
                self.game.draw_text('[已完成] 回车领取奖励', px + pw - 180, start_y + 170,
                                    (100, 255, 100), size=14)
        else:
            # 未接取的模板（字典）
            qdata = main_q
            self.game.draw_text(f'第 {qdata["chapter"]} 章：{qdata["name"]}', px + 30, start_y, (255, 215, 0), size=20)
            self.game.draw_text(qdata['desc'], px + 30, start_y + 28, (200, 200, 200), size=13)
            self.game.draw_text(f'奖励: 金币+{qdata["reward_gold"]}  经验+{qdata["reward_exp"]}',
                                px + 30, start_y + 50, (150, 200, 150), size=13)
            self.game.draw_text('[回车] 接取主线任务', px + pw - 160, start_y + 50,
                                (100, 200, 100), size=14)

            # 目标预览
            y = start_y + 75
            for i, obj in enumerate(qdata.get('objectives', [])):
                oname = {'reach_floor': '到达层数', 'kill_boss': '击败 Boss',
                         'kill': '击杀', 'collect': '收集'}.get(obj['type'], obj['type'])
                self.game.draw_text(f'{i+1}. {oname}: {obj.get("count", 1)}', px + 50, y, (180, 180, 220), size=13)
                y += 20

            # 故事文本
            story = qdata.get('story_text', '')
            if story:
                y += 5
                while len(story) > 50:
                    idx = story.rfind('，', 0, 50)
                    if idx == -1: idx = story.rfind('。', 0, 50)
                    if idx == -1: idx = 50
                    self.game.draw_text(story[:idx+1].strip(), px + 50, y, (140, 140, 160), size=11)
                    story = story[idx+1:]
                    y += 16
                if story:
                    self.game.draw_text(story.strip(), px + 50, y, (140, 140, 160), size=11)
    def _draw_side_quest_board(self, px, py, pw, ph, start_y):
        """支线任务面板"""
        available = self.quest_mgr.get_available_side_quests()
        active = [q for q in self.quest_mgr.quests if q.category == 'side' and not q.claimed]
        claimable = [q for q in self.quest_mgr.quests if q.category == 'side' and q.completed and not q.claimed]

        # 可接取
        self.game.draw_text('\u2014 \u53ef\u63a5\u53d6\u7684\u652f\u7ebf \u2014', px + pw // 2, start_y, (100, 200, 255), size=15, center=True)
        y = start_y + 22
        if not available:
            self.game.draw_text('\u6682\u65e0\u53ef\u63a5\u4efb\u52a1', px + pw // 2, y + 5, (100, 100, 100), size=14, center=True)
            y += 30
        else:
            for i, tpl in enumerate(available):
                is_sel = (i == self.selected_quest and self.selected_quest < len(available))
                bg = (45, 42, 55) if is_sel else None
                if bg:
                    pygame.draw.rect(self.screen, bg, (px + 20, y, pw - 40, 44))
                if is_sel:
                    pygame.draw.rect(self.screen, (100, 200, 255), (px + 20, y, pw - 40, 44), 1)
                self.game.draw_text(tpl['name'], px + 35, y + 2, (255, 255, 255) if is_sel else (200, 200, 200), size=15)
                self.game.draw_text(tpl['giver'], px + pw - 120, y + 2, (140, 140, 160), size=11)
                self.game.draw_text(tpl['desc'], px + 35, y + 20, (150, 150, 150), size=11)
                self.game.draw_text(f'+{tpl["reward_gold"]}G', px + pw - 70, y + 20, (255, 200, 50), size=12)
                y += 50

        # 已完成待领取
        if claimable:
            y += 5
            self.game.draw_text('\u2014 \u5f85\u9886\u53d6 \u2014', px + pw // 2, y, (100, 255, 100), size=14, center=True)
            y += 20
            for q in claimable:
                self.game.draw_text(f'\u2713 {q.name}', px + 50, y, (150, 255, 150), size=14)
                self.game.draw_text('[\u56de\u8f66\u9886\u53d6]', px + pw - 120, y, (100, 200, 100), size=12)
                y += 28

        # 进行中
        if active:
            y += 5
            self.game.draw_text('\u2014 \u8fdb\u884c\u4e2d \u2014', px + pw // 2, y, (255, 180, 80), size=14, center=True)
            y += 20
            for q in active:
                self.game.draw_text(f'{q.name}  {q.get_progress_text()}', px + 50, y, (200, 200, 200), size=13)
                y += 22

    def _draw_dungeon_quest_board(self, px, py, pw, ph, start_y):
        """副本任务面板"""
        available = self.quest_mgr.get_available_dungeon_quests()
        active = [q for q in self.quest_mgr.quests if q.category == 'dungeon' and not q.claimed]
        claimable = [q for q in self.quest_mgr.quests if q.category == 'dungeon' and q.completed and not q.claimed]

        self.game.draw_text('\u2014 \u526f\u672c\u6311\u6218 \u2014', px + pw // 2, start_y, (255, 180, 100), size=15, center=True)
        y = start_y + 22
        if not available and not active:
            self.game.draw_text('\u6682\u65e0\u526f\u672c\u4efb\u52a1', px + pw // 2, y + 5, (100, 100, 100), size=14, center=True)
            y += 30
        else:
            for i, tpl in enumerate(available):
                is_sel = (i == self.selected_quest and self.selected_quest < len(available))
                bg = (45, 42, 55) if is_sel else None
                if bg:
                    pygame.draw.rect(self.screen, bg, (px + 20, y, pw - 40, 42))
                if is_sel:
                    pygame.draw.rect(self.screen, (255, 180, 100), (px + 20, y, pw - 40, 42), 1)
                tier_stars = '\u2605' * tpl.get('tier', 1)
                self.game.draw_text(f'{tier_stars} {tpl["name"]}', px + 35, y + 2, (255, 255, 255) if is_sel else (200, 200, 200), size=15)
                self.game.draw_text(tpl['desc'], px + 35, y + 20, (150, 150, 150), size=11)
                self.game.draw_text(f'+{tpl["reward_gold"]}G', px + pw - 70, y + 2, (255, 200, 50), size=13)
                y += 48

        if claimable:
            y += 5
            self.game.draw_text('\u2014 \u5f85\u9886\u53d6 \u2014', px + pw // 2, y, (100, 255, 100), size=14, center=True)
            y += 20
            for q in claimable:
                self.game.draw_text(f'\u2713 {q.name}', px + 50, y, (150, 255, 150), size=14)
                y += 26

        if active:
            y += 5
            n = y
            for q in active:
                self.game.draw_text(f'{q.name}  {q.get_progress_text()}', px + 50, n, (200, 200, 200), size=13)
                n += 22

    def _draw_daily_quest_board(self, px, py, pw, ph, start_y):
        """每日任务面板"""
        daily = self.quest_mgr.daily_quests
        self.game.draw_text('\u2014 \u6bcf\u65e5\u4efb\u52a1 \u2014', px + pw // 2, start_y, (150, 220, 100), size=15, center=True)
        y = start_y + 22

        if not daily:
            self.game.draw_text('\u6ca1\u6709\u53ef\u7528\u7684\u6bcf\u65e5\u4efb\u52a1', px + pw // 2, y + 10, (100, 100, 100), size=14, center=True)
        else:
            for i, q in enumerate(daily):
                self.game.draw_text(f'{q.name}', px + 40, y, (220, 220, 220), size=15)
                self.game.draw_text(q.desc, px + 40, y + 18, (150, 150, 150), size=12)
                if q.completed and not q.claimed:
                    self.game.draw_text('[\u5df2\u5b8c\u6210]', px + pw - 100, y, (100, 255, 100), size=13)
                    self.game.draw_text('\u56de\u8f66\u9886\u53d6', px + pw - 100, y + 18, (150, 150, 150), size=11)
                elif q.completed:
                    self.game.draw_text('\u2713', px + pw - 60, y, (100, 255, 100), size=18)
                else:
                    self.game.draw_text(f'{q.get_progress_text()}', px + pw - 100, y, (200, 200, 200), size=13)
                    self.game.draw_text(f'+{q.reward_gold}G', px + pw - 100, y + 18, (255, 200, 50), size=12)
                y += 45