"""
游戏结束场景 - 统计展示、评价系统、记录对比、动画效果
"""
import math
import random
import pygame
from src.engine.scene import Scene
from settings import WINDOW_WIDTH, WINDOW_HEIGHT, WHITE, YELLOW, RED, GREEN, GRAY, CYAN, ORANGE


class GameOverScene(Scene):
    """游戏结束/胜利画面"""

    def __init__(self, game, **kwargs):
        super().__init__(game)
        self.victory = kwargs.get('victory', False)
        self.score = kwargs.get('score', 0)
        self.gold = kwargs.get('gold', 0)
        self.kills = kwargs.get('kills', 0)
        self.max_combo = kwargs.get('max_combo', 0)
        self.damage_dealt = kwargs.get('damage_dealt', 0)
        self.damage_taken = kwargs.get('damage_taken', 0)
        self.time_elapsed = kwargs.get('time_elapsed', 0)
        self.character_id = kwargs.get('character_id', 'knight')
        self.selected = 0
        self.options = ['再来一局', '返回菜单']
        self.anim_progress = 0
        self.stars = []
        self.stat_anim_progress = [0, 0, 0, 0, 0, 0, 0]
        self.stat_revealed = [False] * 7
        self.new_records = []
        self.exp_gained = 0
        self.exp_bar_progress = 0

    def on_enter(self):
        self.anim_progress = 0
        self.stat_revealed = [False] * len(self.stat_revealed)
        self.stat_anim_progress = [0] * len(self.stat_anim_progress)
        self.new_records = []
        self.exp_bar_progress = 0
        # 计算经验
        self.exp_gained = self.kills * 10 + self.score // 2 + self.gold // 5
        if self.victory:
            self.exp_gained *= 2
        # 检查新记录
        from src.engine.save import get_save_manager
        sm = get_save_manager()
        if self.score > sm.stats.get('best_score', 0):
            self.new_records.append(('最高分', str(self.score)))
        if self.kills > sm.stats.get('best_kills', 0):
            self.new_records.append(('最多击杀', str(self.kills)))
            sm.stats['best_kills'] = self.kills
        if self.max_combo > sm.stats.get('best_combo', 0):
            self.new_records.append(('最大连击', str(self.max_combo)))
            sm.stats['best_combo'] = self.max_combo
        # 生成粒子
        if self.victory:
            self.stars = [(random.randint(0, WINDOW_WIDTH), random.randint(0, WINDOW_HEIGHT),
                          random.choice([YELLOW, (255, 200, 50), (255, 255, 200), (255, 150, 50)]))
                         for _ in range(70)]
        else:
            self.stars = [(random.randint(0, WINDOW_WIDTH), random.randint(0, WINDOW_HEIGHT),
                          random.choice([(80, 80, 120), (60, 60, 100), (40, 40, 80)]))
                         for _ in range(30)]

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
                    self.switch_to('menu')

    def _select(self):
        if self.selected == 0:
            self.switch_to('character_select')
        elif self.selected == 1:
            self.switch_to('menu')

    def update(self):
        if self.anim_progress < 100:
            self.anim_progress += 2
        # 逐条揭示统计
        reveal_delay = 15
        for i in range(len(self.stat_anim_progress)):
            if self.anim_progress > reveal_delay * (i + 1):
                self.stat_anim_progress[i] = min(100, self.stat_anim_progress[i] + 4)
                if self.stat_anim_progress[i] >= 100:
                    self.stat_revealed[i] = True
        # 经验条
        if self.anim_progress > 85:
            self.exp_bar_progress = min(100, self.exp_bar_progress + 2)

    def draw(self):
        self.screen.fill((15, 15, 30))

        # 背景粒子
        for i, (x, y, c) in enumerate(self.stars):
            y -= random.uniform(0.3, 1.5)
            if y < 0:
                y = WINDOW_HEIGHT
                x = random.randint(0, WINDOW_WIDTH)
            self.stars[i] = (x, y, c)
            sz = 2 if self.victory else 1
            self.game.draw_rect(int(x), int(y), sz, sz, c, alpha=150 if self.victory else 80)

        # 标题
        title_y = 70
        if self.victory:
            pulse = 1 + 0.06 * math.sin(self.anim_progress * 0.08)
            self.game.draw_text('★ 胜 利 ! ★', WINDOW_WIDTH // 2, title_y,
                                YELLOW, size=int(52 * pulse), bold=True, center=True)
            self.game.draw_text('你成功通关了地牢!', WINDOW_WIDTH // 2, title_y + 42, GREEN, size=16, center=True)
        else:
            self.game.draw_text('游 戏 结 束', WINDOW_WIDTH // 2, title_y, RED, size=46, bold=True, center=True)
            self.game.draw_text('你倒在了地牢中...', WINDOW_WIDTH // 2, title_y + 40, GRAY, size=16, center=True)

        # 经验获取
        if self.exp_bar_progress > 0 and self.exp_gained > 0:
            exp_y = title_y + 58 if self.victory else title_y + 58
            self.game.draw_text(f'获得经验: +{self.exp_gained}', WINDOW_WIDTH // 2, exp_y,
                                CYAN, size=14, center=True)
            # 经验条
            bar_x = WINDOW_WIDTH // 2 - 80
            bar_w = int(160 * self.exp_bar_progress / 100)
            pygame.draw.rect(self.screen, (40, 40, 50), (bar_x, exp_y + 16, 160, 6))
            pygame.draw.rect(self.screen, CYAN, (bar_x, exp_y + 16, bar_w, 6))

        # 统计信息
        stats_y = 155
        stats = [
            ('总分', str(self.score), YELLOW),
            ('金币', str(self.gold), (255, 200, 50)),
            ('击杀数', str(self.kills), (255, 150, 100)),
            ('最大连击', str(self.max_combo), (255, 120, 180)),
            ('造成伤害', str(self.damage_dealt), (255, 100, 80)),
            ('受到伤害', str(self.damage_taken), (180, 100, 100)),
        ]
        if self.time_elapsed > 0:
            mins = int(self.time_elapsed // 60)
            secs = int(self.time_elapsed % 60)
            stats.append(('用时', f'{mins}:{secs:02d}', (150, 180, 200)))

        for i, (label, val, lcolor) in enumerate(stats):
            y = stats_y + i * 30
            progress = self.stat_anim_progress[i] if i < len(self.stat_anim_progress) else 100
            if progress > 0:
                alpha = int(255 * progress / 100)
                left_x = WINDOW_WIDTH // 2 - 150 + int((1 - progress / 100) * 50)
                # 标签
                self.game.draw_text(label, left_x, y, GRAY, size=16)
                # 值（滑入动画）
                val_x = WINDOW_WIDTH // 2 + 50 - int((1 - progress / 100) * 30)
                val_color = (*lcolor[:3], min(255, alpha)) if len(lcolor) == 3 else lcolor
                self.game.draw_text(val, val_x, y, val_color, size=18, bold=True)
                # 分隔线
                if self.stat_revealed[i] if i < len(self.stat_revealed) else True:
                    pygame.draw.line(self.screen, (50, 50, 60),
                                     (left_x - 30, y + 16), (val_x + 40, y + 16), 1)

        # 新纪录
        if self.new_records and self.anim_progress > 80:
            record_y = stats_y + len(stats) * 30 + 10
            self.game.draw_text('🏆 新纪录!', WINDOW_WIDTH // 2, record_y, ORANGE, size=18, bold=True, center=True)
            for ri, (rname, rval) in enumerate(self.new_records):
                self.game.draw_text(f'{rname}: {rval}', WINDOW_WIDTH // 2,
                                    record_y + 22 + ri * 18, (255, 200, 100), size=14, center=True)

        # 评价 (在底部之前)
        rank_y = WINDOW_HEIGHT - 135
        if self.anim_progress > 70:
            rank = self._get_rank()
            rank_colors = {'S': YELLOW, 'A': (255, 100, 200), 'B': GREEN, 'C': CYAN, 'D': GRAY}
            rank_color = rank_colors.get(rank, WHITE)
            alpha = min(255, int((self.anim_progress - 70) * 8.5))
            self.game.draw_text('综合评价', WINDOW_WIDTH // 2, rank_y, GRAY, size=16, center=True)
            rank_size = int(40 + 10 * math.sin(self.anim_progress * 0.05))
            self.game.draw_text(rank, WINDOW_WIDTH // 2, rank_y + 28, rank_color,
                                size=rank_size, bold=True, center=True)

        # 选项
        for i, opt in enumerate(self.options):
            color = YELLOW if i == self.selected else WHITE
            y = WINDOW_HEIGHT - 65 + i * 38
            sel_w = int(20 + 3 * math.sin(self.anim_progress * 0.08 + i))
            self.game.draw_text(opt, WINDOW_WIDTH // 2, y, color, size=22, center=True)
            if i == self.selected:
                self.game.draw_text('▸', WINDOW_WIDTH // 2 - 110, y, YELLOW, size=sel_w, center=True)
                self.game.draw_text('◂', WINDOW_WIDTH // 2 + 110, y, YELLOW, size=sel_w, center=True)

    def _get_rank(self):
        """根据得分计算评价"""
        if self.victory and self.score >= 2000:
            return 'S'
        elif self.victory or self.score >= 1000:
            return 'A'
        elif self.score >= 500:
            return 'B'
        elif self.score >= 200:
            return 'C'
        return 'D'

    def _draw_stat(self, label, value, y):
        self.game.draw_text(label, WINDOW_WIDTH // 2 - 60, y, GRAY, size=22, right=True)
        self.game.draw_text(value, WINDOW_WIDTH // 2 + 60, y, YELLOW, size=22)
