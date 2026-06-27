"""
角色选择界面 - 角色预览、属性详情、技能说明、难度选择
"""
import math
import pygame
from src.engine.scene import Scene
from src.engine.resource import get_resources
from settings import WINDOW_WIDTH, WINDOW_HEIGHT, WHITE, YELLOW, GREEN, CYAN, GRAY, RED, ORANGE


class CharacterSelectScene(Scene):
    """角色选择"""

    def __init__(self, game, **kwargs):
        super().__init__(game)
        from src.entities.character import PLAYER_CHARACTERS, SKILL_DATA, DIFFICULTY_LEVELS
        self.characters = list(PLAYER_CHARACTERS.items())
        self.skill_data = SKILL_DATA
        self.difficulties = list(DIFFICULTY_LEVELS.items())
        self.selected = 0
        self.difficulty_idx = 1  # 默认为普通难度
        self.resources = get_resources()
        self.anim_timer = 0
        self.transition_offset = 0
        self.target_offset = 0
        self.hover_char = -1
        self.char_card_alpha = [0] * len(self.characters)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    self.selected = (self.selected - 1) % len(self.characters)
                    self.target_offset = -200
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    self.selected = (self.selected + 1) % len(self.characters)
                    self.target_offset = 200
                elif event.key == pygame.K_UP:
                    self.difficulty_idx = max(0, self.difficulty_idx - 1)
                elif event.key == pygame.K_DOWN:
                    self.difficulty_idx = min(len(self.difficulties) - 1, self.difficulty_idx + 1)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    self._confirm()
                elif event.key == pygame.K_ESCAPE:
                    self.switch_to('menu')
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if 50 < my < WINDOW_HEIGHT - 100:
                    for i in range(len(self.characters)):
                        cx = WINDOW_WIDTH // 2 + (i - self.selected) * 220
                        if abs(mx - cx) < 80:
                            if i == self.selected:
                                self._confirm()
                            else:
                                self.selected = i
                                self.target_offset = 200 if i > self.selected else -200
            if event.type == pygame.MOUSEMOTION:
                mx, my = event.pos
                self.hover_char = -1
                for i in range(len(self.characters)):
                    cx = WINDOW_WIDTH // 2 + (i - self.selected) * 220 + self.transition_offset
                    if 120 < my < 380 and abs(mx - cx) < 80:
                        self.hover_char = i
                        break

    def _confirm(self):
        char_id = self.characters[self.selected][0]
        diff = self.difficulties[self.difficulty_idx][0]
        self.switch_to('hub', character_id=char_id, difficulty=diff)

    def update(self):
        self.anim_timer += 0.05
        # 过渡动画
        self.transition_offset += (self.target_offset - self.transition_offset) * 0.2
        if abs(self.target_offset - self.transition_offset) < 1:
            self.transition_offset = self.target_offset
            self.target_offset = 0
        # 卡片淡入
        for i in range(len(self.char_card_alpha)):
            target = 255 if i == self.selected or i == self.hover_char else 180
            self.char_card_alpha[i] += (target - self.char_card_alpha[i]) * 0.15

    def _get_character_stats(self, char_data):
        """获取角色详细属性"""
        return [
            ('生命', char_data['max_hp'], 200, RED),
            ('速度', char_data['speed'], 10, GREEN),
            ('能量', char_data['max_energy'], 200, CYAN),
            ('攻击', char_data.get('attack', 5), 20, ORANGE),
            ('防御', char_data.get('defense', 1), 10, (100, 150, 255)),
        ]

    def draw(self):
        self.screen.fill((15, 15, 30))

        # 背景装饰线
        for i in range(5):
            y = 150 + i * 80 + int(math.sin(self.anim_timer * 0.3 + i) * 10)
            alpha = 15 + i * 3
            self.game.draw_rect(0, y, WINDOW_WIDTH, 1, (40, 40, 60), alpha=alpha)

        # 标题
        title_pulse = 1 + 0.03 * math.sin(self.anim_timer * 0.8)
        self.game.draw_text('选 择 角 色', WINDOW_WIDTH // 2, 40, YELLOW,
                            size=int(34 * title_pulse), bold=True, center=True)
        self.game.draw_text('选择你的英雄，踏入地牢', WINDOW_WIDTH // 2, 73, GRAY, size=14, center=True)

        # 角色卡片
        for i, (char_id, data) in enumerate(self.characters):
            offset = i - self.selected
            cx = WINDOW_WIDTH // 2 + offset * 200 + self.transition_offset
            cy = 220

            is_selected = (i == self.selected)
            is_hovered = (i == self.hover_char)
            scale = 1.0 if is_selected else 0.72
            alpha = self.char_card_alpha[i] if i < len(self.char_card_alpha) else 180

            card_w = int(150 * scale)
            card_h = int(260 * scale)
            card_rect = pygame.Rect(cx - card_w // 2, cy - card_h // 2, card_w, card_h)

            # 卡片背景
            bg_alpha = min(255, int(alpha * 0.4))
            self.game.draw_rect(card_rect.x, card_rect.y, card_w, card_h,
                                data['color'], alpha=int(bg_alpha))
            border_color = data['color'] if is_selected else GRAY
            border_w = 3 if is_selected else 1
            pygame.draw.rect(self.screen, border_color, card_rect, border_w)

            # 选中发光
            if is_selected:
                glow_alpha = int(30 + 20 * math.sin(self.anim_timer * 2))
                for g in range(4, 8):
                    pygame.draw.rect(self.screen, (*data['color'], glow_alpha // g),
                                     card_rect.inflate(g * 3, g * 3), 1)

            # 角色精灵
            sprites = self.resources.get_player_frames(char_id)
            if sprites:
                frame_idx = int(self.anim_timer * 3) % len(sprites)
                sprite = sprites[frame_idx]
                scaled = pygame.transform.scale(sprite, (int(56 * scale), int(56 * scale)))
                self.screen.blit(scaled, (cx - int(28 * scale), cy - 90))

            # 角色名
            name_color = data['color'] if is_selected else GRAY
            self.game.draw_text(data['name'], cx, cy + 20, name_color, size=int(20 * scale), bold=is_selected, center=True)

            # 角色序号
            self.game.draw_text(f'{i+1}', cx, cy - 110, (80, 80, 100), size=10, center=True)

            # 描述
            if scale > 0.7:
                self.game.draw_text(data['desc'], cx, cy + 46, GRAY, size=int(11 * scale), center=True)

            # 属性条 (仅选中角色展开)
            if is_selected:
                stats = self._get_character_stats(data)
                bar_start_y = cy + 68
                bar_w = 130
                bar_h = 7
                for si, (label, value, max_val, bar_color) in enumerate(stats):
                    sy = bar_start_y + si * 15
                    self.game.draw_text(label, cx - bar_w // 2 - 25, sy - 1, WHITE, size=9, right=True)
                    pct = min(1.0, value / max_val)
                    # 背景条
                    pygame.draw.rect(self.screen, (40, 40, 50),
                                     (cx - bar_w // 2, sy + 2, bar_w, bar_h))
                    # 填充条（带色阶渐变感）
                    fill_w = int(bar_w * pct)
                    pygame.draw.rect(self.screen, bar_color,
                                     (cx - bar_w // 2, sy + 2, fill_w, bar_h))
                    # 高光
                    if fill_w > 4:
                        pygame.draw.line(self.screen, (min(255, bar_color[0]+40), min(255, bar_color[1]+40), min(255, bar_color[2]+40)),
                                          (cx - bar_w // 2 + 2, sy + 3), (cx - bar_w // 2 + fill_w - 2, sy + 3), 1)
                    self.game.draw_text(str(value), cx + bar_w // 2 + 20, sy - 1, GRAY, size=9)

                # 技能信息
                sk = self.skill_data.get(data['skill'], {})
                ps = self.skill_data.get(data['passive'], {})
                sk_y = bar_start_y + len(stats) * 15 + 2
                # 主动技能
                sk_name = sk.get('name', '?')
                sk_desc = sk.get('desc', '')
                if len(sk_desc) > 28:
                    sk_desc = sk_desc[:28] + '..'
                self.game.draw_text(f'[{sk_name}] {sk_desc}', cx, sk_y, YELLOW, size=9, center=True)
                # 被动技能
                ps_name = ps.get('name', '?')
                ps_desc = ps.get('desc', '')
                if len(ps_desc) > 28:
                    ps_desc = ps_desc[:28] + '..'
                self.game.draw_text(f'[{ps_name}] {ps_desc}', cx, sk_y + 13, CYAN, size=9, center=True)

            # 悬停高亮
            if is_hovered and not is_selected:
                pygame.draw.rect(self.screen, (255, 255, 255, 80), card_rect, 2)

        # 难度选择
        diff_y = 430
        self.game.draw_text('难 度 选 择', WINDOW_WIDTH // 2, diff_y - 5, CYAN, size=18, center=True)
        for i, (dlvl, ddata) in enumerate(self.difficulties):
            dx = WINDOW_WIDTH // 2 + (i - 2) * 130
            is_sel = (i == self.difficulty_idx)
            d_color = YELLOW if is_sel else WHITE
            # 难度背景
            if is_sel:
                self.game.draw_rect(dx - 45, diff_y + 18, 90, 30, (255, 215, 0), alpha=30)
                pygame.draw.rect(self.screen, YELLOW, (dx - 45, diff_y + 18, 90, 30), 1)
            self.game.draw_text(ddata['name'], dx, diff_y + 25, d_color, size=18 if is_sel else 15, center=True)
            if is_sel:
                self.game.draw_text('▲', dx, diff_y + 12, YELLOW, size=12, center=True)

        # 难度描述
        diff_desc = self.difficulties[self.difficulty_idx][1].get('desc', '')
        self.game.draw_text(diff_desc, WINDOW_WIDTH // 2, diff_y + 60, GRAY, size=12, center=True)

        # 操作提示
        self.game.draw_text('← → 角色  ↑↓ 难度  |  回车 开始  ESC 返回', WINDOW_WIDTH // 2,
                            WINDOW_HEIGHT - 30, GRAY, size=13, center=True)

        # 当前角色序号
        self.game.draw_text(f'{self.selected + 1} / {len(self.characters)}',
                            WINDOW_WIDTH // 2, WINDOW_HEIGHT - 55, GRAY, size=11, center=True)
