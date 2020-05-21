import pygame, json, os, pickle, dill
from pygame.locals import *
from random import randint

running = True
pygame.init()
pygame.font.init()
clock = pygame.time.Clock()

screen = pygame.display.set_mode((1000,500))

grabbed = False

block = pygame.Rect([100,100,200,150])
dblock = pygame.Rect([100,100,200,20])
mblock = pygame.Rect([0,0,0,0])

color = (0,0,0)
color2 = (128,128,128)
color3 = (255,255,255)

x2,y2 = None,None

pygame.display.set_caption("menu testing v1.3 beta")

while running:
    clock.tick(1000)
    pygame.display.flip()
    screen.fill(color)
    pygame.draw.rect(screen, color3, block)
    pygame.draw.rect(screen, color2, dblock)

    x,y = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                running = False
        
        if event.type == pygame.MOUSEBUTTONDOWN and dblock.collidepoint(x,y):
            x2,y2 = x,y
            grabbed = True

        if event.type == pygame.MOUSEBUTTONUP:
            grabbed = False
            if event.button == 3:
                block = pygame.Rect(x,y,200,150)
                dblock = pygame.Rect(x,y,200,20)

            if event.button == 1:
                pass

        mice = pygame.mouse.get_pressed()

        if mice[0] and grabbed:
            x3,y3 = x-x2, y-y2
            block = pygame.Rect(block.x+x3,block.y+y3,200,150)
            dblock = pygame.Rect(dblock.x+x3,dblock.y+y3,200,20)
            x2,y2 = x,y
            grabbed = True



