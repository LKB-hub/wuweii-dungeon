"""
场景基类 - 所有游戏场景的父类
"""
import pygame


class Scene:
    """场景基类，所有场景（菜单、选人、游戏、UI等）继承此类"""

    def __init__(self, game):
        self.game = game
        self.screen = game.screen
        self.clock = game.clock
        self.done = False
        self.next_scene = None
        self.request_quit = False

    def handle_events(self, events):
        """处理事件"""
        pass

    def update(self):
        """更新逻辑"""
        pass

    def draw(self):
        """绘制画面"""
        pass

    def on_enter(self):
        """进入场景时调用"""
        pass

    def on_exit(self):
        """离开场景时调用"""
        pass

    def switch_to(self, scene_name, **kwargs):
        """切换到另一个场景"""
        self.done = True
        self.next_scene = (scene_name, kwargs)
