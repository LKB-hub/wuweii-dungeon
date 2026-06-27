"""
设置菜单场景 - 音量调节、按键配置、冲突检测、重置确认
"""
import pygame
from src.engine.scene import Scene
from src.engine.font_helper import get_chinese_font
from settings import WINDOW_WIDTH, WINDOW_HEIGHT, WHITE, GRAY, YELLOW, GREEN, RED, CYAN


class SettingsScene(Scene):
    """设置菜单"""

    def __init__(self, game, **kwargs):
        super().__init__(game)
        self.options = [
            {'name': '音效音量', 'key': 'sfx_volume', 'value': 80, 'min': 0, 'max': 100, 'step': 10},
            {'name': '音乐音量', 'key': 'music_volume', 'value': 60, 'min': 0, 'max': 100, 'step': 10},
            {'name': '屏幕震动', 'key': 'screen_shake', 'value': 1, 'min': 0, 'max': 1, 'step': 1, 'toggle': True},
            {'name': '粒子特效', 'key': 'particles', 'value': 1, 'min': 0, 'max': 1, 'step': 1, 'toggle': True},
            {'name': '显示伤害数字', 'key': 'show_damage', 'value': 1, 'min': 0, 'max': 1, 'step': 1, 'toggle': True},
            {'name': '自动瞄准', 'key': 'auto_aim', 'value': 0, 'min': 0, 'max': 1, 'step': 1, 'toggle': True},
            {'name': '全屏模式', 'key': 'fullscreen', 'value': 0, 'min': 0, 'max': 1, 'step': 1, 'toggle': True},
            {'name': '显示FPS', 'key': 'show_fps', 'value': 0, 'min': 0, 'max': 1, 'step': 1, 'toggle': True},
        ]
        self.selected_index = 0
        self.key_bindings = [
            {'name': '上移', 'key': 'W', 'action': 'move_up'},
            {'name': '下移', 'key': 'S', 'action': 'move_down'},
            {'name': '左移', 'key': 'A', 'action': 'move_left'},
            {'name': '右移', 'key': 'D', 'action': 'move_right'},
            {'name': '闪避', 'key': 'SPACE', 'action': 'dodge'},
            {'name': '技能', 'key': 'E', 'action': 'skill'},
            {'name': '换弹', 'key': 'R', 'action': 'reload'},
            {'name': '切换武器', 'key': 'Q', 'action': 'switch_weapon'},
            {'name': '武器1', 'key': '1', 'action': 'slot1'},
            {'name': '武器2', 'key': '2', 'action': 'slot2'},
            {'name': '暂停', 'key': 'P', 'action': 'pause'},
            {'name': '保存', 'key': 'F5', 'action': 'quick_save'},
            {'name': '加载', 'key': 'F9', 'action': 'quick_load'},
        ]
        self.editing_binding = False
        self.edit_binding_index = -1
        self.tab = 'options'  # 'options' or 'controls'
        self.hover_index = -1
        self.show_reset_confirm = False
        self.key_conflicts = []
        self.conflict_flash_timer = 0

    def on_enter(self):
        """进入设置时从存档加载已保存的设置"""
        from src.engine.save import get_save_manager
        sm = get_save_manager()
        saved = sm.settings
        for opt in self.options:
            if opt['key'] in saved:
                val = saved[opt['key']]
                if isinstance(val, bool):
                    opt['value'] = 1 if val else 0
                elif isinstance(val, (int, float)):
                    opt['value'] = int(val)

    def on_exit(self):
        """退出时保存设置"""
        from src.engine.save import get_save_manager
        sm = get_save_manager()
        for opt in self.options:
            sm.settings[opt['key']] = bool(opt['value']) if opt.get('toggle') else opt['value']
        sm.save_settings()

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if self.show_reset_confirm:
                    if event.key == pygame.K_y:
                        self._reset_to_defaults()
                        self.show_reset_confirm = False
                    elif event.key in (pygame.K_n, pygame.K_ESCAPE):
                        self.show_reset_confirm = False
                    continue

                if self.editing_binding:
                    if event.key == pygame.K_ESCAPE:
                        self.editing_binding = False
                        self.edit_binding_index = -1
                    else:
                        key_name = pygame.key.name(event.key).upper()
                        if key_name:
                            # 检查按键冲突
                            conflicts = self._check_key_conflicts(key_name, self.edit_binding_index)
                            if conflicts:
                                self.key_conflicts = conflicts
                                self.conflict_flash_timer = 120
                            self.key_bindings[self.edit_binding_index]['key'] = key_name
                        self.editing_binding = False
                        self.edit_binding_index = -1
                    continue

                if event.key == pygame.K_ESCAPE:
                    self.switch_to('menu')
                elif event.key == pygame.K_TAB:
                    self.tab = 'controls' if self.tab == 'options' else 'options'
                    self.selected_index = 0
                elif event.key in (pygame.K_UP, pygame.K_w):
                    self.selected_index = max(0, self.selected_index - 1)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    max_idx = len(self.options) - 1 if self.tab == 'options' else len(self.key_bindings) - 1
                    self.selected_index = min(max_idx, self.selected_index + 1)
                elif event.key == pygame.K_LEFT:
                    self._adjust_value(-1)
                elif event.key == pygame.K_RIGHT:
                    self._adjust_value(1)
                elif event.key == pygame.K_RETURN:
                    if self.tab == 'controls':
                        self.editing_binding = True
                        self.edit_binding_index = self.selected_index
                elif event.key == pygame.K_r and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    self.show_reset_confirm = True

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mx, my = event.pos
                    self._handle_mouse_click(mx, my)

    def _adjust_value(self, direction):
        if self.tab == 'options':
            opt = self.options[self.selected_index]
            new_val = opt['value'] + direction * opt['step']
            opt['value'] = max(opt['min'], min(opt['max'], new_val))

    def _check_key_conflicts(self, new_key, exclude_index):
        """检查按键冲突"""
        conflicts = []
        for i, bind in enumerate(self.key_bindings):
            if i != exclude_index and bind['key'].upper() == new_key.upper():
                conflicts.append(bind['name'])
        return conflicts

    def _reset_to_defaults(self):
        """重置为默认设置"""
        defaults = {
            'sfx_volume': 80, 'music_volume': 60, 'screen_shake': 1,
            'particles': 1, 'show_damage': 1, 'auto_aim': 0,
            'fullscreen': 0, 'show_fps': 0,
        }
        default_keys = [
            {'key': 'W', 'action': 'move_up'}, {'key': 'S', 'action': 'move_down'},
            {'key': 'A', 'action': 'move_left'}, {'key': 'D', 'action': 'move_right'},
            {'key': 'SPACE', 'action': 'dodge'}, {'key': 'E', 'action': 'skill'},
            {'key': 'R', 'action': 'reload'}, {'key': 'Q', 'action': 'switch_weapon'},
            {'key': '1', 'action': 'slot1'}, {'key': '2', 'action': 'slot2'},
            {'key': 'P', 'action': 'pause'}, {'key': 'F5', 'action': 'quick_save'},
            {'key': 'F9', 'action': 'quick_load'},
        ]
        for opt in self.options:
            if opt['key'] in defaults:
                opt['value'] = defaults[opt['key']]
        for i, bind in enumerate(self.key_bindings):
            if i < len(default_keys):
                bind['key'] = default_keys[i]['key']

    def _get_default_key(self, action):
        """获取操作的默认按键"""
        default_map = {
            'move_up': 'W', 'move_down': 'S', 'move_left': 'A', 'move_right': 'D',
            'dodge': 'SPACE', 'skill': 'E', 'reload': 'R', 'switch_weapon': 'Q',
            'slot1': '1', 'slot2': '2', 'pause': 'P',
            'quick_save': 'F5', 'quick_load': 'F9',
        }
        return default_map.get(action, '?')

    def _handle_mouse_click(self, mx, my):
        start_y = 150
        if self.tab == 'options':
            items = self.options
        else:
            items = self.key_bindings
        for i, item in enumerate(items):
            item_y = start_y + i * 45
            if item_y <= my <= item_y + 35:
                self.selected_index = i
                if self.tab == 'controls':
                    self.editing_binding = True
                    self.edit_binding_index = i
                break

    def update(self):
        if self.conflict_flash_timer > 0:
            self.conflict_flash_timer -= 1

    def draw(self):
        self.screen.fill((20, 20, 30))

        # 标题
        self._draw_text('设 置', WINDOW_WIDTH // 2, 50, WHITE, 36, center=True)

        # Tab 切换
        tab_y = 100
        opt_color = YELLOW if self.tab == 'options' else GRAY
        ctrl_color = YELLOW if self.tab == 'controls' else GRAY
        self._draw_text('[ 游戏选项 ]', 200, tab_y, opt_color, 20, center=True)
        self._draw_text('[ 按键设置 ]', WINDOW_WIDTH - 200, tab_y, ctrl_color, 20, center=True)
        self._draw_text('TAB切换  ESC返回', WINDOW_WIDTH // 2, WINDOW_HEIGHT - 40, GRAY, 16, center=True)

        if self.tab == 'options':
            self._draw_options()
        else:
            self._draw_controls()

        # 重置确认对话框
        if self.show_reset_confirm:
            self._draw_reset_confirm()

        # 按键冲突提示
        if self.conflict_flash_timer > 0 and self.key_conflicts:
            self._draw_conflict_warning()

    def _draw_options(self):
        start_y = 150
        for i, opt in enumerate(self.options):
            y = start_y + i * 45
            is_selected = (i == self.selected_index)
            color = YELLOW if is_selected else WHITE

            # 选项名
            self._draw_text(opt['name'], 100, y + 5, color, 20)

            # 值
            bar_x = 350
            bar_w = 250
            bar_h = 20
            pygame.draw.rect(self.screen, (50, 50, 60), (bar_x, y + 5, bar_w, bar_h))

            if opt.get('toggle'):
                val_text = '开' if opt['value'] else '关'
                val_color = GREEN if opt['value'] else RED
                self._draw_text(val_text, bar_x + bar_w + 40, y + 5, val_color, 18)
                if opt['value']:
                    pygame.draw.rect(self.screen, GREEN, (bar_x, y + 5, bar_w, bar_h))
            else:
                pct = (opt['value'] - opt['min']) / (opt['max'] - opt['min'])
                fill_w = int(bar_w * pct)
                pygame.draw.rect(self.screen, (100, 150, 220), (bar_x, y + 5, fill_w, bar_h))
                self._draw_text(str(opt['value']), bar_x + bar_w + 40, y + 5, WHITE, 18)

            # 选择指示
            if is_selected:
                pygame.draw.rect(self.screen, YELLOW, (bar_x - 2, y + 3, bar_w + 4, bar_h + 4), 2)
                self._draw_text('← → 调整', bar_x + bar_w + 80, y + 5, GRAY, 14)

            # 进度条边框
            pygame.draw.rect(self.screen, WHITE, (bar_x, y + 5, bar_w, bar_h), 1)

    def _draw_controls(self):
        start_y = 150
        for i, bind in enumerate(self.key_bindings):
            y = start_y + i * 38
            is_selected = (i == self.selected_index)
            is_editing = (self.editing_binding and self.edit_binding_index == i)
            color = YELLOW if is_selected else WHITE

            self._draw_text(bind['name'], 100, y + 5, color, 20)

            # 按键显示
            key_x = 400
            if is_editing:
                self._draw_text('... 按下新按键 ...', key_x, y + 5, YELLOW, 20)
                pygame.draw.rect(self.screen, YELLOW, (key_x - 10, y, 280, 32), 2)
            else:
                key_bg = pygame.Rect(key_x, y, 100, 30)
                pygame.draw.rect(self.screen, (60, 60, 80), key_bg)
                if is_selected:
                    pygame.draw.rect(self.screen, YELLOW, key_bg, 2)
                else:
                    pygame.draw.rect(self.screen, GRAY, key_bg, 1)
                self._draw_text(bind['key'], key_x + 50, y + 6, WHITE, 18, center=True)

            if is_selected and not is_editing:
                self._draw_text('ENTER 修改', key_x + 120, y + 5, GRAY, 14)

    def _draw_text(self, text, x, y, color, size, center=False):
        try:
            font = get_chinese_font(size)
            surf = font.render(str(text), True, color)
            if center:
                rect = surf.get_rect(center=(x, y))
                self.screen.blit(surf, rect)
            else:
                self.screen.blit(surf, (x, y))
        except:
            pass
