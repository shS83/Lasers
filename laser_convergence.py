import math
import pygame

pygame.init()
WIDTH, HEIGHT = 800, 600
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Continuous Laser Convergence')

BLACK = (0, 0, 0)
COLORS = [
    (255, 0, 0), (128, 0, 128), (255, 255, 0), (0, 255, 0),
    (0, 0, 255), (0, 255, 255), (255, 0, 255), (128, 128, 0),
    (0, 128, 128), (255, 128, 128), (128, 0, 0), (128, 128, 128),
    (255, 255, 255), (128, 255, 128), (255, 128, 255), (128, 255, 255),
]
COLOR_CHANGE_INTERVAL = 3000  # milliseconds
TARGET_ORBIT_RADIUS = 50
TARGET_ORBIT_SPEED = 0.65  # radians / second
LASER_SPEED = 1  # progress per second
EDGER_SPEED = 180  # pixels per second
EDGER_COUNT = 5
TRAIL_ALPHA = 10  # fade strength: 0 = permanent, 255 = immediate erasure

clock = pygame.time.Clock()


class Edger:
    def __init__(self, distance=0, radius=5):
        self.radius = radius
        self.speed = EDGER_SPEED
        self.w = WIDTH - 2 * radius
        self.h = HEIGHT - 2 * radius
        self.perimeter = 2 * (self.w + self.h)
        self.distance = distance % self.perimeter
        self.x = 0.0
        self.y = 0.0
        self.update(0)

    def update(self, dt):
        self.distance = (self.distance + self.speed * dt) % self.perimeter
        d = self.distance
        r = self.radius
        if d < self.w:
            self.x, self.y = r + d, r
        elif d < self.w + self.h:
            self.x, self.y = WIDTH - r, r + (d - self.w)
        elif d < 2 * self.w + self.h:
            self.x, self.y = WIDTH - r - (d - self.w - self.h), HEIGHT - r
        else:
            self.x, self.y = r, HEIGHT - r - (d - 2 * self.w - self.h)


def create_edgers(count=EDGER_COUNT):
    perimeter = 2 * ((WIDTH - 10) + (HEIGHT - 10))
    return [Edger(i * perimeter / count) for i in range(count)]


class Laser:
    def __init__(self, x, y, target_x, target_y):
        self.start_x = x
        self.start_y = y
        # Target captured at emission; this makes the beams converge on
        # the location that the target occupied when launched.
        self.target_x = target_x
        self.target_y = target_y
        self.progress = 0.0
        self.x = x
        self.y = y
        self.active = True

    def update(self, dt):
        self.progress = min(1.0, self.progress + LASER_SPEED * dt)
        self.x = self.start_x + (self.target_x - self.start_x) * self.progress
        self.y = self.start_y + (self.target_y - self.start_y) * self.progress
        self.active = self.progress < 1.0

    def draw(self, surface, color):
        # Every laser receives CURRENT color, not the color from birth.
        pygame.draw.circle(surface, color, (round(self.x), round(self.y)), 3)



edgers = create_edgers()
lasers = []
fade_surface = pygame.Surface((WIDTH, HEIGHT))
fade_surface.fill(BLACK)
fade_surface.set_alpha(TRAIL_ALPHA)

start_time = pygame.time.get_ticks()
previous_color = 0
running = True
while running:
    dt = min(clock.tick(60) / 1000.0, 0.05)
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False

    now = pygame.time.get_ticks()
    elapsed = (now - start_time) / 1000.0
    color_index = ((now - start_time) // COLOR_CHANGE_INTERVAL) % len(COLORS)
    current_color = COLORS[color_index]

    # Existing trail pixels do not automatically recolor. Clear old-color
    # trails on each switch, so *all visible laser points* share one color.
    if color_index != previous_color:
        SCREEN.fill(BLACK)
        previous_color = color_index

    angle = elapsed * TARGET_ORBIT_SPEED
    target_x = WIDTH / 2 + TARGET_ORBIT_RADIUS * math.cos(angle)
    target_y = HEIGHT / 2 + TARGET_ORBIT_RADIUS * math.sin(angle)

    SCREEN.blit(fade_surface, (0, 0))
    for e in edgers:
        e.update(dt)
        lasers.append(Laser(e.x, e.y, target_x, target_y))

    alive = []
    for laser in lasers:
        laser.update(dt)
        laser.draw(SCREEN, current_color)
        if laser.active:
            alive.append(laser)
    lasers = alive

    # pygame.draw.circle(SCREEN, current_color, (round(target_x), round(target_y)), 5)
    pygame.display.flip()

pygame.quit()
