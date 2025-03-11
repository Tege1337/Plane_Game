import pygame
import sys
import random
import os
import time

# Initialize pygame
pygame.init()

# Screen dimensions
WIDTH = 800
HEIGHT = 600

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 180, 0)
GOLD = (255, 215, 0)
SKY_BLUE = (135, 206, 235)
DARK_BLUE = (0, 0, 50)
PURPLE = (128, 0, 128)
LIGHT_GRAY = (240, 240, 245)  # Lighter gray for cleaner look
DARK_GRAY = (80, 80, 80)
MENU_GRAY = (120, 120, 120)  # Gray color for menu showcase
TEAL = (0, 128, 128)
BUTTON_BLUE = (65, 105, 225)  # Royal blue for buttons

# Create the game window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Plane Collection Game")

# Clock to control game speed
clock = pygame.time.Clock()

# Game states
MENU = 0
PLAYING = 1
GAME_OVER = 2
UPGRADES = 3
current_state = MENU

# Load images
# Make sure these image files exist in the same directory as the script
try:
    plane_img = pygame.image.load("./image-removebg-preview (3).png").convert_alpha()
    collect_img = pygame.image.load("./image-removebg-preview (4).png").convert_alpha()
    avoid_img = pygame.image.load("./image-removebg-preview (6).png").convert_alpha()
    
    # Resize images if needed
    plane_width = 70  # Made bigger
    plane_height = 50  # Made bigger
    plane_img = pygame.transform.scale(plane_img, (plane_width, plane_height))
    
    item_size = 40  # Made bigger
    collect_img = pygame.transform.scale(collect_img, (item_size, item_size))
    avoid_img = pygame.transform.scale(avoid_img, (item_size, item_size))
    
except pygame.error as e:
    print(f"Error loading images: {e}")
    print("Using default shapes instead.")
    # We'll fall back to shapes if images can't be loaded
    plane_img = None
    collect_img = None
    avoid_img = None

# Game variables
collected_towers = 0  # New currency for upgrades
game_over = False
game_won = False
win_time = 0  # For tracking the win screen timer

# Player (plane) properties
player_width = 80  # Made bigger
player_height = 60  # Made bigger
player_x = WIDTH // 2 - player_width // 2
player_y = HEIGHT - player_height - 20
base_player_speed = 5
player_speed = base_player_speed

# Upgrade variables
speed_level = 0
tower_level = 0
eagle_level = 0
currency_per_tower = 1  # New currency per collection
speed_cost = 5  # Reduced costs to match new currency
tower_cost = 3
eagle_cost = 4
currency_boost_cost = 5  # Cost for boosting currency per tower
max_upgrade_level = 5

# Spawn chances - MODIFIED: default more eagles
tower_chance = 0.2  # Default 20% chance for towers (was 0.3)

# Target for win condition
tower_goal = 25  # Need to collect this many towers to win

# Items and obstacles
items = []
item_speed = 5
spawn_rate = 40  # Frames between spawns
spawn_counter = 0

# Create close button (only for gameplay and upgrade screens)
close_button_size = 30
close_button_x = WIDTH - close_button_size - 10
close_button_y = 10

# Font for text
font = pygame.font.SysFont(None, 36)
title_font = pygame.font.SysFont(None, 64)
small_font = pygame.font.SysFont(None, 24)

# Button class for menu
class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        
    def draw(self):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        pygame.draw.rect(screen, BLACK, self.rect, 3, border_radius=10)  # Border
        
        text_surf = font.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
        
    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        
    def is_clicked(self, pos, click):
        return self.rect.collidepoint(pos) and click

# Create buttons for menu
play_button = Button(WIDTH//2 - 100, HEIGHT//2 - 100, 200, 60, "Play Game", GREEN, (0, 220, 0))
upgrades_button = Button(WIDTH//2 - 100, HEIGHT//2, 200, 60, "Upgrades", PURPLE, (180, 0, 180))
quit_button = Button(WIDTH//2 - 100, HEIGHT//2 + 100, 200, 60, "Quit Game", RED, (220, 0, 0))

# Upgrade menu buttons
back_button = Button(WIDTH//2 - 100, HEIGHT - 80, 200, 60, "Back to Menu", BUTTON_BLUE, (100, 149, 237))
speed_button = Button(WIDTH//2 - 200, HEIGHT//2 - 180, 400, 50, f"Speed Up (+{speed_cost})", GREEN, (0, 220, 0))
tower_button = Button(WIDTH//2 - 200, HEIGHT//2 - 110, 400, 50, f"More Towers (+{tower_cost})", GREEN, (0, 220, 0))
eagle_button = Button(WIDTH//2 - 200, HEIGHT//2 - 40, 400, 50, f"Less Eagles (+{eagle_cost})", GREEN, (0, 220, 0))
currency_button = Button(WIDTH//2 - 200, HEIGHT//2 + 30, 400, 50, f"More Currency (+{currency_boost_cost})", GREEN, (0, 220, 0))

def draw_player():
    if plane_img:
        screen.blit(plane_img, (player_x, player_y))
    else:
        # Fallback to drawing a simple plane shape
        pygame.draw.polygon(screen, BLUE, [
            (player_x, player_y + player_height),
            (player_x + player_width // 2, player_y),
            (player_x + player_width, player_y + player_height)
        ])
        # Add wings
        pygame.draw.rect(screen, BLUE, (player_x + 10, player_y + player_height - 15, 
                                         player_width - 20, 10))

def create_item():
    # Calculate adjusted tower chance based on tower level
    adjusted_tower_chance = tower_chance + (tower_level * 0.05)
    
    # Calculate adjusted eagle reduction based on eagle level
    eagle_reduction = eagle_level * 0.1
    adjusted_eagle_chance = 1.0 - adjusted_tower_chance - eagle_reduction
    
    # Ensure we don't go below minimum eagle chance
    if adjusted_eagle_chance < 0.05:
        adjusted_eagle_chance = 0.05
        adjusted_tower_chance = 0.95 - adjusted_eagle_chance
    
    # For debugging
    print(f"Tower chance: {adjusted_tower_chance}, Eagle chance: {adjusted_eagle_chance}")
    
    # Determine item type based on adjusted chances
    rand_val = random.random()
    item_type = "collect" if rand_val < adjusted_tower_chance else "avoid"
    print(f"Created item of type: {item_type}, random value: {rand_val}")
    
    item_x = random.randint(20, WIDTH - 20)
    items.append({
        "x": item_x, 
        "y": 0, 
        "type": item_type,
        "width": item_size,
        "height": item_size
    })

def draw_items():
    for item in items:
        if item["type"] == "collect":
            if collect_img:
                screen.blit(collect_img, (item["x"] - item_size//2, item["y"] - item_size//2))
            else:
                pygame.draw.circle(screen, GOLD, (item["x"], item["y"]), item_size//2)
        else:
            if avoid_img:
                screen.blit(avoid_img, (item["x"] - item_size//2, item["y"] - item_size//2))
            else:
                pygame.draw.circle(screen, RED, (item["x"], item["y"]), item_size//2)

def move_items():
    for item in items[:]:
        item["y"] += item_speed
        # Remove items that fall off screen
        if item["y"] > HEIGHT:
            items.remove(item)

def check_collisions():
    global collected_towers, game_over, game_won, current_state
    for item in items[:]:
        # Create a hitbox for the item
        item_rect = pygame.Rect(
            item["x"] - item_size//2, 
            item["y"] - item_size//2, 
            item_size, 
            item_size
        )
        
        # Create a hitbox for the player
        player_rect = pygame.Rect(player_x, player_y, player_width, player_height)
        
        # Check if player collided with item
        if player_rect.colliderect(item_rect):
            print(f"Collision detected with item type: {item['type']}")
            items.remove(item)
            if item["type"] == "collect":
                # Add currency based on currency_per_tower
                collected_towers += currency_per_tower
                print(f"Collected towers increased to: {collected_towers}")
                if collected_towers >= tower_goal:
                    game_won = True
                    win_time = time.time()
                    current_state = GAME_OVER
            else:
                game_over = True
                current_state = GAME_OVER

def draw_progress():
    # Draw tower collection progress
    progress_text = font.render(f"Towers: {collected_towers}/{tower_goal}", True, BLACK)
    screen.blit(progress_text, (10, 10))
    
    # Display currency per tower
    currency_text = font.render(f"Currency per tower: {currency_per_tower}", True, BLACK)
    screen.blit(currency_text, (10, 50))

def draw_close_button():
    pygame.draw.rect(screen, RED, (close_button_x, close_button_y, 
                                  close_button_size, close_button_size))
    # Draw X
    pygame.draw.line(screen, WHITE, 
                     (close_button_x + 5, close_button_y + 5),
                     (close_button_x + close_button_size - 5, close_button_y + close_button_size - 5), 
                     3)
    pygame.draw.line(screen, WHITE, 
                     (close_button_x + close_button_size - 5, close_button_y + 5),
                     (close_button_x + 5, close_button_y + close_button_size - 5), 
                     3)

def draw_menu():
    # Draw background
    screen.fill(SKY_BLUE)
    
    # Draw title
    title_text = title_font.render("Plane Collection Game", True, BLUE)
    title_rect = title_text.get_rect(center=(WIDTH//2, HEIGHT//4 - 30))
    screen.blit(title_text, title_rect)
    
    # Draw buttons in the middle
    play_button.draw()
    upgrades_button.draw()
    quit_button.draw()
    
    # Update button hover state
    mouse_pos = pygame.mouse.get_pos()
    play_button.check_hover(mouse_pos)
    upgrades_button.check_hover(mouse_pos)
    quit_button.check_hover(mouse_pos)
    
    # Draw bottom menu showcase with gray background
    showcase_height = 150
    showcase_rect = pygame.Rect(0, HEIGHT - showcase_height, WIDTH, showcase_height)
    pygame.draw.rect(screen, MENU_GRAY, showcase_rect)
    pygame.draw.line(screen, BLACK, (0, HEIGHT - showcase_height), (WIDTH, HEIGHT - showcase_height), 3)
    
    # Draw instructions in the showcase area
    instructions = [
        "Use LEFT and RIGHT arrow keys to move the plane",
        "Collect the towers and avoid the eagles",
        f"Each tower is worth {currency_per_tower} currency",
        f"Collect {tower_goal} towers to win!",
        f"Current Currency: {collected_towers}"
    ]
    
    for i, line in enumerate(instructions):
        text = font.render(line, True, WHITE)
        text_rect = text.get_rect(center=(WIDTH//2, HEIGHT - showcase_height + 30 + i*25))
        screen.blit(text, text_rect)

def draw_upgrades_menu():
    # Use a gradient background
    screen.fill(LIGHT_GRAY)
    
    # Draw title with better styling
    title_text = title_font.render("UPGRADES", True, PURPLE)
    title_rect = title_text.get_rect(center=(WIDTH//2, 50))
    screen.blit(title_text, title_rect)
    
    # Draw a decorative header line
    pygame.draw.line(screen, PURPLE, (WIDTH//4, 85), (WIDTH*3//4, 85), 3)
    
    # Display current currency with better styling and make it more prominent
    currency_bg = pygame.Rect(WIDTH//2 - 200, 100, 400, 50)
    pygame.draw.rect(screen, DARK_BLUE, currency_bg, border_radius=5)
    pygame.draw.rect(screen, GOLD, currency_bg, 3, border_radius=5)  # Add gold border
    
    currency_text = title_font.render(f"CURRENCY: {collected_towers}", True, GOLD)
    currency_rect = currency_text.get_rect(center=(WIDTH//2, 125))
    screen.blit(currency_text, currency_rect)
    
    # Update button texts with current costs and levels
    speed_button.text = f"Speed Up (Level {speed_level}/{max_upgrade_level}) - {speed_cost} currency"
    tower_button.text = f"More Towers (Level {tower_level}/{max_upgrade_level}) - {tower_cost} currency"
    eagle_button.text = f"Less Eagles (Level {eagle_level}/{max_upgrade_level}) - {eagle_cost} currency"
    currency_button.text = f"More Currency (Level {currency_per_tower-1}/{max_upgrade_level}) - {currency_boost_cost} currency"
    
    # Draw upgrade descriptions with better styling
    descriptions = [
        f"Current Speed: {base_player_speed + speed_level * 2}",
        f"Tower Spawn Rate: {int((tower_chance + tower_level * 0.05) * 100)}%",
        f"Eagle Reduction: {eagle_level * 10}%",
        f"Currency per Tower: {currency_per_tower}"
    ]
    
    y_positions = [HEIGHT//2 - 140, HEIGHT//2 - 70, HEIGHT//2, HEIGHT//2 + 70]
    
    for i, desc in enumerate(descriptions):
        # Draw description background
        desc_bg = pygame.Rect(WIDTH//2 - 210, y_positions[i] - 10, 420, 25)
        pygame.draw.rect(screen, (220, 220, 240), desc_bg, border_radius=5)
        
        # Draw description text
        text = small_font.render(desc, True, DARK_GRAY)
        text_rect = text.get_rect(center=(WIDTH//2, y_positions[i]))
        screen.blit(text, text_rect)
    
    # Disable buttons if max level reached or not enough currency
    if speed_level >= max_upgrade_level:
        speed_button.color = DARK_GRAY
        speed_button.hover_color = DARK_GRAY
        speed_button.text = f"Speed Up (MAX LEVEL)"
    elif collected_towers < speed_cost:
        speed_button.color = DARK_GRAY
        speed_button.hover_color = DARK_GRAY
    else:
        speed_button.color = TEAL
        speed_button.hover_color = (0, 160, 160)
    
    if tower_level >= max_upgrade_level:
        tower_button.color = DARK_GRAY
        tower_button.hover_color = DARK_GRAY
        tower_button.text = f"More Towers (MAX LEVEL)"
    elif collected_towers < tower_cost:
        tower_button.color = DARK_GRAY
        tower_button.hover_color = DARK_GRAY
    else:
        tower_button.color = TEAL
        tower_button.hover_color = (0, 160, 160)
    
    if eagle_level >= max_upgrade_level:
        eagle_button.color = DARK_GRAY
        eagle_button.hover_color = DARK_GRAY
        eagle_button.text = f"Less Eagles (MAX LEVEL)"
    elif collected_towers < eagle_cost:
        eagle_button.color = DARK_GRAY
        eagle_button.hover_color = DARK_GRAY
    else:
        eagle_button.color = TEAL
        eagle_button.hover_color = (0, 160, 160)
    
    if currency_per_tower-1 >= max_upgrade_level:
        currency_button.color = DARK_GRAY
        currency_button.hover_color = DARK_GRAY
        currency_button.text = f"More Currency (MAX LEVEL)"
    elif collected_towers < currency_boost_cost:
        currency_button.color = DARK_GRAY
        currency_button.hover_color = DARK_GRAY
    else:
        currency_button.color = TEAL
        currency_button.hover_color = (0, 160, 160)
    
    # Draw buttons
    speed_button.draw()
    tower_button.draw()
    eagle_button.draw()
    currency_button.draw()
    back_button.draw()
    
    # Update button hover state
    mouse_pos = pygame.mouse.get_pos()
    speed_button.check_hover(mouse_pos)
    tower_button.check_hover(mouse_pos)
    eagle_button.check_hover(mouse_pos)
    currency_button.check_hover(mouse_pos)
    back_button.check_hover(mouse_pos)

def buy_upgrade(upgrade_type):
    global collected_towers, speed_level, tower_level, eagle_level
    global player_speed, speed_cost, tower_cost, eagle_cost, currency_boost_cost
    global currency_per_tower
    
    if upgrade_type == "speed" and speed_level < max_upgrade_level and collected_towers >= speed_cost:
        collected_towers -= speed_cost
        speed_level += 1
        player_speed = base_player_speed + (speed_level * 2)
        speed_cost = int(speed_cost * 1.5)  # Increase cost for next level
        
    elif upgrade_type == "tower" and tower_level < max_upgrade_level and collected_towers >= tower_cost:
        collected_towers -= tower_cost
        tower_level += 1
        tower_cost = int(tower_cost * 1.5)  # Increase cost for next level
        
    elif upgrade_type == "eagle" and eagle_level < max_upgrade_level and collected_towers >= eagle_cost:
        collected_towers -= eagle_cost
        eagle_level += 1
        eagle_cost = int(eagle_cost * 1.5)  # Increase cost for next level
        
    elif upgrade_type == "currency" and currency_per_tower-1 < max_upgrade_level and collected_towers >= currency_boost_cost:
        collected_towers -= currency_boost_cost
        currency_per_tower += 1  # Each level adds +1 currency per collection
        currency_boost_cost = int(currency_boost_cost * 1.5)  # Increase cost for next level

def show_end_screen():
    screen.fill(DARK_BLUE)
    
    if game_won:
        message = f"You Win! You collected {tower_goal} towers!"
        color = GOLD
        
        # Show countdown timer
        elapsed = time.time() - win_time
        remaining = 5 - elapsed
        
        if remaining <= 0:
            reset_game()
            return MENU
        
        timer_text = font.render(f"Returning to menu in: {int(remaining)}s", True, WHITE)
        timer_rect = timer_text.get_rect(center=(WIDTH // 2, HEIGHT // 3 + 100))
        screen.blit(timer_text, timer_rect)
    else:
        message = "Game Over! You hit an eagle."
        color = RED
    
    text = font.render(message, True, color)
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 3))
    screen.blit(text, text_rect)
    
    score_text = font.render(f"Towers Collected: {collected_towers}/{tower_goal}", True, WHITE)
    score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 3 + 50))
    screen.blit(score_text, score_rect)
    
    # Only show buttons if game was lost (not won)
    if not game_won:
        # Draw buttons for end screen
        back_to_menu = Button(WIDTH//2 - 150, HEIGHT//2 + 30, 300, 60, "Back to Menu", BLUE, (30, 30, 220))
        back_to_menu.draw()
        
        quit_button.draw()
        
        # Check button hover
        mouse_pos = pygame.mouse.get_pos()
        back_to_menu.check_hover(mouse_pos)
        quit_button.check_hover(mouse_pos)
        
        # Check button clicks
        if pygame.mouse.get_pressed()[0]:
            if back_to_menu.is_clicked(mouse_pos, True):
                reset_game()
                return MENU
            elif quit_button.is_clicked(mouse_pos, True):
                return "QUIT"
    
    return GAME_OVER

def reset_game():
    global collected_towers, game_over, game_won, items, player_x
    # Don't reset collected_towers when going back to menu
    # So player keeps their upgrade currency
    game_over = False
    game_won = False
    items = []
    player_x = WIDTH // 2 - player_width // 2

# Main game loop
running = True
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # Mouse click processing
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            
            # Check close button (only in gameplay and upgrade screens)
            if current_state in [PLAYING, UPGRADES]:
                if (close_button_x < mouse_pos[0] < close_button_x + close_button_size and
                    close_button_y < mouse_pos[1] < close_button_y + close_button_size):
                    current_state = MENU
                    reset_game()
            
            # Check menu buttons
            if current_state == MENU:
                if play_button.is_clicked(mouse_pos, True):
                    current_state = PLAYING
                    reset_game()
                elif upgrades_button.is_clicked(mouse_pos, True):
                    current_state = UPGRADES
                elif quit_button.is_clicked(mouse_pos, True):
                    running = False
            
            # Check upgrade menu buttons
            elif current_state == UPGRADES:
                if back_button.is_clicked(mouse_pos, True):
                    current_state = MENU
                elif speed_button.is_clicked(mouse_pos, True) and speed_level < max_upgrade_level and collected_towers >= speed_cost:
                    buy_upgrade("speed")
                elif tower_button.is_clicked(mouse_pos, True) and tower_level < max_upgrade_level and collected_towers >= tower_cost:
                    buy_upgrade("tower")
                elif eagle_button.is_clicked(mouse_pos, True) and eagle_level < max_upgrade_level and collected_towers >= eagle_cost:
                    buy_upgrade("eagle")
                elif currency_button.is_clicked(mouse_pos, True) and currency_per_tower-1 < max_upgrade_level and collected_towers >= currency_boost_cost:
                    buy_upgrade("currency")
    
    # Different handling based on game state
    if current_state == MENU:
        draw_menu()
        # No close button in menu
    
    elif current_state == PLAYING:
        # Get key states for continuous movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and player_x > 0:
            player_x -= player_speed
        if keys[pygame.K_RIGHT] and player_x < WIDTH - player_width:
            player_x += player_speed
        
        # Spawn new items
        spawn_counter += 1
        if spawn_counter >= spawn_rate:
            create_item()
            spawn_counter = 0
        
        # Move items and check collisions
        move_items()
        check_collisions()
        
        # Draw everything
        screen.fill(SKY_BLUE)
        draw_player()
        draw_items()
        draw_progress()
        draw_close_button()  # Keep close button in gameplay
    
    elif current_state == GAME_OVER:
        result = show_end_screen()
        if result == MENU:
            current_state = MENU
        elif result == "QUIT":
            running = False
    
    elif current_state == UPGRADES:
        draw_upgrades_menu()
        draw_close_button()  # Keep close button in upgrades menu
    
    # Update display
    pygame.display.flip()
    
    # Control game speed
    clock.tick(60)

# Quit pygame
pygame.quit()
sys.exit()