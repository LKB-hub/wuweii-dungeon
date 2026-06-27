"""
核心对战场景 - 玩家、敌人、子弹、道具、技能、商店、音效的完整集成
含Boss分阶段AI、成就追踪、屏幕特效、宝箱/楼层切换等
"""
import math
import random
import time
import pygame
from src.engine.scene import Scene
from src.engine.camera import Camera
from src.engine.resource import get_resources
from src.engine.sound import get_sound_manager
from src.engine.save import get_save_manager
from src.engine.achievements import AchievementTracker
from src.entities.player import Player
from src.entities.particle import ParticleSystem, FloatingText
from src.entities.bullet import Bullet, MeleeAttack
from src.entities.item import Item, generate_loot
from src.entities.skills import SkillManager, Turret
from src.entities.boss_ai import BossBrain, BossPhaseManager, create_boss_bullet_pattern
from src.entities.inventory import Inventory, InventoryUI
from src.entities.pet import Pet
from src.entities.effects import VisualEffects
from src.world.dungeon import Dungeon
from src.ui.hud import HUD, Minimap
from settings import (WINDOW_WIDTH, WINDOW_HEIGHT, WHITE, RED, YELLOW,
                      GREEN, ORANGE, GRAY, BLUE, CYAN, PLAYER_SPEED, TILE_SIZE)


class GameplayScene(Scene):
    """主游戏场景"""

    def __init__(self, game, **kwargs):
        super().__init__(game)
        self.character_id = kwargs.get('character_id', 'knight')
        self.difficulty = kwargs.get('difficulty', 1)
        self.paused = False
        self.game_over = False
        self.victory = False
        self.frame_count = 0
        self.kill_count = 0
        self.start_time = time.time()
        self.damage_taken_this_room = 0
        self.saved_state = kwargs.get('saved_state', None)

        # 音效和存档
        self.sound = get_sound_manager()
        self.save_mgr = get_save_manager()

        # 初始化地牢
        self.dungeon = Dungeon()
        self.dungeon.generate(difficulty=self.difficulty)

        # 初始化玩家
        spawn_x, spawn_y = self.dungeon.get_spawn_point()
        self.player = Player(self.character_id, spawn_x, spawn_y)
        self.player._current_room = None

        # 技能系统
        from src.entities.character import PLAYER_CHARACTERS
        self.skill_manager = SkillManager(self.player)
        self.skill_manager.set_skills(PLAYER_CHARACTERS[self.character_id])
        self.player.skill_manager = self.skill_manager  # HUD 需要通过玩家查找技能冷却

        # 炮台列表
        self.turrets = []

        # 背包系统
        self.inventory = Inventory(max_slots=30)
        self.inventory_ui = InventoryUI(game)
        self.inventory.add_item('health_potion_s', 2)
        self.inventory.add_item('bomb', 1)

        # 宠物系统（随机初始宠物）
        import random as _rnd
        pet_choices = ['fire_dragon', 'healing_fairy', 'shadow_cat']
        self.pet = Pet(_rnd.choice(pet_choices), level=1)
        self.pet.x = spawn_x + 40
        self.pet.y = spawn_y

        # 摄像机、粒子、HUD
        self.camera = Camera(self.dungeon.pixel_width, self.dungeon.pixel_height)
        self.camera.set_target(self.player)
        self.particles = ParticleSystem()
        self.floating_texts = []
        self.hud = HUD(self.screen)
        self.minimap = Minimap()
        self.minimap.set_dungeon(self.dungeon)

        # 子弹和攻击
        self.player_bullets = []
        self.melee_attacks = []
        self.enemy_bullets = []

        # 输入
        self.keys_pressed = set()

        # 商店交互状态
        self.shop_hovered_item = None

        # Boss阶段管理
        self.boss_phase_manager = BossPhaseManager()
        self.boss_special_bullets = []

        # 视觉效果
        self.visual_effects = VisualEffects()

        # 成就追踪
        self.achievement_tracker = AchievementTracker()
        self.achievement_tracker.reset_run_stats()

        # 楼层过渡
        self.transitioning = False
        self.transition_timer = 0
        self.transition_alpha = 0

        # 下一层传送门
        self.next_floor_portal = None  # (x, y) 像素坐标
        self.portal_anim = 0

        # 宝箱交互
        self.near_chest = None
        self.chest_opened = set()

        # 房间清理追踪
        self._room_clear_pending = False
        self._room_clear_timer = 0

        # === 从存档恢复状态 ===
        if self.saved_state:
            self._restore_from_save(self.saved_state)

    def _restore_from_save(self, data):
        """从存档数据恢复玩家状态"""
        try:
            from src.entities.weapon import Weapon

            # 恢复基本属性
            self.player.hp = min(data.get('current_hp', self.player.max_hp), data.get('max_hp', self.player.max_hp))
            self.player.max_hp = data.get('max_hp', self.player.max_hp)
            self.player.energy = min(data.get('current_energy', self.player.max_energy), data.get('max_energy', self.player.max_energy))
            self.player.max_energy = data.get('max_energy', self.player.max_energy)
            self.player.gold = data.get('gold', 0)
            self.player.shield = data.get('shield', 0)
            self.player.exp = data.get('exp', 0)
            self.player.exp_to_next = data.get('exp_to_next', 100)
            self.player.level = data.get('level', 1)
            if hasattr(self.player, 'skill_points'):
                self.player.skill_points = data.get('skill_points', 0)
            self.kill_count = data.get('kills', 0)
            self.dungeon.score = data.get('score', 0)

            # 恢复武器（清空默认武器，从存档精确还原）
            weapons = data.get('weapons', [])
            rarities = data.get('weapon_rarities', [])
            levels = data.get('weapon_levels', [])
            ammos = data.get('weapon_ammo', [])
            if weapons:
                self.player.weapon_manager.slots = [None, None]
                for i, wid in enumerate(weapons):
                    if i >= 2 or wid is None:
                        continue
                    weapon = Weapon(wid)
                    if i < len(rarities) and rarities[i]:
                        weapon.rarity = rarities[i]
                    if i < len(levels) and levels[i]:
                        weapon.level = levels[i]
                        weapon.damage = int(weapon.damage * (1.15 ** (weapon.level - 1)))
                    if i < len(ammos) and ammos[i] is not None:
                        weapon.ammo = ammos[i]
                    self.player.weapon_manager.slots[i] = weapon

            self.hud.add_message('存档已恢复!', GREEN)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f'存档恢复失败: {e}')
            self.hud.add_message('存档恢复部分失败', RED)

    def on_enter(self):
        self.hud.add_message(f'进入地牢，消灭所有敌人!', YELLOW)
        self.sound.play('door_open')

    def on_exit(self):
        """离开时自动存档"""
        self._auto_save('exit')

    def handle_events(self, events):
        for event in events:
            # 如果背包打开，先交给背包处理
            if hasattr(self, 'inventory_ui') and self.inventory_ui.visible:
                result = self.inventory_ui.handle_event(event, self.player, self.inventory)
                if isinstance(result, str):
                    if result == '__bomb__':
                        self._detonate_bomb(self.player.x, self.player.y)
                    else:
                        self.hud.add_message(result, GREEN)
                continue

            if event.type == pygame.KEYDOWN:
                self.keys_pressed.add(event.key)
                if event.key == pygame.K_SPACE:
                    self._player_dodge()
                elif event.key == pygame.K_e:
                    if self.near_chest is not None:
                        self._open_chest(self.near_chest)
                    else:
                        self._use_skill()
                elif event.key == pygame.K_r:
                    self.player.reload()
                elif event.key == pygame.K_q:
                    self.player.switch_weapon()
                elif event.key == pygame.K_1:
                    self.player.weapon_manager.switch_to_slot(0)
                elif event.key == pygame.K_2:
                    self.player.weapon_manager.switch_to_slot(1)
                elif event.key == pygame.K_p:
                    self.paused = not self.paused
                    if self.paused:
                        self.hud.add_message('游戏暂停', WHITE)
                elif event.key == pygame.K_TAB:
                    self.minimap.toggle()
                    self.sound.play('menu_click')
                elif event.key == pygame.K_i:
                    if hasattr(self, 'inventory_ui'):
                        self.inventory_ui.toggle()
                        self.sound.play('menu_click')
                elif event.key == pygame.K_m:
                    self.debug_give_all_weapons()
                elif event.key == pygame.K_F5:
                    self._quick_save()
                elif event.key == pygame.K_F9:
                    self._quick_load()
                elif event.key == pygame.K_ESCAPE:
                    # 先自动保存，再打开存档管理（可返回游戏或退出）
                    self._auto_save('exit')
                    self.switch_to('save_manager', is_playing=True)
            elif event.type == pygame.KEYUP:
                self.keys_pressed.discard(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if not self.paused and not self.game_over:
                        # 检查是否点击了商店
                        if self._handle_shop_click(event.pos):
                            return
                        self._player_fire()
                elif event.button == 3:  # 右键使用技能
                    if not self.paused and not self.game_over:
                        self._use_skill()

    def _player_fire(self):
        """玩家开火"""
        bullets_or_attacks = self.player.fire()
        for obj in bullets_or_attacks:
            if isinstance(obj, MeleeAttack):
                self.melee_attacks.append(obj)
            else:
                self.player_bullets.append(obj)

    def _player_dodge(self):
        if not self.paused and not self.game_over:
            self.player.dodge()
            self.sound.play('dash')
            self.particles.emit(self.player.x + self.player.width // 2,
                                self.player.y + self.player.height // 2,
                                5, (200, 200, 255), speed=4, lifetime=8, size=3)

    def _use_skill(self):
        """使用主动技能"""
        if self.paused or self.game_over:
            return
        mouse_pos = pygame.mouse.get_pos()
        mouse_wx = mouse_pos[0] + self.camera.x
        mouse_wy = mouse_pos[1] + self.camera.y
        result = self.skill_manager.use_active(mouse_wx, mouse_wy)
        if result:
            self._handle_skill_result(result)
            self.sound.play('shoot')

    def _handle_skill_result(self, result):
        """处理技能释放结果"""
        stype = result['type']
        px, py = result['player_x'], result['player_y']

        if stype == 'arrow_rain':
            for arrow in result['arrows']:
                b = Bullet(
                    px, py, arrow['angle'],
                    {'bullet_speed': arrow['speed'], 'damage': arrow['damage'],
                     'bullet_type': arrow['bullet_type']},
                    source_is_player=True)
                self.player_bullets.append(b)

        elif stype == 'thunder_storm':
            for strike in result['strikes']:
                # 直接对范围内敌人造成伤害
                for enemy in self.dungeon.enemies:
                    if not enemy.alive:
                        continue
                    dist = math.hypot(enemy.x - strike['x'], enemy.y - strike['y'])
                    if dist < 60:
                        killed = enemy.take_damage(strike['damage'])
                        self.particles.emit_hit(strike['x'], strike['y'])
                        if killed:
                            self._on_enemy_killed(enemy)

        elif stype == 'shadow_step':
            tp = result['teleport']
            self.player.x = tp['target_x']
            self.player.y = tp['target_y']
            self.particles.emit(px, py, 10, (100, 100, 120), speed=5, lifetime=12)
            # 对路径上的敌人造成伤害
            for enemy in self.dungeon.enemies:
                if not enemy.alive:
                    continue
                if enemy.hitbox.colliderect(pygame.Rect(px - 100, py - 100, 200, 200)):
                    killed = enemy.take_damage(tp['damage'])
                    if killed:
                        self._on_enemy_killed(enemy)

        elif stype == 'holy_light':
            heal = result['heal']
            self.player.hp = min(self.player.max_hp, self.player.hp + heal)
            self.hud.add_message(f'+{heal} HP', GREEN)
            self.particles.emit(px, py, 30, (255, 255, 200), speed=6, lifetime=15)
            for enemy in self.dungeon.enemies:
                if not enemy.alive:
                    continue
                dist = math.hypot(enemy.x - px, enemy.y - py)
                if dist < 200:
                    killed = enemy.take_damage(20)
                    if killed:
                        self._on_enemy_killed(enemy)

        elif stype == 'deploy_turret':
            turret = Turret(px + self.player.width // 2, py + self.player.height // 2)
            self.turrets.append(turret)
            self.hud.add_message('炮台已部署!', BLUE)

        elif stype == 'shield_bash':
            dash = result['dash']
            self.player.x += dash['vx']
            self.player.y += dash['vy']
            self.particles.emit(px, py, 8, (150, 150, 255), speed=5, lifetime=8)
            for enemy in self.dungeon.enemies:
                if not enemy.alive:
                    continue
                if enemy.hitbox.colliderect(pygame.Rect(px - 60, py - 60, 120, 120)):
                    killed = enemy.take_damage(dash['damage'])
                    enemy.stun_timer = dash['stun_duration']
                    if killed:
                        self._on_enemy_killed(enemy)

    def _handle_shop_click(self, mouse_pos):
        """处理商店点击"""
        if not self.dungeon.shop:
            return False
        shop = self.dungeon.shop
        mx = mouse_pos[0] + self.camera.x
        my = mouse_pos[1] + self.camera.y
        item = shop.get_item_at(mx, my)
        if item:
            success, msg = shop.buy_item(item, self.player)
            if success:
                self.hud.add_message(msg, YELLOW)
                self.sound.play('pickup')
            else:
                self.hud.add_message(msg, RED)
                self.sound.play('error')
            return True
        return False

    def _auto_save(self, reason=''):
        """自动存档（退出/切换场景时）"""
        if not hasattr(self, 'player') or not self.player:
            return
        try:
            state = {
                'character_id': self.character_id,
                'difficulty': self.difficulty,
                'current_hp': self.player.hp,
                'max_hp': self.player.max_hp,
                'current_energy': int(self.player.energy),
                'max_energy': self.player.max_energy,
                'gold': self.player.gold,
                'shield': self.player.shield,
                'exp': self.player.exp,
                'exp_to_next': self.player.exp_to_next,
                'level': self.player.level,
                'skill_points': self.player.skill_points if hasattr(self.player, 'skill_points') else 0,
                'kills': self.kill_count,
                'score': self.dungeon.score if hasattr(self, 'dungeon') else 0,
                'floor': self.dungeon.floor_number if hasattr(self, 'dungeon') else 1,
                'weapons': [],
                'weapon_rarities': [],
                'weapon_levels': [],
                'weapon_ammo': [],
            }
            for i, w in enumerate(self.player.weapon_manager.slots):
                if w:
                    state['weapons'].append(w.weapon_id)
                    state['weapon_rarities'].append(getattr(w, 'rarity', 'common'))
                    state['weapon_levels'].append(getattr(w, 'level', 1))
                    state['weapon_ammo'].append(w.ammo)
                else:
                    state['weapons'].append(None)
                    state['weapon_rarities'].append(None)
                    state['weapon_levels'].append(None)
                    state['weapon_ammo'].append(None)
            state['room_progress'] = {r.id: r.cleared for r in self.dungeon.rooms} if hasattr(self, 'dungeon') else {}
            if self.save_mgr.save_game(state):
                if reason == 'exit':
                    self.hud.add_message('游戏已自动保存', GREEN)
                elif reason == 'quit':
                    pass  # 关闭窗口时不显示提示
        except Exception as e:
            print(f'自动存档失败: {e}')

    def _quick_save(self):
        """快速保存"""
        state = {
            'character_id': self.character_id,
            'difficulty': self.difficulty,
            'current_hp': self.player.hp,
            'max_hp': self.player.max_hp,
            'gold': self.player.gold,
            'kills': self.kill_count,
            'score': self.dungeon.score,
            'weapons': [w.weapon_id for w in self.player.weapon_manager.slots if w],
            'dungeon_seed': id(self.dungeon) % 10000,
            'room_progress': {r.id: r.cleared for r in self.dungeon.rooms},
        }
        if self.save_mgr.save_game(state):
            self.hud.add_message('游戏已保存!', GREEN)
            self.sound.play('menu_click')

    def _quick_load(self):
        """快速加载（完整还原存档状态）"""
        if self.save_mgr.has_save():
            self.hud.add_message('已加载存档!', YELLOW)
            self.sound.play('menu_click')
            data = self.save_mgr.load_game()
            if data:
                self.switch_to('gameplay',
                               character_id=data.get('character_id', 'knight'),
                               difficulty=data.get('difficulty', 1),
                               saved_state=data)

    def debug_give_all_weapons(self):
        """调试：给予所有武器"""
        from src.entities.character import WEAPON_DATA
        for wid in WEAPON_DATA:
            slot_id, old_weapon = self.player.weapon_manager.equip(wid)
            if old_weapon and hasattr(self, 'inventory'):
                self.inventory.add_item(old_weapon, 1)
                self.hud.add_message(f'\u66ff\u6362\u4e0b\u7684 {old_weapon} \u5df2\u653e\u5165\u80cc\u5305', GREEN)[0]
        self.hud.add_message('获得所有武器!', GREEN)

    def update(self):
        if self.paused or self.game_over:
            return

        self.frame_count += 1

        # 楼层过渡中
        if self.transitioning:
            self._update_transition()
            return

        # 房间清理延迟
        if self._room_clear_pending:
            self._room_clear_timer -= 1
            if self._room_clear_timer <= 0:
                self._room_clear_pending = False
                self._process_room_clear()
            # 清理动画期间仍绘制但不更新敌人/子弹
            self.particles.update()
            self.hud.update()
            return

        # 更新输入
        dx, dy = 0, 0
        if pygame.K_a in self.keys_pressed or pygame.K_LEFT in self.keys_pressed:
            dx -= 1
        if pygame.K_d in self.keys_pressed or pygame.K_RIGHT in self.keys_pressed:
            dx += 1
        if pygame.K_w in self.keys_pressed or pygame.K_UP in self.keys_pressed:
            dy -= 1
        if pygame.K_s in self.keys_pressed or pygame.K_DOWN in self.keys_pressed:
            dy += 1
        self.player.on_input_move(dx, dy)

        # 获取鼠标世界坐标
        mouse_pos = pygame.mouse.get_pos()

        # 更新玩家
        self.player.update(self.keys_pressed, mouse_pos, self.dungeon, self.camera)

        # 自动攻击（按住鼠标左键时连续开火）
        if pygame.mouse.get_pressed()[0]:
            self._player_fire()

        # 更新摄像机
        self.camera.update()

        # === 玩家子弹更新 ===
        for bullet in self.player_bullets[:]:
            bullet.update(self.dungeon)
            if not bullet.alive:
                self.player_bullets.remove(bullet)
                continue

            for enemy in self.dungeon.enemies[:]:
                if not enemy.alive:
                    continue
                if bullet.hitbox.colliderect(enemy.hitbox):
                    dmg = bullet.damage * self.player.get_damage_multiplier()
                    # 背刺检测
                    if hasattr(self.skill_manager, 'passives') and 'backstab' in self.skill_manager.passives:
                        enemy_angle = math.atan2(enemy.y - self.player.y, enemy.x - self.player.x)
                        player_angle = self.player.facing_angle
                        angle_diff = abs((enemy_angle - player_angle + math.pi) % (2 * math.pi) - math.pi)
                        if angle_diff < math.radians(45):
                            dmg *= self.skill_manager.passives['backstab'].get('backstab_multiplier', 2.0)

                    killed = enemy.take_damage(dmg)
                    self.particles.emit_hit(bullet.x, bullet.y)
                    self.floating_texts.append(
                        FloatingText(bullet.x, bullet.y - 20, f"-{int(dmg)}", RED))

                    if bullet.slow_effect:
                        enemy.apply_effect('slow')
                    if bullet.burn_effect:
                        enemy.apply_effect('burn')

                    if bullet.is_explosive:
                        self.particles.emit_explosion(bullet.x, bullet.y)
                        self.visual_effects.start_screen_shake(4, 8)
                        self._apply_explosion_damage(bullet.x, bullet.y, bullet.explosion_radius, bullet.damage)

                    if killed:
                        self._on_enemy_killed(enemy)
                    else:
                        self.player.add_combo()

                    bullet.alive = False
                    if bullet in self.player_bullets:
                        self.player_bullets.remove(bullet)
                    break

        # === 近战攻击 ===
        for attack in self.melee_attacks[:]:
            attack.update()
            if not attack.alive:
                self.melee_attacks.remove(attack)
                continue
            for enemy in self.dungeon.enemies[:]:
                if not enemy.alive:
                    continue
                if enemy in attack.hit_enemies:
                    continue
                if attack.hits_target(enemy.x + enemy.width // 2, enemy.y + enemy.height // 2):
                    dmg = attack.damage * self.player.get_damage_multiplier()
                    killed = enemy.take_damage(dmg)
                    attack.hit_enemies.add(enemy)
                    self.particles.emit_hit(enemy.x + enemy.width // 2, enemy.y + enemy.height // 2)
                    self.floating_texts.append(
                        FloatingText(enemy.x + enemy.width // 2, enemy.y - 20, f"-{int(dmg)}", ORANGE))
                    if killed:
                        self._on_enemy_killed(enemy)
                    else:
                        self.player.add_combo()

        # === 敌人更新 ===
        for enemy in self.dungeon.enemies[:]:
            if not enemy.alive:
                continue
            enemy.update(self.player, self.dungeon)

            # Boss专用AI
            if enemy.is_boss:
                self._update_boss_behavior(enemy)

            # 敌人攻击
            enemy_bullets = enemy.attempt_attack(self.player)
            for eb in enemy_bullets:
                self.enemy_bullets.append(eb)

            # 碰触伤害 (近战敌人)
            if enemy.ai_type in ('chase', 'boss_chase'):
                dist = math.hypot(enemy.x - self.player.x, enemy.y - self.player.y)
                if dist < enemy.attack_range:
                    if self.player.take_damage(enemy.damage):
                        self.particles.emit_hit(self.player.x + self.player.width // 2,
                                                self.player.y + self.player.height // 2)
                        self.floating_texts.append(
                            FloatingText(self.player.x, self.player.y - 20,
                                         f"-{enemy.damage}", RED))
                        self.achievement_tracker.on_damage_taken(
                            enemy.damage, self.player._current_room and
                            self.player._current_room.room_type == 'boss')

        # === Boss特殊子弹 ===
        for bs in self.boss_special_bullets[:]:
            bs.update(self.dungeon)
            if not bs.alive:
                self.boss_special_bullets.remove(bs)
                continue
            if hasattr(bs, '_mine_lifetime'):
                bs._mine_lifetime -= 1
                if bs._mine_lifetime <= 0:
                    bs.alive = False
                continue
            if bs.hitbox.colliderect(self.player.hitbox):
                if self.player.take_damage(bs.damage):
                    self.particles.emit_hit(self.player.x + self.player.width // 2,
                                            self.player.y + self.player.height // 2)
                    self.floating_texts.append(
                        FloatingText(self.player.x, self.player.y - 20, f"-{bs.damage}", RED))
                bs.alive = False
                self.boss_special_bullets.remove(bs)

        # === 敌人子弹 ===
        for bullet in self.enemy_bullets[:]:
            bullet.update(self.dungeon)
            if not bullet.alive:
                self.enemy_bullets.remove(bullet)
                continue
            if bullet.hitbox.colliderect(self.player.hitbox):
                if self.player.take_damage(bullet.damage):
                    self.particles.emit_hit(self.player.x + self.player.width // 2,
                                            self.player.y + self.player.height // 2)
                    self.floating_texts.append(
                        FloatingText(self.player.x, self.player.y - 20, f"-{bullet.damage}", RED))
                    self.achievement_tracker.on_damage_taken(
                        bullet.damage, self.player._current_room and
                        self.player._current_room.room_type == 'boss')
                bullet.alive = False
                self.enemy_bullets.remove(bullet)

        # === 道具和拾取 ===
        for item in self.dungeon.items[:]:
            item.update()
            if not item.alive:
                self.dungeon.items.remove(item)
                continue
            if self._can_pickup(item):
                self._pickup_item(item)

        # === 技能系统 ===
        self.skill_manager.update()

        # === 炮台 ===
        for turret in self.turrets[:]:
            turret.update(self.dungeon.enemies, self.player_bullets)
            if not turret.alive:
                self.turrets.remove(turret)

        # === 宠物更新 ===
        if hasattr(self, 'pet') and self.pet and self.pet.alive:
            pet_result = self.pet.update(self.player, self.dungeon, self.dungeon.enemies)
            if pet_result:
                action, payload = pet_result
                if action == 'bullet' and payload:
                    self.player_bullets.append(payload)
                elif action == 'heal' and payload:
                    self.floating_texts.append(
                        FloatingText(self.player.x, self.player.y - 30, f'+{payload} HP', GREEN))
                    self.particles.emit_heal(self.player.x, self.player.y)

            # 宠物捡金币同步到HUD
            if hasattr(self.pet, 'collect_gold') and self.pet.collect_gold:
                pass  # 拾取逻辑已在pet.update中处理

            # 宠物的经验来自玩家击杀

        # === 陷阱 ===
        trap_effect = self.dungeon.update_traps(self.player)
        if trap_effect:
            self.player.take_damage(trap_effect['damage'])
            if trap_effect.get('burn', 0) > 0:
                self.player.apply_effect('burn')
            if trap_effect.get('poison', 0) > 0:
                self.player.apply_effect('poison')
            self.particles.emit_hit(self.player.x + self.player.width // 2,
                                    self.player.y + self.player.height // 2)
            self.achievement_tracker.on_damage_taken(trap_effect['damage'], False)

        # === 地牢 ===
        self.dungeon.update()

        # === 粒子 ===
        self.particles.update()
        for ft in self.floating_texts[:]:
            ft.update()
            if not ft.alive:
                self.floating_texts.remove(ft)

        # === 视觉效果 ===
        self.visual_effects.update()

        # === 成就系统 ===
        self.achievement_tracker.update()

        # === HUD ===
        self.hud.update()
        self.hud.kill_count = self.kill_count
        self.hud.run_time = int(time.time() - self.start_time)
        self.hud.dungeon_floor = self.dungeon.floor_number if hasattr(self.dungeon, 'floor_number') else 1

        # === 房间检测 ===
        self.player._current_room = self.dungeon.get_room_at(self.player.x, self.player.y)
        room = self.player._current_room
        if room and not room.visited:
            room.visited = True
            self.minimap.mark_visited(room)
            room_type_name = {
                'boss': 'BOSS 房间! 准备战斗!',
                'chest': '宝箱房! 打开宝箱获取奖励!',
                'shop': '商店!',
            }.get(room.room_type, '')
            if room_type_name and room.room_type != 'start':
                self.hud.add_message(room_type_name, YELLOW)
            if room.room_type == 'boss':
                self.achievement_tracker.progress['damage_taken_boss'] = 0
            # 触发房间事件
            if room.room_type not in ('start', 'shop', 'boss', 'chest'):
                self._trigger_room_event(room)

        # === 危险地块检测 ===
        self._check_hazard_tiles()

        # === 宝箱检测 ===
        self._check_chest_proximity()

        # === 房间清理检测 ===
        self._check_room_clear()

        # === Boss房清理 → 召唤传送门 ===
        if self.dungeon.boss_room and self.dungeon.boss_room.cleared:
            if self.next_floor_portal is None:
                cx, cy = self.dungeon.boss_room.center()
                self.next_floor_portal = (cx, cy)
                self.particles.emit_ring(cx, cy, (100, 200, 255), count=20, radius=30, lifetime=30)
                self.sound.play('portal')
                self.hud.add_message('传送门已开启！走向它前往下一层', CYAN)

        # === 传送门交互 ===
        if self.next_floor_portal:
            px, py = self.next_floor_portal
            dist = math.hypot(self.player.x - px, self.player.y - py)
            if dist < 50 and not self.transitioning:
                self._go_to_next_floor()

        # === 胜利条件：最后一层Boss清空 ===
        if self.dungeon.boss_room and self.dungeon.boss_room.cleared:
            if self.dungeon.floor_number >= self.dungeon.max_floor:
                if not self.victory:
                    self.victory = True
                    self._trigger_victory_sequence()

        # === 死亡条件 ===
        if not self.player.is_alive():
            self.particles.emit_death(self.player.x + self.player.width // 2,
                                       self.player.y + self.player.height // 2)
            self.visual_effects.start_screen_shake(12, 20)
            self.visual_effects.trigger_screen_flash((255, 50, 50), 20, 120)
            self.camera.start_shake(15, 25)
            # 死亡时删除当前存档（永久死亡模式）
            try:
                self.save_mgr.delete_save(0)
            except:
                pass
            self.game_over = True
            self.victory = False

        # === 游戏结束延迟后切换场景 ===
        if self.game_over and not self.victory and self.frame_count % 120 == 0:
            self._end_game()
        elif self.victory and self.frame_count % 180 == 0:
            self._end_game()

    def _update_transition(self):
        """楼层过渡动画"""
        self.transition_timer -= 1
        if self.transition_timer > 30:
            self.transition_alpha = min(255, self.transition_alpha + 8)
        elif self.transition_timer > 0:
            self.transition_alpha = max(0, self.transition_alpha - 8)
        else:
            self.transitioning = False
            self.transition_alpha = 0
        self.particles.update()

    def _update_boss_behavior(self, boss):
        """更新Boss阶段行为"""
        state = self.boss_phase_manager.update(boss, self.player, self.dungeon, self.frame_count)
        behavior = BossBrain.get_phase_behavior(boss, self.player, self.dungeon)

        # 应用阶段速度修改（只基于基础速度，避免每帧累乘）
        if 'speed_mult' in behavior:
            from src.entities.character import BOSS_TYPES
            base_speed = boss.speed
            if not hasattr(boss, '_base_speed'):
                boss._base_speed = BOSS_TYPES.get(boss.enemy_type, {}).get('speed', base_speed)
            boss.speed = boss._base_speed * behavior['speed_mult']

        # 执行特殊攻击
        if behavior.get('special_attack'):
            if state['special_cooldown'] <= 0:
                special = behavior['special_attack']
                bullets = BossBrain.execute_special(boss, self.player, self.dungeon, special)
                self.boss_special_bullets.extend(bullets)
                state['special_cooldown'] = special.get('cooldown', 120)

                # 添加特效
                bx = boss.x + boss.width // 2
                by = boss.y + boss.height // 2
                if special['type'] == 'ice_storm':
                    self.visual_effects.trigger_freeze_overlay(30)
                elif special['type'] == 'fire_breath_cone':
                    self.visual_effects.trigger_screen_flash((255, 100, 20), 8, 60)
                    self.camera.start_shake(6, 15)
                elif special['type'] == 'laser_beam':
                    self.visual_effects.trigger_screen_flash((255, 50, 50), 5, 80)
                    self.camera.start_shake(4, 10)
                elif special['type'] == 'dive_bomb':
                    self.visual_effects.start_screen_shake(10, 16)
                    self.camera.start_shake(10, 16)
                elif special['type'] == 'spin_attack':
                    self.visual_effects.add_aura(bx, by, 120, (255, 100, 50), 20, 0.08)
                    self.camera.start_shake(5, 12)
                elif special['type'] == 'missile_barrage':
                    self.visual_effects.trigger_screen_flash((255, 150, 50), 6, 40)
                    self.camera.start_shake(3, 8)

    def _check_chest_proximity(self):
        """检测玩家是否靠近宝箱"""
        room = self.player._current_room
        if not room or room.room_type != 'chest':
            self.near_chest = None
            return
        if room.id in self.chest_opened:
            self.near_chest = None
            return
        cx, cy = room.center()
        dist = math.hypot(cx - self.player.x - self.player.width // 2,
                          cy - self.player.y - self.player.height // 2)
        if dist < 60:
            self.near_chest = room
        else:
            self.near_chest = None

    def _open_chest(self, room):
        """打开宝箱"""
        if room.id in self.chest_opened:
            return
        self.chest_opened.add(room.id)
        cx, cy = room.center()

        # 随机奖励
        reward_type = random.choice(['gold', 'weapon', 'health', 'energy', 'shield'])
        if reward_type == 'gold':
            amount = random.randint(30, 80)
            self.player.gold += amount
            self.hud.add_message(f'宝箱: +{amount} 金币!', YELLOW)
            self.achievement_tracker.on_gold_collected(amount)
        elif reward_type == 'weapon':
            from src.entities.character import SHOP_WEAPONS, WEAPON_DATA
            wid = random.choice(SHOP_WEAPONS)
            slot_id, old_weapon = self.player.weapon_manager.equip(wid)
            wname = WEAPON_DATA[wid]['name']
            msg = f'宝箱: 获得 [{wname}]!'
            if old_weapon and hasattr(self, 'inventory'):
                self.inventory.add_item(old_weapon, 1)
                msg += f' 旧武器已存入背包'
            self.hud.add_message(msg, YELLOW)
            self.achievement_tracker.on_weapon_used(wid)
        elif reward_type == 'health':
            heal = random.randint(30, 60)
            self.player.hp = min(self.player.max_hp, self.player.hp + heal)
            self.hud.add_message(f'宝箱: +{heal} HP!', GREEN)
        elif reward_type == 'energy':
            energy = random.randint(40, 80)
            self.player.energy = min(self.player.max_energy, self.player.energy + energy)
            self.hud.add_message(f'宝箱: +{energy} 能量!', BLUE)
        elif reward_type == 'shield':
            shield = random.randint(20, 40)
            self.player.shield += shield
            self.hud.add_message(f'宝箱: +{shield} 护盾!', (80, 200, 240))

        self.particles.emit(cx, cy, 30, (255, 215, 0), speed=6, lifetime=20)
        self.sound.play('coin')
        self.visual_effects.add_aura(cx, cy, 80, (255, 215, 0), 25, 0.06)

    def _check_room_clear(self):
        """检测房间是否已清理"""
        room = self.player._current_room
        if not room or room.cleared or room.room_type == 'start':
            return
        # 检查房间内是否有存活的敌人
        alive_in_room = [e for e in self.dungeon.enemies
                         if e.alive and self.dungeon.get_room_at(e.x, e.y) == room]
        if not alive_in_room:
            room.cleared = True
            # 房间清理奖励
            room_score = 50 if room.room_type != 'boss' else 200
            self.dungeon.score += room_score
            self.player.rooms_cleared += 1
            self.floating_texts.append(
                FloatingText(room.center()[0], room.center()[1] - 30,
                             f'房间清理! +{room_score}', YELLOW))
            self.hud.add_message('房间已清理!', GREEN)

            # 成就追踪
            self.achievement_tracker.on_room_cleared(room.room_type == 'boss')

            # 打开房门
            room.opened = True

            # 房间清理特效
            cx, cy = room.center()
            self.visual_effects.add_aura(cx, cy, room.width * TILE_SIZE // 2,
                                         (200, 200, 100), 20, 0.04)
            self.particles.emit(cx, cy, 20, (255, 255, 200), speed=3, lifetime=25)

            self._room_clear_pending = True
            self._room_clear_timer = 15

    def _process_room_clear(self):
        """处理房间清理后续（Boss房由传送门系统处理）"""
        room = self.player._current_room
        if not room:
            return

    def _trigger_room_event(self, room):
        """触发房间事件"""
        event = self.dungeon.trigger_room_event(room)
        if not event:
            return

        ename = event['name']
        event_names = {
            'enemy_ambush': '伏击！敌人从暗处涌出！',
            'treasure_room': '发现隐藏宝箱！',
            'healing_fountain': '治疗之泉恢复了你的生命！',
            'trap_gauntlet': '陷阱挑战！小心脚下！',
            'time_rift': '时空裂隙出现...',
        }
        if ename in event_names:
            self.hud.add_message(event_names[ename], ORANGE if ename == 'enemy_ambush' else GREEN)

        # dungeon 处理实际效果
        self.dungeon.apply_room_event(room, self.player)

        # 额外视觉特效
        cx, cy = room.center()
        if ename == 'enemy_ambush':
            self.particles.emit(cx, cy, 15, (255, 50, 50), speed=5, lifetime=15)
        elif ename == 'treasure_room':
            self.particles.emit(cx, cy, 15, (255, 215, 0), speed=4, lifetime=18)
        elif ename == 'healing_fountain':
            self.particles.emit(cx, cy, 20, (100, 255, 100), speed=4, lifetime=20)
        elif ename == 'trap_gauntlet':
            self.particles.emit(cx, cy, 10, (255, 100, 30), speed=3, lifetime=15)
        elif ename == 'time_rift':
            self.visual_effects.trigger_screen_flash((100, 100, 255), 15, 60)

    def _spawn_ambush_enemies(self, room):
        """在房间内生成伏击敌人"""
        from src.entities.character import ENEMY_TYPES
        from src.entities.enemy import Enemy
        count = random.randint(3, 6)
        room_world_x = room.x * TILE_SIZE
        room_world_y = room.y * TILE_SIZE
        room_w = room.width * TILE_SIZE
        room_h = room.height * TILE_SIZE
        for _ in range(count):
            ex = room_world_x + random.randint(40, max(40, room_w - 40))
            ey = room_world_y + random.randint(40, max(40, room_h - 40))
            etype = random.choice(['soldier', 'archer', 'bomber'])
            if etype in ENEMY_TYPES:
                enemy = Enemy(ex, ey, etype)
                self.dungeon.enemies.append(enemy)
                self.minimap.mark_enemy_spawn(enemy)

    def _spawn_event_treasure(self, room):
        """在房间内生成事件宝箱"""
        from src.entities.item import Item
        cx, cy = room.center()
        # 生成一个特殊道具
        item = Item(cx, cy, 'gold_pile', value=random.randint(40, 80))
        self.dungeon.items.append(item)
        self.particles.emit(cx, cy, 15, (255, 215, 0), speed=4, lifetime=18)

    def _spawn_room_traps(self, room):
        """在房间内生成陷阱"""
        room_world_x = room.x * TILE_SIZE
        room_world_y = room.y * TILE_SIZE
        room_w = room.width * TILE_SIZE
        room_h = room.height * TILE_SIZE
        count = random.randint(4, 8)
        for _ in range(count):
            tx = room_world_x + random.randint(40, max(40, room_w - 40))
            ty = room_world_y + random.randint(40, max(40, room_h - 40))
            trap_type = random.choice(['spike', 'fire', 'poison'])
            self.dungeon.add_trap(tx, ty, trap_type)

    def _check_hazard_tiles(self):
        """检测玩家脚下的危险地块"""
        room = self.player._current_room
        if not room:
            return
        tile_x = int(self.player.x + self.player.width // 2) // TILE_SIZE
        tile_y = int(self.player.y + self.player.height // 2) // TILE_SIZE
        tile = self.dungeon.get_tile(tile_x, tile_y)
        if tile is None:
            return
        tile_type = getattr(tile, 'tile_type', 'floor')

        if tile_type == 'lava':
            if self.frame_count % 30 == 0:
                dmg = max(1, int(self.player.max_hp * 0.03))
                self.player.take_damage(dmg)
                self.particles.emit_hit(self.player.x + self.player.width // 2,
                                        self.player.y + self.player.height // 2)
                self.floating_texts.append(
                    FloatingText(self.player.x, self.player.y - 20, f'-{dmg}', RED))
        elif tile_type == 'water':
            if not hasattr(self.player, '_water_slow'):
                self.player._water_slow = True
                self.player.slow_duration = max(self.player.slow_duration, 30)
        elif tile_type == 'pit':
            dist = math.hypot(
                self.player.x + self.player.width // 2 - room.center()[0],
                self.player.y + self.player.height // 2 - room.center()[1])
            if dist < TILE_SIZE * 2:
                self.player.take_damage(20)
                # 传送回房间中心
                cx, cy = room.center()
                self.player.x = cx - self.player.width // 2
                self.player.y = cy - self.player.height // 2
                self.particles.emit(self.player.x, self.player.y, 10, (100, 50, 200), speed=5, lifetime=12)
                self.hud.add_message('掉入深渊！被传送回房间中心!', RED)
        elif tile_type != 'pit':
            if hasattr(self.player, '_water_slow'):
                del self.player._water_slow

    def _go_to_next_floor(self):
        """前往下一层"""
        self.transitioning = True
        self.transition_timer = 60
        self.transition_alpha = 0
        self.sound.play('portal')
        self.hud.add_message(f'前往第 {self.dungeon.floor_number + 1} 层...', CYAN)

        # 新地牢保持玩家状态，重置房间相关内容
        old_gold = self.player.gold
        old_hp = self.player.hp
        old_max_hp = self.player.max_hp
        old_energy = self.player.energy
        old_max_energy = self.player.max_energy
        old_shield = self.player.shield
        old_exp = self.player.exp
        old_level = self.player.level

        # 生成新楼层
        self.dungeon.generate_next_floor()

        # 恢复玩家位置到新楼层起点
        spawn_x, spawn_y = self.dungeon.get_spawn_point()
        self.player.x, self.player.y = spawn_x, spawn_y
        self.player.hp = min(old_hp + 20, old_max_hp)  # 每层奖励回血
        self.player.energy = min(old_energy + 30, old_max_energy)
        self.player.shield = old_shield
        self.player.gold = old_gold
        self.player.exp = old_exp
        self.player.level = old_level
        self.player._current_room = None

        # 更新摄像机
        self.camera = Camera(self.dungeon.pixel_width, self.dungeon.pixel_height)
        self.camera.set_target(self.player)

        # 清空子/弹
        self.player_bullets = []
        self.enemy_bullets = []
        self.melee_attacks = []
        self.boss_special_bullets = []
        self.turrets = []

        # 更新小地图
        self.minimap = Minimap()
        self.minimap.set_dungeon(self.dungeon)

        # 重置传送门
        self.next_floor_portal = None

        # 宠物跟随到新层
        self.pet.x = spawn_x + 40
        self.pet.y = spawn_y

        self.hud.dungeon_floor = self.dungeon.floor_number
        self.hud.add_message(self.dungeon.get_floor_name(), YELLOW)

    def _draw_portal(self, screen):
        if not self.next_floor_portal:
            return
        px, py = self.next_floor_portal
        self.portal_anim += 0.05
        sx, sy = self.camera.apply_point(px, py)
        r = int(20 + 5 * math.sin(self.portal_anim))
        colors = [(100, 180, 255), (150, 200, 255), (200, 220, 255)]
        for i, c in enumerate(colors):
            pr = r + i * 6 + int(3 * math.sin(self.portal_anim + i))
            alpha = 150 - i * 40
            surf = pygame.Surface((pr * 2, pr * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*c, alpha), (pr, pr), pr)
            screen.blit(surf, (sx - pr, sy - pr))
        inner_r = int(8 + 4 * math.sin(self.portal_anim * 1.5))
        pygame.draw.circle(screen, (200, 230, 255), (int(sx), int(sy)), inner_r)
        try:
            from src.engine.font_helper import get_chinese_font
            font = get_chinese_font(12)
            hint = font.render('>>> portal <<<', True, (180, 220, 255))
            screen.blit(hint, (int(sx) - hint.get_width() // 2, int(sy) - r - 22))
        except:
            pass

    def _trigger_victory_sequence(self):
        """触发胜利序列效果"""
        self.visual_effects.start_screen_shake(6, 20)
        self.visual_effects.trigger_screen_flash((255, 215, 0), 30, 100)
        self.sound.play('victory')
        self.game_over = True
        px = self.player.x + self.player.width // 2
        py = self.player.y + self.player.height // 2
        self.particles.emit(px, py, 50, (255, 215, 0), speed=8, lifetime=60)
        self.particles.emit(px, py, 30, (255, 100, 50), speed=5, lifetime=45)
        self.visual_effects.add_aura(px, py, 300, (255, 215, 0), 60, 0.03)

    def _end_game(self):
        """结束游戏并切换场景"""
        hp_pct = self.player.hp / self.player.max_hp
        time_elapsed = time.time() - self.start_time
        self.achievement_tracker.on_game_end(self.victory, time_elapsed, hp_pct,
                                             self.kill_count)
        self.switch_to('gameover',
                       victory=self.victory,
                       score=self.dungeon.score + self.player.gold,
                       gold=self.player.gold,
                       kills=self.kill_count,
                       max_combo=self.player.max_combo,
                       damage_dealt=self.player.damage_dealt,
                       damage_taken=self.player.damage_taken,
                       time_elapsed=time_elapsed,
                       character_id=self.character_id,
                       achievements=self.achievement_tracker.pending_notifications[:])

    def _can_pickup(self, item):
        dist = math.hypot(item.x - self.player.x, item.y - self.player.y)
        return dist < item.pickup_range

    def _pickup_item(self, item):
        result = item.apply(self.player)
        if result == "__bomb__":
            # 炸弹：对所有敌人造成范围伤害
            bomb_damage = 80
            for enemy in self.dungeon.enemies[:]:
                if not enemy.alive:
                    continue
                dist = math.hypot(enemy.x - self.player.x, enemy.y - self.player.y)
                if dist < 300:
                    killed = enemy.take_damage(bomb_damage)
                    self.particles.emit_explosion(enemy.x, enemy.y)
                    if killed:
                        self._on_enemy_killed(enemy)
            self.particles.emit_explosion(self.player.x, self.player.y)
            self.sound.play('explosion')
            self.hud.add_message('炸弹爆炸! 清屏伤害!', (255, 100, 30))
        elif result:
            self.hud.add_message(result, GREEN if 'HP' in str(result) or '金币' in str(result) else WHITE)

    def _on_enemy_killed(self, enemy):
        self.kill_count += 1
        self.dungeon.score += enemy.score
        self.particles.emit_death(enemy.x + enemy.width // 2, enemy.y + enemy.height // 2)
        self.floating_texts.append(
            FloatingText(enemy.x + enemy.width // 2, enemy.y - 30, f"+{enemy.score}", YELLOW))

        # 成就追踪
        self.achievement_tracker.on_enemy_killed(
            is_boss=enemy.is_boss,
            boss_type=enemy.enemy_type if enemy.is_boss else None)

        # Boss死亡特效
        if enemy.is_boss:
            self.visual_effects.start_screen_shake(10, 18)
            self.visual_effects.trigger_screen_flash((255, 200, 50), 15, 100)
            self.visual_effects.add_aura(enemy.x + enemy.width // 2, enemy.y + enemy.height // 2,
                                         200, (255, 215, 0), 40, 0.05)
            self.camera.start_shake(12, 20)
            self.boss_phase_manager.cleanup(enemy)
            self.sound.play('explosion')

        # 自爆
        if enemy.explodes:
            self.particles.emit_explosion(enemy.x + enemy.width // 2, enemy.y + enemy.height // 2)
            self.visual_effects.start_screen_shake(3, 6)
            dist = math.hypot(enemy.x - self.player.x, enemy.y - self.player.y)
            if dist < 80:
                self.player.take_damage(enemy.damage)

        # 生成掉落
        loot = generate_loot(
            enemy.x, enemy.y, enemy.is_boss)
        self.dungeon.items.extend(loot)

    def _apply_explosion_damage(self, x, y, radius, damage):
        for enemy in self.dungeon.enemies[:]:
            if not enemy.alive:
                continue
            dist = math.hypot(enemy.x - x, enemy.y - y)
            if dist < radius:
                killed = enemy.take_damage(damage * 0.5)
                if killed:
                    self._on_enemy_killed(enemy)

    def draw(self):
        # 绘制地牢
        self.dungeon.draw(self.screen, self.camera)

        # 绘制道具
        for item in self.dungeon.items:
            if item.alive:
                item.draw(self.screen, self.camera)

        # 绘制敌人
        for enemy in self.dungeon.enemies:
            if enemy.alive:
                enemy.draw(self.screen, self.camera)

        # 绘制玩家子弹
        for bullet in self.player_bullets:
            if bullet.alive:
                bullet.draw(self.screen, self.camera)

        # 绘制Boss特殊子弹
        for bullet in self.boss_special_bullets:
            if bullet.alive:
                bullet.draw(self.screen, self.camera)

        # 绘制敌人子弹
        for bullet in self.enemy_bullets:
            if bullet.alive:
                bullet.draw(self.screen, self.camera)

        # 绘制近战攻击
        for attack in self.melee_attacks:
            if attack.alive:
                attack.draw(self.screen, self.camera)

        # 绘制炮台
        for turret in self.turrets:
            if turret.alive:
                turret.draw(self.screen, self.camera)

        # 绘制视觉效果（世界坐标）
        self.visual_effects.draw(self.screen, self.camera)

        # 绘制玩家
        self.player.draw(self.screen, self.camera)
        self.player.draw_weapon_effect(self.screen, self.camera)

        # 绘制粒子
        self.particles.draw(self.screen, self.camera)
        for ft in self.floating_texts:
            if ft.alive:
                ft.draw(self.screen, self.camera)

        # 绘制 HUD
        self.hud.draw(self.player)
        self.minimap.draw(self.screen, self.dungeon, self.player)

        # 宝箱提示
        if self.near_chest is not None:
            self.game.draw_text('按 E 打开宝箱', WINDOW_WIDTH // 2, WINDOW_HEIGHT - 60,
                                YELLOW, size=22, center=True)

        # 成就通知（屏幕坐标）
        self.achievement_tracker.draw_notifications(self.screen)

        # 暂停覆盖
        if self.paused:
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            self.screen.blit(overlay, (0, 0))
            self.game.draw_text('游 戏 暂 停', WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 30,
                                WHITE, size=40, center=True)
            self.game.draw_text('按 P 继续  |  ESC 退出', WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 20,
                                GRAY, size=20, center=True)

        # 传送门绘制
        if self.next_floor_portal:
            self._draw_portal(self.screen)

        # 宠物绘制
        if hasattr(self, 'pet') and self.pet and self.pet.alive:
            self.pet.draw(self.screen, self.camera)

        # 背包UI（覆盖在最上层）
        if hasattr(self, 'inventory_ui') and self.inventory_ui.visible:
            self.inventory_ui.update()
            self.inventory_ui.draw(self.screen, self.inventory, self.player)

        # 胜利提示
        if self.victory and not self.paused:
            self.game.draw_text('BOSS 已被击败!', WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 20,
                                YELLOW, size=36, center=True)
            self.game.draw_text('恭喜通关!', WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 30,
                                (255, 200, 100), size=24, center=True)

        # 楼层过渡覆盖
        if self.transitioning:
            alpha = min(255, max(0, self.transition_alpha))
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, alpha))
            self.screen.blit(overlay, (0, 0))
            if alpha > 100:
                self.game.draw_text(f'第 {self.dungeon.floor_number} 层',
                                    WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2,
                                    WHITE, size=36, center=True)
