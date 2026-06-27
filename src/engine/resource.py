"""
资源管理器 - 加载外部精灵图素材，回退到程序化生成
"""
import os
import glob
import random
import math
import pygame
from settings import TILE_SIZE

ASSET_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assets')
TILESET_DIR = os.path.join(ASSET_DIR, 'tileset')


class ResourceManager:
    """管理所有游戏素材：优先加载外部素材，回退到程序化生成"""

    def __init__(self):
        self.sprites = {}
        self._loaded = False

    # ==================== 公共接口 ====================

    def ensure_loaded(self):
        """确保素材已加载（懒加载）"""
        if not self._loaded:
            self._load_all()
            self._loaded = True

    def get(self, key):
        self.ensure_loaded()
        return self.sprites.get(key)

    def get_player_frames(self, name):
        self.ensure_loaded()
        return self.sprites.get(f'player_{name}')

    def get_enemy_frames(self, name):
        self.ensure_loaded()
        return self.sprites.get(f'enemy_{name}')

    def get_tile(self, name):
        self.ensure_loaded()
        return self.sprites.get(f'tile_{name}')

    def get_weapon_icon(self, name):
        self.ensure_loaded()
        return self.sprites.get(f'weapon_{name}')

    def get_bullet_sprite(self, name):
        self.ensure_loaded()
        return self.sprites.get(f'bullet_{name}')

    def get_item_sprite(self, name):
        self.ensure_loaded()
        return self.sprites.get(f'item_{name}')

    # ==================== 主加载流程 ====================

    def _load_all(self):
        """加载所有素材"""
        self._load_dcss_tiles()
        self._fill_missing_player()
        self._fill_missing_enemies()
        self._fill_missing_weapons()
        self._fill_missing_bullets()
        self._fill_missing_items()
        self._fill_missing_tiles()

    # ==================== DCSS 图集加载 ====================

    def _load_dcss_tiles(self):
        """从 assets/tileset/ 加载所有 PNG 到 sprites 字典"""
        if not os.path.isdir(TILESET_DIR):
            print(f"[Resource] Tileset dir not found: {TILESET_DIR}")
            return

        count = 0
        for root, dirs, files in os.walk(TILESET_DIR):
            for fname in files:
                if not fname.lower().endswith('.png'):
                    continue
                full = os.path.join(root, fname)
                try:
                    img = pygame.image.load(full).convert_alpha()
                except Exception as e:
                    print(f"[Resource] Failed to load {fname}: {e}")
                    continue

                # 按目录+文件名建立多级索引
                rel = os.path.relpath(full, TILESET_DIR).replace('\\', '/')
                parts = rel.split('/')
                name_no_ext = os.path.splitext(fname)[0]

                # dcss_<category>_<name>
                category = parts[0] if len(parts) >= 1 else 'misc'
                key = f'dcss_{category}_{name_no_ext}'
                self.sprites[key] = img

                # 也存一份去掉编号的版本，方便匹配
                base_name = name_no_ext.split('_')[0] if '_' in name_no_ext else name_no_ext
                alt_key = f'dcss_{category}_{base_name}'
                if alt_key not in self.sprites:
                    self.sprites[alt_key] = img

                count += 1

        print(f"[Resource] Loaded {count} DCSS tiles")

    # ==================== 映射规则：DCSS 文件名 → 游戏概念 ====================

    _ENEMY_MAP = {
        'soldier':       ('dcss_monster_human',        ['dcss_monster_human', 'dcss_monster_centaur']),
        'archer':        ('dcss_monster_centaur',      ['dcss_monster_centaur']),
        'mage_enemy':    ('dcss_monster_necromancer',  ['dcss_monster_necromancer', 'dcss_monster_demonspawn']),
        'bomber':        ('dcss_monster_orc',          ['dcss_monster_orc']),
        'shield_guard':  ('dcss_monster_iron',         ['dcss_monster_iron', 'dcss_monster_golem']),
        'assassin_enemy':('dcss_monster_kobold',       ['dcss_monster_kobold']),
        'summoner':      ('dcss_monster_demonspawn',   ['dcss_monster_demonspawn']),
        'fire_mage':     ('dcss_monster_efreet',       ['dcss_monster_efreet', 'dcss_monster_fire']),
        'heavy_gunner':  ('dcss_monster_centaur',      ['dcss_monster_centaur']),
        'necromancer':   ('dcss_monster_necromancer',   ['dcss_monster_necromancer']),
        'elite_knight':  ('dcss_monster_knight',       ['dcss_monster_knight', 'dcss_monster_paladin']),
        'ice_witch':     ('dcss_monster_ice',          ['dcss_monster_ice']),
        'mimic':         ('dcss_monster_mimic',        ['dcss_monster_mimic', 'dcss_monster_chest']),
        'ghost':         ('dcss_monster_ghost',        ['dcss_monster_ghost', 'dcss_monster_wraith']),
        'goblin':        ('dcss_monster_goblin',       ['dcss_monster_goblin', 'dcss_monster_kobold']),
        'boss_knight':   ('dcss_monster_unique',       ['dcss_monster_unique']),
        'boss_mage':     ('dcss_monster_demonspawn',   ['dcss_monster_demonspawn']),
        'boss_dragon':   ('dcss_monster_dragon',       ['dcss_monster_dragon']),
        'boss_mech':     ('dcss_monster_golem',        ['dcss_monster_golem', 'dcss_monster_iron']),
    }

    _FLOOR_MAP = {
        'floor':           ['dcss_dungeon_floor_floor', 'dcss_dungeon_floor_black_cobalt'],
        'floor_alt':       ['dcss_dungeon_floor_floor', 'dcss_dungeon_floor_green_crystal'],
        'wall':            ['dcss_dungeon_wall_stone', 'dcss_dungeon_wall_wall'],
        'wall_top':        ['dcss_dungeon_wall_wall'],
        'door':            ['dcss_dungeon_doors_door'],
        'boss_room_floor': ['dcss_dungeon_floor_blood'],
        'chest_room_floor':['dcss_dungeon_floor_gold'],
        'shop_floor':      ['dcss_dungeon_floor_shop', 'dcss_dungeon_floor_floor'],
        'hidden_wall':     ['dcss_dungeon_wall_under', 'dcss_dungeon_wall_stone'],
        'secret_floor':    ['dcss_dungeon_floor_floor', 'dcss_dungeon_floor_rough'],
    }

    # ==================== 回退生成（找不到外部素材时） ====================

    def _try_dcss(self, candidates):
        """尝试从 DCSS 加载，返回第一个找到的 Surface"""
        for key in candidates:
            img = self.sprites.get(key)
            if img:
                return img
        return None

    def _fill_missing_player(self):
        """补充/加载玩家角色精灵"""
        # 从 DCSS player 目录找角色
        # dcss_player 下是零件，我们需要合成；或者从 monster 找人类
        player_names = ['knight', 'ranger', 'mage', 'assassin', 'paladin', 'engineer']
        for name in player_names:
            if self.sprites.get(f'player_{name}'):
                continue
            # 用 monster 中的人类作为通用替代
            src = self._try_dcss([
                'dcss_monster_human', 'dcss_monster_centaur',
                'dcss_player_base_human', 'dcss_player_body_chain'
            ])
            if src:
                # 4 方向帧：同一个图重复 4 次
                frames = [src, src, src, src]
            else:
                frames = self._generate_player_fallback(name)
            self.sprites[f'player_{name}'] = frames

    def _generate_player_fallback(self, name):
        """程序化生成不同职业的区别精灵"""
        s = TILE_SIZE
        colors = {
            'knight': (50, 100, 220), 'ranger': (50, 180, 80),
            'mage': (180, 60, 200), 'assassin': (60, 60, 80),
            'paladin': (255, 215, 0), 'engineer': (200, 150, 50),
        }
        color = colors.get(name, (100, 100, 100))
        frames = []
        for _ in range(4):
            surf = pygame.Surface((s, s), pygame.SRCALPHA)
            cx, cy = s//2, s//2
            if name == 'knight':
                # 骑士 - 盔甲+剑盾
                pygame.draw.rect(surf, color, (cx-10, cy-8, 20, 20))  # 躯体
                pygame.draw.rect(surf, (200,200,220), (cx-12, cy-10, 24, 4))  # 肩甲
                pygame.draw.rect(surf, (180,180,200), (cx-6, cy-14, 12, 6))  # 头盔
                pygame.draw.rect(surf, (150,150,170), (cx+8, cy-4, 6, 12))  # 剑
                pygame.draw.circle(surf, (80,80,120), (cx-8, cy), 6)  # 盾
            elif name == 'ranger':
                # 游侠 - 披风+弓
                pygame.draw.rect(surf, color, (cx-8, cy-6, 16, 16))
                pygame.draw.polygon(surf, (30,100,50), [(cx-6, cy-12), (cx-6, cy-4), (cx-14, cy-8)])
                pygame.draw.line(surf, (120,100,60), (cx+6, cy-8), (cx-4, cy+4), 2)
                pygame.draw.circle(surf, (255,200,150), (cx, cy-10), 4)
            elif name == 'mage':
                # 法师 - 长袍+法杖
                pygame.draw.rect(surf, color, (cx-7, cy-4, 14, 14))
                pygame.draw.polygon(surf, (120,40,160), [(cx-10, cy-8), (cx+10, cy-8), (cx, cy-16)])
                pygame.draw.line(surf, (100,60,120), (cx+8, cy-2), (cx+14, cy+8), 2)
                pygame.draw.circle(surf, (255,200,100), (cx+14, cy+8), 3)
                pygame.draw.circle(surf, (255,220,150), (cx, cy-10), 4)
            elif name == 'assassin':
                # 刺客 - 紧身衣+刃
                pygame.draw.rect(surf, color, (cx-6, cy-4, 12, 12))
                pygame.draw.polygon(surf, (40,40,60), [(cx, cy-14), (cx-4, cy-6), (cx+4, cy-6)])
                pygame.draw.line(surf, (180,180,200), (cx+8, cy+2), (cx+14, cy-6), 2)
                pygame.draw.polygon(surf, (200,200,220), [(cx+14, cy-6), (cx+12, cy-2), (cx+16, cy-2)])
                pygame.draw.circle(surf, (200,180,150), (cx, cy-8), 3)
            elif name == 'paladin':
                # 圣骑士 - 金盔+光环
                pygame.draw.rect(surf, color, (cx-10, cy-8, 20, 20))
                pygame.draw.rect(surf, (200,180,100), (cx-12, cy-10, 24, 4))
                pygame.draw.rect(surf, (180,160,80), (cx-6, cy-14, 12, 6))
                pygame.draw.circle(surf, (255,255,200,80), (cx, cy), 14, 2)
                pygame.draw.line(surf, (200,200,220), (cx+8, cy-2), (cx+14, cy+6), 3)
            elif name == 'engineer':
                # 工程师 - 重甲+机械手
                pygame.draw.rect(surf, color, (cx-9, cy-6, 18, 16))
                pygame.draw.rect(surf, (100,80,30), (cx-8, cy-12, 16, 6))
                pygame.draw.circle(surf, (150,120,60), (cx, cy-14), 3)
                pygame.draw.line(surf, (100,100,120), (cx-10, cy+2), (cx-16, cy+10), 3)
                pygame.draw.rect(surf, (120,120,140), (cx+6, cy+2, 8, 6))
            else:
                pygame.draw.rect(surf, color, (cx-6, cy-6, 12, 12))
                pygame.draw.circle(surf, (255,200,150), (cx, cy-8), 4)
            frames.append(surf)
        return frames

    def _fill_missing_enemies(self):
        """补充敌人精灵"""
        for enemy_name, (primary, fallbacks) in self._ENEMY_MAP.items():
            key = f'enemy_{enemy_name}'
            if self.sprites.get(key):
                continue
            img = self._try_dcss([primary] + fallbacks)
            if img:
                self.sprites[f'enemy_{enemy_name}'] = [img, img, img, img]
            else:
                self.sprites[f'enemy_{enemy_name}'] = self._generate_enemy_fallback(enemy_name)

    def _generate_enemy_fallback(self, name):
        """程序化生成各不相同的敌人精灵"""
        s = TILE_SIZE
        cx, cy = s//2, s//2
        color_map = {
            'soldier': (180, 40, 40), 'archer': (40, 150, 40),
            'mage_enemy': (150, 40, 180), 'bomber': (220, 120, 20),
            'shield_guard': (100, 100, 180), 'assassin_enemy': (60, 60, 60),
            'summoner': (100, 200, 50), 'fire_mage': (255, 80, 20),
            'heavy_gunner': (120, 120, 120), 'necromancer': (80, 20, 80),
            'elite_knight': (200, 50, 50), 'ice_witch': (100, 200, 240),
            'mimic': (180, 150, 50), 'ghost': (180, 180, 220),
            'goblin': (60, 180, 60),
            'boss_knight': (200, 20, 20), 'boss_mage': (150, 30, 200),
            'boss_dragon': (200, 100, 30), 'boss_mech': (100, 100, 120),
        }
        color = color_map.get(name, (100, 100, 100))
        is_boss = name.startswith('boss_')
        frames = []
        for f in range(4):
            surf = pygame.Surface((s, s), pygame.SRCALPHA)
            bsize = 10 if is_boss else 6
            if name == 'soldier':
                pygame.draw.rect(surf, color, (cx-5, cy-4, 10, 10))
                pygame.draw.circle(surf, (220,80,80), (cx, cy-6), 4)
                pygame.draw.rect(surf, (140,20,20), (cx-6, cy-6, 12, 2))
            elif name == 'archer':
                pygame.draw.rect(surf, color, (cx-4, cy-4, 8, 10))
                pygame.draw.circle(surf, (80,200,80), (cx, cy-7), 3)
                pygame.draw.line(surf, (160,120,60), (cx-8, cy-5), (cx+4, cy+2), 2)
            elif name == 'mage_enemy':
                pygame.draw.rect(surf, color, (cx-5, cy-3, 10, 8))
                pygame.draw.polygon(surf, (180,80,220), [(cx, cy-14), (cx-5, cy-6), (cx+5, cy-6)])
                pygame.draw.circle(surf, (200,120,255), (cx, cy-6), 3)
            elif name == 'bomber':
                r = 7
                pygame.draw.circle(surf, color, (cx, cy), r)
                pygame.draw.line(surf, (200,80,20), (cx-2, cy-5), (cx+2, cy-8), 2)
                pygame.draw.circle(surf, (255,200,50), (cx, cy), 3)
            elif name == 'shield_guard':
                pygame.draw.rect(surf, color, (cx-5, cy-4, 10, 10))
                pygame.draw.rect(surf, (140,140,220), (cx-9, cy-3, 8, 8), 2)  # shield
                pygame.draw.circle(surf, (255,255,255), (cx, cy-6), 3)
            elif name == 'assassin_enemy':
                pygame.draw.rect(surf, color, (cx-3, cy-4, 6, 10))
                pygame.draw.line(surf, (180,180,180), (cx+5, cy-6), (cx+10, cy+5), 2)
                pygame.draw.circle(surf, (255,50,50), (cx, cy-6), 2)
            elif name == 'summoner':
                pygame.draw.rect(surf, color, (cx-5, cy-3, 10, 8))
                pygame.draw.circle(surf, (150,255,100), (cx, cy-8), 4)
                for i in range(3):
                    a = i*2.1
                    ex = cx + int(12*math.cos(a))
                    ey = cy + int(12*math.sin(a))
                    pygame.draw.circle(surf, (150,255,100,80), (ex, ey), 3)
            elif name == 'fire_mage':
                pygame.draw.rect(surf, color, (cx-5, cy-3, 10, 8))
                pygame.draw.polygon(surf, (255,150,50), [(cx-3, cy-10), (cx, cy-14), (cx+3, cy-10)])
                pygame.draw.circle(surf, (255,100,0), (cx, cy-7), 3)
            elif name == 'heavy_gunner':
                pygame.draw.rect(surf, (100,100,100), (cx-6, cy-5, 12, 10))
                pygame.draw.rect(surf, color, (cx-5, cy-4, 10, 8))
                pygame.draw.rect(surf, (80,80,80), (cx-10, cy-2, 8, 4))
                pygame.draw.circle(surf, (255,50,50), (cx, cy-6), 3)
            elif name == 'necromancer':
                pygame.draw.rect(surf, color, (cx-4, cy-3, 8, 8))
                pygame.draw.polygon(surf, (120,60,120), [(cx, cy-14), (cx-6, cy-6), (cx+6, cy-6)])
                pygame.draw.circle(surf, (200,100,200), (cx, cy-8), 3)
                pygame.draw.circle(surf, (100,255,100), (cx-3, cy-10), 1)
                pygame.draw.circle(surf, (100,255,100), (cx+3, cy-10), 1)
            elif name == 'elite_knight':
                pygame.draw.rect(surf, color, (cx-6, cy-5, 12, 12))
                pygame.draw.rect(surf, (150,30,30), (cx-8, cy-7, 16, 3))
                pygame.draw.circle(surf, (255,200,0), (cx, cy-6), 3)
                pygame.draw.line(surf, (255,255,200), (cx+8, cy-2), (cx+14, cy+6), 3)
            elif name == 'ice_witch':
                pygame.draw.rect(surf, color, (cx-4, cy-3, 8, 8))
                pygame.draw.polygon(surf, (150,230,255), [(cx-4, cy-12), (cx, cy-16), (cx+4, cy-12)])
                pygame.draw.circle(surf, (200,240,255), (cx, cy-7), 3)
                for i in range(3):
                    ix = cx + int(8*math.cos(i*2.1))
                    iy = cy + int(10*math.sin(i*2.1))
                    pygame.draw.circle(surf, (200,240,255,60), (ix, iy), 2)
            elif name == 'mimic':
                pygame.draw.rect(surf, color, (cx-6, cy-6, 12, 10))
                pygame.draw.rect(surf, (220,200,100), (cx-4, cy-4, 8, 6))
                pygame.draw.line(surf, (100,80,20), (cx-4, cy-2), (cx+4, cy-2), 2)
                pygame.draw.circle(surf, (0,0,0), (cx-2, cy-3), 1)
                pygame.draw.circle(surf, (0,0,0), (cx+2, cy-3), 1)
            elif name == 'ghost':
                pygame.draw.circle(surf, color, (cx, cy), 7)
                pygame.draw.polygon(surf, color, [(cx-7, cy+2), (cx-5, cy+10), (cx-2, cy+4), (cx, cy+10), (cx+2, cy+4), (cx+5, cy+10), (cx+7, cy+2)])
                pygame.draw.circle(surf, (50,50,80), (cx-3, cy-2), 2)
                pygame.draw.circle(surf, (50,50,80), (cx+3, cy-2), 2)
            elif name == 'goblin':
                pygame.draw.circle(surf, color, (cx, cy), 5)
                pygame.draw.circle(surf, (100,220,100), (cx, cy-2), 3)
                pygame.draw.line(surf, (80,80,80), (cx-7, cy-3), (cx-2, cy-1), 2)
                pygame.draw.line(surf, (80,80,80), (cx+7, cy-3), (cx+2, cy-1), 2)
                pygame.draw.circle(surf, (255,50,50), (cx-2, cy-4), 1)
                pygame.draw.circle(surf, (255,50,50), (cx+2, cy-4), 1)
            elif is_boss:
                bcolor = color
                pygame.draw.circle(surf, bcolor, (cx, cy), bsize)
                pygame.draw.circle(surf, (255,255,200,100), (cx, cy), bsize+3, 2)
                pygame.draw.circle(surf, (255,255,0), (cx-2, cy-3), 2)
                pygame.draw.circle(surf, (255,255,0), (cx+2, cy-3), 2)
                pygame.draw.polygon(surf, (255,255,255), [(cx, cy+5), (cx-3, cy+3), (cx+3, cy+3)])
                if 'knight' in name:
                    pygame.draw.rect(surf, (80,80,80), (cx-7, cy-8, 14, 4))
                elif 'mage' in name:
                    pygame.draw.polygon(surf, (180,80,220), [(cx, cy-14), (cx-5, cy-7), (cx+5, cy-7)])
                elif 'dragon' in name:
                    pygame.draw.polygon(surf, (255,150,50), [(cx-8, cy-2), (cx-14, cy-6), (cx-10, cy)])
                    pygame.draw.polygon(surf, (255,150,50), [(cx+8, cy-2), (cx+14, cy-6), (cx+10, cy)])
                elif 'mech' in name:
                    pygame.draw.rect(surf, (150,150,150), (cx-8, cy-6, 16, 4))
                    pygame.draw.circle(surf, (255,0,0), (cx, cy-7), 2)
            else:
                pygame.draw.circle(surf, color, (cx, cy), 5)
                pygame.draw.circle(surf, (255,255,255), (cx, cy-6), 3)
            frames.append(surf)
        return frames

    def _fill_missing_weapons(self):
        """补充武器图标"""
        weapon_map = {
            'pistol': 'dcss_item_weapon_hand_cannon', 'rifle': 'dcss_item_weapon_arbalest',
            'shotgun': 'dcss_item_weapon_blowgun', 'sniper': 'dcss_item_weapon_longbow',
            'smg': 'dcss_item_weapon_hand_cannon', 'laser': 'dcss_item_weapon_rod',
            'rocket': 'dcss_item_weapon_hand_cannon', 'ice_gun': 'dcss_item_weapon_rod',
            'flamethrower': 'dcss_item_weapon_rod', 'sword': 'dcss_item_weapon_long_sword',
            'staff': 'dcss_item_weapon_staff', 'bow': 'dcss_item_weapon_bow',
            'dagger': 'dcss_item_weapon_dagger', 'hammer': 'dcss_item_weapon_mace',
            'laser_sword': 'dcss_item_weapon_demon_blade', 'crossbow': 'dcss_item_weapon_arbalest',
            'elemental_staff': 'dcss_item_weapon_staff', 'scythe': 'dcss_item_weapon_scythe',
            'magic_wand': 'dcss_item_weapon_wand',
            'dual_pistols': 'dcss_item_weapon_hand_cannon',
            'burst_rifle': 'dcss_item_weapon_arbalest',
            'dragon_breath': 'dcss_item_weapon_demon_blade',
            'railgun': 'dcss_item_weapon_rod',
            'gatling': 'dcss_item_weapon_hand_cannon',
            'plasma_rifle': 'dcss_item_weapon_rod',
            'grenade_launcher': 'dcss_item_weapon_hand_cannon',
            'thunder_gun': 'dcss_item_weapon_rod',
        }
        for wname, dcss_key in weapon_map.items():
            key = f'weapon_{wname}'
            if self.sprites.get(key):
                continue
            img = self.sprites.get(dcss_key)
            if img:
                self.sprites[key] = img
            else:
                self.sprites[key] = self._generate_weapon_fallback(wname)

    def _generate_weapon_fallback(self, name):
        """程序化生成各类武器图标"""
        s = 24
        surf = pygame.Surface((s, s), pygame.SRCALPHA)
        cx, cy = s//2, s//2
        if name in ('sword', 'laser_sword', 'dagger'):
            c = (200,200,200) if name != 'laser_sword' else (100,200,255)
            pygame.draw.rect(surf, c, (cx-1, 2, 3, s-8))
            pygame.draw.rect(surf, (120,80,40), (cx-3, s-6, 7, 4))
            if name == 'laser_sword':
                for i in range(3):
                    pygame.draw.rect(surf, (150,220,255,80), (cx-2+i, 4, 2, s-10))
            if name == 'dagger':
                pygame.draw.polygon(surf, (180,180,200), [(cx, 0), (cx-2, 4), (cx+2, 4)])
        elif name == 'staff':
            pygame.draw.rect(surf, (180,60,220), (cx-1, 6, 3, s-8))
            pygame.draw.rect(surf, (200,150,255), (cx-6, 2, 12, 8))
            pygame.draw.circle(surf, (255,200,255), (cx, 4), 3)
        elif name == 'bow':
            for i in range(3, s-5):
                offset = int(5 * math.sin((i-3)/8.0 * math.pi))
                pygame.draw.rect(surf, (140,120,60), (cx-offset, i, 1+2*offset, 2))
            pygame.draw.line(surf, (100,80,40), (cx-5, s-8), (cx+5, 4), 1)
        elif name == 'hammer':
            pygame.draw.rect(surf, (150,150,170), (cx-4, 2, 8, 8))
            pygame.draw.rect(surf, (120,80,40), (cx-1, s//2, 3, s//2))
            for i in range(2):
                pygame.draw.line(surf, (180,180,200), (cx-3, 4+i*3), (cx+4, 4+i*3), 2)
        elif name in ('pistol', 'dual_pistols'):
            pygame.draw.rect(surf, (150,150,150), (4, 6, s-8, 5))
            pygame.draw.rect(surf, (100,80,60), (cx-2, s//2, 5, s//2-2))
            if name == 'dual_pistols':
                pygame.draw.rect(surf, (150,150,150), (2, 10, s-12, 4))
                pygame.draw.rect(surf, (100,80,60), (cx-5, 8, 4, s//2-6))
        elif name in ('rifle', 'burst_rifle', 'sniper'):
            pygame.draw.rect(surf, (140,140,160), (2, cy-2, s-4, 4))
            if name == 'sniper':
                pygame.draw.rect(surf, (100,100,120), (0, cy-1, s-2, 3))
            pygame.draw.rect(surf, (100,80,60), (cx-2, s//2, 5, s//2-2))
            if name == 'burst_rifle':
                pygame.draw.rect(surf, (180,180,200), (4, cy-4, s-10, 8), 1)
        elif name in ('shotgun', 'dragon_breath'):
            pygame.draw.rect(surf, (140,130,120), (2, cy-3, s-4, 6))
            pygame.draw.rect(surf, (120,100,80), (0, cy-1, s-8, 4))
            pygame.draw.rect(surf, (80,60,40), (cx-3, s//2-2, 6, s//2))
            if name == 'dragon_breath':
                pygame.draw.circle(surf, (255,100,20,100), (4, cy), 3)
                pygame.draw.circle(surf, (255,200,50,80), (2, cy-2), 2)
        elif name in ('smg', 'gatling'):
            pygame.draw.rect(surf, (130,130,150), (3, cy-2, s-6, 4))
            pygame.draw.rect(surf, (100,80,60), (cx-2, s//2, 4, s//2-2))
            if name == 'gatling':
                pygame.draw.circle(surf, (100,100,100), (cx, cy-3), 5)
                pygame.draw.circle(surf, (80,80,80), (cx, cy-3), 3)
        elif name in ('laser', 'railgun'):
            c = (100,200,255) if name == 'laser' else (150,100,255)
            pygame.draw.rect(surf, c, (2, cy-2, s-4, 4))
            pygame.draw.rect(surf, (100,80,60), (cx-2, s//2-2, 5, s//2))
            for i in range(3):
                pygame.draw.rect(surf, (200,255,255,60), (4+i*2, cy-4, 2, 8))
        elif name in ('rocket', 'grenade_launcher'):
            pygame.draw.rect(surf, (120,120,100), (3, cy-4, s-10, 8))
            pygame.draw.circle(surf, (150,150,130), (4, cy), 4)
            pygame.draw.rect(surf, (100,80,60), (cx-2, s//2-2, 5, s//2))
            if name == 'rocket':
                pygame.draw.polygon(surf, (255,100,30), [(s-3, cy-2), (s-3, cy+2), (s, cy)])
        elif name in ('ice_gun', 'flamethrower', 'plasma_rifle'):
            base_c = {'ice_gun': (100,200,255), 'flamethrower': (255,120,20), 'plasma_rifle': (150,100,255)}
            c = base_c.get(name, (180,180,180))
            pygame.draw.rect(surf, c, (2, cy-2, s-4, 4))
            pygame.draw.rect(surf, (100,80,60), (cx-2, s//2-2, 5, s//2))
            if name == 'flamethrower':
                pygame.draw.circle(surf, (255,50,0,80), (4, cy-2), 4)
                pygame.draw.circle(surf, (255,200,50,60), (2, cy-3), 3)
        elif name == 'thunder_gun':
            pygame.draw.rect(surf, (100,100,180), (2, cy-2, s-4, 4))
            pygame.draw.rect(surf, (100,80,60), (cx-2, s//2-2, 5, s//2))
            for i in range(3):
                x = 3 + i*3
                pygame.draw.line(surf, (200,200,255), (x, cy-6), (x+3, cy+2), 2)
        else:
            pygame.draw.rect(surf, (180,180,180), (4, 4, s-8, s//2-2))
            pygame.draw.rect(surf, (100,80,60), (cx-2, s//2, 5, s//2-2))
        return surf

    def _fill_missing_bullets(self):
        """补充子弹精灵"""
        bullet_colors = {
            'normal': (255, 255, 200), 'fire': (255, 80, 20),
            'ice': (150, 220, 255), 'laser': (100, 200, 255),
            'rocket': (255, 80, 20), 'energy': (200, 100, 255),
            'arrow': (200, 180, 100),
        }
        for btype, color in bullet_colors.items():
            key = f'bullet_{btype}'
            if self.sprites.get(key):
                continue
            surf = pygame.Surface((10, 10), pygame.SRCALPHA)
            pygame.draw.circle(surf, color, (5, 5), 3)
            self.sprites[key] = surf

    def _fill_missing_items(self):
        """补充道具精灵"""
        item_colors = {
            'gold': (255, 215, 0), 'health': (255, 60, 60), 'energy': (100, 150, 255),
            'shield': (80, 180, 255), 'chest': (180, 150, 50),
            'speed_boost': (255, 255, 100), 'damage_boost': (255, 100, 50),
            'regen': (100, 255, 100), 'berserk': (255, 50, 50),
            'magnet': (200, 120, 250), 'bomb': (60, 60, 60),
            'exp': (100, 255, 100), 'weapon_drop': (255, 215, 0),
            'gold_chest': (200, 170, 80),
        }
        # Try DCSS item icons first
        dcss_item_map = {
            'gold': 'dcss_item_gold',
            'health': 'dcss_item_potion', 'energy': 'dcss_item_potion',
            'chest': 'dcss_item_misc', 'shield': 'dcss_item_armor_shields',
            'speed_boost': 'dcss_item_potion', 'damage_boost': 'dcss_item_potion',
        }
        for iname, color in item_colors.items():
            key = f'item_{iname}'
            if self.sprites.get(key):
                continue
            dcss_key = dcss_item_map.get(iname)
            dcss_img = self.sprites.get(dcss_key) if dcss_key else None
            if dcss_img:
                self.sprites[key] = dcss_img
            else:
                surf = pygame.Surface((20, 20), pygame.SRCALPHA)
                pygame.draw.circle(surf, color, (10, 10), 8)
                self.sprites[key] = surf

    def _fill_missing_tiles(self):
        """补充瓦片精灵（含主题变体）"""
        tile_colors = {
            'floor': (60, 50, 40), 'floor_alt': (55, 45, 38),
            'wall': (80, 80, 90), 'wall_top': (90, 90, 100),
            'door': (100, 80, 50),
            'boss_room_floor': (50, 30, 30), 'chest_room_floor': (55, 45, 42),
            'shop_floor': (50, 55, 50), 'hidden_wall': (70, 70, 75),
            'secret_floor': (40, 35, 50), 'mini_boss_floor': (50, 30, 35),
            'water': (30, 60, 80), 'lava': (80, 30, 10), 'pit': (10, 10, 15),
        }
        
        # 主题装饰 - 用于 tile 上叠加小装饰
        theme_deco = {
            'dungeon': lambda surf, c: self._tile_add_deco(surf, c, [(3,3,2),(10,12,2),(18,6,1)], (50,45,40)),
            'crypt': lambda surf, c: self._tile_add_deco(surf, c, [(5,5,1),(12,15,2),(20,8,1)], (40,35,50)),
            'forge': lambda surf, c: self._tile_add_deco(surf, c, [(8,10,1),(2,12,2),(22,4,1)], (80,50,20)),
            'ice_cave': lambda surf, c: self._tile_add_deco(surf, c, [(4,3,1),(16,5,2),(20,15,1)], (150,200,255)),
            'jungle': lambda surf, c: self._tile_add_deco(surf, c, [(6,10,2),(14,8,1),(22,18,2)], (40,100,40)),
        }
        
        for tname, color in tile_colors.items():
            key = f'tile_{tname}'
            if self.sprites.get(key):
                continue
            candidates = self._FLOOR_MAP.get(tname, [])
            found = self._try_dcss(candidates)
            if found:
                self.sprites[key] = found
            else:
                surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
                surf.fill(color)
                for _ in range(TILE_SIZE // 2):
                    rx = random.randint(1, TILE_SIZE - 3)
                    ry = random.randint(1, TILE_SIZE - 3)
                    v = random.randint(-8, 8)
                    c = (max(0, min(255, color[0] + v)),
                         max(0, min(255, color[1] + v)),
                         max(0, min(255, color[2] + v)))
                    pygame.draw.rect(surf, c, (rx, ry, 2, 2))
                # 主题花纹
                if tname == 'floor':
                    for tfn in theme_deco.values():
                        tfn(surf, color)
                        break  # only apply first theme as default
                self.sprites[key] = surf
                
        # 主题 floor 变体
        for theme_name, deco_fn in theme_deco.items():
            for base_name in ['floor', 'wall']:
                key = f'tile_{theme_name}_{base_name}'
                if self.sprites.get(key):
                    continue
                base_color = tile_colors.get(base_name, (60,50,40))
                surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
                surf.fill(base_color)
                for _ in range(TILE_SIZE // 2):
                    rx = random.randint(1, TILE_SIZE - 3)
                    ry = random.randint(1, TILE_SIZE - 3)
                    v = random.randint(-8, 8)
                    c = (max(0, min(255, base_color[0] + v)),
                         max(0, min(255, base_color[1] + v)),
                         max(0, min(255, base_color[2] + v)))
                    pygame.draw.rect(surf, c, (rx, ry, 2, 2))
                deco_fn(surf, base_color)
                self.sprites[key] = surf

    def _tile_add_deco(self, surf, base_color, dots, deco_color):
        """在瓦片上添加装饰点"""
        for x, y, s in dots:
            c = (max(0, deco_color[0]), max(0, deco_color[1]), max(0, deco_color[2]))
            pygame.draw.rect(surf, c, (x, y, s, s))


# 全局单例
_resources = None


def get_resources():
    global _resources
    if _resources is None:
        _resources = ResourceManager()
    return _resources
