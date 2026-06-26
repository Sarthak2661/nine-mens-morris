import constants
from GUI import NineMensMorrisGUI
from logic import NineMensMorrisGame
from menu import HomePage, Menu, DifficultySelector


if __name__ == '__main__':
    home = HomePage()
    home.display()
    
    menu = Menu()
    menu.display_menu()
    selected_option = menu.get_selected_option()

    difficulty = None
    if selected_option == constants.H_VS_C:
        difficulty_selector = DifficultySelector()
        difficulty_selector.display_selector()
        difficulty = difficulty_selector.get_selected_difficulty()

    game = NineMensMorrisGame(game_mode=selected_option, difficulty=difficulty)
    gui = NineMensMorrisGUI(game)
    gui.main_loop()
