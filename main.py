import pygame
import random
import math
import sys

# Initialize Pygame
pygame.init()

# Game settings
WIDTH, HEIGHT = 800, 600
FPS = 60
PLAYER_SPEED = 300  # Units per second
BULLET_SPEED = 600
ENEMY_SPEED = 100

# Colors
WHITE = (255, 255, 255)
RED = (200, 50, 50)
GREEN = (50, 200, 50)
BLACK = (0, 0, 0)

# Setup screen
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF)
pygame.display.set_caption("Top-Down Shooter")
clock = pygame.time.Clock()

# Font for FPS display
font = pygame.font.SysFont(None, 24)

# Player class
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((40, 40))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.speed = PLAYER_SPEED

    def update(self, keys, dt):
        dx, dy = 0, 0
        if keys[pygame.K_w]: dy = -1
        if keys[pygame.K_s]: dy = 1
        if keys[pygame.K_a]: dx = -1
        if keys[pygame.K_d]: dx = 1

        movement = pygame.Vector2(dx, dy)
        if movement.length() > 0:
            movement = movement.normalize()

        self.rect.x += movement.x * self.speed * dt
        self.rect.y += movement.y * self.speed * dt
        self.rect.clamp_ip(screen.get_rect())

# Bullet class with direction-based rotation
class Bullet(pygame.sprite.Sprite):
    def __init__(self, pos, direction):
        super().__init__()
        self.original_image = pygame.Surface((20, 6), pygame.SRCALPHA)
        pygame.draw.rect(self.original_image, WHITE, (0, 0, 20, 6))

        self.velocity = pygame.Vector2(direction).normalize() * BULLET_SPEED
        angle = math.degrees(math.atan2(-self.velocity.y, self.velocity.x))
        self.image = pygame.transform.rotate(self.original_image, angle)
        self.rect = self.image.get_rect(center=pos)

    def update(self, dt):
        self.rect.x += self.velocity.x * dt
        self.rect.y += self.velocity.y * dt
        if not screen.get_rect().colliderect(self.rect):
            self.kill()

# Enemy class
class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((30, 30))
        self.image.fill(RED)
        self.rect = self.image.get_rect(center=(random.randint(0, WIDTH), random.randint(0, HEIGHT)))

    def update(self, player_pos, dt):
        direction = pygame.Vector2(player_pos) - pygame.Vector2(self.rect.center)
        if direction.length() > 0:
            direction = direction.normalize()
        self.rect.x += direction.x * ENEMY_SPEED * dt
        self.rect.y += direction.y * ENEMY_SPEED * dt

# Sprite groups
player = Player()
bullets = pygame.sprite.Group()
enemies = pygame.sprite.Group()
all_sprites = pygame.sprite.Group(player)

# Spawn enemies every few seconds
SPAWNENEMY = pygame.USEREVENT + 1
pygame.time.set_timer(SPAWNENEMY, 2000)

# Game loop
running = True
while running:
    dt = clock.tick(FPS) / 1000.0
    keys = pygame.key.get_pressed()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == SPAWNENEMY:
            enemy = Enemy()
            enemies.add(enemy)
            all_sprites.add(enemy)

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            direction = (mx - player.rect.centerx, my - player.rect.centery)
            bullet = Bullet(player.rect.center, direction)
            bullets.add(bullet)
            all_sprites.add(bullet)

    # Update
    player.update(keys, dt)
    for bullet in bullets:
        bullet.update(dt)
    for enemy in enemies:
        enemy.update(player.rect.center, dt)

    # Check bullet collision
    hits = pygame.sprite.groupcollide(enemies, bullets, True, True)

    # Drawing
    screen.fill(BLACK)
    all_sprites.draw(screen)

    # Draw FPS
    fps_text = font.render(f"FPS: {int(clock.get_fps())}", True, WHITE)
    screen.blit(fps_text, (10, 10))

    pygame.display.flip()

pygame.quit()
sys.exit()

