from hanabi import Game
import agent
import random
import os 
import importlib
import sys
import math
import argparse
import multiprocessing as mp

tqdm_enabled = False
try:
    from tqdm import tqdm # try to import tqdm if available
    tqdm_enabled = True
except ImportError:
    tqdm_enabled = False

for f in os.listdir("agents"):
    if f.endswith(".py") and f != "__init__.py":
        importlib.import_module("agents."+f[:-3])


class NullStream(object):
    def write(self, *args):
        pass

names = ["Shangdi", "Nu Wa", "Yu Di", "Tian", "Pangu"]

# The core part that actually plays hanabi
def play_hanabi(i: int, seed: int, agents: list[str]):
    if seed is not None:
        random.seed(seed+i+1)
    players = []
    for i,a in enumerate(agents):
        players.append(agent.get(a)[1](names[i], i))

    g = Game(players, NullStream())
    try:
        return g.run()
    except Exception:
        import traceback
        traceback.print_exc()
    
def main(n=100, seed=0, agents=[]):
    # tqdm progress bar
    progress_bar = None
    if tqdm_enabled:
        progress_bar = tqdm(total=n)

    pts = []

    # Callback function
    def gameover(points: int): 
        pts.append(points)
        if progress_bar is not None:
            progress_bar.update()

    if not agents:
        agents = []

    while len(agents) < 2:
        agents.append("random")
    
    # play hanabi
    pool = mp.Pool(mp.cpu_count())
    for i in range(n):
        pool.apply_async(play_hanabi, args=(i, seed, agents), callback=gameover)
    pool.close() 
    pool.join()
    if tqdm_enabled:
        progress_bar.close()

    # output results
    if n < 10:
        print("Scores:", pts)
    
    if n > 1:
        mean = sum(pts)*1.0/len(pts)
        print("mean: %.2f"%(mean))
        ssqs = [(p-mean)**2 for p in pts]
        print("stddev: %.2f"%(math.sqrt(sum(ssqs)/(len(pts)-1))))
        print("range", min(pts), max(pts))
    
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Simulate several games of Hanabi.')
    parser.add_argument('agents', metavar='A', nargs='*',
                        help='the agent types that should play (minimum 2)')
    parser.add_argument('--list', dest='list', action='store_true',
                        default=False, help='Show available agent types and quit')
    parser.add_argument('-n', '--count', '--games', dest='n', action='store',
                        type=int, default=100, help='How many games should the agents play?')
    parser.add_argument('-s', '--seed', dest='seed', action='store',
                        type=int, default=0, help='The random seed to be used')
    parser.add_argument('-r', '--random', dest='rand', action='store_true',
                        default=False, help='Do not use random seed; make games truly random.')
    args = parser.parse_args()
    if args.list:
        print("Available agents:")
        for id in agent.ids():
            print("  %s: %s"%(id, agent.get(id)[0]))
    else:
        main(args.n, (None if args.rand else args.seed), args.agents)