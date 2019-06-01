from collections import OrderedDict

import numpy as np
from gym import spaces


class HERGoalEnvWrapper(object):
    """
    A wrapper that allow to use dict observation space (coming from GoalEnv) with
    the RL algorithms.
    It assumes that all the spaces of the dict space are of the same type.

    :param env: (gym.GoalEnv)
    """

    def __init__(self, env):
        super(HERGoalEnvWrapper, self).__init__()
        self.env = env
        self.metadata = self.env.metadata
        self.action_space = env.action_space
        self.spaces = list(env.observation_space.spaces.values())
        # TODO: check that all spaces are of the same type
        # (current limitation of the wrapper)
        # TODO: check when dim > 1

        # Sanity check because we are doing dict to array operations
        subspaces_keys = list(env.observation_space.spaces.keys())
        desired_keys = ['achieved_goal', 'desired_goal', 'observation']
        assert subspaces_keys == desired_keys,\
            "The keys of the GoalEnv must be ordered"\
            "in the following order:{} != {}".format(desired_keys, subspaces_keys)

        goal_space_shape = env.observation_space.spaces['achieved_goal'].shape
        self.obs_dim = env.observation_space.spaces['observation'].shape[0]
        self.goal_dim = goal_space_shape[0]
        total_dim = self.obs_dim + 2 * self.goal_dim

        if len(goal_space_shape) == 2:
            assert goal_space_shape[1] == 1, "Only 1D observation spaces are supported yet"
        else:
            assert len(goal_space_shape) == 1, "Only 1D observation spaces are supported yet"

        if isinstance(self.spaces[0], spaces.MultiBinary):
            self.observation_space = spaces.MultiBinary(total_dim)

        elif isinstance(self.spaces[0], spaces.Box):
            lows = np.concatenate([space.low for space in self.spaces])
            highs = np.concatenate([space.high for space in self.spaces])
            self.observation_space = spaces.Box(lows, highs, dtype=np.float32)

        elif isinstance(self.spaces[0], spaces.Discrete):
            pass

        else:
            raise NotImplementedError()

    @staticmethod
    def convert_dict_to_obs(obs_dict):
        """
        :param obs_dict: (dict<np.ndarray>)
        :return: (np.ndarray)
        """
        # Note: achieved goal is not removed from the observation
        # this is helpful to have a revertible transformation
        return np.concatenate([obs for obs in obs_dict.values()])

    def convert_obs_to_dict(self, observations):
        """
        Inverse operation of convert_dict_to_obs

        :param observations: (np.ndarray)
        :return: (OrderedDict<np.ndarray>)
        """
        return OrderedDict([
            ('achieved_goal', observations[:self.goal_dim]),
            ('desired_goal', observations[self.goal_dim:2 * self.goal_dim]),
            ('observation', observations[-self.obs_dim:]),
        ])

    def step(self, action):
        obs, reward, done, info = self.env.step(action)
        return self.convert_dict_to_obs(obs), reward, done, info

    def seed(self, seed=None):
        return self.env.seed(seed)

    def reset(self):
        return self.convert_dict_to_obs(self.env.reset())

    def compute_reward(self, achieved_goal, desired_goal, info):
        return self.env.compute_reward(achieved_goal, desired_goal, info)

    def render(self, mode='human'):
        return self.env.render(mode)

    def close(self):
        return self.env.close()
