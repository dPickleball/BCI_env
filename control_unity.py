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
import os
string_channel = StringSideChannel()
channel = CustomDataChannel()
reward_cum = [0, 0]
channel.send_data(serve=212, p1=reward_cum[0], p2=reward_cum[1])
print("Hello dPickleBall Player")
unity_env = UnityEnvironment(r"put your 'dp.exe' path here ", side_channels=[string_channel, channel])
print("environment created")
env = UnityParallelEnv(unity_env)
print("petting zoo setup")
env.reset()
print("ready to go!")
# print available agents
print("Agent Names", env.agents)
count=0
try:
    while env.agents:
        count+=1
        left_cmds, right_cmds = read_commands()
        """
        you may use any method to get the command from BCI device,
        the function read_commands() is only for your reference:)
        """
        action_left = [0, 0, 0, 0]
        action_right = [0, 0, 0, 0]
        #action_left
        if 'w' in left_cmds:
            action_left[0] = 1
        if 's' in left_cmds:
            action_left[0] = 2
        if 'd' in left_cmds:
            action_left[1] = 1
        if 'a' in left_cmds:
            action_left[1] = 2
        if 'e' in left_cmds:
            action_left[2] = 1
        if 'q' in left_cmds:
            action_left[2] = 2
        #action_right
        if 'i' in right_cmds:
            action_right[0] = 1
        if 'k' in right_cmds:
            action_right[0] = 2
        if 'l' in right_cmds:
            action_right[1] = 1
        if 'j' in right_cmds:
            action_right[1] = 2
        if 'o' in right_cmds:
            action_right[2] = 1
        if 'u' in right_cmds:
            action_right[2] = 2
        actions = {env.agents[0]: action_left, env.agents[1]: action_right}
        observation, reward, done, info = env.step(actions)
        reward_cum[0] += reward[env.agents[0]]
        reward_cum[1] += reward[env.agents[1]]
        if done[env.agents[0]] or done[env.agents[1]]:
            sys.exit()
        obs = observation[env.agents[0]]['observation'][0]


except KeyboardInterrupt:
    print("Progress interrupted")
finally:
    env.close()