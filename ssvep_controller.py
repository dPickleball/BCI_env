import pygame
import threading
import socket
import json
import time
from dataclasses import dataclass, field
from mlagents_envs.environment import UnityEnvironment
from mlagents_envs.envs.unity_parallel_env import UnityParallelEnv
import matplotlib.pyplot as plt
import sys
import cv2
from mlagents_envs.envs.custom_side_channel import CustomDataChannel, StringSideChannel
from uuid import UUID
import math
import numpy as np
from pynput import keyboard

key_states = set()

unity_ready = False
unity_env = None
env = None


def on_press(key):
    try:
        key_states.add(key.char)
    except AttributeError:
        pass


def on_release(key):
    try:
        key_states.discard(key.char)
    except AttributeError:
        pass

@dataclass
class TextInput:
    rect: pygame.Rect
    label: str
    value: float
    active: bool = False
    buffer: str = field(default_factory=str)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            if self.active:
                self.buffer = ""
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                try:
                    v = float(self.buffer) if self.buffer.strip() else self.value
                    if v > 0:
                        self.value = v
                except ValueError:
                    pass
                self.active = False
            elif event.key == pygame.K_BACKSPACE:
                self.buffer = self.buffer[:-1]
            else:
                ch = event.unicode
                if ch.isdigit() or ch in (".",):
                    self.buffer += ch

    def draw(self, surface, font):
        border_color = (255, 255, 255) if self.active else (180, 180, 180)
        pygame.draw.rect(surface, (35, 35, 35), self.rect, border_radius=6)
        pygame.draw.rect(surface, border_color, self.rect, 2, border_radius=6)

        label_surf = font.render(self.label, True, (220, 220, 220))
        surface.blit(label_surf, (self.rect.x + 8, self.rect.y + 6))

        txt = self.buffer if self.active and self.buffer != "" else f"{self.value:.2f} Hz"
        val_surf = font.render(txt, True, (240, 240, 240))
        surface.blit(val_surf, (self.rect.x + 8, self.rect.y + 28))


def run_ssvep_court(
        fullscreen: bool = True,
        court_margin: int = 80,
        window_size=(1200, 675),
        max_fps: int = 120,
):
    rmax = -1000
    rmin = 1000
    pygame.init()
    pygame.display.set_caption("SSVEP Court")

    flags = pygame.FULLSCREEN if fullscreen else 0
    screen = pygame.display.set_mode(window_size, flags)
    if fullscreen:
        window_size = screen.get_size()  # 取真实全屏尺寸

    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 20)
    small_font = pygame.font.SysFont("consolas", 16)
    big_font = pygame.font.SysFont("consolas", 28, bold=True)
    W, H = window_size
    PANEL_W = 320

    court_rect = pygame.Rect(
        PANEL_W + court_margin,
        (H - (W - PANEL_W - 2 * court_margin) * 28 / 69) / 2,
        W - PANEL_W - 2 * court_margin,
        (W - PANEL_W - 2 * court_margin) * 28 / 69
    )

    pygame.draw.rect(screen, (32, 100, 32), court_rect, border_radius=16)
    pygame.draw.rect(screen, (220, 220, 220), court_rect, width=4, border_radius=16)

    mid_x = court_rect.left + court_rect.width // 2
    pygame.draw.line(screen, (220, 220, 220),
                     (mid_x, court_rect.top), (mid_x, court_rect.bottom), 3)
    actions_block = [
        ("up", 12.0),
        ("down", 10.0),
        ("forward", 15.0),
        ("back", 8.0),
        ("turn_right", 13.0),
        ("turn_left", 7.5),
    ]
    inputs = []
    box_w, box_h = PANEL_W - 40, 64
    y0 = 120
    gap = 12
    for i, (name, val) in enumerate(actions_block):
        r = pygame.Rect(20, y0 + i * (box_h + gap), box_w, box_h)
        inputs.append(TextInput(rect=r, label=name, value=val))

    def button_offsets(radius):
        return {
            "up": (0, -radius),
            "down": (0, radius),
            "forward": (radius, -radius),
            "back": (-radius, radius),
            "turn_right": (radius, 0),
            "turn_left": (-radius, 0),
        }

    def map_to_court(nx, ny):
        x = court_rect.left + nx * court_rect.width / 13.8 + court_rect.width / 2
        y = court_rect.top - ny * court_rect.height / 5.6 + court_rect.height / 2
        return int(x), int(y)

    # Start listener
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()

    string_channel = StringSideChannel()
    channel = CustomDataChannel()

    reward_cum = [0, 0]
    channel.send_data(serve=212, p1=reward_cum[0], p2=reward_cum[1])
    print("waiting for envirenment")

    def start_unity():

        global unity_env, env, unity_ready
        unity_env = UnityEnvironment(None, side_channels=[string_channel, channel])
        print("environment created")
        env = UnityParallelEnv(unity_env)
        print("petting zoo setup")
        env.reset()
        print("ready to go!")
        # print available agents
        print("Agent Names", env.agents)
        unity_ready = True

    # 主循环
    t0 = time.perf_counter()
    threading.Thread(target=start_unity, daemon=True).start()
    while not unity_ready or not hasattr(env, "agents") or len(env.agents) == 0:
        pygame.event.pump()
        font = pygame.font.SysFont(None, 48)
        text = font.render("Waiting for Unity...", True, (255, 255, 255))
        screen.blit(text, (100, 100))
        pygame.display.flip()
        clock.tick(max_fps)

    print("Unity fully ready, starting loop...")
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            for box in inputs:
                box.handle_event(event)
        if env.agents:
            action_left = [0, 0, 0, 0]
            action_right = [0, 0, 0, 0]
            if 'w' in key_states:
                action_left[0] = 1
            if 's' in key_states:
                action_left[0] = 2
            if 'd' in key_states:
                action_left[1] = 1
            if 'a' in key_states:
                action_left[1] = 2
            if 'e' in key_states:
                action_left[2] = 1
            if 'q' in key_states:
                action_left[2] = 2
            if 'i' in key_states:
                action_right[0] = 1
            if 'k' in key_states:
                action_right[0] = 2
            if 'l' in key_states:
                action_right[1] = 1
            if 'j' in key_states:
                action_right[1] = 2
            if 'o' in key_states:
                action_right[2] = 1
            if 'u' in key_states:
                action_right[2] = 2
            actions = {env.agents[0]: action_left, env.agents[1]: action_right}
            observation, reward, done, info = env.step(actions)
            print(observation[env.agents[0]]["observation"][1:])
            print(observation[env.agents[1]]["observation"][:])
            # get Unity index
            bx = observation[env.agents[0]]["observation"][1][4]
            by = observation[env.agents[0]]["observation"][1][5]
            p1x = observation[env.agents[0]]["observation"][1][1]
            p1y = observation[env.agents[0]]["observation"][1][2]
            p2x = observation[env.agents[1]]["observation"][0][1]
            p2y = observation[env.agents[1]]["observation"][0][2]
            pr1 = observation[env.agents[0]]["observation"][1][3]
            pr2 = observation[env.agents[1]]["observation"][0][3]
            pr1 = (math.degrees(math.asin(pr1)) * 2)
            pr2 = (math.degrees(math.asin(pr2)) * 2)
            rmax = max(rmax, pr1)
            rmin = min(rmin, pr1)
            print(rmax, rmin, pr1)
            p1x1 = p1x - math.sin(-math.pi * pr1 / 180) * 0.4
            p1y1 = p1y - math.cos(-math.pi * pr1 / 180) * 0.4
            p1x2 = p1x + math.sin(-math.pi * pr1 / 180) * 0.4
            p1y2 = p1y + math.cos(-math.pi * pr1 / 180) * 0.4
            ball_pos = map_to_court(bx, by)
            paddle1_pos1 = map_to_court(p1x1, p1y1)
            paddle1_pos2 = map_to_court(p1x2, p1y2)
            p2x1 = p2x - math.sin(-math.pi * pr2 / 180) * 0.4
            p2y1 = p2y - math.cos(-math.pi * pr2 / 180) * 0.4
            p2x2 = p2x + math.sin(-math.pi * pr2 / 180) * 0.4
            p2y2 = p2y + math.cos(-math.pi * pr2 / 180) * 0.4
            paddle2_pos1 = map_to_court(p2x1, p2y1)
            paddle2_pos2 = map_to_court(p2x2, p2y2)
            reward_cum[0] += reward[env.agents[0]]
            reward_cum[1] += reward[env.agents[1]]
            if done[env.agents[0]] or done[env.agents[1]]:
                sys.exit()
            obs = observation[env.agents[0]]['observation'][0]
        now = time.perf_counter() - t0
        screen.fill((18, 18, 18))
        pygame.draw.rect(screen, (28, 28, 28), pygame.Rect(0, 0, PANEL_W, H))
        title = big_font.render("SSVEP Controls", True, (230, 230, 230))
        screen.blit(title, (20, 20))
        hint = small_font.render("Click box -> type number -> Enter", True, (160, 160, 160))
        screen.blit(hint, (20, 80))
        for box in inputs:
            box.draw(screen, font)
        freq_map = {box.label: box.value for box in inputs}
        pygame.draw.rect(screen, (32, 100, 32), court_rect, border_radius=16)  # 草地
        pygame.draw.rect(screen, (220, 220, 220), court_rect, width=4, border_radius=16)  # 外框
        mid_x = court_rect.centerx
        pygame.draw.line(screen, (220, 220, 220),
                         (mid_x, court_rect.top), (mid_x, court_rect.bottom), 3)
        pygame.draw.line(screen, (240, 240, 255), paddle1_pos1, paddle1_pos2, int(court_rect.height * 20 / 528))
        pygame.draw.line(screen, (240, 240, 255), paddle2_pos1, paddle2_pos2, int(court_rect.height * 20 / 528))
        pygame.draw.circle(screen, (255, 210, 40), ball_pos, int(court_rect.height * 40 / 528))  # ball

        ring_radius = 120
        size = 60
        offs = button_offsets(ring_radius)
        for name, _ in actions_block:
            ox, oy = offs[name]
            cx, cy = paddle1_pos1[0] + ox, paddle1_pos1[1] + oy
            rect = pygame.Rect(0, 0, size, size)
            rect.center = (cx, cy)

            f = max(0.1, float(freq_map[name])) # Hz
            phase = (now * f) % 1.0
            on = phase < 0.5

            bg = (255, 255, 255) if on else (30, 30, 30)
            fg = (10, 10, 10) if on else (230, 230, 230)

            pygame.draw.rect(screen, bg, rect, border_radius=10)
            pygame.draw.rect(screen, (200, 200, 200), rect, 2, border_radius=10)

            label = small_font.render(name, True, fg)
            lw, lh = label.get_size()
            screen.blit(label, (rect.centerx - lw // 2, rect.centery - lh // 2))
        hud = small_font.render(
            f"Paddle1: ({p1x:.2f},{p1y:.2f})   Ball: ({bx:.2f},{by:.2f})", True, (200, 200, 200)
        )
        screen.blit(hud, (PANEL_W + 20, 20))
        pygame.display.flip()
        clock.tick(max_fps)
    pygame.quit()


if __name__ == "__main__":
    run_ssvep_court(fullscreen=False)
