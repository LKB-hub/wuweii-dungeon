"""
角色数据定义 - 可玩角色、敌人类型、武器、技能、道具、成就
完整扩展版：22+武器、15+敌人、4个Boss、主动/被动技能、成就系统
"""

# ============ 可玩角色 (6个) ============
PLAYER_CHARACTERS = {
    'knight': {
        'name': '骑士', 'desc': '近战专精，高生命值，护盾坚韧',
        'max_hp': 120, 'speed': 3.5, 'max_energy': 150,
        'starting_weapon': 'sword', 'color': (50, 100, 220),
        'skill': 'shield_bash', 'passive': 'iron_wall',
    },
    'ranger': {
        'name': '游侠', 'desc': '远程射击，射速极快，暴击率高',
        'max_hp': 80, 'speed': 4.5, 'max_energy': 180,
        'starting_weapon': 'bow', 'color': (50, 180, 80),
        'skill': 'arrow_rain', 'passive': 'eagle_eye',
    },
    'mage': {
        'name': '法师', 'desc': '魔法攻击，低生命高伤害，元素专精',
        'max_hp': 60, 'speed': 4.0, 'max_energy': 250,
        'starting_weapon': 'staff', 'color': (180, 60, 200),
        'skill': 'thunder_storm', 'passive': 'mana_flow',
    },
    'assassin': {
        'name': '刺客', 'desc': '高速移动，背刺暴击，隐身能力',
        'max_hp': 55, 'speed': 5.5, 'max_energy': 160,
        'starting_weapon': 'dagger', 'color': (60, 60, 80),
        'skill': 'shadow_step', 'passive': 'backstab',
    },
    'paladin': {
        'name': '圣骑士', 'desc': '攻守兼备，神圣之力，治愈光环',
        'max_hp': 100, 'speed': 3.0, 'max_energy': 180,
        'starting_weapon': 'hammer', 'color': (255, 215, 0),
        'skill': 'holy_light', 'passive': 'healing_aura',
    },
    'engineer': {
        'name': '工程师', 'desc': '召唤炮台，远程支援，高能量',
        'max_hp': 70, 'speed': 3.5, 'max_energy': 220,
        'starting_weapon': 'shotgun', 'color': (200, 150, 50),
        'skill': 'deploy_turret', 'passive': 'scrap_collect',
    },
}

# ============ 敌人类型 (15种) ============
ENEMY_TYPES = {
    'soldier': {
        'name': '近卫兵', 'hp': 40, 'speed': 2.0, 'damage': 10,
        'attack_range': 40, 'attack_cooldown': 45,
        'color': (180, 40, 40), 'ai': 'chase', 'score': 50,
    },
    'archer': {
        'name': '弓箭手', 'hp': 25, 'speed': 1.5, 'damage': 8,
        'attack_range': 300, 'attack_cooldown': 90,
        'color': (40, 150, 40), 'ai': 'keep_distance', 'score': 60,
        'bullet_type': 'arrow',
    },
    'mage_enemy': {
        'name': '暗法师', 'hp': 30, 'speed': 1.8, 'damage': 12,
        'attack_range': 250, 'attack_cooldown': 80,
        'color': (150, 40, 180), 'ai': 'keep_distance', 'score': 70,
        'bullet_type': 'energy',
    },
    'bomber': {
        'name': '自爆兵', 'hp': 20, 'speed': 3.5, 'damage': 25,
        'attack_range': 30, 'attack_cooldown': 30,
        'color': (220, 120, 20), 'ai': 'chase', 'explodes': True,
        'score': 80,
    },
    'shield_guard': {
        'name': '盾兵', 'hp': 70, 'speed': 1.5, 'damage': 15,
        'attack_range': 35, 'attack_cooldown': 60,
        'color': (100, 100, 180), 'ai': 'shield_wall', 'score': 100,
        'block_front': True,
    },
    'assassin_enemy': {
        'name': '暗杀者', 'hp': 30, 'speed': 4.0, 'damage': 18,
        'attack_range': 30, 'attack_cooldown': 50,
        'color': (60, 60, 60), 'ai': 'flank', 'score': 120,
        'dash_attack': True,
    },
    'summoner': {
        'name': '召唤师', 'hp': 40, 'speed': 1.5, 'damage': 5,
        'attack_range': 200, 'attack_cooldown': 200,
        'color': (100, 200, 50), 'ai': 'flee', 'score': 150,
        'summons_minions': True,
    },
    'fire_mage': {
        'name': '火法师', 'hp': 35, 'speed': 1.8, 'damage': 15,
        'attack_range': 220, 'attack_cooldown': 70,
        'color': (255, 80, 20), 'ai': 'keep_distance', 'score': 90,
        'bullet_type': 'fire', 'burn_effect': True,
    },
    'heavy_gunner': {
        'name': '重装枪手', 'hp': 100, 'speed': 1.2, 'damage': 12,
        'attack_range': 280, 'attack_cooldown': 20,
        'color': (120, 120, 120), 'ai': 'turret', 'score': 180,
        'bullet_type': 'normal', 'burst_fire': 3,
    },
    'necromancer': {
        'name': '死灵法师', 'hp': 50, 'speed': 2.0, 'damage': 10,
        'attack_range': 250, 'attack_cooldown': 120,
        'color': (80, 20, 80), 'ai': 'keep_distance', 'score': 200,
        'bullet_type': 'energy', 'revive_corpses': True,
    },
    'elite_knight': {
        'name': '精英骑士', 'hp': 150, 'speed': 2.5, 'damage': 22,
        'attack_range': 50, 'attack_cooldown': 35,
        'color': (200, 50, 50), 'ai': 'chase', 'score': 220,
        'charge_attack': True,
    },
    'ice_witch': {
        'name': '冰女巫', 'hp': 45, 'speed': 2.0, 'damage': 10,
        'attack_range': 240, 'attack_cooldown': 55,
        'color': (100, 200, 240), 'ai': 'keep_distance', 'score': 160,
        'bullet_type': 'ice', 'slow_effect': True,
    },
    'mimic': {
        'name': '宝箱怪', 'hp': 80, 'speed': 3.0, 'damage': 20,
        'attack_range': 40, 'attack_cooldown': 40,
        'color': (180, 150, 50), 'ai': 'ambush', 'score': 250,
        'disguised': True,
    },
    'ghost': {
        'name': '幽灵', 'hp': 25, 'speed': 2.5, 'damage': 8,
        'attack_range': 60, 'attack_cooldown': 60,
        'color': (180, 180, 220), 'ai': 'phase', 'score': 130,
        'phasing': True,
    },
    'goblin': {
        'name': '哥布林', 'hp': 15, 'speed': 4.5, 'damage': 5,
        'attack_range': 25, 'attack_cooldown': 25,
        'color': (60, 180, 60), 'ai': 'hit_and_run', 'score': 30,
        'steals_gold': True,
    },
}

# ============ Boss 类型 (4个) ============
BOSS_TYPES = {
    'boss_knight': {
        'name': '暗黑骑士', 'hp': 300, 'speed': 2.0, 'damage': 20,
        'attack_range': 60, 'attack_cooldown': 40,
        'color': (200, 20, 20), 'ai': 'boss_chase',
        'score': 500, 'size_mult': 1.5,
        'phases': ['slash', 'charge', 'spin'],
    },
    'boss_mage': {
        'name': '大法师萨鲁曼', 'hp': 250, 'speed': 1.5, 'damage': 18,
        'attack_range': 300, 'attack_cooldown': 35,
        'color': (150, 30, 200), 'ai': 'boss_ranged',
        'score': 600, 'size_mult': 1.4,
        'phases': ['fireball', 'ice_storm', 'teleport', 'summon'],
    },
    'boss_dragon': {
        'name': '远古巨龙', 'hp': 500, 'speed': 1.8, 'damage': 25,
        'attack_range': 80, 'attack_cooldown': 50,
        'color': (200, 100, 30), 'ai': 'boss_dragon',
        'score': 800, 'size_mult': 2.0,
        'phases': ['fire_breath', 'tail_swipe', 'fly_dive'],
    },
    'boss_mech': {
        'name': '战争机甲X', 'hp': 400, 'speed': 1.2, 'damage': 22,
        'attack_range': 350, 'attack_cooldown': 25,
        'color': (100, 100, 120), 'ai': 'boss_turret',
        'score': 700, 'size_mult': 1.6,
        'phases': ['missile_barrage', 'laser_beam', 'mine_field'],
    },
}

# ============ 武器数据 (22种) ============
WEAPON_DATA = {
    'pistol': {
        'name': '手枪', 'type': 'ranged', 'tier': 1,
        'damage': 10, 'fire_rate': 30, 'bullet_speed': 10,
        'bullet_type': 'normal', 'mag_size': 12, 'spread': 3,
        'bullets_per_shot': 1, 'cost': 0,
    },
    'dual_pistols': {
        'name': '双枪', 'type': 'ranged', 'tier': 2,
        'damage': 7, 'fire_rate': 18, 'bullet_speed': 10,
        'bullet_type': 'normal', 'mag_size': 20, 'spread': 8,
        'bullets_per_shot': 2, 'cost': 80,
    },
    'rifle': {
        'name': '步枪', 'type': 'ranged', 'tier': 1,
        'damage': 8, 'fire_rate': 15, 'bullet_speed': 12,
        'bullet_type': 'normal', 'mag_size': 30, 'spread': 5,
        'bullets_per_shot': 1, 'cost': 0,
    },
    'burst_rifle': {
        'name': '三连发步枪', 'type': 'ranged', 'tier': 2,
        'damage': 6, 'fire_rate': 20, 'bullet_speed': 11,
        'bullet_type': 'normal', 'mag_size': 24, 'spread': 4,
        'bullets_per_shot': 3, 'cost': 100,
    },
    'shotgun': {
        'name': '霰弹枪', 'type': 'ranged', 'tier': 1,
        'damage': 6, 'fire_rate': 50, 'bullet_speed': 8,
        'bullet_type': 'normal', 'mag_size': 6, 'spread': 20,
        'bullets_per_shot': 5, 'cost': 0,
    },
    'dragon_breath': {
        'name': '龙息霰弹', 'type': 'ranged', 'tier': 3,
        'damage': 10, 'fire_rate': 45, 'bullet_speed': 8,
        'bullet_type': 'fire', 'mag_size': 4, 'spread': 18,
        'bullets_per_shot': 7, 'burn_effect': True, 'cost': 150,
    },
    'sniper': {
        'name': '狙击枪', 'type': 'ranged', 'tier': 2,
        'damage': 45, 'fire_rate': 90, 'bullet_speed': 20,
        'bullet_type': 'normal', 'mag_size': 5, 'spread': 0,
        'bullets_per_shot': 1, 'cost': 120,
    },
    'railgun': {
        'name': '电磁炮', 'type': 'ranged', 'tier': 3,
        'damage': 80, 'fire_rate': 120, 'bullet_speed': 30,
        'bullet_type': 'laser', 'mag_size': 3, 'spread': 0,
        'bullets_per_shot': 1, 'piercing': True, 'cost': 200,
    },
    'smg': {
        'name': '冲锋枪', 'type': 'ranged', 'tier': 1,
        'damage': 5, 'fire_rate': 6, 'bullet_speed': 9,
        'bullet_type': 'normal', 'mag_size': 40, 'spread': 10,
        'bullets_per_shot': 1, 'cost': 0,
    },
    'gatling': {
        'name': '加特林', 'type': 'ranged', 'tier': 3,
        'damage': 4, 'fire_rate': 2, 'bullet_speed': 10,
        'bullet_type': 'normal', 'mag_size': 100, 'spread': 15,
        'bullets_per_shot': 1, 'cost': 180,
    },
    'laser': {
        'name': '激光枪', 'type': 'ranged', 'tier': 2,
        'damage': 12, 'fire_rate': 20, 'bullet_speed': 16,
        'bullet_type': 'laser', 'mag_size': 25, 'spread': 2,
        'bullets_per_shot': 1, 'cost': 90,
    },
    'plasma_rifle': {
        'name': '等离子步枪', 'type': 'ranged', 'tier': 3,
        'damage': 18, 'fire_rate': 12, 'bullet_speed': 14,
        'bullet_type': 'energy', 'mag_size': 20, 'spread': 4,
        'bullets_per_shot': 1, 'explosive': True, 'explosion_radius': 30,
        'cost': 160,
    },
    'rocket': {
        'name': '火箭筒', 'type': 'ranged', 'tier': 2,
        'damage': 35, 'fire_rate': 70, 'bullet_speed': 6,
        'bullet_type': 'rocket', 'mag_size': 3, 'spread': 5,
        'bullets_per_shot': 1, 'explosive': True, 'explosion_radius': 60,
        'cost': 130,
    },
    'grenade_launcher': {
        'name': '榴弹发射器', 'type': 'ranged', 'tier': 3,
        'damage': 28, 'fire_rate': 55, 'bullet_speed': 5,
        'bullet_type': 'rocket', 'mag_size': 5, 'spread': 10,
        'bullets_per_shot': 1, 'explosive': True, 'explosion_radius': 50,
        'cost': 170,
    },
    'ice_gun': {
        'name': '冰冻枪', 'type': 'ranged', 'tier': 2,
        'damage': 7, 'fire_rate': 18, 'bullet_speed': 7,
        'bullet_type': 'ice', 'mag_size': 20, 'spread': 8,
        'bullets_per_shot': 1, 'slow_effect': True, 'cost': 90,
    },
    'flamethrower': {
        'name': '火焰喷射器', 'type': 'ranged', 'tier': 2,
        'damage': 4, 'fire_rate': 3, 'bullet_speed': 5,
        'bullet_type': 'fire', 'mag_size': 50, 'spread': 25,
        'bullets_per_shot': 2, 'burn_effect': True, 'cost': 100,
    },
    'thunder_gun': {
        'name': '雷霆之枪', 'type': 'ranged', 'tier': 3,
        'damage': 15, 'fire_rate': 22, 'bullet_speed': 12,
        'bullet_type': 'energy', 'mag_size': 18, 'spread': 5,
        'bullets_per_shot': 1, 'chain_lightning': True, 'cost': 190,
    },
    'sword': {
        'name': '长剑', 'type': 'melee', 'tier': 1,
        'damage': 25, 'fire_rate': 25,
        'range': 50, 'arc': 120, 'cost': 0,
    },
    'dagger': {
        'name': '暗杀匕首', 'type': 'melee', 'tier': 1,
        'damage': 18, 'fire_rate': 12,
        'range': 35, 'arc': 60, 'cost': 0,
    },
    'hammer': {
        'name': '圣锤', 'type': 'melee', 'tier': 2,
        'damage': 35, 'fire_rate': 40,
        'range': 55, 'arc': 140, 'knockback': True, 'cost': 80,
    },
    'laser_sword': {
        'name': '光剑', 'type': 'melee', 'tier': 3,
        'damage': 40, 'fire_rate': 18,
        'range': 60, 'arc': 180, 'cost': 200,
    },
    'staff': {
        'name': '能量法杖', 'type': 'ranged', 'tier': 1,
        'damage': 14, 'fire_rate': 25, 'bullet_speed': 7,
        'bullet_type': 'energy', 'mag_size': 15, 'spread': 5,
        'bullets_per_shot': 3, 'cost': 0,
    },
    'bow': {
        'name': '猎弓', 'type': 'ranged', 'tier': 1,
        'damage': 15, 'fire_rate': 35, 'bullet_speed': 8,
        'bullet_type': 'arrow', 'mag_size': 1, 'spread': 2,
        'bullets_per_shot': 1, 'cost': 0,
    },
    'crossbow': {
        'name': '连弩', 'type': 'ranged', 'tier': 2,
        'damage': 12, 'fire_rate': 20, 'bullet_speed': 10,
        'bullet_type': 'arrow', 'mag_size': 5, 'spread': 4,
        'bullets_per_shot': 2, 'cost': 90,
    },
    'elemental_staff': {
        'name': '元素法杖', 'type': 'ranged', 'tier': 3,
        'damage': 20, 'fire_rate': 28, 'bullet_speed': 8,
        'bullet_type': 'energy', 'mag_size': 12, 'spread': 3,
        'bullets_per_shot': 3, 'burn_effect': True, 'slow_effect': True, 'cost': 200,
    },
    'scythe': {
        'name': '死神镰刀', 'type': 'melee', 'tier': 3,
        'damage': 50, 'fire_rate': 35,
        'range': 70, 'arc': 200, 'lifesteal': 0.1, 'cost': 220,
    },
    'magic_wand': {
        'name': '魔法短杖', 'type': 'ranged', 'tier': 2,
        'damage': 10, 'fire_rate': 15, 'bullet_speed': 6,
        'bullet_type': 'energy', 'mag_size': 30, 'spread': 15,
        'bullets_per_shot': 2, 'homing': True, 'cost': 110,
    },
}

# ============ 武器稀有度 ============
WEAPON_RARITY = {
    'common': {'mult': 1.0, 'color': (150, 150, 150), 'name': '普通', 'drop_weight': 50},
    'uncommon': {'mult': 1.2, 'color': (100, 200, 100), 'name': '非凡', 'drop_weight': 30},
    'rare': {'mult': 1.5, 'color': (80, 150, 255), 'name': '稀有', 'drop_weight': 15},
    'epic': {'mult': 1.8, 'color': (200, 80, 200), 'name': '史诗', 'drop_weight': 4},
    'legendary': {'mult': 2.2, 'color': (255, 180, 20), 'name': '传说', 'drop_weight': 1},
}

WEAPON_RARITY_ORDER = ['common', 'uncommon', 'rare', 'epic', 'legendary']


# ============ 武器升级树 ============
WEAPON_UPGRADES = {
    'pistol': 'dual_pistols',
    'rifle': 'burst_rifle',
    'shotgun': 'dragon_breath',
    'bow': 'crossbow',
    'staff': 'elemental_staff',
    'smg': 'gatling',
    'laser': 'railgun',
    'sword': 'laser_sword',
    'rocket': 'grenade_launcher',
}

# 可在商店购买的武器
SHOP_WEAPONS = [
    'dual_pistols', 'burst_rifle', 'sniper', 'laser', 'rocket',
    'ice_gun', 'flamethrower', 'hammer', 'dragon_breath', 'gatling',
    'plasma_rifle', 'grenade_launcher', 'railgun', 'thunder_gun', 'laser_sword',
    'crossbow', 'elemental_staff', 'scythe', 'magic_wand',
]

# ============ 道具数据 ============
ITEM_DATA = {
    'health_small': {'name': '小血瓶', 'heal': 25, 'cost': 15, 'color': (255, 80, 80)},
    'health_large': {'name': '大血瓶', 'heal': 60, 'cost': 35, 'color': (255, 40, 40)},
    'energy_small': {'name': '小蓝瓶', 'energy': 40, 'cost': 10, 'color': (80, 120, 255)},
    'energy_large': {'name': '大蓝瓶', 'energy': 90, 'cost': 25, 'color': (50, 80, 255)},
    'shield_pack': {'name': '护盾包', 'shield': 30, 'cost': 30, 'color': (80, 200, 240)},
    'bomb': {'name': '炸弹', 'damage': 80, 'cost': 20, 'color': (255, 140, 0)},
}

# ============ 技能数据 ============
SKILL_DATA = {
    'shield_bash': {
        'name': '盾击', 'energy_cost': 50, 'cooldown': 180,
        'desc': '向前冲刺，眩晕路径上的敌人并造成20点伤害',
        'damage': 20, 'stun_duration': 40, 'dash_distance': 120,
    },
    'arrow_rain': {
        'name': '箭雨', 'energy_cost': 60, 'cooldown': 200,
        'desc': '向周围360度发射12支箭矢',
        'arrow_count': 12, 'damage': 8,
    },
    'thunder_storm': {
        'name': '雷暴', 'energy_cost': 70, 'cooldown': 240,
        'desc': '在周围随机位置召唤闪电，造成30点伤害',
        'strike_count': 8, 'damage': 30, 'radius': 200,
    },
    'shadow_step': {
        'name': '暗影步', 'energy_cost': 40, 'cooldown': 120,
        'desc': '瞬移到瞄准位置，对路径上的敌人造成40点伤害',
        'damage': 40, 'teleport_range': 200,
    },
    'holy_light': {
        'name': '圣光', 'energy_cost': 60, 'cooldown': 300,
        'desc': '大范围圣光：回复30HP并对周围敌人造成20伤害',
        'heal': 30, 'damage': 20, 'radius': 200,
    },
    'deploy_turret': {
        'name': '部署炮台', 'energy_cost': 50, 'cooldown': 360,
        'desc': '在当前位置放置一个自动攻击的炮台，持续15秒',
        'turret_damage': 8, 'turret_fire_rate': 20, 'duration': 900,
    },
    'iron_wall': {
        'name': '铁壁', 'type': 'passive',
        'desc': '每10秒获得5点护盾（上限50）',
        'shield_per_tick': 5, 'tick_interval': 600,
    },
    'eagle_eye': {
        'name': '鹰眼', 'type': 'passive',
        'desc': '暴击率+15%',
        'crit_chance_bonus': 0.15,
    },
    'mana_flow': {
        'name': '法力涌动', 'type': 'passive',
        'desc': '能量自然回复速度+50%',
        'energy_regen_bonus': 0.5,
    },
    'backstab': {
        'name': '背刺', 'type': 'passive',
        'desc': '从目标背后攻击时伤害+100%',
        'backstab_multiplier': 2.0,
    },
    'healing_aura': {
        'name': '治愈光环', 'type': 'passive',
        'desc': '每秒回复1点生命值',
        'heal_per_second': 1,
    },
    'scrap_collect': {
        'name': '废铁收集', 'type': 'passive',
        'desc': '击杀敌人额外掉落3-8金币',
        'bonus_gold': (3, 8),
    },
}

# ============ 成就数据 ============
ACHIEVEMENTS = {
    'first_kill': {'name': '初次击杀', 'desc': '击败第一个敌人', 'icon': 'skull'},
    'kill_100': {'name': '百人斩', 'desc': '累计击败100个敌人', 'icon': 'swords'},
    'kill_500': {'name': '屠夫', 'desc': '累计击败500个敌人', 'icon': 'axe'},
    'boss_slayer': {'name': 'Boss杀手', 'desc': '击败第一个Boss', 'icon': 'crown'},
    'all_bosses': {'name': '全Boss通缉', 'desc': '击败所有类型的Boss', 'icon': 'trophy'},
    'no_damage_room': {'name': '完美房间', 'desc': '无伤通关一个房间', 'icon': 'shield'},
    'no_damage_boss': {'name': '完美Boss战', 'desc': '无伤击败Boss', 'icon': 'star'},
    'gold_1000': {'name': '小富翁', 'desc': '累积获得1000金币', 'icon': 'coin'},
    'gold_5000': {'name': '大富豪', 'desc': '累积获得5000金币', 'icon': 'gem'},
    'speed_run': {'name': '速通', 'desc': '在3分钟内通关', 'icon': 'bolt'},
    'weapon_master': {'name': '武器大师', 'desc': '使用过所有类型的武器', 'icon': 'crosshair'},
    'survivor': {'name': '幸存者', 'desc': '以低于10%血量通关', 'icon': 'heart'},
    'pacifist': {'name': '和平主义者', 'desc': '一局中击杀少于5个敌人通关', 'icon': 'dove'},
}

# ============ 陷阱数据 ============
TRAP_TYPES = {
    'spike': {'name': '尖刺陷阱', 'damage': 15, 'cooldown': 60, 'trigger_radius': 20, 'visible': True},
    'fire_trap': {'name': '火焰陷阱', 'damage': 8, 'burn_duration': 60, 'cooldown': 90, 'trigger_radius': 25, 'visible': True},
    'poison_gas': {'name': '毒气陷阱', 'damage': 3, 'poison_duration': 120, 'cooldown': 120, 'trigger_radius': 30, 'visible': False},
    'arrow_trap': {'name': '暗箭陷阱', 'damage': 20, 'cooldown': 80, 'trigger_radius': 16, 'visible': False},
}

# ============ 装饰物数据 ============
DECORATIONS = [
    {'name': 'candle', 'symbol': 'i', 'color': (255, 200, 50), 'animated': True},
    {'name': 'barrel', 'symbol': 'o', 'color': (139, 90, 43), 'destructible': True},
    {'name': 'crate', 'symbol': '#', 'color': (160, 120, 60), 'destructible': True},
    {'name': 'skull_deco', 'symbol': 'x', 'color': (200, 200, 200), 'ominous': True},
    {'name': 'torch', 'symbol': 'T', 'color': (255, 150, 30), 'animated': True},
    {'name': 'spider_web', 'symbol': '~', 'color': (180, 180, 180)},
    {'name': 'mushroom', 'symbol': 'u', 'color': (200, 100, 200), 'glowing': True},
    {'name': 'stalagmite', 'symbol': '^', 'color': (100, 100, 100)},
    {'name': 'blood_pool', 'symbol': ',', 'color': (120, 20, 20), 'ominous': True},
    {'name': 'chains', 'symbol': '|', 'color': (80, 80, 80)},
]

# ============ 难度等级 ============
DIFFICULTY_LEVELS = {
    1: {'name': '简单', 'enemy_hp_mult': 0.8, 'enemy_count_mult': 0.7, 'boss_hp_mult': 0.8},
    2: {'name': '普通', 'enemy_hp_mult': 1.0, 'enemy_count_mult': 1.0, 'boss_hp_mult': 1.0},
    3: {'name': '困难', 'enemy_hp_mult': 1.3, 'enemy_count_mult': 1.4, 'boss_hp_mult': 1.3},
    4: {'name': '噩梦', 'enemy_hp_mult': 1.8, 'enemy_count_mult': 1.8, 'boss_hp_mult': 1.6},
    5: {'name': '地狱', 'enemy_hp_mult': 2.5, 'enemy_count_mult': 2.2, 'boss_hp_mult': 2.0},
}

# ============ 房间主题 ============
ROOM_THEMES = {
    'dungeon': {
        'wall_colors': [(70, 70, 80), (80, 80, 90), (90, 85, 75)],
        'floor_colors': [(50, 45, 40), (55, 48, 42), (45, 40, 38)],
        'ambient_light': (20, 15, 10),
    },
    'crypt': {
        'wall_colors': [(50, 45, 55), (55, 50, 60), (60, 50, 50)],
        'floor_colors': [(40, 35, 45), (42, 36, 48), (38, 32, 42)],
        'ambient_light': (15, 10, 20),
    },
    'forge': {
        'wall_colors': [(90, 70, 50), (95, 75, 55), (85, 65, 45)],
        'floor_colors': [(60, 40, 30), (62, 42, 32), (55, 38, 28)],
        'ambient_light': (30, 20, 5),
    },
    'ice_cave': {
        'wall_colors': [(100, 120, 150), (110, 130, 160), (90, 115, 145)],
        'floor_colors': [(80, 95, 120), (82, 97, 122), (75, 90, 115)],
        'ambient_light': (10, 20, 35),
    },
    'jungle': {
        'wall_colors': [(40, 80, 40), (45, 85, 45), (35, 75, 35)],
        'floor_colors': [(30, 60, 30), (32, 62, 32), (28, 55, 28)],
        'ambient_light': (15, 25, 5),
    },
}

# ============ 敌人波次数据 ============
ENEMY_WAVE_PATTERNS = {
    'ambush': {'delay': 30, 'spread': 'circle', 'min_count': 3, 'max_count': 6},
    'reinforcement': {'delay': 90, 'spread': 'line', 'min_count': 2, 'max_count': 4},
    'boss_phase': {'delay': 60, 'spread': 'square', 'min_count': 2, 'max_count': 5},
    'flanking': {'delay': 45, 'spread': 'v_shape', 'min_count': 2, 'max_count': 3},
}

# ============ 特殊房间事件数据 ============
ROOM_EVENTS = [
    {'name': 'enemy_ambush', 'weight': 30, 'desc': '进入房间时触发伏击',
     'msg': '小心！敌人从暗处涌来...'},
    {'name': 'treasure_room', 'weight': 15, 'desc': '发现额外的宝箱',
     'msg': '你发现了一个隐藏的宝箱!'},
    {'name': 'healing_fountain', 'weight': 10, 'desc': '发现恢复喷泉',
     'msg': '一股温暖的泉水恢复了你的生命...'},
    {'name': 'trap_gauntlet', 'weight': 20, 'desc': '陷阱遍布的房间',
     'msg': '房间里布满了陷阱！小心脚下...'},
    {'name': 'time_rift', 'weight': 5, 'desc': '时间裂隙，敌人变慢',
     'msg': '时间似乎在这里流动得更慢...'},
]

# ============ 增益效果数据 ============
BUFF_TYPES = {
    'attack_up': {'name': '攻击力上升', 'duration': 600, 'icon': '⚔', 'desc': '攻击力+30%', 'atk_mult': 1.3},
    'speed_up': {'name': '速度上升', 'duration': 600, 'icon': '💨', 'desc': '移速+40%', 'spd_mult': 1.4},
    'damage_reduce': {'name': '减伤', 'duration': 450, 'icon': '🛡', 'desc': '受到伤害-30%', 'dmg_mult': 0.7},
    'life_steal': {'name': '生命偷取', 'duration': 300, 'icon': '❤', 'desc': '造成伤害的20%回复生命', 'lifesteal': 0.2},
    'infinite_energy': {'name': '无限能量', 'duration': 360, 'icon': '⚡', 'desc': '能量消耗为0', 'energy_free': True},
    'double_gold': {'name': '双倍金币', 'duration': 480, 'icon': '💰', 'desc': '获得金币翻倍', 'gold_mult': 2.0},
}
