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
    
    def move_c(self, x,y):
        self.rect_data[0] += x
        self.rect_data[1] += y
        super().__init__(self.rect_data, color=self.color)
    
    def is_clicked(self, mbtn=0):
        return pygame.mouse.get_pressed()[mbtn] and self.collidepoint(pygame.mouse.get_pos())

class GoalBlock(BasicBlock):
    def __init__(self, rect_data, material, color):
        super().__init__(rect_data, material=material, color=color)
    
    def reached(self, rect):
        return self.colliderect(rect)

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
    
    def get_offset(self): # fix so inverted gravity works with as well
        return (self.rect_data[0], self.rect_data[1]-5, self.rect_data[2], self.rect_data[3])

class Game(object):
    def __init__(self, grav, tick_rate):
        self.grav = grav
        self.accel_speed = .2
        self.max_accel = -2
        self.drag = .1
        self.running = True
        self.draw_data = -1

        self.dt = 0
        self.tf = 0
        self.loc = 37, 1010

        self.win = False
        self.win_tick = 0
        self.last_win = 0
        self.win_cooldown = 4000

        self.draw_tick = 0
        self.draw_delay = 10
        self.draw = 1

        self.click_x = 0
        self.click_y = 0

        self.ref = None
        self.moving = False

        self.box_size_x = 50
        self.box_size_y = 50

        self.keys = None
        self.mice = None

        self.materials = {}
        self.sprites = {}

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
    
    def load_sprites(self):
        a = os.listdir("resources/sprites")
        self.sprites['none'] = 'none'
        for i in a:
            path = i
            self.sprites[i] = {}
            d= 0
            for x in os.listdir(f"resources/sprites/{i}"):
                self.sprites[i][d] = pygame.image.load(f"resources/sprites/{i}/{x}")
                d+=1
            
    
    def calc_vels(self, x, y, obj): # no use for now
        X = x - obj.x
        Y = y - obj.x
        return (X/self.dt), (Y/self.dt)
    
    def calc_normal_coords(self, x,y):
        if self.box_size_x < 0 and self.box_size_y < 0:
            return self.click_x, self.click_y
            
        elif self.box_size_x < 0:
            return self.click_x, y

        elif self.box_size_y < 0:
            return x,self.click_y
        else:
            return x,y
    
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
                pygame.draw.rect(self.level.screen, (0,255,0), r1, 3) # show's selection

            if not r1.static:
                self.apply_drag_force(r1, self.drag)
            
                G = self.compute_grav_accel(r1)
                r1.vely+= G * (self.dt/1000)

                if abs(r1.vely) > r1.terminal:
                    r1.vely = r1.terminal

                r1.move_c(0, r1.vely) # Y velocity collision checks
                for r2 in rect_list:
                    if r1.uid != r2.uid:
                        if r1.colliderect(r2):
                            self.loc = (r1.x ,r1.y-2) # move to function - beware of inverse gravity 
                            r1.move_c(0,-r1.vely)
                            r1.vely = r1.vely - r1.vely
                            if r1.uid == player.state.uid:
                                player.jumps = 2
                    
                r1.move_c(r1.velx, 0) # X velocity collison checks
                for r2 in rect_list:
                    if r1.uid != r2.uid:
                        if r1.colliderect(r2):
                            r1.move_c(-r1.velx, 0)
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

    def display_win(self):
        millis = self.win_tick-self.last_win
        seconds=(millis/1000) % 60
        minutes=(millis/(1000*60))%60
        minutes = int(minutes)

        win_txt = self.font.render(f"You won, in %d minutes and %f seconds!" % (minutes, seconds), False, (255, 155, 0))    
        r = self.level.screen.get_rect()
        rect = pygame.Rect(0,0,420,30)
        rect.center=r.center
        pygame.draw.rect(self.level.screen, (0,255,0), rect, 3)
        pygame.draw.rect(self.level.screen, (10,10,10), rect, 0)
        self.level.screen.blit(win_txt, rect.topleft)
        
        if self.tick - self.win_tick >= self.win_cooldown:
            self.last_win = self.win_tick
            self.win = False

    def draw_rects(self, screen, rect_list, player):
        for r in rect_list:
            if r.material == "none":
                pygame.draw.rect(screen, r.color, r, 2)
            else:
                if r.uid != player.uid:
                    picture = pygame.transform.scale(self.materials[r.material], (r.width, r.height))
                    screen.blit(picture, r.get_offset() or r)
        
        pygame.draw.rect(self.level.screen, self.goal.color, self.goal)
    
    def draw_sprites(self, screen, r):
        if r.material == "none":
            pass
        else:
            picture = pygame.transform.scale(self.sprites['player2'][r.material], (r.width, r.height))
            screen.blit(picture, r.get_offset() or r)

    def draw_bg(self, bg_image, player):
        if self.tick - self.draw_tick >= self.draw_delay and self.draw == 0:
            self.level.screen.blit(bg_image, (0,0))
            self.draw_tick = self.tick
        elif self.draw == 1:
            self.level.screen.fill((0,0,0))

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

                n_x, n_y = self.calc_normal_coords(x,y)

                if event.button == 1:
                    b = StaticBlock(10, (n_x, n_y, abs(self.box_size_x) ,abs(self.box_size_y)), self.current_mat, color=(255,255,255))
                    self.blocks.append(b)
                
                if event.button == 2:
                    self.moving = False
                
                if event.button == 3:
                    if self.box_size_x < 0 and self.box_size_y < 0:
                        b = NonStaticBlock(2, (n_x, n_y, abs(self.box_size_x),abs(self.box_size_y)), self.current_mat, color=(200,55,55))
                        self.blocks.append(b)
                
            
            if event.type == pygame.MOUSEMOTION and self.moving:
                self.ref.move_c(event.rel[0], event.rel[1])

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    player.jump(game.grav, 2.13)
                
                if event.key == pygame.K_b:
                    player.jump(game.grav, 2.13)

                if event.key == pygame.K_F3:
                   self.draw_data = -self.draw_data
                
                if event.key == pygame.K_F7:
                    pygame.image.save(self.level.screen, f"{self.tick}.jpeg")

                if event.key == pygame.K_g:
                    self.level.save_map(self.blocks)
                
                if event.key == pygame.K_1:
                    self.blocks = self.level.load_map('b')
                    player.tp(self.loc)
                    self.last_win = self.tick
                    self.blocks.append(player.state)
                
                if event.key == pygame.K_2:
                    self.blocks = self.level.load_map('c')
                    player.tp(self.loc)
                    self.last_win = self.tick
                    self.blocks.append(player.state)

                if event.key == pygame.K_q:
                    self.running = False
                
                if event.key == pygame.K_LSHIFT:
                    x,y = pygame.mouse.get_pos()
                    player.state.move_to(x,y)
                
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

                if event.key == pygame.K_z and len(self.blocks) > 0:
                    self.blocks.pop()
                
                if event.key == pygame.K_c:
                    self.blocks = self.level.default_map()
                    self.blocks.append(player.state)

    def pressed(self, player):
        if self.keys[pygame.K_a]:
            player.move_left(self.accel_speed)

        if self.keys[pygame.K_d]:
            player.move_right(self.accel_speed)
        
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
        game.load_materials()
        game.load_sprites()
        boundary = BasicBlock((0,0,1920,1080), "none")
        state = PlayerBlock(1,(37, 1013, 12, 12), material="none" ,color=(255,0,0))
        player = PlayerObj(self.sprites['player2'], state, self.max_accel)
        self.goal = GoalBlock((26, 46, 50, 50), "none", (255,255,0))
        pygame.display.set_caption(f"v5.2 - working build - textures")
        self.font = pygame.font.SysFont('Arial', 20)

        self.blocks = self.level.default_map()
        self.blocks.append(player.state)

        bg_image = pygame.transform.scale(self.materials["bg_sky"], (1920, 1080))
        print(self.level.screen.get_flags())

        while self.running:
            self.clock.tick(self.tick_rate)
            self.tick = pygame.time.get_ticks()
            self.record_times()
            self.record_pressed()
            self.mouse_block = self.get_mouse_block()

            player.prev_state = player.state

            self.draw_bg(bg_image, player)

            self.event_loop(player)
            self.pressed(player)

            self.reaction_loop(self.blocks, player)

            self.draw_rects(self.level.screen, self.blocks, player)

            self.draw_sprites(self.level.screen, player.state)

            player.animate(self.tick)
            
            if self.goal.reached(player.state):
                player.tp(self.loc)
                self.win_tick = self.tick
                self.win = True

            if not boundary.contains(player.state):
                player.died(self.loc)
            
            if self.win:
                self.display_win()

            xv_txt = self.font.render(f'x-velocity: {player.state.velx}', False, (255, 0, 0))
            yv_txt = self.font.render(f'y-velocity: {player.state.vely}', False, (255, 0, 0))
            grav_txt = self.font.render(f'gravity: {self.grav}', False, (255, 0, 0))
            dt_txt = self.font.render(f'dt: {self.dt} (above 6 = bad)', False, (255, 0, 0))
            fps_txt = self.font.render('FPS: {0:.8}'.format(self.clock.get_fps()), False, (255, 0, 0))
            boxsz_txt = self.font.render(f"box_size: {self.box_size_x}x{self.box_size_y}", False, (255,0,0))
            blocks_txt = self.font.render(f"blocks: {len(self.blocks)}", False, (255,0,0))
            mat_txt = self.font.render(f"current_mat: {self.current_mat}", False, (255,0,0))

            if self.draw_data == 1:
                self.level.screen.blit(boxsz_txt, (1700,10))
                self.level.screen.blit(blocks_txt, (1700, 30))
                self.level.screen.blit(fps_txt, (20, 20))
                self.level.screen.blit(yv_txt, (20, 40))
                self.level.screen.blit(xv_txt, (20, 60))
                self.level.screen.blit(grav_txt, (20, 80))
                self.level.screen.blit(mat_txt, (20, 100))
                self.level.screen.blit(dt_txt, (20, 120))

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
    
    def load_map(self, var):
        blocks = []
        map_data = json.load(open(f"resources/maps/tut-{var}.json", "r"))
        for i in map_data['blocks']:
            b = StaticBlock(10, i, "none", color=(255,255,255))
            b.normalize()
            blocks.append(b)
        
        return blocks

    def default_map(self):
        block1 = StaticBlock(10, (1920,0,10,1080), "none", color=(0,0,0))

        block2 = StaticBlock(10, (-10,0,10,1080), "none", color=(0,0,0))

        block3 = StaticBlock(10, (0,-10,1920,10), "none", color=(0,0,0))

        return [block1, block2, block3]

class PlayerObj(object):
    def __init__(self, sprite_data, state_data, max_accel):
        self.sprite_data = sprite_data
        self.state = state_data
        self.prev_state = state_data
        self.max_accel = max_accel
        self.uid = state_data.uid

        self.jumps = 2
        self.dashes = 1
        self.lives = 3

        self.ani_index = 0
        self.ani_start = 0
        self.ani_limit = 0

        self.ani_tick = 0
    
    def move_left(self, accel_speed):
        self.animate_left()
        self.state.velx += -accel_speed
        if self.state.velx < self.max_accel:
            self.state.velx = self.max_accel
    
    def move_right(self, accel_speed):
        self.animate_right()
        self.state.velx += accel_speed
        if self.state.velx > -self.max_accel:
            self.state.velx = -self.max_accel
        
    def jump(self, grav, accel_speed):
        if bool(self.jumps):
            if grav > 0:
                self.state.vely -= accel_speed
            elif grav < 0:
                self.state.vely += accel_speed
            else:
                b = randint(0,1)
                if b == 1:
                    self.state.vely += accel_speed
                elif b == 0:
                    self.state.vely -= accel_speed
                
                print(b)

            self.jumps -=1
    
    def animate_left(self):
        self.ani_start = 1
        self.ani_limit = 1
        self.ani_index = 1

    def animate_right(self):
        self.ani_start = 0
        self.ani_limit = 0
        self.ani_index = 0

    def animate(self, tick):
        if tick - self.ani_tick >= 100:
            self.state.material = self.ani_index
            self.ani_tick = tick
            self.ani_index += 1
            if self.ani_index >= self.ani_limit:
                self.ani_index = self.ani_start

    def died(self, loc): 
        self.lives-=1
        self.state.move_to(loc[0], loc[1])
    
    def tp(self, loc):
        self.state.move_to(loc[0], loc[1])

class GeneralField(object):
    def __init__(self, state_data):
        self.state = state_data
        self.uid = state_data.uid
    
    def field_contains(self, obj_state):
        return self.colliderect(rect)
    
    def call(self, func):
        func()


game = Game(9, 200)
game.game_loop()
