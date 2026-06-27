"""
游戏引擎核心 - 场景管理器 + 主循环 + 调试工具
"""
import sys
import time
import math
import pygame
from settings import WINDOW_WIDTH, WINDOW_HEIGHT, TITLE, FPS, BLACK
from src.engine.font_helper import get_chinese_font


class Game:
    """游戏主类，管理场景和主循环"""

    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.scenes = {}
        self.current_scene = None
        self.font_cache = {}
        self._debug = False
        self._show_fps = False
        self._dev_mode = False  # 开发者模式
        self._fps_history = []
        self._frame_count = 0
        self._start_time = time.time()
        self._auto_save_enabled = True
        self._auto_save_timer = 0
        self._auto_save_interval = 300  # 5分钟自动保存
        # 额外的字体缓存
        self.font_cache_small = {}

    def add_scene(self, name, scene_class):
        """注册场景"""
        self.scenes[name] = scene_class

    def start(self, start_scene, **kwargs):
        """启动游戏，进入初始场景"""
        self._switch_scene(start_scene, **kwargs)
        self._run()

    def _switch_scene(self, name, **kwargs):
        """切换场景"""
        if self.current_scene:
            self.current_scene.on_exit()
        scene_class = self.scenes.get(name)
        if not scene_class:
            print(f"错误: 场景 '{name}' 未注册!")
            self.running = False
            return
        self.current_scene = scene_class(self, **kwargs)
        self.current_scene.on_enter()

    def _run(self):
        """主游戏循环"""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self._frame_count += 1

            # 收集事件
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    # 关闭窗口前自动保存
                    if self.current_scene:
                        self.current_scene.on_exit()
                    self.running = False
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F3:
                        self._show_fps = not self._show_fps
                    if event.key == pygame.K_F1:
                        self._debug = not self._debug
                    if event.key == pygame.K_F4:
                        self._dev_mode = not self._dev_mode
                        print(f'[Dev] Dev mode: {"ON" if self._dev_mode else "OFF"}')
                    if event.key == pygame.K_F2:
                        self._take_screenshot()

            # 自动保存
            if self._auto_save_enabled:
                self._auto_save_timer += 1
                if self._auto_save_timer >= self._auto_save_interval * FPS:
                    self._auto_save_timer = 0
                    self._trigger_auto_save()

            # 场景处理
            if self.current_scene:
                self.current_scene.handle_events(events)
                self.current_scene.update()
                self.screen.fill(BLACK)
                self.current_scene.draw()

                # 帧率显示
                if self._show_fps:
                    self._draw_fps()

                # 调试信息
                if self._debug:
                    self._draw_debug_info()

                # 开发者模式
                if self._dev_mode:
                    self._draw_dev_overlay()

                pygame.display.flip()

                # 场景切换
                if self.current_scene.done:
                    next_info = self.current_scene.next_scene
                    if next_info:
                        name, kwargs = next_info
                        self._switch_scene(name, **kwargs)
                    elif self.current_scene.request_quit:
                        self.running = False

        pygame.quit()
        sys.exit()

    def _draw_fps(self):
        """绘制FPS"""
        fps = int(self.clock.get_fps())
        color = (100, 255, 100) if fps >= 55 else (255, 255, 100) if fps >= 30 else (255, 100, 100)
        font = self.get_font(14)
        surf = font.render(f'FPS: {fps}', True, color)
        self.screen.blit(surf, (WINDOW_WIDTH - 70, 5))
        # 帧时间图
        self._fps_history.append(fps)
        if len(self._fps_history) > 100:
            self._fps_history.pop(0)
        graph_x = WINDOW_WIDTH - 110
        for i, hfps in enumerate(self._fps_history):
            h = min(40, max(1, int(hfps / 2)))
            gcolor = (100, 255, 100) if hfps >= 55 else (255, 255, 100) if hfps >= 30 else (255, 100, 100)
            pygame.draw.line(self.screen, gcolor,
                             (graph_x + i, 25), (graph_x + i, 25 - h), 1)


    def _draw_dev_overlay(self):
        """开发者模式 - 显示底层调试信息"""
        fps = int(self.clock.get_fps())
        elapsed = int(time.time() - self._start_time)
        h, m, s = elapsed // 3600, (elapsed % 3600) // 60, elapsed % 60
        font = self.get_font(11)
        lines = [f'[DEV MODE]', f'FPS: {fps}  Frame: {self._frame_count}',
                 f'Scene: {type(self.current_scene).__name__ if self.current_scene else "None"}',
                 f'Uptime: {h:02d}:{m:02d}:{s:02d}']
        try:
            if hasattr(self.current_scene, 'dungeon') and self.current_scene.dungeon:
                d = self.current_scene.dungeon
                lines.append(f'Floor: {d.floor_number}/{d.max_floor}  Rooms: {len(d.rooms)}')
                lines.append(f'Enemies: {len(d.enemies)}  Items: {len(d.items)}')
            if hasattr(self.current_scene, 'player') and self.current_scene.player:
                p = self.current_scene.player
                lines.append(f'Player: ({int(p.x)},{int(p.y)})  HP: {p.hp}/{p.max_hp}')
                lines.append(f'Facing: {int(math.degrees(p.facing_angle))}deg  Dir: {p.direction}')
                lines.append(f'Speed: {p.active_speed:.1f}')
                if hasattr(p, 'weapon_manager') and p.weapon_manager.get_current():
                    w = p.weapon_manager.get_current()
                    lines.append(f'Weapon: {w.weapon_id}  Ammo: {w.ammo}/{w.max_ammo}')
            if hasattr(self.current_scene, 'camera') and self.current_scene.camera:
                c = self.current_scene.camera
                lines.append(f'Camera: ({int(c.x)},{int(c.y)})  Zoom: {c.zoom:.2f}')
        except:
            pass
        y = 2
        for line in lines:
            surf = font.render(line, True, (0, 255, 255))
            bg = pygame.Surface((surf.get_width() + 4, surf.get_height() + 2), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 160))
            self.screen.blit(bg, (300, y))
            self.screen.blit(surf, (302, y + 1))
            y += 15
        status = 'DEV MODE'
        parts = []
        if self._debug: parts.append('DEBUG')
        if self._show_fps: parts.append('FPS')
        if parts: status += ' [' + '+'.join(parts) + ']'
        s_surf = font.render(status, True, (0, 255, 255))
        s_bg = pygame.Surface((s_surf.get_width() + 4, s_surf.get_height() + 2), pygame.SRCALPHA)
        s_bg.fill((0, 0, 0, 160))
        self.screen.blit(s_bg, (WINDOW_WIDTH - 200, self.screen.get_height() - 16))
        self.screen.blit(s_surf, (WINDOW_WIDTH - 198, self.screen.get_height() - 15))

    def _draw_debug_info(self):
        """绘制调试信息"""
        font = self.get_font(12)
        elapsed = int(time.time() - self._start_time)
        h, m, s = elapsed // 3600, (elapsed % 3600) // 60, elapsed % 60
        info_lines = [
            f'Frame: {self._frame_count}',
            f'Scene: {type(self.current_scene).__name__ if self.current_scene else "None"}',
            f'Uptime: {h:02d}:{m:02d}:{s:02d}',
            f'Memory: scenes={len(self.scenes)}, fonts={len(self.font_cache)}',
        ]
        for i, line in enumerate(info_lines):
            surf = font.render(line, True, (200, 200, 200))
            bg = pygame.Surface((surf.get_width() + 6, surf.get_height() + 2), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 120))
            self.screen.blit(bg, (2, 2 + i * 16))
            self.screen.blit(surf, (5, 3 + i * 16))

    def _take_screenshot(self):
        """截图保存"""
        import os
        ss_dir = 'screenshots'
        if not os.path.exists(ss_dir):
            os.makedirs(ss_dir)
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(ss_dir, f'screenshot_{timestamp}.png')
        try:
            pygame.image.save(self.screen, filename)
            print(f'截图已保存: {filename}')
        except Exception as e:
            print(f'截图失败: {e}')

    def _trigger_auto_save(self):
        """触发自动保存"""
        if self.current_scene and hasattr(self.current_scene, 'save_game'):
            try:
                self.current_scene.save_game()
            except:
                pass

    def get_font(self, size=24, bold=False):
        """获取缓存字体"""
        key = (size, bold)
        if key not in self.font_cache:
            self.font_cache[key] = get_chinese_font(size)
        return self.font_cache[key]

    def draw_text(self, text, x, y, color=(255, 255, 255), size=24, bold=False,
                  center=False, right=False):
        """便捷文字绘制"""
        font = self.get_font(size, bold)
        surf = font.render(str(text), True, color)
        if center:
            rect = surf.get_rect(center=(x, y))
            self.screen.blit(surf, rect)
        elif right:
            rect = surf.get_rect(midright=(x, y))
            self.screen.blit(surf, rect)
        else:
            self.screen.blit(surf, (x, y))

    def draw_rect(self, x, y, w, h, color, border=0, alpha=None):
        """便捷矩形绘制（支持透明度）"""
        if alpha is not None:
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            surf.fill((*color, alpha))
            self.screen.blit(surf, (x, y))
        else:
            pygame.draw.rect(self.screen, color, (x, y, w, h), border)

    def draw_circle(self, x, y, radius, color, border=0):
        """便捷圆形绘制"""
        pygame.draw.circle(self.screen, color, (int(x), int(y)), radius, border)

    def toggle_debug(self):
        """切换调试模式"""
        self._debug = not self._debug
        self._show_fps = self._debug
        state = 'ON' if self._debug else 'OFF'
        print(f'[Debug] Debug mode: {state}')

    def toggle_fps(self):
        """切换FPS显示"""
        self._show_fps = not self._show_fps
        state = 'ON' if self._show_fps else 'OFF'
        print(f'[Debug] FPS display: {state}')
