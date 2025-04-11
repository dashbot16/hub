import pygame
import random
import math
import sys

# Initialize Pygame
pygame.init()

# Game settings
WIDTH, HEIGHT = 800, 600
FPS = 60
PLAYER_SPEED = 300
BULLET_SPEED = 600
ENEMY_SPEED = 100
PLAYER_HEALTH = 5
ENEMY_HEALTH = 3
INVINCIBILITY_DURATION = 1.0  # seconds
KNOCKBACK_STRENGTH = 150
WAVE_SIZE_INCREMENT = 2

# Colors
WHITE = (255, 255, 255)
RED = (200, 50, 50)
GREEN = (50, 200, 50)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
BLUE = (50, 150, 255)
DARK_BLUE = (10, 30, 60)

# Setup screen
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF)
pygame.display.set_caption("Top-Down Shooter")
clock = pygame.time.Clock()

# Font for text display
font = pygame.font.SysFont(None, 24)
game_over_font = pygame.font.SysFont(None, 72)
pause_font = pygame.font.SysFont(None, 48)

# Particle class
class Particle:
    def __init__(self, pos):
        self.pos = pygame.Vector2(pos)
        self.velocity = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)) * 100
        self.lifetime = random.uniform(0.3, 0.6)
        self.radius = random.randint(2, 4)

    def update(self, dt):
        self.lifetime -= dt
        self.pos += self.velocity * dt

    def draw(self, surface):
        if self.lifetime > 0:
            pygame.draw.circle(surface, RED, (int(self.pos.x), int(self.pos.y)), self.radius)

# Screen shake
shake_timer = 0
shake_magnitude = 0

def trigger_screen_shake(magnitude, duration):
    global shake_timer, shake_magnitude
    shake_timer = duration
    shake_magnitude = magnitude

def apply_screen_shake():
    if shake_timer > 0:
        return pygame.Vector2(random.randint(-shake_magnitude, shake_magnitude), random.randint(-shake_magnitude, shake_magnitude))
    return pygame.Vector2(0, 0)

# Player class
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.original_image = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.polygon(self.original_image, GREEN, [(0, 0), (40, 20), (0, 40)])
        self.image = self.original_image
        self.rect = self.image.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.speed = PLAYER_SPEED
        self.health = PLAYER_HEALTH
        self.last_hit_time = -INVINCIBILITY_DURATION
        self.velocity = pygame.Vector2(0, 0)

    def update(self, keys, dt):
        self.rect.x += self.velocity.x * dt
        self.rect.y += self.velocity.y * dt
        self.velocity *= 0.9

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

        mx, my = pygame.mouse.get_pos()
        angle = math.degrees(math.atan2(self.rect.centery - my, mx - self.rect.centerx))
        self.image = pygame.transform.rotate(self.original_image, angle)
        self.rect = self.image.get_rect(center=self.rect.center)

    def take_damage(self, current_time, source_pos):
        if current_time - self.last_hit_time >= INVINCIBILITY_DURATION:
            self.health -= 1
            self.last_hit_time = current_time
            knockback = pygame.Vector2(self.rect.center) - pygame.Vector2(source_pos)
            if knockback.length() > 0:
                knockback = knockback.normalize() * KNOCKBACK_STRENGTH
                self.velocity += knockback
            trigger_screen_shake(5, 0.2)
            if self.health <= 0:
                return True
        return False

# Bullet class
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
        self.health = ENEMY_HEALTH

    def update(self, player_pos, dt):
        direction = pygame.Vector2(player_pos) - pygame.Vector2(self.rect.center)
        if direction.length() > 0:
            direction = direction.normalize()
        self.rect.x += direction.x * ENEMY_SPEED * dt
        self.rect.y += direction.y * ENEMY_SPEED * dt

    def draw_health_bar(self, surface):
        health_ratio = self.health / ENEMY_HEALTH
        bar_width = self.rect.width
        bar_height = 5
        bar_x = self.rect.left
        bar_y = self.rect.top - bar_height - 4
        pygame.draw.rect(surface, GRAY, (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(surface, GREEN, (bar_x, bar_y, bar_width * health_ratio, bar_height))

# Sprite groups
player = Player()
bullets = pygame.sprite.Group()
enemies = pygame.sprite.Group()
all_sprites = pygame.sprite.Group(player)
particles = []

# Events
SPAWNENEMY = pygame.USEREVENT + 1
pygame.time.set_timer(SPAWNENEMY, 1000)

def draw_player_health_bar(surface, player):
    max_width = 275
    bar_height = 8
    health_ratio = player.health / PLAYER_HEALTH
    bar_width = int(max_width * health_ratio)
    x = WIDTH // 2 - max_width // 2
    y = 20
    pygame.draw.rect(surface, DARK_BLUE, (x - 2, y - 2, max_width + 4, bar_height + 4))
    pygame.draw.rect(surface, BLUE, (x, y, bar_width, bar_height))

# Game loop
running = True
game_over = False
paused = False
wave = 1
total_enemies = 5
spawned_enemies = 0


def spawn_wave(wave_size):
    global spawned_enemies
    for _ in range(wave_size):
        enemy = Enemy()
        enemies.add(enemy)
        all_sprites.add(enemy)
    spawned_enemies += wave_size

spawn_wave(total_enemies)

while running:
    dt = clock.tick(FPS) / 1000.0
    keys = pygame.key.get_pressed()
    current_time = pygame.time.get_ticks() / 1000.0

    if shake_timer > 0:
        shake_timer -= dt

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if not game_over and not paused:
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                direction = (mx - player.rect.centerx, my - player.rect.centery)
                bullet = Bullet(player.rect.center, direction)
                bullets.add(bullet)
                all_sprites.add(bullet)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                paused = not paused

    if not game_over and not paused:
        player.update(keys, dt)
        bullets.update(dt)
        for enemy in enemies:
            enemy.update(player.rect.center, dt)

        for bullet in bullets:
            hit_list = pygame.sprite.spritecollide(bullet, enemies, False)
            for enemy in hit_list:
                enemy.health -= 1
                bullet.kill()
                particles.extend([Particle(enemy.rect.center) for _ in range(5)])
                trigger_screen_shake(3, 0.1)
                if enemy.health <= 0:
                    enemy.kill()

        player_hit_list = pygame.sprite.spritecollide(player, enemies, False)
        for enemy in player_hit_list:
            if player.take_damage(current_time, enemy.rect.center):
                game_over = True

        if len(enemies) == 0:
            wave += 1
            total_enemies += WAVE_SIZE_INCREMENT
            spawn_wave(total_enemies)

    for p in particles[:]:
        p.update(dt)
        if p.lifetime <= 0:
            particles.remove(p)

    # Drawing
    offset = apply_screen_shake()
    screen.fill(BLACK)
    screen.blit(screen.copy(), offset)

    all_sprites.draw(screen)
    for enemy in enemies:
        enemy.draw_health_bar(screen)
    for p in particles:
        p.draw(screen)

    draw_player_health_bar(screen, player)

    fps_text = font.render(f"FPS: {int(clock.get_fps())}", True, WHITE)
    screen.blit(fps_text, (10, 10))

    if game_over:
        over_text = game_over_font.render("GAME OVER", True, RED)
        screen.blit(over_text, (WIDTH // 2 - over_text.get_width() // 2, HEIGHT // 2 - over_text.get_height() // 2))

    if paused and not game_over:
        pause_text = pause_font.render("PAUSED", True, WHITE)
        screen.blit(pause_text, (WIDTH // 2 - pause_text.get_width() // 2, HEIGHT // 2 - pause_text.get_height() // 2))

    pygame.display.flip()

pygame.quit()
sys.exit()

