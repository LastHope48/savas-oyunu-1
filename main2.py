from game import Game
from update_manager import apply_pending_update

apply_pending_update()

if __name__ == "__main__":
    Game().run()
