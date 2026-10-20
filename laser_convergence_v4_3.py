#!/usr/bin/env python3
"""Rotating Glyph Waves v4.3 — continuous full rotation and no center marker and real font glyphs.

Run: uv run --with pygame laser_convergence_v4_3.py

Keys:
  1 = | glyph, 2 = S glyph, T = type any single Unicode glyph
  +/- = font size, A/D = fewer/more glyphs per ray
  Z/X = fewer/more rays, arrows = wave/orbit speed
  G = glow, J/K = edge speed, [/]=trail length, C=clear trails, SPACE = pause
"""
from __future__ import annotations

import math
import pygame
import random

WIDTH, HEIGHT = 800, 600
FPS = 156
RAYS = 36
GLYPHS_PER_RAY = 150
FONT_SIZE = 36
GLYPH = '´ '
TARGET_ORBIT_RADIUS = 50.0
TARGET_ORBIT_SPEED = 0.65
COLOR_CHANGE_INTERVAL = 3.0
WAVE_SPEED = 2.3
EDGE_SPEED = 180.0  # pixels per second along the screen perimeter
WAVE_FREQUENCY = 0.32
TRAIL_HALF_LIFE = 0.15  # seconds: older glyph marks fade to 50% in this time
COLORS = [
    (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)) for _ in range(16)
]


def color_at(elapsed):
    phase = elapsed / COLOR_CHANGE_INTERVAL
    idx = int(phase) % len(COLORS)
    t = phase % 1.0
    # Smoothstep LERP (no abrupt change in rate at palette boundaries).
    t = t * t * (3.0 - 2.0 * t)
    return tuple(round(a + (b - a) * t)
                 for a, b in zip(COLORS[idx], COLORS[(idx + 1) % len(COLORS)]))


def edge_position(distance):
    margin = 10
    w, h = WIDTH - 2 * margin, HEIGHT - 2 * margin
    d = distance % (2 * (w + h))
    if d < w:
        return margin + d, margin
    if d < w + h:
        return WIDTH - margin, margin + d - w
    if d < 2 * w + h:
        return WIDTH - margin - (d - w - h), HEIGHT - margin
    return margin, HEIGHT - margin - (d - 2 * w - h)


def make_positions(ray_count, glyphs_per_ray, distance_offset, target_x, target_y):
    """Move edge emitters clockwise and attach each glyph chain to the target.

    The emission points remain equally spaced by perimeter distance; their
    movement is continuous even when wrapping around screen corners.
    """
    perimeter = 2 * (WIDTH - 20 + HEIGHT - 20)
    result = []
    for ray in range(ray_count):
        sx, sy = edge_position(ray * perimeter / ray_count + distance_offset)
        base = math.atan2(target_y - sy, target_x - sx)
        for j in range(glyphs_per_ray):
            t = (j + 0.25) / (glyphs_per_ray + 0.7)
            x = sx + (target_x - sx) * t
            y = sy + (target_y - sy) * t
            result.append((x, y, base, j, ray))
    return result


def make_glyph_cache(font, char, steps=72):
    # Render the actual font character once, then cache rotation surfaces.
    # White glyphs get their shared LERP color applied to the entire glyph layer.
    original = font.render(char, True, (255, 255, 255)).convert_alpha()
    if original.get_width() == 0:
        original = font.render('|', True, (255, 255, 255)).convert_alpha()
    # Crop to actual character ink so glyphs rotate around their true center.
    bounds = original.get_bounding_rect(min_alpha=1)
    if bounds.width and bounds.height:
        original = original.subsurface(bounds).copy()
    pad = max(original.get_width(), original.get_height()) + 4
    base = pygame.Surface((pad * 2, pad * 2), pygame.SRCALPHA).convert_alpha()
    base.blit(original, original.get_rect(center=base.get_rect().center))
    return [pygame.transform.rotate(base, -(360 * k / steps)).convert_alpha()
            for k in range(steps)]


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('Rotating Glyph Waves v4.3 — Continuous Rotation')
    clock = pygame.time.Clock()
    layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA).convert_alpha()
    trails = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA).convert_alpha()
    trails.fill((0, 0, 0, 0))
    trail_half_life = TRAIL_HALF_LIFE
    font_size, glyph, rays, per_ray = FONT_SIZE, GLYPH, RAYS, GLYPHS_PER_RAY
    positions = []
    font = pygame.font.SysFont('dejavusansmono', font_size)
    cache = make_glyph_cache(font, glyph)
    hud_font = pygame.font.SysFont('monospace', 15)
    elapsed = 0.0
    orbit_speed, wave_speed = TARGET_ORBIT_SPEED, WAVE_SPEED
    edge_speed = EDGE_SPEED
    edge_distance = 0.0
    paused = False
    glow = False
    awaiting_char = False
    show_hud = False
    running = True

    while running:
        dt = min(clock.tick(FPS) / 1000, 0.05)
        rebuild_glyphs = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.TEXTINPUT and awaiting_char:
                if event.text and event.text[0].isprintable() and not event.text[0].isspace():
                    glyph = event.text[0]
                    rebuild_glyphs = True
                awaiting_char = False
                pygame.key.stop_text_input()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if awaiting_char:
                        awaiting_char = False
                        pygame.key.stop_text_input()
                    else:
                        running = False
                elif awaiting_char:
                    continue
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_1:
                    glyph = '|'
                    rebuild_glyphs = True
                elif event.key == pygame.K_2:
                    glyph = 'S'
                    rebuild_glyphs = True
                elif event.key == pygame.K_t:
                    awaiting_char = True
                    pygame.key.start_text_input()
                elif event.key in (pygame.K_EQUALS, pygame.K_KP_PLUS):
                    font_size = min(100, font_size + 2)
                    rebuild_glyphs = True
                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    font_size = max(8, font_size - 2)
                    rebuild_glyphs = True
                elif event.key == pygame.K_a:
                    per_ray = max(8, per_ray - 8)
                elif event.key == pygame.K_d:
                    per_ray = min(150, per_ray + 8)
                elif event.key == pygame.K_z:
                    rays = max(4, rays - 2)
                elif event.key == pygame.K_x:
                    rays = min(90, rays + 2)
                elif event.key == pygame.K_LEFT:
                    wave_speed = max(0.0, wave_speed - 0.2)
                elif event.key == pygame.K_RIGHT:
                    wave_speed += 0.2
                elif event.key == pygame.K_DOWN:
                    orbit_speed = max(0.0, orbit_speed - .1)
                elif event.key == pygame.K_UP:
                    orbit_speed += .1
                elif event.key == pygame.K_j:
                    edge_speed = max(0.0, edge_speed - 20)
                elif event.key == pygame.K_k:
                    edge_speed += 20
                elif event.key == pygame.K_g:
                    glow = not glow
                elif event.key == pygame.K_LEFTBRACKET:
                    trail_half_life = max(0.05, trail_half_life - 0.05)
                elif event.key == pygame.K_RIGHTBRACKET:
                    trail_half_life = min(3.0, trail_half_life + 0.05)
                elif event.key == pygame.K_c:
                    trails.fill((0, 0, 0, 0))
                elif event.key == pygame.K_h:
                    show_hud = not show_hud
        if rebuild_glyphs:
            font = pygame.font.SysFont('dejavusansmono', font_size)
            cache = make_glyph_cache(font, glyph)
        if not paused:
            elapsed += dt
            edge_distance += edge_speed * dt

        target_x = WIDTH / 2 + TARGET_ORBIT_RADIUS * math.cos(elapsed * orbit_speed)
        target_y = HEIGHT / 2 + TARGET_ORBIT_RADIUS * math.sin(elapsed * orbit_speed)
        positions = make_positions(rays, per_ray, edge_distance, target_x, target_y)
        screen.fill((0, 0, 0))
        layer.fill((0, 0, 0, 0))

        for x, y, base, j, ray in positions:
            phase = elapsed * wave_speed - j * WAVE_FREQUENCY + ray * .24
            # Continuous rotation: unbounded phase means full 360-degree
            # revolutions instead of pendulum-like sin(phase) rocking.
            angle = base + phase
            k = int((angle % math.tau) * len(cache) / math.tau + .5) % len(cache)
            glyph_surface = cache[k]
            layer.blit(glyph_surface, glyph_surface.get_rect(center=(round(x), round(y))))

        color = color_at(elapsed)
        # Tint only the already-rendered glyph pixels; keep transparent areas
        # transparent and never paint a rectangular target/overlay.
        layer.fill(color, special_flags=pygame.BLEND_RGB_MULT)
        # Fade the previous RGBA image by a frame-rate independent amount.
        # Multiplying alpha rather than RGB preserves trail colors and avoids
        # black rectangles that appear with opaque overlays.
        if not paused:
            decay = round(255 * (0.5 ** (dt / trail_half_life)))
            trails.fill((255, 255, 255, decay), special_flags=pygame.BLEND_RGBA_MULT)
            trails.blit(layer, (0, 0))
        if glow:
            small = pygame.transform.smoothscale(trails, (WIDTH // 5, HEIGHT // 5))
            blurry = pygame.transform.smoothscale(small, (WIDTH, HEIGHT))
            blurry.set_alpha(95)
            screen.blit(blurry, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        screen.blit(trails, (0, 0))

        if show_hud:
            label = (f"'{glyph}' {font_size}px | {rays} rays x {per_ray} = {len(positions)} glyphs | "
                     f"{clock.get_fps():.0f} FPS | 1:| 2:S T:type +/-:size A/D:density "
                     f"Z/X:rays J/K:edge({edge_speed:.0f}) [/] trail({trail_half_life:.2f}s) C:clear G:glow H:hide")
            text = hud_font.render(label, True, (210, 220, 240))
            if text.get_width() > WIDTH - 12:
                text = pygame.transform.smoothscale(text, (WIDTH - 12, text.get_height()))
            screen.blit(text, (6, 6))
            if awaiting_char:
                prompt = hud_font.render('Type any character...', True, (255, 200, 110))
                screen.blit(prompt, (6, 27))
        pygame.display.flip()
    pygame.key.stop_text_input()
    pygame.quit()


if __name__ == '__main__':
    main()
