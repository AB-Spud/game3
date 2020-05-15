import pygame, json, os
from pygame.locals import *
from random import randint

class BasicBlock(pygame.Rect):
    def __init__(self, rect_data, color=(10,10,10)):
        self.uid = id(self)
        self.color = color
        self.rect_data = list(rect_data)
        self.width = rect_data[2]
        self.height = rect_data[3]
        super().__init__(rect_data)
    
    def move_to(self, x,y):
        self.rect_data[0] = x
        self.rect_data[1] = y
        super().__init__(self.rect_data)
    
    def move(self, x,y):
        self.rect_data[0] += x
        self.rect_data[1] += y
        super().__init__(self.rect_data, color=self.color)

class StaticBlock(BasicBlock):
    def __init__(self, mass, rect_data, color):
        self.mass = mass
        self.static = True
        super().__init__(rect_data, color=color)

class NonStaticBlock(BasicBlock):
    def __init__(self, mass, rect_data, color):
        self.mass = mass
        self.velx = 0
        self.vely = 0
        self.static = False
        super().__init__(rect_data, color=color)

class PlayerBlock(NonStaticBlock):
    def __init__(self, mass, rect_data,color):
        super().__init__(mass, rect_data, color=color)

class Game(object):
    def __init__(self, grav, tick_rate):
        self.grav = grav
        self.accel_speed = .2
        self.max_accel = -2
        self.drag = .1
        self.running = True

        self.jumps = 2
        self.dash = 1

        self.dt = 0
        self.tf = 0

        self.box_size = 50

        self.keys = None
        self.mice = None

        pygame.init()
        pygame.font.init()

        self.clock = pygame.time.Clock()
        self.tick_rate = tick_rate
    
    def record_times(self):
        self.dt = pygame.time.get_ticks()- self.tf
        self.tf = pygame.time.get_ticks()
    
    def record_pressed(self):
        self.keys = pygame.key.get_pressed()
        self.mice = pygame.mouse.get_pressed()
    
    def get_mouse_block(self):
        x,y = pygame.mouse.get_pos()
        return pygame.Rect(x,y,5,5), x,y
    
    def calc_vels(self, x, y, obj): # no use for now
        X = x - obj.x
        Y = y - obj.x
        return (X/self.dt), (Y/self.dt)
    
    def compute_grav_accel(self, obj): # computes give objects gravity acceleration speed
        return obj.mass * self.grav

    def apply_drag_force(self, obj, drag): # drag force to slow x axis objects
        if obj.velx > 0:
            obj.velx -=drag
            if obj.velx < 0:
                obj.velx = 0

        if obj.velx < 0:
            obj.velx +=drag
            if obj.velx > 0:
                obj.velx = 0

    def reaction_loop(self, rect_list, player):
        for r1 in rect_list:
            self.mbk,x,y = self.get_mouse_block()
            if r1.colliderect(self.mbk) and self.mice[1]:
                r1.move_to(x-r1.width/2,y-r1.height/2)

            if not r1.static:
                self.apply_drag_force(r1, self.drag)
            
                G = self.compute_grav_accel(r1)
                r1.vely+= G * (self.dt/1000)

                r1.move(0, r1.vely) # Y velocity collision checks
                for r2 in rect_list:
                    if r1.uid != r2.uid:
                        if r1.colliderect(r2):
                            r1.move(0,-r1.vely)
                            r1.vely = r1.vely - r1.vely
                            if r1.uid == player.uid:
                                self.jumps = 2
                    
                r1.move(r1.velx, 0) # X velocity collison checks
                for r2 in rect_list:
                    if r1.uid != r2.uid:
                        if r1.colliderect(r2):
                            r1.move(-r1.velx, 0)
                            if not r2.static:
                                if r1.velx > 0:
                                    if (r1.velx - r2.mass + r1.mass) <= 0:
                                        pass
                                    else:
                                        r2.velx = r1.velx - r2.mass + r1.mass
                                else:
                                    if (r1.velx + r2.mass - r1.mass) >= 0:
                                        pass
                                    else:
                                        r2.velx = r1.velx + r2.mass - r1.mass
              
    def draw_rects(self, screen, rect_list):
        for r in rect_list:
            pygame.draw.rect(screen, r.color, r)

    def event_loop(self, player):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
            
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    x,y = pygame.mouse.get_pos()
                    b = StaticBlock(10, (x-(self.box_size/2),y-(self.box_size/2),self.box_size,self.box_size), color=(0,0,0))
                    self.blocks.append(b)
                
                if event.button == 3:
                    x,y = pygame.mouse.get_pos()
                    b = NonStaticBlock(2, (x-(self.box_size/2),y-(self.box_size/2),self.box_size,self.box_size), color=(200,55,55))
                    self.blocks.append(b)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    self.running = False
                
                if event.key == pygame.K_LSHIFT:
                    x,y = pygame.mouse.get_pos()
                    player.move_to(x,y)
                
                if event.key == pygame.K_0:
                    self.grav = -self.grav
                                
                if event.key == pygame.K_EQUALS:
                    self.grav+=1
                
                if event.key == pygame.K_MINUS:
                    self.grav-=1

                if event.key == pygame.K_SPACE:
                    if bool(self.jumps):
                        if game.grav > 0:
                            player.vely -= 2
                        elif game.grav < 0:
                            player.vely += 2
                        else:
                            pass # nothing interesting happens when gravity is set to 0
                                 # note : try checking collisions for value to offset here
                
                        self.jumps-=1

                if event.key == pygame.K_z:
                    self.blocks.pop()
                
                if event.key == pygame.K_c:
                    self.blocks = self.level.default_map()
                    self.blocks.append(player)

    def pressed(self, player):
        if self.keys[pygame.K_a]:
            player.velx += -self.accel_speed
            if player.velx < self.max_accel:
                player.velx = self.max_accel

        if self.keys[pygame.K_d]:
            player.velx += self.accel_speed
            if player.velx > -self.max_accel:
                player.velx = -self.max_accel
        
        # Needs cooldowns
        # if self.keys[pygame.K_LCTRL] and bool(self.dash) and self.keys[pygame.K_d]:
        #     player.velx += 5
        
        # if self.keys[pygame.K_LCTRL] and bool(self.dash) and self.keys[pygame.K_a]:
        #     player.velx -= 5

        if self.keys[pygame.K_LEFTBRACKET]:
            if self.box_size > 1:
                self.box_size-=1
        
        if self.keys[pygame.K_RIGHTBRACKET]:
            self.box_size+=1
        
        if self.mice[0] or self.mice[2]:
            x,y = pygame.mouse.get_pos()
            pygame.draw.rect(self.level.screen, (0,255,0),[x-(self.box_size/2),y-(self.box_size/2),self.box_size,self.box_size])

    def game_loop(self):
        self.level = Map()
        player = PlayerBlock(1,(500, 250, 10, 10), color=(255,0,0))
        font = pygame.font.SysFont('Arial', 20)
        self.blocks = self.level.default_map()
        self.blocks.append(player)
        while self.running:
            self.level.screen.fill((128,128,128))
            self.clock.tick(self.tick_rate)
            self.record_times()
            self.record_pressed()
            self.mouse_block = self.get_mouse_block()

            self.event_loop(player)
            self.pressed(player)

            self.reaction_loop(self.blocks, player)

            self.draw_rects(self.level.screen, self.blocks)

            xv_txt = font.render(f'x-velocity: {player.velx}', False, (255, 0, 0))
            yv_txt = font.render(f'y-velocity: {player.vely}', False, (255, 0, 0))
            grav_txt = font.render(f'gravity: {self.grav}', False, (255, 0, 0))
            fps_txt = font.render('FPS: {0:.8}'.format(self.clock.get_fps()), False, (255, 0, 0))
            boxsz_txt = font.render(f"box_size: {self.box_size}", False, (255,0,0))


            self.level.screen.blit(boxsz_txt, (890,10))
            self.level.screen.blit(fps_txt, (20, 20))
            self.level.screen.blit(yv_txt, (20, 40))
            self.level.screen.blit(xv_txt, (20, 60))
            self.level.screen.blit(grav_txt, (20, 80))

            pygame.display.flip()


class Map(object):
    def __init__(self):
        self.screen = pygame.display.set_mode((1000,500))

    def default_map(self):
        color = (0,0,0)
        block = StaticBlock(10,(0, 490, 1000, 1000), color=color)
        block2 = StaticBlock(10,(0, 0, 1000, 10), color=color)

        block3 = StaticBlock(10,(0, 0, 10, 500), color=color)
        block4 = StaticBlock(10,(990, 0, 1000, 500), color=color)

        return [block,block2,block3,block4]

game = Game(9, 200)
game.game_loop()
