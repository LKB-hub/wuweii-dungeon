"""
游戏入口 - 元气地牢 Roguelike 地牢冒险
启动选项: python main.py [--debug] [--fullscreen] [--nosound]
"""
import pygame
import sys
import os
import argparse
import traceback
sys.path.insert(0, '.')

from src.engine.game import Game
from src.ui.menu import MenuScene
from src.ui.character_select import CharacterSelectScene
from src.ui.gameplay import GameplayScene
from src.ui.gameover import GameOverScene
from src.ui.settings_menu import SettingsScene
from src.ui.hub import HubScene
from src.ui.save_manager import SaveManagerScene



class AchievementsScene:
    """成就展示场景 - 内联定义避免循环导入"""
    def __init__(self, game, **kwargs):
        self.game = game
        self.screen = game.screen
        self.done = False
        self.next_scene = None
        self.request_quit = False
        from src.engine.save import get_save_manager
        self.save_mgr = get_save_manager()
        from src.entities.character import ACHIEVEMENTS
        self.all_achievements = ACHIEVEMENTS
        self.unlocked = self.save_mgr.stats.get('achievements', {})
        self.scroll = 0

    def on_enter(self):
        pass

    def on_exit(self):
        pass

    def switch_to(self, name, **kwargs):
        self.done = True
        self.next_scene = (name, kwargs)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.switch_to('menu')
                elif event.key in (pygame.K_UP, pygame.K_w):
                    self.scroll = max(0, self.scroll - 40)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.scroll += 40

    def update(self):
        pass

    def draw(self):
        self.screen.fill((20, 20, 35))
        font = self.game.get_font(28)
        title = font.render('成 就', True, (255, 215, 0))
        self.screen.blit(title, title.get_rect(center=(400, 30)))

        y = 80 - self.scroll
        for aid, ach in self.all_achievements.items():
            if 60 < y < 550:
                locked = aid not in self.unlocked
                color = (255, 255, 255) if not locked else (80, 80, 80)
                name_text = font.render(ach['name'], True, color)
                self.screen.blit(name_text, (80, y))
                desc_font = self.game.get_font(16)
                desc_text = desc_font.render(ach['desc'], True, color)
                self.screen.blit(desc_text, (80, y + 30))
                status = '✓' if not locked else '✗'
                status_color = (100, 255, 100) if not locked else (120, 120, 120)
                status_text = font.render(status, True, status_color)
                self.screen.blit(status_text, (740, y))
            y += 55

        hint = self.game.get_font(14).render('ESC 返回 | ↑↓ 滚动', True, (120, 120, 120))
        self.screen.blit(hint, hint.get_rect(center=(400, 570)))


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='元气地牢 - Roguelike 地牢冒险')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    parser.add_argument('--fullscreen', action='store_true', help='全屏模式')
    parser.add_argument('--nosound', action='store_true', help='禁用音效')
    parser.add_argument('--version', action='version', version='元气地牢 v1.0')
    return parser.parse_args()


def setup_environment(args):
    """设置运行环境"""
    # 确保必要目录存在
    for d in ['saves', 'screenshots', 'logs']:
        if not os.path.exists(d):
            os.makedirs(d)
    # 设置窗口标题
    pygame.display.set_caption('元气地牢 v1.0')


def main():
    """主函数"""
    args = parse_args()

    try:
        game = Game()

        # 应用启动参数
        if args.debug:
            game._debug = True
            game._show_fps = True
        if args.nosound:
            try:
                from src.engine.sound import get_sound_manager
                get_sound_manager().enabled = False
            except:
                pass

        setup_environment(args)

        game.add_scene('menu', MenuScene)
        game.add_scene('character_select', CharacterSelectScene)
        game.add_scene('gameplay', GameplayScene)
        game.add_scene('gameover', GameOverScene)
        game.add_scene('settings', SettingsScene)
        game.add_scene('achievements', AchievementsScene)
        game.add_scene('hub', HubScene)
        game.add_scene('save_manager', SaveManagerScene)
        
        print('=' * 40)
        print('  元气地牢 v1.0 - 启动!')
        if args.debug:
            print('  [调试模式] F1:切换调试 F2:截图 F3:切换FPS')
        print('=' * 40)

        game.start('menu')

    except Exception as e:
        print(f'\n严重错误: {e}')
        traceback.print_exc()
        # 写入错误日志
        try:
            with open('logs/error.log', 'w', encoding='utf-8') as f:
                f.write(f'Error: {e}\n')
                traceback.print_exc(file=f)
        except:
            pass
        sys.exit(1)


if __name__ == '__main__':
    main()
