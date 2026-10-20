#!/usr/bin/env python3
"""Continuous Laser Convergence — live target tracking and synchronized lerp colors.
Run: uv run --with pygame laser_convergence_v2.py
Controls: ESC quit | SPACE pause | UP/DOWN change orbit speed
"""

from __future__ import annotations

import math
from collections import deque

import pygame

pygame.init()
WIDTH, HEIGHT = 800, 600
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Continuous Laser Convergence — Live Tracking")

BLACK = (0, 0, 0)
COLORS = [
    (255, 0, 0), (128, 0, 128), (255, 255, 0), (0, 255, 0),
    (0, 0, 255), (0, 255, 255), (255, 0, 255), (128, 128, 0),
    (0, 128, 128), (255, 128, 128), (128, 0, 0), (128, 128, 128),
    (255, 255, 255), (128, 255, 128), (255, 128, 255), (128, 255, 255),
]

COLOR_CHANGE_INTERVAL = 3.0       # Seconds from one palette color to the next
TARGET_ORBIT_RADIUS = 50.0
TARGET_ORBIT_SPEED = 0.65         # Radians per second
LASER_SPEED = 0.5                # Progress / second
EDGER_SPEED = 250.0              # Pixels / second
EDGER_COUNT = 15
TRAIL_LIFETIME = 0.9            # Seconds
TRAIL_RADIUS = 5
FPS = 156

clock = pygame.time.Clock()
trail_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA).convert_alpha()


def lerp_color(a, b, t):
    """Linear color interpolation, t clamped to 0..1."""
    t = max(0.0, min(1.0, t))
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def palette_color(seconds):
    """All lasers use the same smoothly changing RGB at a given time."""
    progress = seconds / COLOR_CHANGE_INTERVAL
    index = int(progress) % len(COLORS)
    t = progress % 1.0
    return lerp_color(COLORS[index], COLORS[(index + 1) % len(COLORS)], t)


class Edger:
    def __init__(self, distance=0.0, radius=5):
        self.radius = radius
        self.speed = EDGER_SPEED
        self.w = WIDTH - 2 * radius
        self.h = HEIGHT - 2 * radius
        self.perimeter = 2 * (self.w + self.h)
        self.distance = distance % self.perimeter
        self.x = 0.0
        self.y = 0.0
        self.update(0.0)

    def update(self, dt):
        self.distance = (self.distance + self.speed * dt) % self.perimeter
        d, r = self.distance, self.radius
        if d < self.w:
            self.x, self.y = r + d, r
        elif d < self.w + self.h:
            self.x, self.y = WIDTH - r, r + d - self.w
        elif d < 2 * self.w + self.h:
            self.x, self.y = WIDTH - r - (d - self.w - self.h), HEIGHT - r
        else:
            self.x, self.y = r, HEIGHT - r - (d - 2 * self.w - self.h)


def create_edgers(count=EDGER_COUNT):
    perimeter = 2 * ((WIDTH - 10) + (HEIGHT - 10))
    return [Edger(i * perimeter / count) for i in range(count)]


class Laser:
    def __init__(self, x, y):
        self.start_x = self.x = float(x)
        self.start_y = self.y = float(y)
        self.progress = 0.0
        self.active = True

    def update(self, dt, target_x, target_y):
        self.progress = min(1.0, self.progress + LASER_SPEED * dt)
        # End point is updated EVERY FRAME rather than captured at launch.
        # Moving endpoints bend the trajectory toward the orbiting target.
        self.x = self.start_x + (target_x - self.start_x) * self.progress
        self.y = self.start_y + (target_y - self.start_y) * self.progress
        self.active = self.progress < 1.0


def main():
    edgers = create_edgers()
    lasers = []
    # Historical positions, not historical colors: all visible trails recolor
    # together during the lerp, including existing trail pixels.
    trails = deque()  # (simulation_time, x, y)
    elapsed = 0.0
    paused = False
    orbit_speed = TARGET_ORBIT_SPEED
    running = True

    while running:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_UP:
                    orbit_speed += 0.1
                elif event.key == pygame.K_DOWN:
                    orbit_speed = max(0.0, orbit_speed - 0.1)

        if not paused:
            elapsed += dt

        angle = elapsed * orbit_speed
        target_x = WIDTH / 2 + TARGET_ORBIT_RADIUS * math.cos(angle)
        target_y = HEIGHT / 2 + TARGET_ORBIT_RADIUS * math.sin(angle)
        color = palette_color(elapsed)

        if not paused:
            for edger in edgers:
                edger.update(dt)
                lasers.append(Laser(edger.x, edger.y))

            active = []
            for laser in lasers:
                laser.update(dt, target_x, target_y)
                trails.append((elapsed, laser.x, laser.y))
                if laser.active:
                    active.append(laser)
            lasers = active
            while trails and elapsed - trails[0][0] > TRAIL_LIFETIME:
                trails.popleft()

        SCREEN.fill(BLACK)
        trail_surface.fill((0, 0, 0, 0))
        for born, x, y in trails:
            age = elapsed - born
            alpha = max(0, min(255, round(210 * (1.0 - age / TRAIL_LIFETIME) ** 1.8)))
            if alpha:
                pygame.draw.circle(trail_surface, (*color, alpha), (round(x), round(y)), TRAIL_RADIUS)
        SCREEN.blit(trail_surface, (0, 0))
        for laser in lasers:
            pygame.draw.circle(SCREEN, color, (round(laser.x), round(laser.y)), 3)
        # pygame.draw.circle(SCREEN, color, (round(target_x), round(target_y)), 5)
        pygame.display.flip()

    pygame.quit()


if __name__ == '__main__':
    main()
