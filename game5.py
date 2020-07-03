import pygame, json, os
from pygame.locals import *
from random import randint

class BasicBlock(pygame.Rect):
    def __init__(self, rect_data, material, color=(10,10,10)):
        self.uid = id(self)
        self.color = color
        self.material = material
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
    
    def is_clicked(self, mbtn=0):
        return pygame.mouse.get_pressed()[mbtn] and self.collidepoint(pygame.mouse.get_pos())

class StaticBlock(BasicBlock):
    def __init__(self, mass, rect_data, material, color):
        self.mass = mass
        self.static = True
        super().__init__(rect_data, material=material, color=color)

class NonStaticBlock(BasicBlock):
    def __init__(self, mass, rect_data, material, color, terminal=30):
        self.mass = mass
        self.terminal = terminal
        self.velx = 0
        self.vely = 0
        self.static = False
        super().__init__(rect_data, material=material, color=color)

class PlayerBlock(NonStaticBlock):
    def __init__(self, mass, rect_data, material, color):
        self.material = material
        super().__init__(mass, rect_data, material=material, color=color)

class Game(object):
    def __init__(self, grav, tick_rate):
        self.grav = grav
        self.accel_speed = .2
        self.max_accel = -2
        self.drag = .1
        self.running = True
        self.draw_data = -1

        self.jumps = 2
        self.dash = 1
        self.lives = 3

        self.dt = 0
        self.tf = 0

        self.click_x = 0
        self.click_y = 0

        self.ref = None
        self.moving = False

        self.box_size_x = 50
        self.box_size_y = 50

        self.keys = None
        self.mice = None

        self.materials = {}

        self.current_mat = "none"
        self.mat_count = 0

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
    
    def load_materials(self):
        a = os.listdir("resources/materials")
        self.materials['none'] = 'none'
        for i in a:
            try:
                self.materials[i.split(".")[0]] = pygame.image.load(f"resources/materials/{i}").convert()
            except Exception as error:
                print(error)
    
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
            if r1.is_clicked(1):
                self.ref = r1
                self.moving = True

            if not r1.static:
                self.apply_drag_force(r1, self.drag)
            
                G = self.compute_grav_accel(r1)
                r1.vely+= G * (self.dt/1000)

                if abs(r1.vely) > r1.terminal:
                    r1.vely = r1.terminal

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
            if r.material == "none":
                pygame.draw.rect(screen, r.color, r, 2)
            else:
                picture = pygame.transform.scale(self.materials[r.material], (r.width, r.height))
                screen.blit(picture, r)

    def event_loop(self, player):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.click_x,self.click_y = pygame.mouse.get_pos()
            
            if event.type == pygame.MOUSEBUTTONUP:
                x,y = pygame.mouse.get_pos()
                self.box_size_x = self.click_x - x
                self.box_size_y = self.click_y - y

                if event.button == 1:
                    b = StaticBlock(10, (x,y,self.box_size_x,self.box_size_y), self.current_mat, color=(255,255,255))
                    b.normalize()
                    self.blocks.append(b)
                
                if event.button == 2:
                    self.moving = False
                
                if event.button == 3:
                    if self.box_size_x < 0 and self.box_size_y < 0:
                        b = NonStaticBlock(2, (self.click_x,self.click_y, abs(self.box_size_x),abs(self.box_size_y)), self.current_mat, color=(200,55,55))
                    else:
                        b = NonStaticBlock(2, (x,y, abs(self.box_size_x),abs(self.box_size_y)), self.current_mat, color=(200,55,55))
                    b.normalize()
                    self.blocks.append(b)
            
            if event.type == pygame.MOUSEMOTION and self.moving:
                self.ref.move_ip(event.rel)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F3:
                   self.draw_data = -self.draw_data

                if event.key == pygame.K_g:
                    self.level.save_map(self.blocks)
                
                if event.key == pygame.K_h:
                    self.blocks = self.level.load_map()
                    player.move_to(37, 1013)
                    self.blocks.append(player)

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

                if event.key == pygame.K_UP:
                    self.mat_count += 1
                    a = list(self.materials.keys())
                    if self.mat_count >= len(a):
                        self.mat_count = 0
                    
                    self.current_mat = a[self.mat_count]

                if event.key == pygame.K_DOWN:
                    self.mat_count -= 1
                    a = list(self.materials.keys())
                    if self.mat_count < 0:
                        self.mat_count = len(a)-1
                    
                    self.current_mat = a[self.mat_count]

                if event.key == pygame.K_SPACE:
                    if bool(self.jumps):
                        if game.grav > 0:
                            player.vely -= 2.1
                        elif game.grav < 0:
                            player.vely += 2.1
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
            self.box_size_x-=1
            self.box_size_y-=1
        
        if self.keys[pygame.K_RIGHTBRACKET]:
            self.box_size_x+=1
            self.box_size_y+=1

        if self.keys[pygame.K_p]:
            self.box_size_x+=1
        
        if self.keys[pygame.K_o]:
            self.box_size_x-=1

        if self.keys[pygame.K_l]:
            self.box_size_y+=1
        
        if self.keys[pygame.K_k]:
            self.box_size_y-=1
        
        if self.mice[0] or self.mice[2]:
            x,y = pygame.mouse.get_pos()
            self.box_size_x = self.click_x - x
            self.box_size_y = self.click_y - y
            pygame.draw.rect(self.level.screen, (0,255,0),[x,y,self.box_size_x,self.box_size_y], 1)

    def game_loop(self):
        self.level = Map()
        boundary = BasicBlock((0,0,1920,1080), "none")
        player = PlayerBlock(1,(37, 1013, 10, 10), material="none" ,color=(255,0,0))
        pygame.display.set_caption(f"v5.2 - working build - textures")
        font = pygame.font.SysFont('Arial', 20)

        self.blocks = self.level.default_map()
        self.blocks.append(player)
        game.load_materials()
        bg_image = pygame.transform.scale(self.materials["bg_sky"], (1920, 1080))
        print(self.level.screen.get_flags())

        while self.running:
            # self.level.screen.fill((155,155,155))
            self.clock.tick(self.tick_rate)
            self.record_times()
            self.record_pressed()
            self.mouse_block = self.get_mouse_block()
            self.level.screen.blit(bg_image, (0,0))

            self.event_loop(player)
            self.pressed(player)

            self.reaction_loop(self.blocks, player)

            self.draw_rects(self.level.screen, self.blocks)

            if not boundary.contains(player):
                player.move_to(37, 1013)

            xv_txt = font.render(f'x-velocity: {player.velx}', False, (255, 0, 0))
            yv_txt = font.render(f'y-velocity: {player.vely}', False, (255, 0, 0))
            grav_txt = font.render(f'gravity: {self.grav}', False, (255, 0, 0))
            fps_txt = font.render('FPS: {0:.8}'.format(self.clock.get_fps()), False, (255, 0, 0))
            boxsz_txt = font.render(f"box_size: {self.box_size_x}x{self.box_size_y}", False, (255,0,0))
            blocks_txt = font.render(f"blocks: {len(self.blocks)}", False, (255,0,0))
            mat_txt = font.render(f"current_mat: {self.current_mat}", False, (255,0,0))

            if self.draw_data == 1:
                self.level.screen.blit(boxsz_txt, (1700,10))
                self.level.screen.blit(blocks_txt, (1700, 30))
                self.level.screen.blit(fps_txt, (20, 20))
                self.level.screen.blit(yv_txt, (20, 40))
                self.level.screen.blit(xv_txt, (20, 60))
                self.level.screen.blit(grav_txt, (20, 80))
                self.level.screen.blit(mat_txt, (20, 100))

            pygame.display.flip()


class Map(object):
    def __init__(self):
        os.environ['SDL_VIDEO_CENTERED'] = '1'
        self.screen = pygame.display.set_mode((1920,1080), pygame.NOFRAME | pygame.DOUBLEBUF | pygame.HWSURFACE)
    
    def save_map(self, map):
        map_data = []
        for i in map:
            if type(i) != PlayerBlock:
                map_data.append(i.rect_data)
            else:
                print(i.rect_data)
        json.dump({"blocks": map_data}, open("resources/maps/tut.json", "w"))
    
    def load_map(self):
        blocks = []
        map_data = json.load(open("resources/maps/tut.json", "r"))
        for i in map_data['blocks']:
            blocks.append(StaticBlock(10, i, "none", color=(255,255,255)))
        
        return blocks

    def default_map(self):
        block1 = StaticBlock(10, (1920,0,10,1080), "none", color=(0,0,0))

        block2 = StaticBlock(10, (-10,0,10,1080), "none", color=(0,0,0))

        block3 = StaticBlock(10, (0,-10,1920,10), "none", color=(0,0,0))

        return [block1, block2, block3]

game = Game(9, 200)
game.game_loop()
