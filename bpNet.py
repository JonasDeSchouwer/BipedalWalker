import torch
import torch.nn as nn
import torch.nn.functional as F

from utils import DEVICE


class bpQNet(torch.nn.Module):
    def __init__(self, num_observations, num_actions):
        super(bpQNet, self).__init__()

        self.num_observations = num_observations
        self.num_actions = num_actions

        self.fcl1 = nn.Linear(num_observations+num_actions, 100)
        self.fcl2 = nn.Linear(100,50)
        self.fcl3 = nn.Linear(50,1)

        # bounds of the network output (used for normalization)
        self.LOWER = -200
        self.UPPER = 400

    def normalize(self, x):
        """
        normalize [-LOWER,UPPER] into [-1,1]
        """
        return torch.clip(2*(x-self.LOWER)/(self.UPPER-self.LOWER)-1, min=-1, max=1)

    def denormalize(self, x):
        """
        denormalize [-1,1] into [-LOWER,UPPER]
        [-1,1]: network output
        [-LOWER, UPPER]: predicted reward
        """
        return (x+1)/2 * (self.UPPER-self.LOWER) + self.LOWER

    def forward(self, state):
        """
        return the Q-value for a given state x (obs+actions)
        :param state: B x obs+act matrix:
            first obs elements: observation
            last act element: action
        """
        x = torch.as_tensor(state, dtype=torch.float32, device=DEVICE)
        x = self.fcl1(x)
        x = F.relu(x)
        x = self.fcl2(x)
        x = F.relu(x)
        x = self.fcl3(x)
        x = torch.tanh(x)
        x = self.denormalize(x)

        return x
    
    def save(self, path):
        torch.save(self.state_dict(), path)
    
    def load(self, path):
        self.load_state_dict(torch.load(path))
        self.eval()


    
class bpPNet(torch.nn.Module):
    def __init__(self, num_observations, num_actions):
        super(bpPNet, self).__init__()

        self.num_observations = num_observations
        self.num_actions = num_actions

        self.fcl1 = nn.Linear(num_observations, 100)
        self.fcl2 = nn.Linear(100,50)
        self.fcl3 = nn.Linear(50,num_actions)

    def forward(self, obs):
        """
        return the action with lowest q-value for a given obs x
        :param obs: B x obs matrix
        """
        x = torch.as_tensor(obs, dtype=torch.float32, device=DEVICE)
        x = self.fcl1(x)
        x = F.relu(x)
        x = self.fcl2(x)
        x = F.relu(x)
        x = self.fcl3(x)
        x = torch.tanh(x)       #because the actions are in [-1,1]

        return x
    
    def select_action(self, obs, sigma=1):
        """
        select an action based on parameter sigma:
            sigma >= 1:     return the action selected by the policy net
            sigma <= 0:     return a random action
        """

        actions = self.forward(obs)
        rand = 2*torch.rand(size=actions.shape, device=DEVICE) - 1   #create random tensor between -1 and 1

        if sigma >= 1:
            return actions
        elif sigma <= 0:
            return rand
        else:
            return sigma*actions + (1-sigma) * rand

    def save(self, path):
        torch.save(self.state_dict(), path)
    
    def load(self, path):
        self.load_state_dict(torch.load(path))
        self.eval()