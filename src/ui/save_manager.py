"""
存档管理 - 多存档位浏览、保存、加载、删除
"""
import os
import math
import pygame
from src.engine.scene import Scene
from src.engine.font_helper import get_chinese_font
from settings import WINDOW_WIDTH, WINDOW_HEIGHT, WHITE, YELLOW, GREEN, RED, GRAY, CYAN, ORANGE


CHAR_NAMES = {
    'knight': '骑士', 'ranger': '游侠', 'mage': '法师',
    'assassin': '刺客', 'paladin': '圣骑士', 'engineer': '工程师',
}


class SaveManagerScene(Scene):
    """存档管理界面"""

    def __init__(self, game, **kwargs):
        super().__init__(game)
        from src.engine.save import get_save_manager, MAX_SAVE_SLOTS
        self.save_mgr = get_save_manager()
        self.max_slots = MAX_SAVE_SLOTS
        self.slot_data = []  # 预览数据列表
        self.selected = 0
        self.anim_timer = 0
        self.mode = 'browse'  # 'browse', 'confirm_delete', 'confirm_save'
        self.confirm_target = -1
        self.message = ''
        self.message_timer = 0
        self.is_playing = kwargs.get('is_playing', False)  # 是否在游戏中打开

    def on_enter(self):
        self.refresh_slots()

    def refresh_slots(self):
        """刷新存档槽位数据"""
        self.slot_data = []
        for s in range(self.max_slots):
            preview = self.save_mgr.get_save_preview(s)
            self.slot_data.append(preview)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if self.mode == 'confirm_delete':
                    if event.key == pygame.K_y:
                        self.save_mgr.delete_save(self.confirm_target)
                        self.refresh_slots()
                        self.message = f'存档 {self.confirm_target + 1} 已删除'
                        self.message_timer = 120
                        self.mode = 'browse'
                    elif event.key in (pygame.K_n, pygame.K_ESCAPE):
                        self.mode = 'browse'
                        self.confirm_target = -1
                    continue

                if event.key == pygame.K_ESCAPE:
                    if self.is_playing:
                        self.switch_to('gameplay')
                    else:
                        self.switch_to('menu')
                elif event.key == pygame.K_UP:
                    self.selected = (self.selected - 1) % self.max_slots
                elif event.key == pygame.K_DOWN:
                    self.selected = (self.selected + 1) % self.max_slots
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    self._action_load()
                elif event.key == pygame.K_s:
                    self._action_save()
                elif event.key == pygame.K_d:
                    self._action_delete()
                elif event.key == pygame.K_l:
                    self._action_load()
                elif event.key == pygame.K_i:
                    # 查看存档详情
                    pass

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mx, my = event.pos
                    # 点击存档槽
                    for i in range(self.max_slots):
                        sx = 200
                        sy = 120 + i * 100
                        if sx <= mx <= sx + 880 and sy <= my <= sy + 85:
                            self.selected = i
                            self._action_load()
                            break

    def _action_load(self):
        """加载选中的存档"""
        if self.slot_data[self.selected] is None:
            self.message = '该存档位是空的'
            self.message_timer = 60
            return
        data = self.save_mgr.load_game(self.selected)
        if data:
            self.switch_to('gameplay',
                           character_id=data.get('character_id', 'knight'),
                           difficulty=data.get('difficulty', 1),
                           saved_state=data)

    def _action_save(self):
        """保存到选中的存档位"""
        # 从 gameplay 调用时才有意义
        if self.is_playing:
            self.confirm_target = self.selected
            self.mode = 'confirm_save'
            self.message = f'保存到存档 {self.selected + 1}？ (Y/N)'
            self.message_timer = 180
        else:
            self.message = '只能在游戏中保存'
            self.message_timer = 60

    def _action_delete(self):
        """删除选中的存档"""
        if self.slot_data[self.selected] is None:
            self.message = '该存档位已是空的'
            self.message_timer = 60
            return
        self.confirm_target = self.selected
        self.mode = 'confirm_delete'
        self.message = f'确定删除存档 {self.selected + 1}？ (Y/N)'
        self.message_timer = 0

    def update(self):
        self.anim_timer += 0.03
        if self.message_timer > 0:
            self.message_timer -= 1

    def draw(self):
        self.screen.fill((18, 16, 30))

        # 标题
        title_pulse = 1 + 0.03 * math.sin(self.anim_timer * 0.8) if 'math' in dir() else 1
        try:
            self.game.draw_text('存 档 管 理', WINDOW_WIDTH // 2, 40, YELLOW,
                                size=34, bold=True, center=True)
        except:
            pass
        self.game.draw_text(f'共 {self.max_slots} 个存档位', WINDOW_WIDTH // 2, 72, GRAY, size=14, center=True)

        # 绘制每个存档槽
        for i in range(self.max_slots):
            preview = self.slot_data[i]
            sy = 120 + i * 100
            sx = 200
            slot_w = 880
            slot_h = 85
            is_selected = (i == self.selected)

            # 背景
            bg_color = (35, 32, 50) if is_selected else (25, 22, 40)
            border_color = YELLOW if is_selected else (60, 58, 80)
            border_w = 2 if is_selected else 1

            self.game.draw_rect(sx, sy, slot_w, slot_h, bg_color)
            pygame.draw.rect(self.screen, border_color, (sx, sy, slot_w, slot_h), border_w)

            # 选中发光
            if is_selected:
                glow = int(20 + 15 * math.sin(self.anim_timer * 2))
                pygame.draw.rect(self.screen, (*YELLOW[:3], glow), (sx - 1, sy - 1, slot_w + 2, slot_h + 2), 1)

            # 存档编号
            self.game.draw_text(f'#{i + 1}', sx + 30, sy + 10, GRAY, size=20, bold=True)

            if preview is None:
                # 空存档位
                self.game.draw_text('— 空 —', sx + slot_w // 2, sy + slot_h // 2, (60, 60, 75), size=18, center=True)
                self.game.draw_text('选择后按 S 保存', sx + slot_w // 2, sy + slot_h // 2 + 22, (50, 50, 60), size=12, center=True)
            else:
                # 有存档数据
                cid = preview.get('character', '?')
                cname = CHAR_NAMES.get(cid, cid)
                floor = preview.get('floor', 1)
                level = preview.get('level', 1)
                gold = preview.get('gold', 0)
                score = preview.get('score', 0)
                ts = preview.get('time', '')

                # 角色名
                self.game.draw_text(f'{cname}', sx + 80, sy + 12, WHITE, size=20, bold=True)
                # 楼层 & 等级
                self.game.draw_text(f'楼层: {floor}F  |  等级: Lv.{level}', sx + 80, sy + 40, CYAN, size=14)
                # 金币和分数
                self.game.draw_text(f'金币: {gold}', sx + 350, sy + 12, (255, 200, 50), size=16)
                self.game.draw_text(f'分数: {score}', sx + 350, sy + 40, ORANGE, size=14)
                # 时间
                if ts:
                    # Try to format timestamp
                    time_str = ts[:19] if len(ts) > 19 else ts
                    self.game.draw_text(time_str, sx + 550, sy + 12, GRAY, size=12)
                # 操作提示
                self.game.draw_text('L=加载  S=保存  D=删除', sx + 550, sy + 42, (80, 80, 100), size=12)

        # 底部提示
        y = WINDOW_HEIGHT - 40
        self.game.draw_text('↑↓ 选择  |  回车/空格 加载  |  S 保存  |  D 删除  |  ESC 返回',
                            WINDOW_WIDTH // 2, y, GRAY, size=13, center=True)

        # 消息
        if self.message_timer > 0:
            alpha = min(255, self.message_timer * 4)
            color = (*YELLOW[:3], alpha)
            self.game.draw_text(self.message, WINDOW_WIDTH // 2, WINDOW_HEIGHT - 80,
                                YELLOW, size=18, center=True)

        # 删除确认弹窗
        if self.mode == 'confirm_delete':
            self._draw_confirm_dialog(f'删除存档 #{self.confirm_target + 1}？\\n此操作不可恢复', RED)

    def _draw_confirm_dialog(self, text, color=RED):
        """绘制确认对话框"""
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        pw, ph = 400, 150
        px, py = (WINDOW_WIDTH - pw) // 2, (WINDOW_HEIGHT - ph) // 2
        self.game.draw_rect(px, py, pw, ph, (30, 28, 40))
        pygame.draw.rect(self.screen, color, (px, py, pw, ph), 2)

        self.game.draw_text('⚠ 确认', px + pw // 2, py + 30, color, size=22, center=True)
        self.game.draw_text(text.replace('\\n', ' '), px + pw // 2, py + 60, WHITE, size=16, center=True)
        self.game.draw_text('Y = 确认  |  N / ESC = 取消', px + pw // 2, py + 110, GRAY, size=14, center=True)
