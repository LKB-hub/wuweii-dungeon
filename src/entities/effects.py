"""
视觉特效管理器 - 屏幕震动、闪电链、护盾破碎、光环、地面标记等
"""
import math
import random
import pygame
from settings import WINDOW_WIDTH, WINDOW_HEIGHT


class VisualEffects:
    """全局视觉效果管理器"""

    def __init__(self):
        # 屏幕震动
        self.screen_shake_active = False
        self.screen_shake_intensity = 0
        self.screen_shake_duration = 0
        self.screen_shake_timer = 0
        self.screen_shake_offset_x = 0
        self.screen_shake_offset_y = 0

        # 闪电链
        self.lightning_bolts = []

        # 光环
        self.auras = []

        # 地面标记（AOE范围指示）
        self.ground_markers = []

        # 屏幕闪光
        self.screen_flash_active = False
        self.screen_flash_color = (255, 255, 255)
        self.screen_flash_alpha = 0
        self.screen_flash_timer = 0

        # 冻结效果
        self.freeze_overlay_active = False
        self.freeze_overlay_timer = 0

        # 毒雾效果
        self.poison_clouds = []

    def start_screen_shake(self, intensity=8, duration=15):
        """触发屏幕震动"""
        self.screen_shake_active = True
        self.screen_shake_intensity = intensity
        self.screen_shake_duration = duration
        self.screen_shake_timer = duration

    def get_shake_offset(self):
        """获取当前帧的屏幕震动偏移"""
        if not self.screen_shake_active:
            return (0, 0)
        if self.screen_shake_timer <= 0:
            self.screen_shake_active = False
            self.screen_shake_offset_x = 0
            self.screen_shake_offset_y = 0
            return (0, 0)
        progress = self.screen_shake_timer / self.screen_shake_duration
        intensity = self.screen_shake_intensity * progress
        self.screen_shake_offset_x = random.uniform(-intensity, intensity)
        self.screen_shake_offset_y = random.uniform(-intensity, intensity)
        self.screen_shake_timer -= 1
        return (self.screen_shake_offset_x, self.screen_shake_offset_y)

    def add_lightning_bolt(self, x1, y1, x2, y2, color=(200, 220, 255),
                           thickness=2, lifetime=15, branch_chance=0.3):
        """添加闪电链效果"""
        self.lightning_bolts.append({
            'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
            'color': color, 'thickness': thickness,
            'lifetime': lifetime, 'timer': lifetime,
            'segments': self._generate_lightning_segments(x1, y1, x2, y2, branch_chance),
        })

    def _generate_lightning_segments(self, x1, y1, x2, y2, branch_chance):
        """生成闪电的分段路径"""
        segments = []
        segments.append((x1, y1))
        segments.append((x2, y2))

        # 在主路径中间添加锯齿点
        mid_count = random.randint(3, 7)
        for i in range(1, mid_count):
            t = i / (mid_count + 1)
            mx = x1 + (x2 - x1) * t
            my = y1 + (y2 - y1) * t
            # 偏移
            offset = random.uniform(-30, 30)
            perp_x = -(y2 - y1)
            perp_y = (x2 - x1)
            length = math.sqrt(perp_x ** 2 + perp_y ** 2)
            if length > 0:
                perp_x /= length
                perp_y /= length
            mx += perp_x * offset
            my += perp_y * offset
            segments.append((mx, my))

        # 分支
        if random.random() < branch_chance:
            mid_idx = random.randint(1, len(segments) - 2)
            bx, by = segments[mid_idx]
            b_angle = random.uniform(0, math.pi * 2)
            b_dist = random.uniform(20, 60)
            bex = bx + math.cos(b_angle) * b_dist
            bey = by + math.sin(b_angle) * b_dist
            segments.append((bex, bey))

        return segments

    def add_aura(self, x, y, radius, color, lifetime=30, pulse_speed=0.05):
        """添加光环效果"""
        self.auras.append({
            'x': x, 'y': y, 'radius': radius, 'color': color,
            'lifetime': lifetime, 'timer': lifetime,
            'pulse_phase': random.uniform(0, math.pi * 2),
            'pulse_speed': pulse_speed,
        })

    def add_ground_marker(self, x, y, radius, color, lifetime=60,
                          marker_type='circle'):
        """添加地面标记（AOE预警）"""
        self.ground_markers.append({
            'x': x, 'y': y, 'radius': radius, 'color': color,
            'lifetime': lifetime, 'timer': lifetime,
            'marker_type': marker_type,
            'alpha': 100,
        })

    def trigger_screen_flash(self, color=(255, 255, 255), duration=10, max_alpha=80):
        """触发屏幕闪光"""
        self.screen_flash_active = True
        self.screen_flash_color = color
        self.screen_flash_alpha = max_alpha
        self.screen_flash_timer = duration

    def trigger_freeze_overlay(self, duration=30):
        """触发冻结覆盖效果"""
        self.freeze_overlay_active = True
        self.freeze_overlay_timer = duration

    def add_poison_cloud(self, x, y, radius, lifetime=120):
        """添加毒雾"""
        self.poison_clouds.append({
            'x': x, 'y': y, 'radius': radius,
            'lifetime': lifetime, 'timer': lifetime,
            'particles': [(random.randint(-radius, radius),
                           random.randint(-radius, radius))
                          for _ in range(20)],
        })

    def update(self):
        """更新所有效果"""
        # 闪电
        for bolt in self.lightning_bolts[:]:
            bolt['timer'] -= 1
            if bolt['timer'] <= 0:
                self.lightning_bolts.remove(bolt)

        # 光环
        for aura in self.auras[:]:
            aura['timer'] -= 1
            aura['pulse_phase'] += aura['pulse_speed']
            if aura['timer'] <= 0:
                self.auras.remove(aura)

        # 地面标记
        for marker in self.ground_markers[:]:
            marker['timer'] -= 1
            progress = 1 - (marker['timer'] / marker['lifetime'])
            marker['alpha'] = int(100 * (1 - progress))
            if marker['timer'] <= 0:
                self.ground_markers.remove(marker)

        # 屏幕闪光
        if self.screen_flash_active:
            self.screen_flash_timer -= 1
            if self.screen_flash_timer <= 0:
                self.screen_flash_active = False
                self.screen_flash_alpha = 0
            else:
                progress = self.screen_flash_timer / max(1, self.screen_flash_timer + 1)
                self.screen_flash_alpha = int(self.screen_flash_alpha * progress)

        # 冻结覆盖
        if self.freeze_overlay_active:
            self.freeze_overlay_timer -= 1
            if self.freeze_overlay_timer <= 0:
                self.freeze_overlay_active = False

        # 毒雾
        for cloud in self.poison_clouds[:]:
            cloud['timer'] -= 1
            if cloud['timer'] <= 0:
                self.poison_clouds.remove(cloud)

    def draw(self, screen, camera):
        """绘制视觉效果（世界坐标需通过camera转换）"""
        # 绘制地面标记
        for marker in self.ground_markers:
            sx, sy = camera.apply_point(marker['x'], marker['y'])
            r = int(marker['radius'])
            # 绘制填充圆（半透明）
            surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            alpha = min(255, marker['alpha'])
            c = (*marker['color'], alpha)
            pygame.draw.circle(surf, c, (r, r), r)
            screen.blit(surf, (sx - r, sy - r))
            # 边框
            color_with_alpha = (*marker['color'], min(255, marker['alpha'] + 50))
            pygame.draw.circle(screen, color_with_alpha, (int(sx), int(sy)),
                               r, 2)

        # 绘制光环
        for aura in self.auras:
            sx, sy = camera.apply_point(aura['x'], aura['y'])
            pulse = 1 + math.sin(aura['pulse_phase']) * 0.15
            r = int(aura['radius'] * pulse)
            alpha = int(255 * (aura['timer'] / aura['lifetime']))
            color = (*aura['color'], min(255, alpha))
            pygame.draw.circle(screen, (aura['color']), (int(sx), int(sy)), r + 2, 2)
            surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, color, (r, r), r)
            screen.blit(surf, (sx - r, sy - r))

        # 绘制闪电
        for bolt in self.lightning_bolts:
            sx1, sy1 = camera.apply_point(bolt['x1'], bolt['y1'])
            sx2, sy2 = camera.apply_point(bolt['x2'], bolt['y2'])
            alpha = int(255 * (bolt['timer'] / bolt['lifetime']))
            color = (*bolt['color'], alpha)
            if len(bolt['segments']) >= 2:
                drawn_segs = [(camera.apply_point(*seg)) for seg in bolt['segments']]
                pygame.draw.lines(screen, bolt['color'], False,
                                  drawn_segs, bolt['thickness'])

        # 绘制毒雾
        for cloud in self.poison_clouds:
            sx, sy = camera.apply_point(cloud['x'], cloud['y'])
            alpha = int(60 * (cloud['timer'] / cloud['lifetime']))
            color = (100, 180, 60, alpha)
            r = cloud['radius']
            surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            for px, py in cloud['particles']:
                prx = r + px
                pry = r + py
                p_alpha = min(255, alpha + random.randint(-20, 20))
                p_color = (*color[:3], max(0, p_alpha))
                pygame.draw.circle(surf, p_color, (prx, pry), random.randint(3, 8))
            screen.blit(surf, (sx - r, sy - r))

        # 绘制屏幕闪光
        if self.screen_flash_active and self.screen_flash_alpha > 0:
            flash_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            flash_surf.fill((*self.screen_flash_color, self.screen_flash_alpha))
            screen.blit(flash_surf, (0, 0))

        # 绘制冻结覆盖
        if self.freeze_overlay_active:
            freeze_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            freeze_surf.fill((100, 150, 255, 40))
            # 冰霜纹理
            for _ in range(30):
                fx = random.randint(0, WINDOW_WIDTH)
                fy = random.randint(0, WINDOW_HEIGHT)
                pygame.draw.circle(freeze_surf, (180, 210, 255, 50),
                                   (fx, fy), random.randint(20, 50))
            screen.blit(freeze_surf, (0, 0))
