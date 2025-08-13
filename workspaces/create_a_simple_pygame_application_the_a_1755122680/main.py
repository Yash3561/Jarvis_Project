import pygame

pygame.init()

screen = pygame.display.set_mode((600, 400))
pygame.display.set_caption("Diagonal Motion")

white = (255, 255, 255)
black = (0, 0, 0)

x = 0
y = 0
square_size = 20
speed = 5

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(black)

    pygame.draw.rect(screen, white, (x, y, square_size, square_size))

    x += speed
    y += speed

    if x > 600 - square_size or y > 400 - square_size:
        x = 0
        y = 0

    pygame.display.flip()

pygame.quit()