"""
主菜单场景 - 动画标题、存档检测、粒子特效、版本信息
"""
import math
import random
import pygame
from src.engine.scene import Scene
from settings import WINDOW_WIDTH, WINDOW_HEIGHT, WHITE, YELLOW, ORANGE, GRAY, GREEN, RED, CYAN


class MenuScene(Scene):
    """游戏主菜单"""

    def __init__(self, game, **kwargs):
        super().__init__(game)
        self.options = ['开始游戏', '继续游戏', '设置', '存档管理', '成就', '退出']
        self.selected = 0
        self.title_y = 0
        self.menu_alpha = 0
        self.bg_particles = [(random.randint(0, WINDOW_WIDTH),
                              random.randint(0, WINDOW_HEIGHT),
                              random.randint(1, 3))
                             for _ in range(60)]
        self.bg_stars = [(random.randint(0, WINDOW_WIDTH),
                         random.randint(0, WINDOW_HEIGHT),
                         random.uniform(0.3, 1.5))
                        for _ in range(80)]
        self.title_pulse = 0
        self.has_save = False
        self.total_games = 0
        self.total_wins = 0

    def on_enter(self):
        self.title_y = -100
        self.menu_alpha = 0
        # 检查存档和统计
        from src.engine.save import get_save_manager
        sm = get_save_manager()
        self.has_save = sm.has_save()
        self.total_games = sm.stats.get('total_games', 0)
        self.total_wins = sm.stats.get('total_wins', 0)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    self.selected = (self.selected - 1) % len(self.options)
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    self.selected = (self.selected + 1) % len(self.options)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    self._select()
                elif event.key == pygame.K_ESCAPE:
                    self.game.running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                for i, opt in enumerate(self.options):
                    opt_rect = pygame.Rect(WINDOW_WIDTH // 2 - 100, 320 + i * 60, 200, 40)
                    if opt_rect.collidepoint(mx, my):
                        self.selected = i
                        self._select()

    def _select(self):
        from src.engine.save import get_save_manager
        if self.selected == 0:
            self.switch_to('character_select')
        elif self.selected == 1:
            save_mgr = get_save_manager()
            self.switch_to('hub')
        elif self.selected == 2:
            self.switch_to('settings')
        elif self.selected == 3:
            self.switch_to('save_manager')
        elif self.selected == 4:
            self.switch_to('achievements')
        elif self.selected == 5:
            self.game.running = False

    def update(self):
        # 标题动画
        if self.title_y < 110:
            self.title_y += 4
        if self.menu_alpha < 255:
            self.menu_alpha += 8
        self.title_pulse += 0.05

        # 背景粒子
        for i, (x, y, speed) in enumerate(self.bg_particles):
            y += speed * 0.5
            if y > WINDOW_HEIGHT:
                y = 0
                x = random.randint(0, WINDOW_WIDTH)
            self.bg_particles[i] = (x, y, speed)
        # 星星闪烁
        for i, (x, y, bright) in enumerate(self.bg_stars):
            bright = random.uniform(0.3, 1.5)
            self.bg_stars[i] = (x, y, bright)

    def draw(self):
        # 背景
        self.screen.fill((8, 8, 20))

        # 星星背景
        for x, y, bright in self.bg_stars:
            alpha = int(100 * bright)
            size = int(2 * bright)
            self.game.draw_rect(int(x), int(y), size, size, (180, 200, 255), alpha=min(255, alpha))

        # 粒子背景
        for x, y, speed in self.bg_particles:
            alpha = 40 + int(speed * 15)
            self.game.draw_rect(int(x), int(y), 2, 2, (80, 100, 160), alpha=alpha)

        # 标题（带脉冲效果）
        pulse = 1 + 0.05 * math.sin(self.title_pulse)
        title_size = int(56 * pulse)
        self.game.draw_text('元 气 地 牢', WINDOW_WIDTH // 2, self.title_y,
                            YELLOW, size=title_size, bold=True, center=True)
        self.game.draw_text('Roguelike 地牢冒险', WINDOW_WIDTH // 2, self.title_y + 50,
                            GRAY, size=18, center=True)

        # 统计信息
        if self.total_games > 0:
            stats_text = f'共冒险 {self.total_games} 次'
            if self.total_wins > 0:
                stats_text += f'  |  通关 {self.total_wins} 次'
            self.game.draw_text(stats_text, WINDOW_WIDTH // 2, self.title_y + 72,
                                GRAY, size=12, center=True)

        # 版本号
        self.game.draw_text('v1.0', WINDOW_WIDTH - 60, WINDOW_HEIGHT - 30, GRAY, size=14)

        # 菜单选项
        menu_start = 290
        for i, opt in enumerate(self.options):
            color = YELLOW if i == self.selected else WHITE
            y = menu_start + i * 55
            # 禁用/特殊颜色
            if i == 1:
                from src.engine.save import get_save_manager
                if not get_save_manager().has_save():
                    color = (80, 80, 80)
                else:
                    color = GREEN if i == self.selected else (150, 220, 150)

            self.game.draw_text(opt, WINDOW_WIDTH // 2, y, color, size=28, center=True)
            if i == self.selected:
                arrow_x = WINDOW_WIDTH // 2 - 130
                arrow_w = int(20 + 3 * math.sin(self.title_pulse * 2))
                self.game.draw_text('▸', arrow_x, y, YELLOW, size=arrow_w, center=True)
                self.game.draw_text('◂', WINDOW_WIDTH // 2 + 130, y, YELLOW, size=arrow_w, center=True)

        # 操作提示
        self.game.draw_text('↑↓ 选择 | 回车 确认 | ESC 退出', WINDOW_WIDTH // 2, WINDOW_HEIGHT - 40,
                            GRAY, size=14, center=True)

        # 底部装饰线
        deco_y = WINDOW_HEIGHT - 50
        for i in range(3):
            dx = WINDOW_WIDTH // 2 + (i - 1) * 120
            alpha = int(100 + 80 * math.sin(self.title_pulse * 0.7 + i))
            self.game.draw_rect(dx - 30, deco_y, 60, 2, YELLOW, alpha=alpha)
