"""
任务系统 - 主线/支线/副本/每日，完整世界观
"""
import random
import math
from datetime import date as dt_date


# ============ 世界观背景 ============
LORE = {
    'world': '艾尔迪亚大陆——一块被远古魔法战争撕裂的土地。十二层深渊地牢通往世界核心，每一层都封印着一段历史。',
    'player': '你是"破晓者"的后裔，肩负着净化深渊、恢复大陆平衡的使命。从地表遗迹出发，一步一步深入地心。',
    'faction': {
        'dawn':     {'name': '破晓骑士团', 'desc': '守护地表秩序的古老组织，你的使命之源'},
        'deepone':  {'name': '深渊教团',   'desc': '崇拜黑暗力量的秘密结社，制造了地牢的怪物'},
        'merchant': {'name': '自由商盟',   'desc': '遍布地下的商人网络，中立但消息灵通'},
    },
    'location': {
        'hub':       {'name': '曙光营地', 'desc': '地表最后的根据地，骑士团据点'},
        'floor_1':   {'name': '幽暗地牢', 'desc': '地牢第一层，被遗忘的监狱下层'},
        'floor_4':   {'name': '地下墓地', 'desc': '古代英雄的安息之地，亡灵徘徊'},
        'floor_7':   {'name': '熔岩锻造场', 'desc': '深渊教团的兵器工厂，炙热难耐'},
        'floor_10':  {'name': '远古龙巢', 'desc': '巨龙的沉睡之地，龙骨遍地'},
        'floor_12':  {'name': '世界核心', 'desc': '深渊的最深处，封印着灭世之力'},
    },
}

# 存档中的主线进度 key
STORY_PROGRESS_KEY = 'story_chapter'

# 物品奖励定义（被引用但不在此定义）
REWARD_ITEMS = {
    'scroll_teleport':  {'name': '传送卷轴', 'desc': '随机传送', 'color': (150,100,200)},
    'pet_egg_common':   {'name': '普通宠物蛋', 'desc': '随机孵化一只宠物', 'color': (200,180,220)},
    'pet_egg_rare':     {'name': '稀有宠物蛋', 'desc': '孵化稀有宠物', 'color': (255,215,0)},
    'key_skeleton':     {'name': '骷髅钥匙', 'desc': '开启隐藏房间', 'color': (180,180,180)},
    'weapon_token':     {'name': '武器兑换券', 'desc': '在商店换一件武器', 'color': (255,200,50)},
    'ancient_relic':    {'name': '远古遗物', 'desc': '神秘的古物，可兑换大量金币', 'color': (255,150,50)},
}


# ============ 主线任务 ============
# 12章，对应12层地牢
MAIN_QUESTS = [
    {
        'id': 'main_01', 'chapter': 1, 'floor': 1,
        'name': '破晓之始',
        'desc': '深渊裂隙在地表蔓延。前往地牢第一层，击败守卫监狱的暗黑骑士。',
        'objectives': [
            {'type': 'reach_floor', 'target': 1, 'count': 1},
            {'type': 'kill_boss', 'target': 'boss_knight', 'count': 1},
        ],
        'reward_gold': 100, 'reward_exp': 50,
        'reward_item': 'health_potion_m',
        'story_text': '你踏入幽暗地牢的第一层。墙壁上刻满古老的符文，空气中弥漫着潮湿与铁锈的气息。'
                      '远处传来锁链拖曳的声音——暗黑骑士就在前方。',
        'complete_text': '暗黑骑士轰然倒下，监狱的结界碎裂。你感受到一股温暖的力量涌入身体——这是破晓者的血脉在苏醒。',
    },
    {
        'id': 'main_02', 'chapter': 2, 'floor': 2,
        'name': '阴影低语',
        'desc': '深渊教团的爪牙在第二层集结。击败暗法师头目，获取教团情报。',
        'objectives': [
            {'type': 'reach_floor', 'target': 2, 'count': 1},
            {'type': 'kill', 'target': 'mage_enemy', 'count': 10},
        ],
        'reward_gold': 150, 'reward_exp': 80,
        'reward_item': 'energy_potion',
        'story_text': '第二层的墙壁上挂着紫色的帷幔，空气中有硫磺的味道。黑暗魔法在这里留下了深深的烙印。',
        'complete_text': '你发现了深渊教团的标记——一个倒置的三角符号。他们在寻找某样东西，就在地牢的更深处。',
    },
    {
        'id': 'main_03', 'chapter': 3, 'floor': 3,
        'name': '烈焰试炼',
        'desc': '第三层已被火焰吞噬。穿越熔岩区，击败火焰之主。',
        'objectives': [
            {'type': 'reach_floor', 'target': 3, 'count': 1},
            {'type': 'kill_boss', 'target': 'boss_dragon', 'count': 1},
        ],
        'reward_gold': 200, 'reward_exp': 120,
        'reward_item': 'bomb',
        'story_text': '热浪扑面而来。第三层是一座活火山内部，岩浆河将岩石分割成无数小岛。火焰之主在岩浆最深处沉睡。',
        'complete_text': '火焰之主化作灰烬，一块赤红色的晶石从它体内掉落。晶石中封印着一句古语："向下，直到世界的心跳。"',
    },
    {
        'id': 'main_04', 'chapter': 4, 'floor': 4,
        'name': '亡灵低语',
        'desc': '第四层——古代英雄的墓地。死去的战士不会安息，击败死灵法师，让他们重新沉睡。',
        'objectives': [
            {'type': 'reach_floor', 'target': 4, 'count': 1},
            {'type': 'kill', 'target': 'necromancer', 'count': 5},
            {'type': 'kill_boss', 'target': 'boss_mage', 'count': 1},
        ],
        'reward_gold': 250, 'reward_exp': 150,
        'reward_item': 'scroll_teleport',
        'story_text': '墓地中回荡着古老的战歌。这里的亡灵曾是抗击深渊的第一代勇士。死灵法师亵渎了他们的安眠。',
        'complete_text': '死灵法师的法杖断裂，亡灵们化作光点消散。一束光从穹顶射下，照亮了一面刻满英雄名字的石墙。',
    },
    {
        'id': 'main_05', 'chapter': 5, 'floor': 5,
        'name': '冰封之心',
        'desc': '第五层的寒冰洞穴中，冰女巫用永恒的寒冬封锁了前路。',
        'objectives': [
            {'type': 'reach_floor', 'target': 5, 'count': 1},
            {'type': 'kill', 'target': 'ice_witch', 'count': 3},
        ],
        'reward_gold': 300, 'reward_exp': 180,
        'reward_item': 'shield_potion',
        'story_text': '厚厚的冰层覆盖了所有的墙壁和地面。你的呼吸凝结成霜。冰女巫就坐在洞穴深处的冰封王座上。',
        'complete_text': '冰层碎裂，春天仿佛在一瞬间重回这层地牢。你看见冰层下封存着远古植物的化石。',
    },
    {
        'id': 'main_06', 'chapter': 6, 'floor': 6,
        'name': '锻造之秘',
        'desc': '第六层是深渊教团的兵器工厂。摧毁他们的生产线，击败战争机甲。',
        'objectives': [
            {'type': 'reach_floor', 'target': 6, 'count': 1},
            {'type': 'kill_boss', 'target': 'boss_mech', 'count': 1},
        ],
        'reward_gold': 350, 'reward_exp': 200,
        'reward_item': 'weapon_token',
        'story_text': '蒸汽与火焰交织。巨大的齿轮和锻造锤轰鸣作响。战争机甲X是教团最致命的造物。',
        'complete_text': '机甲的核心碎裂，整个工厂停止了运转。你在废墟中发现了一份设计图——上面画着前往更深处的路线。',
    },
    {
        'id': 'main_07', 'chapter': 7, 'floor': 7,
        'name': '龙息之地',
        'desc': '第七层是远古巨龙的巢穴。火焰与毁灭笼罩着这片区域。',
        'objectives': [
            {'type': 'reach_floor', 'target': 7, 'count': 1},
            {'type': 'kill_boss', 'target': 'boss_dragon', 'count': 1},
        ],
        'reward_gold': 400, 'reward_exp': 250,
        'reward_item': 'pet_egg_common',
        'story_text': '龙骨堆积成山，空气中弥漫着硫磺。远古巨龙睁开金色的眼睛，审视着闯入者。',
        'complete_text': '巨龙低下了高傲的头颅，化作一片金色的鳞片落在你手中。它说："深渊之下，封印着连我都畏惧的东西。"',
    },
    {
        'id': 'main_08', 'chapter': 8, 'floor': 8,
        'name': '毒沼迷踪',
        'desc': '第八层是剧毒丛林，瘴气弥漫，暗影猫妖出没。',
        'objectives': [
            {'type': 'reach_floor', 'target': 8, 'count': 1},
            {'type': 'kill', 'target': 'assassin_enemy', 'count': 8},
        ],
        'reward_gold': 450, 'reward_exp': 280,
        'reward_item': 'regen_potion',
        'story_text': '参天的毒蘑菇和巨大的蕨类植物遮天蔽日。瘴气会让你产生幻觉——你仿佛看到了破晓者前辈们的影子。',
        'complete_text': '穿过毒沼，你找到了一座远古祭坛。祭坛上刻着十二星座，其中三个已经暗淡无光。',
    },
    {
        'id': 'main_09', 'chapter': 9, 'floor': 9,
        'name': '暗影议会',
        'desc': '第九层是深渊教团的议会大厅。五位暗影法师在此集会。',
        'objectives': [
            {'type': 'reach_floor', 'target': 9, 'count': 1},
            {'type': 'kill', 'target': 'mage_enemy', 'count': 15},
            {'type': 'kill_boss', 'target': 'boss_mage', 'count': 1},
        ],
        'reward_gold': 500, 'reward_exp': 320,
        'reward_item': 'ancient_relic',
        'story_text': '紫色的魔法火焰照亮了巨大的圆形大厅。五把高背椅上坐着深渊教团的精英议会成员。',
        'complete_text': '议会覆灭，你从他们手中夺回了一块世界核心的碎片。碎片在你手中微微发光，仿佛在呼唤着什么。',
    },
    {
        'id': 'main_10', 'chapter': 10, 'floor': 10,
        'name': '远古守护者',
        'desc': '第十层是远古巨龙的真正巢穴。守护者不会让你轻易通过。',
        'objectives': [
            {'type': 'reach_floor', 'target': 10, 'count': 1},
            {'type': 'kill_boss', 'target': 'boss_dragon', 'count': 1},
        ],
        'reward_gold': 600, 'reward_exp': 380,
        'reward_item': 'pet_egg_rare',
        'story_text': '比之前所有的龙都更加庞大。远古守护者盘踞在洞穴中央，它的眼睛如同两颗燃烧的太阳。',
        'complete_text': '守护者的身体化作光点消散，留下了通往世界核心的最后通道。你感觉到大地在震颤。',
    },
    {
        'id': 'main_11', 'chapter': 11, 'floor': 11,
        'name': '教团覆灭',
        'desc': '第十一层——深渊教团的最后堡垒。击败教团首领，终结他们的阴谋。',
        'objectives': [
            {'type': 'reach_floor', 'target': 11, 'count': 1},
            {'type': 'kill_boss', 'target': 'boss_knight', 'count': 1},
        ],
        'reward_gold': 700, 'reward_exp': 450,
        'reward_item': 'key_skeleton',
        'story_text': '黑色的魔法屏障笼罩着这层地牢。教团首领——一个身穿黑袍的人影——在等待着你。"你终究还是来了，破晓者。"',
        'complete_text': '"这只是一个开始……"黑袍人消失前留下这句话。你面前的最后一道门缓缓打开，通往世界核心。',
    },
    {
        'id': 'main_12', 'chapter': 12, 'floor': 12,
        'name': '世界核心',
        'desc': '最终章。深入世界核心，面对深渊的源头，封印它——或者被它吞噬。',
        'objectives': [
            {'type': 'reach_floor', 'target': 12, 'count': 1},
            {'type': 'kill_boss', 'target': 'boss_mech', 'count': 2},
            {'type': 'kill_boss', 'target': 'boss_mage', 'count': 2},
        ],
        'reward_gold': 1000, 'reward_exp': 1000,
        'reward_item': 'ancient_relic',
        'story_text': '世界核心——一个巨大的能量漩涡悬浮在空中。无数条能量触须连接着地牢的每一层。'
                      '深渊的源头就在这里，它是一个古老的意识体，被囚禁了数千年。',
        'complete_text': '世界核心的光芒渐渐平息。你用自己的血脉重新封印了深渊。艾尔迪亚大陆恢复了平静，'
                        '但你知道——封印终有一天会再次松动。那时，新的破晓者将会出现。',
    },
]


# ============ 支线任务 ============
SIDE_QUESTS = [
    {
        'id': 'side_cat', 'chapter': 0,
        'name': '丢失的猫',
        'giver': '曙光营地的小孩',
        'desc': '营地的小孩拜托你在地牢中找回他丢失的暗影猫。它可能在第三层附近游荡。',
        'objectives': [
            {'type': 'collect', 'target': 'pet_collar', 'count': 1, 'special': True},
        ],
        'reward_gold': 80, 'reward_exp': 40,
        'reward_item': 'pet_egg_common',
        'story_text': '"我的小猫咪跑到地牢里去了！它脖子上戴着一个银色项圈，上面有我妈妈的名字……"',
        'complete_text': '你把项圈还给小孩。他破涕为笑，送给你一枚宠物蛋作为感谢。',
    },
    {
        'id': 'side_recipe', 'chapter': 0,
        'name': '失传的食谱',
        'giver': '营地厨师',
        'desc': '厨师想复刻古代料理"龙息炖菜"，需要收集火法师的灰烬和冰晶。',
        'objectives': [
            {'type': 'kill', 'target': 'fire_mage', 'count': 8},
            {'type': 'kill', 'target': 'ice_witch', 'count': 5},
        ],
        'reward_gold': 120, 'reward_exp': 60,
        'reward_item': 'health_potion_l',
        'story_text': '"我爷爷的爷爷曾是宫廷厨师！听说龙息炖菜能让战士浑身充满力量。你帮我找齐材料，我分你一份！"',
        'complete_text': '炖菜出锅的瞬间，整个营地都飘满了香气。你吃了一口，感觉浑身充满了力量！（最大HP永久+10）',
    },
    {
        'id': 'side_tome', 'chapter': 0,
        'name': '失落的典籍',
        'giver': '营地学者',
        'desc': '学者在研究深渊的历史，需要你从地牢中找回散落的五本古籍。',
        'objectives': [
            {'type': 'explore', 'target': 'secret', 'count': 5},
        ],
        'reward_gold': 200, 'reward_exp': 100,
        'reward_item': 'scroll_teleport',
        'story_text': '"深渊的历史比我们想象的更加悠久。这些古籍散落在秘密房间中，它们记载着封印的方法。"',
        'complete_text': '学者翻阅着古籍，脸色变得凝重。"这个封印……原来破晓者本身就是钥匙。"',
    },
    {
        'id': 'side_arena', 'chapter': 0,
        'name': '竞技场挑战',
        'giver': '神秘斗篷人',
        'desc': '地牢深处有一个隐藏的竞技场。击败所有挑战者，证明你的实力。',
        'objectives': [
            {'type': 'kill', 'target': 'elite', 'count': 10},
            {'type': 'kill_boss', 'target': 'any', 'count': 2},
        ],
        'reward_gold': 300, 'reward_exp': 180,
        'reward_item': 'weapon_token',
        'story_text': '"强者之路充满挑战。竞技场不问出身，只看实力。你——敢来吗？"',
        'complete_text': '斗篷人摘下兜帽，露出一张苍老的面孔。"你是百年来第一个完成所有挑战的人。这枚令牌代表你的荣耀。"',
    },
    {
        'id': 'side_merchant', 'chapter': 0,
        'name': '商路护航',
        'giver': '自由商盟代表',
        'desc': '商盟的一批珍贵货物被困在第六层。清理沿途的敌人，护送货物回营地。',
        'objectives': [
            {'type': 'reach_floor', 'target': 6, 'count': 1},
            {'type': 'kill', 'target': 'soldier', 'count': 20},
        ],
        'reward_gold': 250, 'reward_exp': 120,
        'reward_item': 'shield_potion',
        'story_text': '"那批货物是我们商盟三个月的收入！深渊教团伏击了我们的护卫队。帮我们夺回来，酬劳好说！"',
        'complete_text': '货物安全运回营地。商盟代表不仅支付了佣金，还告诉你一个秘密——第七层有一条通往核心的捷径。',
    },
    {
        'id': 'side_ghost', 'chapter': 0,
        'name': '未竟的遗愿',
        'giver': '骑士团幽灵',
        'desc': '第四层墓地中，一个幽灵骑士请求你击败曾经杀死他的暗影刺客。',
        'objectives': [
            {'type': 'kill', 'target': 'assassin_enemy', 'count': 15},
        ],
        'reward_gold': 180, 'reward_exp': 100,
        'reward_item': 'key_skeleton',
        'story_text': '"我生前是破晓者的前辈……被深渊教团的刺客从背后偷袭。为我复仇，我的灵魂才能安息。"',
        'complete_text': '幽灵骑士的灵魂化作一道光，融入你的武器。"谢谢……破晓者的荣光永不熄灭。"你的武器升级了！',
    },
    {
        'id': 'side_petmaster', 'chapter': 0,
        'name': '宠物大师',
        'giver': '宠物屋的饲养员',
        'desc': '饲养员想研究不同宠物的进化路径。带你的宠物升到5级，让他记录数据。',
        'objectives': [
            {'type': 'pet_level', 'target': 'any', 'count': 5},
        ],
        'reward_gold': 150, 'reward_exp': 80,
        'reward_item': 'pet_egg_common',
        'story_text': '"每只宠物的进化都让我着迷！你的小可爱很有潜力，让我看看它能成长到什么程度！"',
        'complete_text': '饲养员兴奋地记录着数据。"太神奇了！这种进化模式我以前从未见过！这枚蛋送给你，就当是谢礼！"',
    },
    {
        'id': 'side_weaponmaster', 'chapter': 0,
        'name': '武器大师',
        'giver': '铁匠铺的铁匠',
        'desc': '铁匠想打造一把传说中的武器，需要收集10种不同的武器作为参考。',
        'objectives': [
            {'type': 'collect', 'target': 'weapon', 'count': 10, 'special': True},
        ],
        'reward_gold': 300, 'reward_exp': 150,
        'reward_item': 'weapon_token',
        'story_text': '"传说中有一把可以切开深渊的武器！只要我收集足够的样本，就能还原它的锻造方法！"',
        'complete_text': '铁匠挥舞着新打造的长剑，剑刃上闪烁着蓝色的光芒。"成了！这把剑送给你——它叫"破晓之锋"！"',
    },
]


# ============ 副本任务（周期性刷新） ============
DUNGEON_QUESTS = [
    {
        'id': 'dungeon_clear_1', 'tier': 1,
        'name': '地牢清剿·初级',
        'desc': '清理任意一层的所有敌人（Boss房间除外）',
        'objectives': [{'type': 'clear_floor', 'target': 'any', 'count': 3}],
        'reward_gold': 100, 'reward_exp': 60,
        'cooldown': 2,  # 每2次地牢进入可接一次
    },
    {
        'id': 'dungeon_clear_2', 'tier': 2,
        'name': '地牢清剿·中级',
        'desc': '清理包含Boss房的完整一层',
        'objectives': [{'type': 'clear_floor_boss', 'target': 'any', 'count': 2}],
        'reward_gold': 200, 'reward_exp': 120,
        'cooldown': 3,
    },
    {
        'id': 'dungeon_clear_3', 'tier': 3,
        'name': '地牢清剿·高级',
        'desc': '连续清理三层地牢',
        'objectives': [{'type': 'clear_floors_sequential', 'target': 'any', 'count': 3}],
        'reward_gold': 500, 'reward_exp': 300,
        'cooldown': 5,
    },
    {
        'id': 'dungeon_hunt', 'tier': 2,
        'name': '狩猎任务',
        'desc': '击败指定数量的精英敌人',
        'objectives': [{'type': 'kill', 'target': 'elite', 'count': 8}],
        'reward_gold': 250, 'reward_exp': 150,
        'cooldown': 3,
    },
    {
        'id': 'dungeon_boss', 'tier': 2,
        'name': 'Boss猎杀',
        'desc': '击败两个不同种类的Boss',
        'objectives': [{'type': 'kill_boss', 'target': 'any', 'count': 2}],
        'reward_gold': 350, 'reward_exp': 200,
        'cooldown': 4,
    },
    {
        'id': 'dungeon_gold', 'tier': 1,
        'name': '淘金热',
        'desc': '在地牢中收集500金币',
        'objectives': [{'type': 'collect', 'target': 'gold', 'count': 500}],
        'reward_gold': 150, 'reward_exp': 50,
        'cooldown': 2,
    },
    {
        'id': 'dungeon_secret', 'tier': 2,
        'name': '秘密探索者',
        'desc': '发现秘密房间',
        'objectives': [{'type': 'explore', 'target': 'secret', 'count': 3}],
        'reward_gold': 200, 'reward_exp': 100,
        'cooldown': 2,
    },
]

# 每日任务
DAILY_QUEST_POOL = [
    {'id': 'daily_kill',  'name': '日常·击杀', 'type': 'kill', 'target': 'any', 'count': 20,
     'reward_gold': 80,  'reward_exp': 40,  'desc': '击杀 20 个敌人'},
    {'id': 'daily_gold',  'name': '日常·淘金', 'type': 'collect', 'target': 'gold', 'count': 300,
     'reward_gold': 60,  'reward_exp': 30,  'desc': '获得 300 金币'},
    {'id': 'daily_clear', 'name': '日常·清剿', 'type': 'explore', 'target': 'room', 'count': 8,
     'reward_gold': 70,  'reward_exp': 35,  'desc': '清理 8 个房间'},
]


# ============ 所有模板合集 ============
ALL_TEMPLATES = MAIN_QUESTS + SIDE_QUESTS + DUNGEON_QUESTS + DAILY_QUEST_POOL


class Quest:
    """单个任务实例（主线/支线/副本/每日）"""

    def __init__(self, template_id, current=0):
        self.template_id = template_id
        self.current = current
        self.completed = False
        self.claimed = False
        self.data = {}
        for tpl in ALL_TEMPLATES:
            if tpl['id'] == template_id:
                self.data = dict(tpl)
                break
        if not self.data:
            self.data = {'name': '未知任务', 'type': 'kill', 'target': 'any', 'count': 1,
                         'reward_gold': 0, 'reward_exp': 0, 'desc': ''}

    @property
    def name(self): return self.data.get('name', self.template_id)
    @property
    def desc(self): return self.data.get('desc', '')
    @property
    def count_needed(self): return self.data.get('count', 1) if 'count' in self.data else (
        self.data.get('objectives', [{}])[0].get('count', 1) if self.data.get('objectives') else 1)
    @property
    def reward_gold(self): return self.data.get('reward_gold', 0)
    @property
    def reward_exp(self): return self.data.get('reward_exp', 0)
    @property
    def reward_item(self): return self.data.get('reward_item', None)
    @property
    def category(self):
        if self.template_id.startswith('main_'): return 'main'
        if self.template_id.startswith('side_'): return 'side'
        if self.template_id.startswith('dungeon_'): return 'dungeon'
        if self.template_id.startswith('daily_'): return 'daily'
        return 'other'
    @property
    def story_text(self): return self.data.get('story_text', '')
    @property
    def complete_text(self): return self.data.get('complete_text', '')
    @property
    def objectives(self): return self.data.get('objectives', [{'type': self.data.get('type', 'kill'),
        'target': self.data.get('target', 'any'), 'count': self.data.get('count', 1)}])

    def get_progress_text(self):
        """返回当前进度文本"""
        obs = self.objectives
        if len(obs) == 1 and 'count' in obs[0]:
            return f'{self.current}/{obs[0]["count"]}'
        return f''

    def progress(self, amount=1):
        """推进任务进度"""
        if self.completed or self.claimed:
            return False
        self.current = min(self.count_needed, self.current + amount)
        if self.current >= self.count_needed:
            self.completed = True
        return self.completed

    def claim(self):
        """领取奖励"""
        if not self.completed or self.claimed:
            return (0, 0, None)
        self.claimed = True
        return (self.reward_gold, self.reward_exp, self.reward_item)

    def to_dict(self):
        return {'id': self.template_id, 'current': self.current,
                'completed': self.completed, 'claimed': self.claimed}

    @staticmethod
    def from_dict(d):
        q = Quest(d['id'], d.get('current', 0))
        q.completed = d.get('completed', False)
        q.claimed = d.get('claimed', False)
        return q


class QuestManager:
    """全能任务管理器"""

    def __init__(self):
        self.quests = []          # 已接任务
        self.completed_ids = set()  # 已完成的任务ID
        self.story_chapter = 0     # 当前主线章节(0=未开始)
        self.dungeon_runs = 0      # 副本冷却计数器
        self.daily_quests = []
        self.daily_date = ''

    def get_main_quest(self):
        """获取当前主线任务"""
        if self.story_chapter >= len(MAIN_QUESTS):
            return None  # 主线已全部完成
        mq = MAIN_QUESTS[self.story_chapter]
        # 如果已接未完成，返回Quest实例
        for q in self.quests:
            if q.template_id == mq['id']:
                return q
        return mq  # 返回模板（可接）

    def advance_story(self):
        """推进主线进度"""
        self.story_chapter += 1
        if self.story_chapter < len(MAIN_QUESTS):
            next_q = MAIN_QUESTS[self.story_chapter]
            # 自动接取下一章
            self.add_quest(next_q['id'])
            return next_q
        return None

    def add_quest(self, template_id):
        """接取任务"""
        if template_id in self.completed_ids:
            return False
        for q in self.quests:
            if q.template_id == template_id:
                return False
        self.quests.append(Quest(template_id))
        return True

    def remove_quest(self, template_id):
        self.quests = [q for q in self.quests if q.template_id != template_id]

    def get_quest(self, template_id):
        for q in self.quests:
            if q.template_id == template_id:
                return q
        return None

    def add_progress(self, quest_type, target, amount=1):
        """推进所有匹配的任务进度，返回新完成的任务列表"""
        results = []
        for q in self.quests:
            if q.completed or q.claimed:
                continue
            for obj in q.objectives:
                match = False
                if obj['type'] == quest_type:
                    if obj['target'] == target or obj['target'] == 'any':
                        match = True
                if match:
                    if q.progress(amount):
                        results.append(q)
                    break
        return results

    def claim_quest(self, template_id):
        """领取任务奖励"""
        q = self.get_quest(template_id)
        if q and q.completed and not q.claimed:
            gold, exp, item = q.claim()
            self.completed_ids.add(template_id)
            self.remove_quest(template_id)
            # 如果是主线任务，推进剧情
            if template_id.startswith('main_'):
                next_chapter = self.advance_story()
            return (gold, exp, item)
        return (0, 0, None)

    def refresh_daily(self, today_str=None):
        """刷新每日任务"""
        if today_str is None:
            today_str = str(dt_date.today())
        if self.daily_date == today_str:
            return
        self.daily_date = today_str
        self.daily_quests = []
        chosen = random.sample(DAILY_QUEST_POOL, min(3, len(DAILY_QUEST_POOL)))
        for tpl in chosen:
            self.daily_quests.append(Quest(tpl['id']))

    def get_available_side_quests(self):
        """获取可接取的支线任务"""
        available = []
        for tpl in SIDE_QUESTS:
            if tpl['id'] not in self.completed_ids:
                found = any(q.template_id == tpl['id'] for q in self.quests)
                if not found:
                    available.append(tpl)
        return available

    def get_available_dungeon_quests(self):
        """获取可接取的副本任务（根据冷却）"""
        available = []
        for tpl in DUNGEON_QUESTS:
            if tpl['id'] not in self.completed_ids:
                found = any(q.template_id == tpl['id'] for q in self.quests)
                if not found:
                    available.append(tpl)
        return available

    def get_active_by_category(self, category):
        """按分类获取进行中的任务"""
        return [q for q in self.quests if q.category == category and not q.completed]

    def to_dict(self):
        return {
            'quests': [q.to_dict() for q in self.quests],
            'completed': list(self.completed_ids),
            'story_chapter': self.story_chapter,
            'dungeon_runs': self.dungeon_runs,
            'daily_date': self.daily_date,
            'daily': [q.to_dict() for q in self.daily_quests],
        }

    def from_dict(self, data):
        if not data:
            return
        self.quests = [Quest.from_dict(d) for d in data.get('quests', [])]
        self.completed_ids = set(data.get('completed', []))
        self.story_chapter = data.get('story_chapter', 0)
        self.dungeon_runs = data.get('dungeon_runs', 0)
        self.daily_date = data.get('daily_date', '')
        self.daily_quests = [Quest.from_dict(d) for d in data.get('daily', [])]
