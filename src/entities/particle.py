"""
粒子特效系统 - 子弹击中、爆炸、受伤等视觉反馈
"""
import math
import random
import pygame
from src.engine.font_helper import get_chinese_font


class Particle:
    """单个粒子"""

    def __init__(self, x, y, vx, vy, lifetime, color, size=2):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.color = color
        self.size = size
        self.alive = True

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.95
        self.vy *= 0.95
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.alive = False

    def draw(self, screen, camera):
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        size = max(1, int(self.size * (self.lifetime / self.max_lifetime)))
        sx, sy = camera.apply_point(int(self.x), int(self.y))
        if alpha > 0:
            color_with_alpha = (min(self.color[0], 255), min(self.color[1], 255),
                                min(self.color[2], 255), alpha)
            try:
                s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, color_with_alpha, (size, size), size)
                screen.blit(s, (sx - size, sy - size))
            except:
                pass


class ParticleSystem:
    """粒子管理器"""

    def __init__(self):
        self.particles = []
        self.text_particles = []
        self.attraction_particles = []
        self.trail_emitters = []
        self.afterimages = []
        self.floating_texts = []
        self.screen_shake_duration = 0
        self.screen_shake_intensity = 0

    def emit(self, x, y, count, color, speed=3, lifetime=15, size=2,
             pattern='circle'):
        """发射粒子"""
        for _ in range(count):
            if pattern == 'circle':
                angle = random.uniform(0, math.pi * 2)
                spd = random.uniform(speed * 0.5, speed)
                vx = math.cos(angle) * spd
                vy = math.sin(angle) * spd
            elif pattern == 'line':
                angle = random.uniform(0, math.pi * 2)
                spd = random.uniform(speed * 0.5, speed)
                vx = math.cos(angle) * spd * 0.3
                vy = math.sin(angle) * spd
            elif pattern == 'spark':
                angle = random.uniform(0, math.pi * 2)
                spd = random.uniform(speed, speed * 2)
                vx = math.cos(angle) * spd
                vy = math.sin(angle) * spd
            elif pattern == 'burst':
                angle = random.uniform(0, math.pi * 2)
                spd = random.uniform(speed * 0.3, speed)
                vx = math.cos(angle) * spd
                vy = math.sin(angle) * spd - random.uniform(0, speed)
            elif pattern == 'lightning':
                vx = random.uniform(-speed * 0.3, speed * 0.3)
                vy = random.uniform(-speed, -speed * 0.3)
            else:
                vx = random.uniform(-speed, speed)
                vy = random.uniform(-speed, speed)

            lifetime_var = random.randint(lifetime // 2, lifetime)
            particle = Particle(x, y, vx, vy, lifetime_var, color, size)
            self.particles.append(particle)

    def emit_hit(self, x, y):
        self.emit(x, y, 6, (255, 255, 150), speed=3, lifetime=10, size=3, pattern='circle')

    def emit_explosion(self, x, y):
        self.emit(x, y, 20, (255, 150, 30), speed=5, lifetime=20, size=4, pattern='circle')
        self.emit(x, y, 10, (255, 255, 200), speed=3, lifetime=8, size=2, pattern='circle')
        self.start_screen_shake(5, 4)

    def emit_death(self, x, y):
        self.emit(x, y, 15, (200, 50, 50), speed=4, lifetime=20, size=3, pattern='circle')
        self.emit(x, y, 8, (255, 100, 100), speed=3, lifetime=12, size=2, pattern='circle')

    def emit_fire(self, x, y):
        self.emit(x, y, 2, (255, 100, 20), speed=2, lifetime=15, size=3, pattern='spark')
        self.emit(x, y, 1, (255, 200, 30), speed=1, lifetime=8, size=4, pattern='burst')

    def emit_ice(self, x, y):
        self.emit(x, y, 5, (150, 220, 255), speed=2, lifetime=12, size=3, pattern='circle')

    def emit_lightning(self, x, y):
        """闪电特效"""
        self.emit(x, y, 10, (200, 200, 255), speed=5, lifetime=8, size=2, pattern='lightning')
        self.emit(x, y, 3, (255, 255, 255), speed=8, lifetime=4, size=3, pattern='lightning')

    def emit_heal(self, x, y):
        """治疗特效"""
        self.emit(x, y, 8, (100, 255, 100), speed=2, lifetime=20, size=3, pattern='burst')
        self.emit(x, y, 5, (200, 255, 200), speed=1, lifetime=15, size=4, pattern='circle')

    def emit_shield(self, x, y):
        """护盾特效"""
        self.emit(x, y, 6, (80, 180, 255), speed=2, lifetime=18, size=3, pattern='circle')

    def emit_teleport(self, x, y):
        """瞬移特效"""
        self.emit(x, y, 20, (150, 100, 200), speed=6, lifetime=15, size=3, pattern='circle')

    def emit_ring(self, x, y, color, count=24, radius=20, lifetime=20):
        """环形扩散粒子"""
        for i in range(count):
            angle = (math.pi * 2 * i) / count
            spd = random.uniform(2, 4)
            vx = math.cos(angle) * spd
            vy = math.sin(angle) * spd
            p = Particle(x + math.cos(angle) * radius, y + math.sin(angle) * radius,
                         vx, vy, lifetime, color, size=3)
            self.particles.append(p)

    def emit_spiral(self, x, y, color, count=30, lifetime=25):
        """螺旋上升粒子"""
        for i in range(count):
            angle = (math.pi * 2 * i) / count + random.uniform(-0.3, 0.3)
            spd = random.uniform(1, 3)
            vx = math.cos(angle) * spd
            vy = -random.uniform(2, 5)
            p = Particle(x, y, vx, vy, lifetime, color, size=2)
            self.particles.append(p)

    def emit_fountain(self, x, y, color, count=15, lifetime=30):
        """喷泉式粒子"""
        for _ in range(count):
            angle = random.uniform(-0.3, 0.3) - math.pi / 2
            spd = random.uniform(3, 7)
            vx = math.cos(angle) * spd + random.uniform(-1, 1)
            vy = math.sin(angle) * spd
            p = Particle(x + random.uniform(-10, 10), y,
                         vx, vy, lifetime, color, size=3)
            self.particles.append(p)

    def emit_crit(self, x, y, damage):
        """暴击特效 - 大字+碎片粒子"""
        self.emit(x, y, 12, (255, 200, 20), speed=6, lifetime=18, size=3, pattern='spark')
        self.emit(x, y, 6, (255, 255, 255), speed=4, lifetime=10, size=2, pattern='circle')
        tp = TextParticle(x, y - 20, f'暴击! {damage}', (255, 160, 20), size=24, duration=45, spread=50)
        self.text_particles.append(tp)
        self.start_screen_shake(4, 3)

    def emit_combo(self, x, y, combo):
        """连击特效"""
        size = min(14 + combo, 36)
        duration = 30 + combo * 2
        tp = TextParticle(x, y - 10, f'{combo} 连击!',
                          (255, 255, 100) if combo < 10 else (255, 150, 30),
                          size=size, duration=duration)
        self.text_particles.append(tp)
        if combo >= 5:
            self.emit(x, y, combo, (255, 200, 100), speed=3, lifetime=12, size=2, pattern='circle')

    def emit_item_pickup(self, x, y, item_name, rarity_color=(200, 200, 200)):
        """物品拾取特效"""
        self.emit(x, y, 8, (255, 255, 200), speed=2, lifetime=15, size=2, pattern='burst')
        tp = TextParticle(x, y - 25, item_name, rarity_color, size=14, duration=35, spread=30)
        self.text_particles.append(tp)

    def emit_aura_pulse(self, x, y, color, radius=40, lifetime=20):
        """光环脉冲 - 从中心向外扩展的环"""
        for ring in range(3):
            delay = ring * 0.15 * lifetime
            p = RingParticle(x, y, color, radius + ring * 10, lifetime - int(delay),
                             expand_speed=1.5 + ring * 0.5)
            p.lifetime -= int(delay)
            self.particles.append(p)

    def emit_status_text(self, x, y, text, color=(200, 200, 255), size=14):
        """状态文字提示（免疫/抵抗等）"""
        tp = TextParticle(x, y - 15, text, color, size=size, duration=40, spread=25)
        self.text_particles.append(tp)

    def add_text(self, x, y, text, color=(255, 255, 255)):
        """添加浮动战斗文字"""
        ft = FloatingText(x, y, text, color)
        self.floating_texts.append(ft)

    def add_afterimage(self, sprite, x, y):
        """添加残影"""
        ai = AfterImage(sprite, x, y)
        self.afterimages.append(ai)

    def emit_attraction(self, x, y, target_x, target_y, count, color, lifetime=30):
        """发射被吸引到目标的粒子"""
        for _ in range(count):
            p = AttractionParticle(
                x + random.uniform(-15, 15), y + random.uniform(-15, 15),
                target_x, target_y, lifetime, color, size=2, pull_strength=0.4
            )
            self.attraction_particles.append(p)

    def emit_trail(self, x, y, color=(200, 200, 200)):
        """尾迹特效"""
        for _ in range(2):
            particle = Particle(
                x + random.uniform(-3, 3), y + random.uniform(-3, 3),
                random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5),
                random.randint(5, 10), color, size=random.randint(1, 2)
            )
            self.particles.append(particle)

    def start_screen_shake(self, duration=10, intensity=5):
        """触发屏幕震动"""
        self.screen_shake_duration = max(self.screen_shake_duration, duration)
        self.screen_shake_intensity = max(self.screen_shake_intensity, intensity)

    def get_screen_shake_offset(self):
        """获取屏幕震动偏移"""
        if self.screen_shake_duration > 0:
            ox = random.uniform(-self.screen_shake_intensity, self.screen_shake_intensity)
            oy = random.uniform(-self.screen_shake_intensity, self.screen_shake_intensity)
            return ox, oy
        return 0, 0

    def update(self):
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.alive]
        for tp in self.text_particles:
            tp.update()
        self.text_particles = [tp for tp in self.text_particles if tp.alive]
        for ap in self.attraction_particles:
            ap.update()
        self.attraction_particles = [ap for ap in self.attraction_particles if ap.alive]
        for ai in self.afterimages:
            ai.update()
        self.afterimages = [ai for ai in self.afterimages if ai.alive]
        for ft in self.floating_texts:
            ft.update()
        self.floating_texts = [ft for ft in self.floating_texts if ft.alive]
        for te in self.trail_emitters:
            te.update()
        if self.screen_shake_duration > 0:
            self.screen_shake_duration -= 1
            self.screen_shake_intensity *= 0.9

    def draw(self, screen, camera):
        shake_x, shake_y = self.get_screen_shake_offset()
        for p in self.particles:
            p.draw(screen, camera)
        for tp in self.text_particles:
            tp.draw(screen, camera)
        for ap in self.attraction_particles:
            ap.draw(screen, camera)
        for ai in self.afterimages:
            ai.draw(screen, camera)
        for ft in self.floating_texts:
            ft.draw(screen, camera)
        for te in self.trail_emitters:
            te.draw(screen, camera)
        return shake_x, shake_y


class FloatingText:
    """浮动文字"""

    def __init__(self, x, y, text, color=(255, 255, 255), duration=40):
        self.x = x
        self.y = y
        self.text = str(text)
        self.color = color
        self.duration = duration
        self.max_duration = duration
        self.alive = True

    def update(self):
        self.y -= 1.5
        self.duration -= 1
        if self.duration <= 0:
            self.alive = False

    def draw(self, screen, camera):
        sx, sy = camera.apply_point(int(self.x), int(self.y))
        alpha = int(255 * (self.duration / self.max_duration))
        try:
            font = get_chinese_font(16)
            base = self.color
            if len(base) == 3:
                faded = (base[0], base[1], base[2])
            else:
                faded = base
            surf = font.render(self.text, True, faded)
            surf.set_alpha(alpha)
            screen.blit(surf, (sx - surf.get_width() // 2, sy - surf.get_height() // 2))
        except:
            pass


class TextParticle:
    """渐隐扩散文字粒子 - 用于暴击/连击/状态提示"""

    def __init__(self, x, y, text, color=(255, 255, 255), size=18, duration=50, spread=40):
        self.x = x
        self.y = y
        self.start_x = x
        self.start_y = y
        self.text = str(text)
        self.color = color
        self.size = size
        self.duration = duration
        self.max_duration = duration
        self.spread = spread
        self.alive = True
        angle = random.uniform(0, math.pi * 2)
        self.vx = math.cos(angle) * random.uniform(0.3, 1.2)
        self.vy = -random.uniform(1.5, 3.5)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.96
        self.vy *= 0.96
        self.duration -= 1
        if self.duration <= 0:
            self.alive = False

    def draw(self, screen, camera):
        sx, sy = camera.apply_point(int(self.x), int(self.y))
        progress = self.duration / self.max_duration
        alpha = int(255 * progress)
        scale = 1.0 + (1.0 - progress) * 0.5
        try:
            font = get_chinese_font(int(self.size * scale))
            surf = font.render(self.text, True, self.color)
            surf.set_alpha(alpha)
            screen.blit(surf, (sx - surf.get_width() // 2, sy - surf.get_height() // 2))
        except:
            pass


class TrailEmitter:
    """持续尾迹发射器 - 附加到弹幕或实体上"""

    def __init__(self, color=(255, 200, 100), interval=2, lifetime=12, size=2):
        self.color = color
        self.interval = interval
        self.lifetime = lifetime
        self.size = size
        self.timer = 0
        self.trail_particles = []

    def emit_at(self, x, y):
        """在位置产生尾迹粒子"""
        self.timer += 1
        if self.timer >= self.interval:
            self.timer = 0
            for _ in range(2):
                p = Particle(
                    x + random.uniform(-4, 4), y + random.uniform(-4, 4),
                    random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5),
                    random.randint(self.lifetime // 2, self.lifetime),
                    self.color, self.size
                )
                self.trail_particles.append(p)

    def update(self):
        for p in self.trail_particles:
            p.update()
        self.trail_particles = [p for p in self.trail_particles if p.alive]

    def draw(self, screen, camera):
        for p in self.trail_particles:
            p.draw(screen, camera)


class AttractionParticle(Particle):
    """引力粒子 - 被吸引到目标点"""

    def __init__(self, x, y, target_x, target_y, lifetime, color, size=2, pull_strength=0.3):
        super().__init__(x, y, 0, 0, lifetime, color, size)
        self.target_x = target_x
        self.target_y = target_y
        self.pull_strength = pull_strength

    def update(self):
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 1:
            self.vx += (dx / dist) * self.pull_strength
            self.vy += (dy / dist) * self.pull_strength
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.92
        self.vy *= 0.92
        self.lifetime -= 1
        if self.lifetime <= 0 or dist < 4:
            self.alive = False


class AfterImage:
    """残影效果 - 玩家闪避时留下半透明残影"""

    def __init__(self, sprite, x, y, duration=8, alpha=120):
        self.sprite = sprite
        self.x = x
        self.y = y
        self.duration = duration
        self.max_duration = duration
        self.alpha = alpha
        self.alive = True

    def update(self):
        self.duration -= 1
        if self.duration <= 0:
            self.alive = False

    def draw(self, screen, camera):
        sx, sy = camera.apply_point(int(self.x), int(self.y))
        progress = self.duration / self.max_duration
        alpha = int(self.alpha * progress)
        faded = self.sprite.copy()
        faded.set_alpha(alpha)
        screen.blit(faded, (sx - faded.get_width() // 2, sy - faded.get_height() // 2))


class RingParticle(Particle):
    """环形扩散粒子 - 从中心向外扩展的光环"""

    def __init__(self, x, y, color, radius, lifetime, expand_speed=1.0):
        super().__init__(x, y, 0, 0, lifetime, color, size=1)
        self.radius = radius
        self.current_radius = 0
        self.expand_speed = expand_speed

    def update(self):
        self.current_radius += self.expand_speed
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.alive = False

    def draw(self, screen, camera):
        sx, sy = camera.apply_point(int(self.x), int(self.y))
        progress = self.lifetime / self.max_lifetime
        alpha = int(200 * progress)
        r = int(self.current_radius)
        if r > 0 and alpha > 0:
            ring_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            c = self.color
            pygame.draw.circle(ring_surf, (*c, alpha), (r, r), r, max(1, r // 8))
            screen.blit(ring_surf, (sx - r, sy - r))
