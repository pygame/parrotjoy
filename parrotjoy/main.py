import pygame


def main(args):
    try:
        gamemain(args)
    except KeyboardInterrupt:
        print('Keyboard Interrupt...')
        print('Exiting')

def gamemain(args):
    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode((640, 480))
    pygame.display.set_caption("parrotjoy")

    going = True
    while going:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                going = False

    pygame.quit()
