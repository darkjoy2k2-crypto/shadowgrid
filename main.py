import sys
import argparse
from src.main import GameApp

def main() -> None:
    parser = argparse.ArgumentParser(description="Shadowgrid Game Engine")
    parser.add_argument("--width", type=int, default=1280, help="Target window width")
    parser.add_argument("--height", type=int, default=720, help="Target window height")
    parser.add_argument("--display", type=int, default=0, help="Monitor index")
    parser.add_argument("--fullscreen", action="store_true", help="Enable fullscreen mode")
    parser.add_argument("--game", type=str, default="shadowgrid", help="Game mode: 'shadowgrid' or 'persuasion'")
    args = parser.parse_args()
    
    app = GameApp(args.width, args.height, args.display, args.fullscreen, args.game)
    app.run()

if __name__ == "__main__":
    main()
