"""
摄像机类 - 实现跟随玩家的大地图视野
"""
import pygame
from settings import WINDOW_WIDTH, WINDOW_HEIGHT


class Camera:
    """2D 摄像机，跟随目标实体移动，支持震屏和缩放"""

    def __init__(self, world_width, world_height):
        self.world_width = world_width  # 像素
        self.world_height = world_height
        self.x = 0
        self.y = 0
        self.target = None
        self.smooth_speed = 0.1

        # 震屏系统
        self.shake_intensity = 0
        self.shake_duration = 0
        self.shake_timer = 0
        self.shake_offset_x = 0
        self.shake_offset_y = 0

        # 缩放系统
        self.zoom = 1.0
        self.target_zoom = 1.0
        self.zoom_speed = 0.05
        self.zoom_min = 0.5
        self.zoom_max = 2.0

        # 缓动追踪（用于镜头切换）
        self._transition_timer = 0
        self._transition_target = None

    def set_target(self, target):
        """设置跟随目标"""
        self.target = target

    def start_shake(self, intensity, duration):
        """触发震屏效果"""
        if intensity > self.shake_intensity or duration > self.shake_duration:
            self.shake_intensity = max(self.shake_intensity, intensity)
            self.shake_duration = max(self.shake_duration, duration)
            self.shake_timer = self.shake_duration

    def set_zoom(self, zoom, instant=False):
        """设置缩放级别"""
        self.target_zoom = max(self.zoom_min, min(self.zoom_max, zoom))
        if instant:
            self.zoom = self.target_zoom

    def zoom_to(self, zoom, speed=None):
        """平滑缩放到目标"""
        self.target_zoom = max(self.zoom_min, min(self.zoom_max, zoom))
        if speed is not None:
            self.zoom_speed = speed

    def transition_to(self, target_x, target_y, duration=30):
        """平滑过渡到指定位置"""
        self._transition_timer = duration
        self._transition_target = (target_x, target_y)

    def update(self):
        """更新摄像机位置、震屏和缩放"""
        import random

        # 震屏
        if self.shake_timer > 0:
            decay = self.shake_timer / max(1, self.shake_duration)
            intensity = self.shake_intensity * decay
            self.shake_offset_x = random.uniform(-intensity, intensity)
            self.shake_offset_y = random.uniform(-intensity, intensity)
            self.shake_timer -= 1
        else:
            self.shake_offset_x = 0
            self.shake_offset_y = 0
            self.shake_intensity = 0
            self.shake_duration = 0

        # 缩放平滑过渡
        if abs(self.zoom - self.target_zoom) > 0.001:
            self.zoom += (self.target_zoom - self.zoom) * self.zoom_speed
        else:
            self.zoom = self.target_zoom

        # 位置跟随
        if self._transition_timer > 0:
            self._transition_timer -= 1
            t = self._transition_timer / max(1, self._transition_timer + 1)
            target_x = self._transition_target[0] - WINDOW_WIDTH // 2
            target_y = self._transition_target[1] - WINDOW_HEIGHT // 2
            self.x += (target_x - self.x) * (1 - t) * 0.3
            self.y += (target_y - self.y) * (1 - t) * 0.3
        elif self.target:
            target_x = self.target.x - WINDOW_WIDTH // 2
            target_y = self.target.y - WINDOW_HEIGHT // 2
            self.x += (target_x - self.x) * self.smooth_speed
            self.y += (target_y - self.y) * self.smooth_speed

        # 边界限制
        self.x = max(0, min(self.x, self.world_width - WINDOW_WIDTH))
        self.y = max(0, min(self.y, self.world_height - WINDOW_HEIGHT))

        # 如果世界比窗口小，居中
        if self.world_width <= WINDOW_WIDTH:
            self.x = (self.world_width - WINDOW_WIDTH) // 2
        if self.world_height <= WINDOW_HEIGHT:
            self.y = (self.world_height - WINDOW_HEIGHT) // 2

    def apply(self, rect_or_pos):
        """将世界坐标转换为屏幕坐标（含震屏偏移和缩放）"""
        if isinstance(rect_or_pos, pygame.Rect):
            return rect_or_pos.move(-int(self.x + self.shake_offset_x),
                                    -int(self.y + self.shake_offset_y))
        elif isinstance(rect_or_pos, tuple) and len(rect_or_pos) == 2:
            return (rect_or_pos[0] - int(self.x + self.shake_offset_x),
                    rect_or_pos[1] - int(self.y + self.shake_offset_y))
        return rect_or_pos

    def apply_point(self, x, y):
        """将世界坐标点转换为屏幕坐标（含震屏偏移）"""
        return (x - int(self.x + self.shake_offset_x),
                y - int(self.y + self.shake_offset_y))

    def get_shake_offset(self):
        """获取当前震屏偏移"""
        return (self.shake_offset_x, self.shake_offset_y)

    def is_shaking(self):
        """是否正在震屏"""
        return self.shake_timer > 0
