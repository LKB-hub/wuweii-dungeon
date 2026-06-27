"""
音效系统 - 加载外部音效文件，回退到程序化生成
"""
import os
import glob
import math
import struct
import random
import pygame

SFX_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assets', 'sfx')


class SoundManager:
    """管理游戏音效：优先加载 WAV 文件，回退到程序化生成"""

    def __init__(self):
        self.sounds = {}
        self.enabled = True
        self.volume = 0.3
        self._loaded = False

    def ensure_loaded(self):
        if not self._loaded:
            self._load_sfx_files()
            self._fill_with_procedural()
            self._loaded = True

    # ==================== 外部音效加载 ====================

    def _load_sfx_files(self):
        """从 assets/sfx/ 加载所有 WAV 文件"""
        if not os.path.isdir(SFX_DIR):
            print(f"[Sound] SFX dir not found: {SFX_DIR}")
            return

        count = 0
        for root, dirs, files in os.walk(SFX_DIR):
            for fname in files:
                if not fname.lower().endswith('.wav'):
                    continue

                full = os.path.join(root, fname)
                name_no_ext = os.path.splitext(fname)[0]

                try:
                    sound = pygame.mixer.Sound(full)
                    sound.set_volume(self.volume)
                except Exception as e:
                    print(f"[Sound] Failed to load {fname}: {e}")
                    continue

                # 按原始文件名注册
                self.sounds[name_no_ext] = sound

                # 智能映射：根据文件名关键词建立 game_sound_name → sound file 映射
                # 这些映射让游戏里 sound.play('shoot') 能找到对应的 wav
                mappings = self._guess_mappings(name_no_ext.lower())
                for mapping_name in mappings:
                    if mapping_name not in self.sounds:
                        self.sounds[mapping_name] = sound

                count += 1

        print(f"[Sound] Loaded {count} SFX files")

    @staticmethod
    def _guess_mappings(filename):
        """根据文件名猜测对应的游戏音效名称"""
        f = filename.lower()
        results = []

        # 战斗音效
        if any(k in f for k in ['shoot', 'shot', 'gun', 'fire', 'blast']):
            results.extend(['shoot', 'fire'])
        if any(k in f for k in ['hit', 'hurt', 'damage', 'punch']):
            results.extend(['hit'])
        if any(k in f for k in ['explo', 'boom', 'bomb']):
            results.extend(['explosion'])
        if any(k in f for k in ['sword', 'slash', 'slice', 'swing']):
            results.extend(['sword_slash'])
        if any(k in f for k in ['bow', 'arrow', 'twang']):
            results.extend(['bow_twang'])
        if any(k in f for k in ['laser', 'zap', 'beam']):
            results.extend(['laser_zap', 'shoot'])
        if any(k in f for k in ['staff', 'magic', 'spell', 'cast']):
            results.extend(['staff_cast'])
        if any(k in f for k in ['ice', 'freeze', 'crack']):
            results.extend(['ice_crack'])
        if any(k in f for k in ['fire', 'flame', 'whoosh']):
            results.extend(['fire_whoosh'])
        if any(k in f for k in ['lightn', 'thunder', 'electr']):
            results.extend(['lightning'])
        if any(k in f for k in ['crossbow', 'click']):
            results.extend(['crossbow_click'])

        # 道具/拾取
        if any(k in f for k in ['pickup', 'collect', 'get', 'grab']):
            results.extend(['pickup'])
        if any(k in f for k in ['coin', 'gold', 'money']):
            results.extend(['coin'])
        if any(k in f for k in ['heal', 'health', 'cure']):
            results.extend(['heal'])
        if any(k in f for k in ['shield', 'protect']):
            results.extend(['shield_up'])
        if any(k in f for k in ['chest', 'open', 'treasure']):
            results.extend(['chest_open'])

        # 玩家动作
        if any(k in f for k in ['dash', 'dodge', 'roll', 'step']):
            results.extend(['dash', 'dodge_success'])
        if any(k in f for k in ['door', 'gate']):
            results.extend(['door_open'])
        if any(k in f for k in ['foot', 'step', 'walk']):
            results.extend(['footstep'])
        if any(k in f for k in ['death', 'die', 'dead']):
            results.extend(['death'])
        if any(k in f for k in ['level', 'upgrade', 'gain']):
            results.extend(['level_up'])
        if any(k in f for k in ['victory', 'win', 'success', 'fanfare']):
            results.extend(['victory'])
        if any(k in f for k in ['error', 'fail', 'wrong']):
            results.extend(['error'])

        # 菜单/UI
        if any(k in f for k in ['click', 'select', 'menu', 'button', 'confirm']):
            results.extend(['menu_click'])
        if any(k in f for k in ['portal', 'teleport', 'warp']):
            results.extend(['portal'])
        if any(k in f for k in ['charge', 'power']):
            results.extend(['charge_up'])
        if any(k in f for k in ['combo', 'chain']):
            results.extend(['combo_5'])

        # 怪物
        if any(k in f for k in ['roar', 'howl', 'growl', 'monster', 'beast', 'giant', 'ogre']):
            results.extend(['boss_roar'])

        return results

    # ==================== 程序化回退生成 ====================

    def _fill_with_procedural(self):
        """为缺失的音效生成程序化版本"""
        generators = {
            'shoot':      (self._gen_shoot, 0.10),
            'hit':        (self._gen_hit, 0.08),
            'explosion':  (self._gen_explosion, 0.30),
            'pickup':     (self._gen_pickup, 0.12),
            'dash':       (self._gen_dash, 0.15),
            'door_open':  (self._gen_door, 0.20),
            'boss_roar':  (self._gen_boss_roar, 0.50),
            'death':      (self._gen_death, 0.25),
            'level_up':   (self._gen_level_up, 0.40),
            'menu_click': (self._gen_menu_click, 0.05),
            'error':      (self._gen_error, 0.10),
            'heal':       (self._gen_heal, 0.20),
            'shield_up':  (self._gen_shield_up, 0.18),
            'ice_crack':  (self._gen_ice_crack, 0.15),
            'fire_whoosh':(self._gen_fire_whoosh, 0.25),
            'lightning':  (self._gen_lightning, 0.25),
            'coin':       (self._gen_coin, 0.06),
            'victory':    (self._gen_victory, 0.80),
            'sword_slash':(self._gen_sword_slash, 0.12),
            'bow_twang':  (self._gen_bow_twang, 0.10),
            'staff_cast': (self._gen_staff_cast, 0.18),
            'laser_zap':  (self._gen_laser_zap, 0.20),
            'crossbow_click':(self._gen_crossbow_click, 0.08),
            'footstep':   (self._gen_footstep, 0.04),
            'chest_open': (self._gen_chest_open, 0.30),
            'portal':     (self._gen_portal, 0.40),
            'charge_up':  (self._gen_charge_up, 0.35),
            'combo_5':    (self._gen_combo_5, 0.25),
            'combo_10':   (self._gen_combo_10, 0.35),
            'dodge_success':(self._gen_dodge_success, 0.15),
        }

        for name, (generator, duration) in generators.items():
            if name in self.sounds:
                continue
            self._generate_procedural(name, generator, duration)

    def _generate_procedural(self, name, generator, duration):
        """生成单个程序化音效"""
        try:
            sample_rate = 22050
            num_samples = int(sample_rate * duration)
            samples = generator(num_samples, sample_rate)
            data = struct.pack(f'<{len(samples)}h', *samples)
            sound = pygame.mixer.Sound(buffer=data)
            sound.set_volume(self.volume)
            self.sounds[name] = sound
        except Exception as e:
            print(f"[Sound] Procedural gen failed [{name}]: {e}")

    # ==================== API ====================

    def play(self, name):
        if not self.enabled:
            return
        self.ensure_loaded()
        sound = self.sounds.get(name)
        if sound:
            sound.play()
        else:
            print(f"[Sound] No sound found for: {name}")

    def toggle(self):
        self.enabled = not self.enabled

    # ==================== 程序化音效生成（完整保留原版） ====================

    @staticmethod
    def _envelope(samples, attack_pct=0.05, release_pct=0.3):
        n = len(samples)
        result = list(samples)
        attack_end = int(n * attack_pct)
        release_start = int(n * (1 - release_pct))
        for i in range(n):
            if i < attack_end:
                result[i] = int(result[i] * (i / max(1, attack_end)))
            elif i > release_start:
                result[i] = int(result[i] * ((n - i) / max(1, n - release_start)))
        return result

    @staticmethod
    def _gen_shoot(num_samples, rate):
        samples = []
        freq = 800
        for i in range(num_samples):
            t = i / rate
            val = int(8000 * math.sin(2 * math.pi * freq * t) * math.exp(-t * 60))
            noise = int(2000 * (2 * ((i * 12345) % 1000) / 1000 - 1) * math.exp(-t * 40))
            samples.append(max(-32768, min(32767, val + noise)))
        return SoundManager._envelope(samples, 0.02, 0.5)

    @staticmethod
    def _gen_hit(num_samples, rate):
        samples = []
        freq = 400
        for i in range(num_samples):
            t = i / rate
            val = int(6000 * math.sin(2 * math.pi * freq * t) * math.exp(-t * 80))
            samples.append(max(-32768, min(32767, val)))
        return SoundManager._envelope(samples, 0.01, 0.3)

    @staticmethod
    def _gen_explosion(num_samples, rate):
        samples = []
        for i in range(num_samples):
            t = i / rate
            noise = (2 * ((i * 67890) % 1000) / 1000 - 1)
            val = int(12000 * noise * math.exp(-t * 12))
            if t < 0.05:
                val += int(8000 * math.sin(2 * math.pi * 60 * t) * math.exp(-t * 20))
            samples.append(max(-32768, min(32767, val)))
        return SoundManager._envelope(samples, 0.01, 0.4)

    @staticmethod
    def _gen_pickup(num_samples, rate):
        samples = []
        for i in range(num_samples):
            t = i / rate
            freq = 600 + 800 * (t / max(1, num_samples / rate))
            val = int(4000 * math.sin(2 * math.pi * freq * t) * math.exp(-t * 15))
            samples.append(max(-32768, min(32767, val)))
        return SoundManager._envelope(samples, 0.03, 0.2)

    @staticmethod
    def _gen_dash(num_samples, rate):
        samples = []
        for i in range(num_samples):
            t = i / rate
            freq = 200 + 300 * math.sin(t * 30)
            val = int(5000 * math.sin(2 * math.pi * freq * t) * math.exp(-t * 20))
            samples.append(max(-32768, min(32767, val)))
        return SoundManager._envelope(samples, 0.02, 0.4)

    @staticmethod
    def _gen_door(num_samples, rate):
        samples = []
        for i in range(num_samples):
            t = i / rate
            freq = 300
            val = int(5000 * math.sin(2 * math.pi * freq * t) * math.exp(-t * 8))
            noise = int(2000 * (2 * ((i * 45678) % 1000) / 1000 - 1) * math.exp(-t * 10))
            samples.append(max(-32768, min(32767, val + noise)))
        return SoundManager._envelope(samples, 0.05, 0.5)

    @staticmethod
    def _gen_boss_roar(num_samples, rate):
        samples = []
        for i in range(num_samples):
            t = i / rate
            base = math.sin(2 * math.pi * 80 * t)
            warble = math.sin(2 * math.pi * 15 * math.sin(2 * math.pi * 3 * t) * t)
            val = int(15000 * (base * 0.6 + warble * 0.4) * math.exp(-t * 5))
            samples.append(max(-32768, min(32767, val)))
        return SoundManager._envelope(samples, 0.1, 0.5)

    @staticmethod
    def _gen_death(num_samples, rate):
        samples = []
        for i in range(num_samples):
            t = i / rate
            freq = 300 - 200 * (t / max(1, num_samples / rate))
            val = int(6000 * math.sin(2 * math.pi * freq * t) * math.exp(-t * 8))
            noise = int(3000 * (2 * ((i * 56789) % 1000) / 1000 - 1) * math.exp(-t * 10))
            samples.append(max(-32768, min(32767, val + noise)))
        return SoundManager._envelope(samples, 0.02, 0.6)

    @staticmethod
    def _gen_level_up(num_samples, rate):
        samples = []
        notes = [523, 659, 784, 1047]
        note_dur = num_samples // len(notes)
        for ni, freq in enumerate(notes):
            for i in range(note_dur):
                idx = ni * note_dur + i
                if idx >= num_samples:
                    break
                t = (idx - ni * note_dur) / rate
                val = int(5000 * math.sin(2 * math.pi * freq * t) * math.exp(-t * 5))
                samples.append(max(-32768, min(32767, val)))
        return SoundManager._envelope(samples, 0.05, 0.3)

    @staticmethod
    def _gen_menu_click(num_samples, rate):
        samples = []
        freq = 1000
        for i in range(num_samples):
            t = i / rate
            val = int(4000 * math.sin(2 * math.pi * freq * t) * math.exp(-t * 80))
            samples.append(max(-32768, min(32767, val)))
        return SoundManager._envelope(samples, 0.01, 0.2)

    @staticmethod
    def _gen_error(num_samples, rate):
        samples = []
        for i in range(num_samples):
            t = i / rate
            freq = 200
            val = int(4000 * math.sin(2 * math.pi * freq * t) * math.exp(-t * 15))
            if t > 0.04:
                freq = 150
                val = int(3000 * math.sin(2 * math.pi * freq * (t - 0.04)) * math.exp(-(t - 0.04) * 20))
            samples.append(max(-32768, min(32767, val)))
        return SoundManager._envelope(samples, 0.02, 0.3)

    @staticmethod
    def _gen_heal(num_samples, rate):
        samples = []
        for i in range(num_samples):
            t = i / rate
            freq = 500 + 300 * (t / max(1, num_samples / rate))
            val = int(4000 * math.sin(2 * math.pi * freq * t) * math.exp(-t * 6))
            val += int(2000 * math.sin(2 * math.pi * freq * 1.5 * t) * math.exp(-t * 8))
            samples.append(max(-32768, min(32767, val)))
        return SoundManager._envelope(samples, 0.05, 0.3)

    @staticmethod
    def _gen_shield_up(num_samples, rate):
        samples = []
        for i in range(num_samples):
            t = i / rate
            freq = 300 + 200 * math.sin(t * 15)
            val = int(5000 * math.sin(2 * math.pi * freq * t) * math.exp(-t * 10))
            samples.append(max(-32768, min(32767, val)))
        return SoundManager._envelope(samples, 0.03, 0.3)

    @staticmethod
    def _gen_ice_crack(num_samples, rate):
        samples = []
        for i in range(num_samples):
            t = i / rate
            noise = (2 * ((i * 34567) % 1000) / 1000 - 1)
            freq = 800 - 500 * (t / max(1, num_samples / rate))
            val = int(6000 * noise * math.exp(-t * 25))
            val += int(3000 * math.sin(2 * math.pi * freq * t) * math.exp(-t * 30))
            samples.append(max(-32768, min(32767, val)))
        return SoundManager._envelope(samples, 0.02, 0.4)

    @staticmethod
    def _gen_fire_whoosh(num_samples, rate):
        samples = []
        for i in range(num_samples):
            t = i / rate
            noise = (2 * ((i * 56789) % 1000) / 1000 - 1)
            val = int(8000 * noise * math.exp(-t * 10))
            val += int(2000 * math.sin(2 * math.pi * 200 * t) * math.exp(-t * 8))
            samples.append(max(-32768, min(32767, val)))
        return SoundManager._envelope(samples, 0.02, 0.5)

    @staticmethod
    def _gen_lightning(num_samples, rate):
        samples = []
        for i in range(num_samples):
            t = i / rate
            noise = (2 * ((i * 78901) % 1000) / 1000 - 1)
            crackle = int(12000 * noise * math.exp(-t * 30))
            if t < 0.05:
                crackle += int(8000 * math.sin(2 * math.pi * 1000 * t) * math.exp(-t * 40))
            samples.append(max(-32768, min(32767, crackle)))
        return SoundManager._envelope(samples, 0.01, 0.3)

    @staticmethod
    def _gen_coin(num_samples, rate):
        samples = []
        for i in range(num_samples):
            t = i / rate
            freq = 1500 + 500 * math.sin(t * 50)
            val = int(3000 * math.sin(2 * math.pi * freq * t) * math.exp(-t * 40))
            samples.append(max(-32768, min(32767, val)))
        return SoundManager._envelope(samples, 0.01, 0.1)

    @staticmethod
    def _gen_victory(num_samples, rate):
        notes = [523, 659, 784, 1047, 1319, 1568]
        samples = []
        note_dur = num_samples // len(notes)
        for ni, freq in enumerate(notes):
            for i in range(note_dur):
                idx = ni * note_dur + i
                if idx >= num_samples:
                    break
                t = i / rate
                val = int(4000 * math.sin(2 * math.pi * freq * t) * math.exp(-t * 3))
                val += int(1500 * math.sin(2 * math.pi * freq * 1.5 * t) * math.exp(-t * 4))
                samples.append(max(-32768, min(32767, val)))
        return SoundManager._envelope(samples, 0.03, 0.4)

    @staticmethod
    def _gen_sword_slash(num_samples, rate):
        samples = []
        for i in range(num_samples):
            t = i / rate
            noise = (2 * ((i * 11111) % 1000) / 1000 - 1)
            val = int(7000 * noise * math.exp(-t * 25))
            val += int(3000 * math.sin(2 * math.pi * 600 * t) * math.exp(-t * 30))
            samples.append(max(-32768, min(32767, val)))
        return SoundManager._envelope(samples, 0.01, 0.3)

    @staticmethod
    def _gen_bow_twang(num_samples, rate):
        samples = []
        for i in range(num_samples):
            t = i / rate
            freq = 900 - 300 * math.exp(-t * 50)
            val = int(4000 * math.sin(2 * math.pi * freq * t) * math.exp(-t * 30))
            samples.append(max(-32768, min(32767, val)))
        return SoundManager._envelope(samples, 0.01, 0.2)

    @staticmethod
    def _gen_staff_cast(num_samples, rate):
        samples = []
        for i in range(num_samples):
            t = i / rate
            freq = 200 + 400 * (t / max(1, num_samples / rate))
            val = int(5000 * math.sin(2 * math.pi * freq * t) * math.exp(-t * 8))
            val += int(3000 * math.sin(2 * math.pi * freq * 2 * t) * math.exp(-t * 6))
            samples.append(max(-32768, min(32767, val)))
        return SoundManager._envelope(samples, 0.03, 0.3)

    @staticmethod
    def _gen_laser_zap(num_samples, rate):
        samples = []
        for i in range(num_samples):
            t = i / rate
            freq = 1200 - 400 * (t / max(1, num_samples / rate))
            noise = (2 * ((i * 33333) % 1000) / 1000 - 1)
            val = int(5000 * math.sin(2 * math.pi * freq * t) * math.exp(-t * 15))
            val += int(4000 * noise * math.exp(-t * 20))
            samples.append(max(-32768, min(32767, val)))
        return SoundManager._envelope(samples, 0.01, 0.2)

    @staticmethod
    def _gen_crossbow_click(num_samples, rate):
        samples = []
        for i in range(num_samples):
            t = i / rate
            val = int(5000 * math.sin(2 * math.pi * 500 * t) * math.exp(-t * 60))
            val += int(3000 * (2 * ((i * 22222) % 1000) / 1000 - 1) * math.exp(-t * 40))
            samples.append(max(-32768, min(32767, val)))
        return SoundManager._envelope(samples, 0.01, 0.2)

    @staticmethod
    def _gen_footstep(num_samples, rate):
        samples = []
        for i in range(num_samples):
            t = i / rate
            noise = (2 * ((i * 7777) % 1000) / 1000 - 1)
            val = int(2000 * noise * math.exp(-t * 50))
            samples.append(max(-32768, min(32767, val)))
        return SoundManager._envelope(samples, 0.01, 0.1)

    @staticmethod
    def _gen_chest_open(num_samples, rate):
        samples = []
        notes = [400, 600, 800, 1000]
        note_dur = num_samples // len(notes)
        for ni, freq in enumerate(notes):
            for i in range(note_dur):
                idx = ni * note_dur + i
                if idx >= num_samples:
                    break
                t = i / rate
                val = int(4000 * math.sin(2 * math.pi * freq * t) * math.exp(-t * 8))
                samples.append(max(-32768, min(32767, val)))
        return SoundManager._envelope(samples, 0.02, 0.3)

    @staticmethod
    def _gen_portal(num_samples, rate):
        samples = []
        for i in range(num_samples):
            t = i / rate
            freq = 300 + 200 * math.sin(t * 5)
            val = int(6000 * math.sin(2 * math.pi * freq * t) * math.exp(-t * 4))
            val += int(3000 * math.sin(2 * math.pi * freq * 1.3 * t) * math.exp(-t * 5))
            samples.append(max(-32768, min(32767, val)))
        return SoundManager._envelope(samples, 0.05, 0.4)

    @staticmethod
    def _gen_charge_up(num_samples, rate):
        samples = []
        for i in range(num_samples):
            t = i / rate
            freq = 100 + 400 * (t / max(1, num_samples / rate))
            val = int(4000 * math.sin(2 * math.pi * freq * t) * (0.5 + 0.5 * t / max(1, num_samples / rate)))
            samples.append(max(-32768, min(32767, val)))
        return SoundManager._envelope(samples, 0.1, 0.2)

    @staticmethod
    def _gen_combo_5(num_samples, rate):
        samples = []
        notes = [600, 800, 1000]
        note_dur = num_samples // len(notes)
        for ni, freq in enumerate(notes):
            for i in range(note_dur):
                idx = ni * note_dur + i
                if idx >= num_samples:
                    break
                t = i / rate
                val = int(4000 * math.sin(2 * math.pi * freq * t) * math.exp(-t * 10))
                samples.append(max(-32768, min(32767, val)))
        return SoundManager._envelope(samples, 0.03, 0.2)

    @staticmethod
    def _gen_combo_10(num_samples, rate):
        samples = []
        notes = [400, 600, 800, 1000, 1200]
        note_dur = num_samples // len(notes)
        for ni, freq in enumerate(notes):
            for i in range(note_dur):
                idx = ni * note_dur + i
                if idx >= num_samples:
                    break
                t = i / rate
                val = int(5000 * math.sin(2 * math.pi * freq * t) * math.exp(-t * 8))
                val += int(2000 * math.sin(2 * math.pi * freq * 2 * t) * math.exp(-t * 6))
                samples.append(max(-32768, min(32767, val)))
        return SoundManager._envelope(samples, 0.03, 0.3)

    @staticmethod
    def _gen_dodge_success(num_samples, rate):
        samples = []
        for i in range(num_samples):
            t = i / rate
            freq = 800 + 400 * math.sin(t * 20)
            val = int(3000 * math.sin(2 * math.pi * freq * t) * math.exp(-t * 15))
            samples.append(max(-32768, min(32767, val)))
        return SoundManager._envelope(samples, 0.02, 0.3)


# 全局单例
_sound_manager = None


def get_sound_manager():
    global _sound_manager
    if _sound_manager is None:
        _sound_manager = SoundManager()
    return _sound_manager
