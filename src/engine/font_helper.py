"""
字体辅助 - 解决 Windows 中文显示问题
"""
import pygame
from functools import lru_cache


@lru_cache(maxsize=32)
def get_chinese_font(size):
    """获取支持中文的字体（带缓存）"""
    font_paths = [
        "C:/Windows/Fonts/simhei.ttf",         # 黑体
        "C:/Windows/Fonts/NotoSansSC-VF.ttf",   # Noto 简体中文
        "C:/Windows/Fonts/simkai.ttf",          # 楷体
        "C:/Windows/Fonts/Source Han Serif SC Heavy (TrueType).ttf",
        "C:/Windows/Fonts/msyh.ttc",            # 微软雅黑（备用）
    ]
    for path in font_paths:
        try:
            return pygame.font.Font(path, size)
        except:
            continue
    try:
        return pygame.font.SysFont("simhei", size)
    except:
        pass
    try:
        return pygame.font.SysFont("microsoftyahei", size)
    except:
        pass
    return pygame.font.Font(None, size)
