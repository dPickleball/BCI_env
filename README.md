# BCI_env
This repository provides the environment files and environment control code examples that the BCI group needs to use.
  
##In order to send movement commands to the pickleball envirenment, youcan refer to the control_unity.py. 
  The function you need to develop by yourself is read_commands: 
```python
try:
    while env.agents:
        count+=1
        left_cmds, right_cmds = read_commands()
        action_left = [0, 0, 0, 0]
        action_right = [0, 0, 0, 0]


```
Quite similar with that in the file test_paral_keyboard.py, the mapping rules are: 
*WSAD* means up, down, left, right
*QE* means rotation_left, rotation_right
*IKJL* means up, down, left, right
*UO* means rotation_left, rotation_right

```python
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
```
