import sys
from src.main import GameApp
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Shadowgrid Game Engine")
    parser.add_argument("--width", type=int, default=1280, help="Target window width")
    parser.add_argument("--height", type=int, default=720, help="Target window height")
    parser.add_argument("--display", type=int, default=0, help="Monitor index")
    parser.add_argument("--fullscreen", action="store_true", help="Enable fullscreen mode")
    args = parser.parse_args()
    
    app = GameApp(args.width, args.height, args.display, args.fullscreen)
    app.run()
