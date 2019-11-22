# define a dqn agent here
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.transforms as T 
from collections import namedtuple
import random
import math


# structure of dqn policy_net and target_net
class build_DQN(nn.Module):
    def __init__(self, rows, cols):
        super().__init__()
        
        # input is the board matrix
        # apply softmax for 8 possible actions at the end
        self.fc1 = nn.Linear(in_features=rows*cols, out_features=24)   
        self.fc2 = nn.Linear(in_features=24, out_features=32)
        self.out = nn.Linear(in_features=32, out_features=8)


    def forward(self, start_point):
        t = start_point.flatten(start_dim=1)
        t = F.relu(self.fc1(t))
        t = F.relu(self.fc2(t))
        t = F.softmax(self.out(t))
        return t


# Experience
Experience = namedtuple(
    'Experience',
    ('state', 'action', 'next_state', 'reward')
)

# Replay Memory
class ReplayMemory():
    def __init__(self, capacity):
        self.capacity = capacity
        self.memory = []
        self.exp_count = 0

    
    def exp_save(self, experience):
        if len(self.memory) < self.capacity:
            self.memory.append(experience)
        else:
            self.memory[self.exp_count % self.capacity] = experience
        self.exp_count += 1

    
    # randomly pick batch_size experience from replay memory
    def sample(self, batch_size):
        return random.sample(self.memory, batch_size)


# the epsilon greedy strategy
class EpsilonGreedyStrategy():
    def __init__(self, start, end, decay):
        # starting, ending, decay values of epsilon
        self.start = start
        self.end = end
        self.decay = decay

    
    # exponential decay
    def get_exploration_rate(self, current_step):
        return self.end + (self.start - self.end) * \
            math.exp(-1. * current_step * self.decay)


# the agent
class dqnAgent():
    def __init__(self, strategy, num_actions, device):
        self.current_step = 0
        self.strategy = strategy
        self.num_actions = num_actions
        self.device = device

    
    def select_action(self, state, policy_net):
        rate = self.strategy.get_exploration_rate(self.current_step)
        self.current_step += 1

        if rate > random.random():
            # explore
            action = random.randrange(self.num_actions)
            return torch.tensor([action]).to(self.device)
        else:
            # exploit
            with torch.no_grad():
                return policy_net(state).argmax(dim=1).to(self.device)


def extract_tensors(experiences):
    # convert batch of experiences to experience of batches
    # e.g. experience(1,1,1,1), experience(2,2,2,2) -> experience(1,2),(1,2),(1,2),(1,2)
    batch = Experience(*zip(*experiences))
    
    states = torch.cat(batch.state)
    actions = torch.cat(batch.action)
    next_states = torch.cat(batch.next_state)
    rewards = torch.cat(batch.reward)
    
    return (states, actions, next_states, rewards)


# Calculating Q-values
class QValues():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    @staticmethod
    def get_current(policy_net, states, actions):
        # get current q values
        return policy_net(states).gather(dim=1, index=actions.unsqueeze(-1))
    
    
    @staticmethod
    def get_next(target_net, next_states):                
        # final_state_locations = next_states.flatten(start_dim=1) \
        #     .max(dim=1)[0].eq(0).type(torch.bool)
        # non_final_state_locations = (final_state_locations == False)
        # non_final_states = next_states[non_final_state_locations]
        # batch_size = next_states.shape[0]
        # values = torch.zeros(batch_size).to(QValues.device)
        # values[non_final_state_locations] = target_net(non_final_states).max(dim=1)[0].detach()
        # return values
        pass