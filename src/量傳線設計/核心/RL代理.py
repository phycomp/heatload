"""RL 閉環優化（PPO）"""
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import PPO
from 量傳線設計.核心.優化 import 評估設計, SPEC_CONFIG

class 傳輸線環境(gym.Env):
    def __init__(self, spec_name):
        super().__init__()
        self.spec_name = spec_name
        self.spec = SPEC_CONFIG[spec_name]
        self.action_space = spaces.Box(low=-0.1, high=0.1, shape=(5,), dtype=np.float32)
        self.observation_space = spaces.Box(low=0, high=1, shape=(5,), dtype=np.float32)
        self.params = {"w": 35, "s": 100, "h": 0.129, "t": 2, "pitch": 2.0}
        self.steps = 0

    def reset(self, seed=None, options=None):
        self.params = {"w": 35, "s": 100, "h": 0.129, "t": 2, "pitch": 2.0}
        self.steps = 0
        return self._obs(), {}

    def _obs(self):
        return np.array([self.params["w"]/100, self.params["s"]/500, self.params["h"]/0.3,
                         self.params["t"]/20, self.params["pitch"]/3.0], dtype=np.float32)

    def step(self, action):
        self.params["w"] = max(10, min(100, self.params["w"] + float(action[0])*10))
        self.params["s"] = max(50, min(500, self.params["s"] + float(action[1])*50))
        self.params["h"] = max(0.05, min(0.3, self.params["h"] + float(action[2])*0.05))
        self.params["t"] = max(1, min(20, self.params["t"] + float(action[3])*2))
        self.params["pitch"] = max(self.spec["pitch_min"], min(self.spec["pitch_max"],
                                 self.params["pitch"] + float(action[4])*0.5))
        f1, f2 = 評估設計(self.params, self.spec_name)
        reward = -0.5*f1 - 0.5*f2
        if f1 == float("inf"):
            reward -= 10
        self.steps += 1
        done = self.steps >= 50
        return self._obs(), float(reward), done, False, {}

def 建立環境(spec_name):
    return 傳輸線環境(spec_name)

def 訓練RL(spec_name, total_timesteps=1000):
    env = 建立環境(spec_name)
    model = PPO("MlpPolicy", env, verbose=0)
    # 訓練並記錄獎勵
    rewards = []
    obs, _ = env.reset()
    for _ in range(total_timesteps):
        action, _ = model.predict(obs, deterministic=False)
        obs, reward, done, truncated, _ = env.step(action)
        rewards.append(float(reward))
        if done or truncated:
            obs, _ = env.reset()
    model.learn(total_timesteps=total_timesteps)
    return model, rewards
