import pygame
import random
import sys
import asyncio
from abc import ABC, abstractmethod
import math

pygame.init()

WIDTH, HEIGHT = 1440, 900
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Game")
clock = pygame.time.Clock()

WHITE = (245, 245, 245)
BLACK = (30, 30, 30)
BLUE = (70, 130, 255)
RED = (220, 80, 80)
GREEN = (80, 200, 120)
GRAY = (180, 180, 180)

# =========================
# 이미지 로드 (pygbag: 직접 Surface로 대체)
# =========================
def make_icon(color, size=24):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(surf, color, (size//2, size//2), size//2)
    return surf

blink_img  = make_icon((100, 100, 255))
recall_img = make_icon((100, 200, 100))
purse_img  = make_icon((255, 200, 50))

# =========================
# Base
# =========================
class GameObject(ABC):
    def __init__(self):
        self._alive = True

    @property
    def is_alive(self):
        return self._alive

    def destroy(self):
        self._alive = False

    @property
    def rect(self):
        pass

    @abstractmethod
    def update(self): pass

    @abstractmethod
    def draw(self, surface): pass

# =========================
# Player
# =========================
class Player(GameObject):
    def __init__(self):
        super().__init__()
        self._x = 100
        self._y = 300
        self._size = 40
        self._speed = 8

        self._hp = 175
        self._max_hp = 175

        self._aim_dx = 1
        self._aim_dy = 0

        self._move_dx = 0
        self._move_dy = 0

        self._blink_stack = 3
        self._blink_max_stack = 3
        self._blink_cooldown = 0
        self._blink_recharge_time = 180
        self._blink_max = 180
        self._blink_pressed_last = False

        self._history = []
        self._recall_cooldown = 0
        self._recall_max = 60 * 13

        self._recalling = False
        self._recall_timer = 0
        self._recall_duration = 55
        self._recall_start = (0, 0)
        self._recall_target = (0, 0)
        self._recall_path = []

        self._ammo = 40
        self._reloading = False
        self._reload_timer = 0
        self._reload_max = 60
        self._fire_timer = 0
        self._bullet_delay = 2

        self._purse_charge = 0
        self._purse_ready = False

    @property
    def rect(self):
        return pygame.Rect(int(self._x), int(self._y), self._size, self._size)

    def take_damage(self, amount):
        self._hp -= amount
        if self._hp <= 0:
            self.destroy()

    def add_purse(self, dmg):
        self._purse_charge += dmg
        if self._purse_charge >= 1375:
            self._purse_charge = 1375
            self._purse_ready = True

    def use_purse(self):
        if self._purse_ready:
            self._purse_ready = False
            self._purse_charge = 0
            return True
        return False

    def blink(self):
        if self._blink_stack <= 0:
            return
        dx = self._move_dx
        dy = self._move_dy
        if dx == 0 and dy == 0:
            return
        self._x += dx * 100
        self._y += dy * 100
        self._blink_stack -= 1

    def recall(self):
        if self._recall_cooldown > 0 or self._recalling:
            return
        if len(self._history) < 180:
            return
        self._recall_path = self._history[-180:]
        _, _, old_hp = self._recall_path[0]
        if old_hp >= self._hp:
            self._hp = old_hp
        self._recalling = True
        self._recall_timer = 0
        self._recall_cooldown = self._recall_max

    def shoot(self, objects):
        if self._reloading or self._recalling:
            return
        if self._ammo <= 0:
            self.reload()
            return
        if pygame.mouse.get_pressed()[0]:
            self._fire_timer += 1
            if self._fire_timer >= self._bullet_delay:
                cx = self._x + self._size / 2
                cy = self._y + self._size / 2
                perp_x = -self._aim_dy
                perp_y = self._aim_dx
                offset = 8
                objects.append(Bullet(cx + perp_x*offset, cy + perp_y*offset,
                                      self._aim_dx, self._aim_dy))
                objects.append(Bullet(cx - perp_x*offset, cy - perp_y*offset,
                                      self._aim_dx, self._aim_dy))
                self._ammo -= 2
                self._fire_timer = 0
        else:
            self._fire_timer = 0

    def reload(self):
        if not self._reloading:
            self._reloading = True
            self._reload_timer = self._reload_max

    def update(self):
        if self._blink_stack < self._blink_max_stack:
            self._blink_cooldown += 1
            if self._blink_cooldown >= self._blink_recharge_time:
                self._blink_stack += 1
                self._blink_cooldown = 0

        self.add_purse(5 / 60)
        keys = pygame.key.get_pressed()

        if self._recalling:
            step = 3
            index = self._recall_timer * step
            if index < len(self._recall_path):
                reverse_index = len(self._recall_path) - 1 - index
                x, y, _ = self._recall_path[reverse_index]
                self._x = x
                self._y = y
                self._recall_timer += 1
            else:
                self._recalling = False
                self._ammo = 40
                self._reloading = False
                self._reload_timer = 0
            return

        self._x = max(0, min(WIDTH - self._size, self._x))
        self._y = max(0, min(HEIGHT - self._size, self._y))

        dx, dy = 0, 0
        if keys[pygame.K_a]: dx -= 1
        if keys[pygame.K_d]: dx += 1
        if keys[pygame.K_w]: dy -= 1
        if keys[pygame.K_s]: dy += 1

        if dx or dy:
            length = math.hypot(dx, dy)
            dx /= length
            dy /= length
            self._x += dx * self._speed
            self._y += dy * self._speed
            self._move_dx = dx
            self._move_dy = dy

        mx, my = pygame.mouse.get_pos()
        cx = self._x + self._size/2
        cy = self._y + self._size/2
        dx = mx - cx
        dy = my - cy
        length = math.hypot(dx, dy)
        if length != 0:
            self._aim_dx = dx/length
            self._aim_dy = dy/length

        self._history.append((self._x, self._y, self._hp))
        if len(self._history) > 300:
            self._history.pop(0)

        if keys[pygame.K_LSHIFT] and not self._blink_pressed_last:
            self.blink()
        self._blink_pressed_last = keys[pygame.K_LSHIFT]

        if keys[pygame.K_e]:
            self.recall()

        if self._recall_cooldown > 0:
            self._recall_cooldown -= 1

        if self._reloading:
            self._reload_timer -= 1
            if self._reload_timer <= 0:
                self._ammo = 40
                self._reloading = False

    def draw(self, surface):
        color = (150, 150, 255) if self._recalling else BLUE
        pygame.draw.rect(surface, color, self.rect)
        cx = self._x + self._size/2
        cy = self._y + self._size/2
        pygame.draw.line(surface, BLACK,
                         (cx, cy),
                         (cx + self._aim_dx*50, cy + self._aim_dy*50), 3)
        if self._purse_ready:
            pygame.draw.rect(surface, (255, 200, 0), self.rect, 3)

# =========================
# Enemy / Bullet / HealPack
# =========================
class Enemy(GameObject):
    def __init__(self):
        super().__init__()
        self._radius = 20
        self._hp = 220
        self._attack_cd = 0
        self.reset()

    @property
    def rect(self):
        return pygame.Rect(self._x-20, self._y-20, 40, 40)

    def reset(self):
        self._x = random.randint(WIDTH, WIDTH+400)
        self._y = random.randint(50, HEIGHT-50)
        self._hp = 220

    def take_damage(self, dmg):
        self._hp -= dmg
        if self._hp <= 0:
            self.destroy()

    def update(self):
        self._x -= 4
        if self._attack_cd > 0:
            self._attack_cd -= 1
        if self._x < -50:
            self.destroy()

    def draw(self, surface):
        pygame.draw.circle(surface, RED, (int(self._x), int(self._y)), 20)

    def on_player_collision(self, player):
        if self._attack_cd == 0:
            player.take_damage(70)
            self._attack_cd = 30

class Bullet(GameObject):
    def __init__(self, x, y, dx, dy):
        super().__init__()
        self._x = x
        self._y = y
        self._dx = dx
        self._dy = dy

    @property
    def rect(self):
        return pygame.Rect(self._x, self._y, 5, 5)

    def update(self):
        self._x += self._dx * 20
        self._y += self._dy * 20
        if self._x < 0 or self._x > WIDTH or self._y < 0 or self._y > HEIGHT:
            self.destroy()

    def draw(self, surface):
        pygame.draw.circle(surface, BLACK, (int(self._x), int(self._y)), 3)

class HealPack(GameObject):
    def __init__(self):
        super().__init__()
        self._x = random.randint(100, WIDTH-100)
        self._y = random.randint(100, HEIGHT-100)

    @property
    def rect(self):
        return pygame.Rect(self._x, self._y, 20, 20)

    def update(self): pass

    def draw(self, surface):
        pygame.draw.rect(surface, GREEN, self.rect)

# =========================
# Pulse Bomb
# =========================
class PulseBomb(GameObject):
    def __init__(self, x, y, dx, dy):
        super().__init__()
        self._x = x
        self._y = y
        self._dx = dx
        self._dy = dy
        self._timer = 0
        self._attached = None
        self._max_lifetime = 90

    @property
    def rect(self):
        return pygame.Rect(self._x-5, self._y-5, 10, 10)

    def update(self):
        if self._attached:
            self._x = self._attached._x
            self._y = self._attached._y
        else:
            self._x += self._dx * 4
            self._y += self._dy * 4
        self._timer += 1
        if self._timer >= self._max_lifetime:
            self.destroy()

    def attach(self, enemy):
        self._attached = enemy

    def draw(self, surface):
        if self._attached:
            t = pygame.time.get_ticks() // 100
            pulse = 5 + (t % 10)
            pygame.draw.circle(surface, (255, 80, 80),
                               (int(self._x), int(self._y)), 12 + pulse, 2)
            pygame.draw.circle(surface, (0, 0, 0),
                               (int(self._x), int(self._y)), 5)
        else:
            pygame.draw.circle(surface, BLACK,
                               (int(self._x), int(self._y)), 5)

class Explosion(GameObject):
    def __init__(self, x, y):
        super().__init__()
        self._x = x
        self._y = y
        self._timer = 0
        self._duration = 20

    @property
    def rect(self):
        return pygame.Rect(self._x, self._y, 0, 0)

    def update(self):
        self._timer += 1
        if self._timer >= self._duration:
            self.destroy()

    def draw(self, surface):
        progress = self._timer / self._duration
        radius = int(5 + 15 * progress)
        alpha = int(255 * (1 - progress))
        color = (255, 200, 50)
        temp = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
        pygame.draw.circle(temp, (*color, alpha), (radius, radius), radius)
        surface.blit(temp, (self._x - radius, self._y - radius))

# =========================
# UI
# =========================
def draw_ui(surface, player):
    font = pygame.font.SysFont(None, 24)

    hp_bar_width = 200
    hp_bar_height = 20
    x = 20
    y = HEIGHT - 60

    pygame.draw.rect(surface, GRAY, (x, y, hp_bar_width, hp_bar_height))
    pygame.draw.rect(surface, GREEN, (x, y, hp_bar_width * (player._hp / player._max_hp), hp_bar_height))
    surface.blit(font.render(f"HP: {int(player._hp)}/{player._max_hp}", True, BLACK), (x, y - 25))

    right_x = WIDTH - 220
    base_y = HEIGHT - 260

    surface.blit(font.render(f"Ammo: {player._ammo}/40", True, BLACK), (right_x, base_y))

    if player._reloading:
        sec = player._reload_timer / 60
        surface.blit(font.render(f"Reloading... {sec:.1f}s", True, RED), (right_x, base_y + 25))

    surface.blit(recall_img, (right_x, base_y + 60))
    if player._recall_cooldown > 0:
        text = f"Recall CD: {player._recall_cooldown / 60:.1f}s"
        color = BLACK
    else:
        text = "Recall Ready"
        color = GREEN
    surface.blit(font.render(text, True, color), (right_x + 30, base_y + 60))

    surface.blit(blink_img, (right_x, base_y + 90))
    if player._blink_stack == player._blink_max_stack:
        text = f"Blink: {player._blink_stack}/3 (Ready)"
    else:
        remain = (player._blink_recharge_time - player._blink_cooldown) / 60
        text = f"Blink: {player._blink_stack}/3 (+{remain:.1f}s)"
    surface.blit(font.render(text, True, BLACK), (right_x + 30, base_y + 90))

    surface.blit(purse_img, (right_x, base_y + 140))
    surface.blit(font.render(f"Purse: {int(player._purse_charge)}/1375", True, BLACK), (right_x + 30, base_y + 140))

    if player._purse_ready:
        surface.blit(font.render("Purse READY", True, RED), (right_x + 30, base_y + 165))

# =========================
# Main async loop (pygbag 필수)
# =========================
async def main():
    player = Player()
    objects = [player] + [Enemy() for _ in range(6)] + [HealPack()]

    while True:
        clock.tick(60)

        if not player.is_alive:
            screen.fill(WHITE)
            font = pygame.font.SysFont(None, 72)
            text = font.render("GAME OVER", True, RED)
            screen.blit(text, (WIDTH // 2 - 150, HEIGHT // 2 - 50))
            pygame.display.flip()
            await asyncio.sleep(2)
            return

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    if player.use_purse():
                        cx = player._x + player._size/2
                        cy = player._y + player._size/2
                        objects.append(PulseBomb(cx, cy, player._aim_dx, player._aim_dy))

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3:
                    if player.use_purse():
                        cx = player._x + player._size/2
                        cy = player._y + player._size/2
                        objects.append(PulseBomb(cx, cy, player._aim_dx, player._aim_dy))

        for obj in objects:
            obj.update()

        player.shoot(objects)

        enemies = [o for o in objects if isinstance(o, Enemy)]
        bullets = [o for o in objects if isinstance(o, Bullet)]
        bombs   = [o for o in objects if isinstance(o, PulseBomb)]
        heals   = [o for o in objects if isinstance(o, HealPack)]

        if len(heals) < 3:
            objects.append(HealPack())

        for b in bullets:
            for e in enemies:
                if b.rect.colliderect(e.rect):
                    e.take_damage(6)
                    player.add_purse(6)
                    b.destroy()
                    break

        for bomb in bombs:
            for e in enemies:
                if bomb.rect.colliderect(e.rect):
                    bomb.attach(e)

        for bomb in bombs:
            if bomb._timer >= 84:
                for e in enemies:
                    if math.hypot(e._x - bomb._x, e._y - bomb._y) <= 20:
                        e.take_damage(350)
                objects.append(Explosion(bomb._x, bomb._y))
                bomb.destroy()

        for e in enemies:
            if player.rect.colliderect(e.rect):
                e.on_player_collision(player)

        for h in heals:
            if player.rect.colliderect(h.rect):
                player._hp = player._max_hp
                h.destroy()

        while len([o for o in objects if isinstance(o, Enemy)]) < 6:
            objects.append(Enemy())

        objects = [o for o in objects if o.is_alive or isinstance(o, Player)]

        screen.fill(WHITE)
        for obj in objects:
            obj.draw(screen)

        draw_ui(screen, player)
        pygame.display.flip()

        await asyncio.sleep(0)  # pygbag 필수: 브라우저에 제어권 반환

asyncio.run(main())
