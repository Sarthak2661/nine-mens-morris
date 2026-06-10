import sys
import os
import pygame

import constants


class HomePage:
    """Homepage with background image and start button"""
    def __init__(self):
        self.screen = pygame.display.set_mode((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
        pygame.display.set_caption("Nine Men's Morris")
        self.clock = pygame.time.Clock()
        self.started = False
        self.show_instructions = False
        self.title_font = pygame.font.SysFont("Segoe UI", 72, bold=True)
        self.subtitle_font = pygame.font.SysFont("Segoe UI", 28)
        self.start_button_rect = pygame.Rect(175, 480, 300, 70)
        self.how_to_play_button_rect = pygame.Rect(525, 480, 250, 70)
        
        # Load background image
        self.background = None
        try:
            bg_path = os.path.join(os.path.dirname(__file__), "resources", "background.jpg")
            if os.path.exists(bg_path):
                self.background = pygame.image.load(bg_path)
                self.background = pygame.transform.scale(self.background, 
                                                        (constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
        except Exception as e:
            print(f"Could not load background: {e}")

    def display(self):
        while not self.started:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.start_button_rect.collidepoint(event.pos):
                        self.started = True
                    elif self.how_to_play_button_rect.collidepoint(event.pos):
                        instructions = InstructionsScreen()
                        instructions.display()

            self.draw()
            pygame.display.flip()
            self.clock.tick(30)

    def draw(self):
        # Draw background with gradient overlay
        if self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill((139, 90, 43))
        
        # Semi-transparent dark overlay
        overlay = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
        overlay.set_alpha(80)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Title with elegant styling
        title = self.title_font.render("Nine Men's Morris", True, (255, 255, 255))
        title_rect = title.get_rect(center=(constants.SCREEN_WIDTH // 2, 120))
        # Add shadow effect
        shadow = self.title_font.render("Nine Men's Morris", True, (0, 0, 0))
        self.screen.blit(shadow, (title_rect.x + 3, title_rect.y + 3))
        self.screen.blit(title, title_rect)
        
        # Subtitle
        subtitle = self.subtitle_font.render("An Ancient Strategy Game", True, (220, 200, 170))
        self.screen.blit(subtitle, subtitle.get_rect(center=(constants.SCREEN_WIDTH // 2, 220)))
        
        # Decorative line
        pygame.draw.line(self.screen, (218, 165, 32), (150, 280), (750, 280), 2)
        
        # Game description
        desc_font = pygame.font.SysFont("Segoe UI", 18)
        desc = desc_font.render("Place, move, and capture your opponent's pieces to win", True, (200, 200, 200))
        self.screen.blit(desc, desc.get_rect(center=(constants.SCREEN_WIDTH // 2, 330)))
        
        # Start button
        self.draw_button(self.start_button_rect, "START GAME", (60, 120, 200), (100, 160, 255))
        # How to Play button
        self.draw_button(self.how_to_play_button_rect, "HOW TO PLAY", (120, 80, 40), (180, 120, 60))

    def draw_button(self, rect, text, color, hover_color):
        # Button background with shadow
        shadow_rect = pygame.Rect(rect.x + 4, rect.y + 4, rect.width, rect.height)
        pygame.draw.rect(self.screen, (0, 0, 0), shadow_rect, border_radius=15)
        
        # Button itself
        pygame.draw.rect(self.screen, color, rect, border_radius=15)
        pygame.draw.rect(self.screen, (255, 255, 255), rect, width=2, border_radius=15)
        
        # Text
        label = pygame.font.SysFont("Segoe UI", 24, bold=True).render(text, True, (255, 255, 255))
        self.screen.blit(label, label.get_rect(center=rect.center))


class InstructionsScreen:
    """Instructions and information about the game"""
    def __init__(self):
        self.screen = pygame.display.set_mode((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
        pygame.display.set_caption("Nine Men's Morris - How to Play")
        self.clock = pygame.time.Clock()
        self.done = False
        self.scroll_offset = 0
        self.title_font = pygame.font.SysFont("Segoe UI", 48, bold=True)
        self.heading_font = pygame.font.SysFont("Segoe UI", 26, bold=True)
        self.text_font = pygame.font.SysFont("Segoe UI", 18)
        self.back_button_rect = pygame.Rect(50, 670, 150, 40)
        
        # Prepare instruction text
        self.instructions = self._prepare_instructions()

    def _prepare_instructions(self):
        """Prepare game instructions with accurate Nine Men's Morris rules"""
        lines = [
            ("ABOUT NINE MEN'S MORRIS", "heading"),
            ("Ancient strategy game with 5000+ years of history across cultures worldwide.", "text"),
            ("A perfect information game - both players see everything on the board.", "text"),
            ("", "text"),
            
            ("OBJECTIVE", "heading"),
            ("Win by reducing opponent to 2 pieces OR by blocking all their moves.", "text"),
            ("", "text"),
            
            ("GAME PHASES", "heading"),
            ("PHASE 1: PLACEMENT", "subheading"),
            ("• Take turns placing 9 pieces on empty board points", "text"),
            ("• Form a 'mill' (3 pieces in a line) to capture opponent piece", "text"),
            ("• Cannot remove piece from mill unless all opponent pieces are in mills", "text"),
            ("", "text"),
            
            ("PHASE 2: MOVEMENT", "subheading"),
            ("• Move pieces to adjacent empty points only (no jumping!)", "text"),
            ("• Form mills to capture opponent pieces as before", "text"),
            ("• Can break & reform same mill repeatedly to capture multiple pieces", "text"),
            ("", "text"),
            
            ("PHASE 3: FLYING (When you have 3 pieces)", "subheading"),
            ("• Move pieces to ANY empty point on the board (not just adjacent)", "text"),
            ("• Helps the weaker player stage a comeback in endgame", "text"),
            ("", "text"),
            
            ("WIN CONDITIONS", "heading"),
            ("✓ Opponent reduced to 2 pieces or fewer", "text"),
            ("✓ Opponent with 3+ pieces has no legal adjacent moves", "text"),
            ("✓ Opponent cannot form new mills to continue playing", "text"),
            ("", "text"),
            
            ("KEY RULES", "heading"),
            ("• Mills are ONLY horizontal or vertical (NOT diagonal)", "text"),
            ("• Pieces slide along board lines - no jumping allowed", "text"),
            ("• Captured pieces are permanently removed", "text"),
            ("• With perfect play from both sides = DRAW", "text"),
            ("", "text"),
            
            ("GAME MODES", "heading"),
            ("HUMAN VS HUMAN: Two players, one computer", "text"),
            ("EASY: Computer plays randomly - learn the game", "text"),
            ("NORMAL: Balanced strategy - good challenge", "text"),
            ("HARD: Near-optimal play - expert challenge", "text"),
            ("", "text"),
            
            ("WINNING STRATEGY", "heading"),
            ("✓ Control the CENTER for max flexibility", "text"),
            ("✓ Create 2+ potential mills to force decisions", "text"),
            ("✓ Keep pieces CONNECTED for defense", "text"),
            ("✓ Don't isolate pieces where they can be trapped", "text"),
            ("✓ Anticipate opponent's next moves and mill threats", "text"),
        ]
        return lines

    def display(self):
        while not self.done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.back_button_rect.collidepoint(event.pos):
                        self.done = True
                    # Mouse wheel scroll down
                    elif event.button == 4:  # Scroll up
                        self.scroll_offset = max(0, self.scroll_offset - 40)
                    elif event.button == 5:  # Scroll down
                        self.scroll_offset += 40
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.scroll_offset = max(0, self.scroll_offset - 30)
                    elif event.key == pygame.K_DOWN:
                        self.scroll_offset += 30
                    elif event.key == pygame.K_ESCAPE:
                        self.done = True

            self.draw()
            pygame.display.flip()
            self.clock.tick(30)

    def draw(self):
        # Modern background with gradient
        self.screen.fill((245, 245, 245))
        
        # Title bar
        title_bar = pygame.Rect(0, 0, constants.SCREEN_WIDTH, 80)
        pygame.draw.rect(self.screen, (139, 90, 43), title_bar)
        
        # Render title with proper shadow offset
        title_text = "How to Play"
        title = self.title_font.render(title_text, True, (255, 255, 255))
        title_rect = title.get_rect(center=(constants.SCREEN_WIDTH // 2, 42))
        
        # Shadow offset (2px right, 2px down)
        title_shadow = self.title_font.render(title_text, True, (0, 0, 0))
        shadow_rect = title_shadow.get_rect(center=(constants.SCREEN_WIDTH // 2 + 2, 42 + 2))
        self.screen.blit(title_shadow, shadow_rect)
        self.screen.blit(title, title_rect)
        
        # Instructions area with background
        content_area = pygame.Rect(30, 95, constants.SCREEN_WIDTH - 60, 570)
        pygame.draw.rect(self.screen, (255, 255, 255), content_area, border_radius=10)
        pygame.draw.rect(self.screen, (200, 150, 100), content_area, width=3, border_radius=10)
        
        # Instructions text
        y = 110 - self.scroll_offset
        max_y = 660
        
        for text, text_type in self.instructions:
            if text_type == "heading":
                line = self.heading_font.render(text, True, (50, 50, 50))
                color = (50, 50, 50)
                font = self.heading_font
            elif text_type == "subheading":
                line = self.heading_font.render(text, True, (100, 100, 100))
                color = (100, 100, 100)
                font = self.heading_font
            else:
                line = self.text_font.render(text, True, (0, 0, 0))
                color = (0, 0, 0)
                font = self.text_font
            
            if y > 95 and y < max_y:
                self.screen.blit(line, (70, y))
            
            y += font.get_height() + 5
        
        # Back button
        pygame.draw.rect(self.screen, (139, 90, 43), self.back_button_rect, border_radius=8)
        pygame.draw.rect(self.screen, (255, 255, 255), self.back_button_rect, width=2, border_radius=8)
        back_text = self.text_font.render("← BACK", True, (255, 255, 255))
        self.screen.blit(back_text, back_text.get_rect(center=self.back_button_rect.center))
        
        # Scroll hint
        hint_font = pygame.font.SysFont("Segoe UI", 14)
        hint = hint_font.render("Use UP/DOWN arrows or mouse wheel to scroll | ESC to go back", True, (100, 100, 100))
        self.screen.blit(hint, (15, 690))


class Menu:
    """Game mode selection menu"""
    def __init__(self):
        self.screen = pygame.display.set_mode((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
        pygame.display.set_caption("Nine Men's Morris - Game Mode")
        self.clock = pygame.time.Clock()
        self.selected_option = None
        self.title_font = pygame.font.SysFont("Segoe UI", 52, bold=True)
        self.font = pygame.font.SysFont("Segoe UI", 28)
        self.small_font = pygame.font.SysFont("Segoe UI", 20)
        self.human_vs_human_button_rect = pygame.Rect(200, 300, 500, 70)
        self.human_vs_computer_button_rect = pygame.Rect(200, 420, 500, 70)

    def display_menu(self):
        while self.selected_option is None:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.human_vs_human_button_rect.collidepoint(event.pos):
                        self.selected_option = constants.H_VS_H
                    elif self.human_vs_computer_button_rect.collidepoint(event.pos):
                        self.selected_option = constants.H_VS_C

            self.draw_menu()
            pygame.display.flip()
            self.clock.tick(30)

    def draw_menu(self):
        # Background
        self.screen.fill((139, 90, 43))
        
        # Title with shadow
        title = self.title_font.render("Select Game Mode", True, (255, 255, 255))
        title_rect = title.get_rect(center=(constants.SCREEN_WIDTH // 2, 100))
        title_shadow = self.title_font.render("Select Game Mode", True, (0, 0, 0))
        self.screen.blit(title_shadow, (title_rect.x + 2, title_rect.y + 2))
        self.screen.blit(title, title_rect)
        
        # Subtitle
        subtitle = self.small_font.render("Choose how you want to play", True, (220, 200, 170))
        self.screen.blit(subtitle, subtitle.get_rect(center=(constants.SCREEN_WIDTH // 2, 200)))
        
        # Decorative line
        pygame.draw.line(self.screen, (218, 165, 32), (100, 250), (800, 250), 2)
        
        # Buttons with enhanced styling
        self.draw_button(self.human_vs_human_button_rect, "🎮 Human vs Human", (60, 120, 200))
        self.draw_button(self.human_vs_computer_button_rect, "🤖 Human vs Computer", (140, 100, 60))

    def draw_button(self, rect, text, color):
        # Shadow
        shadow_rect = pygame.Rect(rect.x + 4, rect.y + 4, rect.width, rect.height)
        pygame.draw.rect(self.screen, (0, 0, 0), shadow_rect, border_radius=15)
        
        # Button
        pygame.draw.rect(self.screen, color, rect, border_radius=15)
        pygame.draw.rect(self.screen, (255, 255, 255), rect, width=3, border_radius=15)
        
        # Text
        label = self.font.render(text, True, (255, 255, 255))
        self.screen.blit(label, label.get_rect(center=rect.center))

    def get_selected_option(self):
        return self.selected_option


class DifficultySelector:
    """Difficulty selection for human vs computer mode"""
    def __init__(self):
        self.screen = pygame.display.set_mode((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
        pygame.display.set_caption("Nine Men's Morris - Select Difficulty")
        self.clock = pygame.time.Clock()
        self.selected_difficulty = None
        self.title_font = pygame.font.SysFont("Segoe UI", 52, bold=True)
        self.font = pygame.font.SysFont("Segoe UI", 28)
        self.small_font = pygame.font.SysFont("Segoe UI", 20)
        self.easy_button_rect = pygame.Rect(200, 280, 500, 70)
        self.normal_button_rect = pygame.Rect(200, 385, 500, 70)
        self.hard_button_rect = pygame.Rect(200, 490, 500, 70)

    def display_selector(self):
        while self.selected_difficulty is None:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.easy_button_rect.collidepoint(event.pos):
                        self.selected_difficulty = constants.EASY
                    elif self.normal_button_rect.collidepoint(event.pos):
                        self.selected_difficulty = constants.NORMAL
                    elif self.hard_button_rect.collidepoint(event.pos):
                        self.selected_difficulty = constants.HARD

            self.draw_selector()
            pygame.display.flip()
            self.clock.tick(30)

    def draw_selector(self):
        # Background
        self.screen.fill((139, 90, 43))
        
        # Title with shadow
        title = self.title_font.render("Select Difficulty", True, (255, 255, 255))
        title_rect = title.get_rect(center=(constants.SCREEN_WIDTH // 2, 100))
        title_shadow = self.title_font.render("Select Difficulty", True, (0, 0, 0))
        self.screen.blit(title_shadow, (title_rect.x + 2, title_rect.y + 2))
        self.screen.blit(title, title_rect)
        
        # Subtitle
        subtitle = self.small_font.render("How challenging should your opponent be?", True, (220, 200, 170))
        self.screen.blit(subtitle, subtitle.get_rect(center=(constants.SCREEN_WIDTH // 2, 180)))
        
        # Decorative line
        pygame.draw.line(self.screen, (218, 165, 32), (100, 240), (800, 240), 2)
        
        # Buttons
        self.draw_button(self.easy_button_rect, "EASY - Random moves", (60, 150, 80))
        self.draw_button(self.normal_button_rect, "NORMAL - Smart play", (180, 120, 40))
        self.draw_button(self.hard_button_rect, "HARD - Expert AI", (150, 60, 60))

    def draw_button(self, rect, text, color):
        # Shadow
        shadow_rect = pygame.Rect(rect.x + 4, rect.y + 4, rect.width, rect.height)
        pygame.draw.rect(self.screen, (0, 0, 0), shadow_rect, border_radius=15)
        
        # Button
        pygame.draw.rect(self.screen, color, rect, border_radius=15)
        pygame.draw.rect(self.screen, (255, 255, 255), rect, width=3, border_radius=15)
        
        # Text
        label = self.font.render(text, True, (255, 255, 255))
        self.screen.blit(label, label.get_rect(center=rect.center))

    def get_selected_difficulty(self):
        return self.selected_difficulty
