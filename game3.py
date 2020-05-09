import pygame, json, os
from random import randint

class Game(object):
    def __init__(self, cheats, fps):
        pygame.init()
        pygame.font.init()
        self.running = True
        self.saving = False
        self.paused = False
        self.paused2 = False
        self.win = False
        self.cheats = cheats
        self.font = pygame.font.SysFont('Arial', 20)
        self.save_name = ''
        self.chng_lvl = ''

        self.black = (0,0,0)
        self.white = (255,255,255)
        self.grey = (128, 128, 128)
        self.purple = (128, 0, 128)
        self.red = (255,0,0)
        self.gold = (255, 215, 0)

        self.clock = pygame.time.Clock()
        self.fps = fps
        self.win_tick = 0
        self.last_win = 0
        self.physics_data = False
        self.win_cooldown = 2000

        self.xgrav = 0
        self.ygrav = 2
        self.max_vel = 5
        self.friction = .5

        self.box_size = 50

        self.hard_objects = {}
        self.player_objects = {}
        self.goal_objects = {}
        self.player_colors = {}
    
    def load_data(self, map_path):
        self.level = Map(map_path)
        self.player = Player("will")
        self.res = self.level.map_data['res']
        self.box_ids = []
        self.player.xpos = self.level.player_spawn[0]
        self.player.ypos = self.level.player_spawn[1]
        self.player.update_rect_data()
        self.ygrav = self.level.map_grav
        self.max_vel = self.level.map_vel
        self.friction = self.level.map_friction
        self.room = self.level.start_room
        self.door = list(self.level.map_doors.keys())[-1]

        self.init_rooms(self.hard_objects)

        self.goal_objects.update(self.level.goal)

        pygame.display.set_caption(f"LEVEL: {self.level.level_name} | USER: {self.player.name} | CHEATS: {self.cheats}")       
    
    def start_game(self, map_path):
        self.level = Map(map_path)
        self.player = Player("will")
        self.res = None
        self.box_ids = None
        self.player.xpos = None
        self.player.ypos = None
        self.ygrav = None
        self.max_vel = None
        self.friction = None
        self.room = None
        self.door = None

        self.load_data(map_path)

        while self.running:
            self.tick = pygame.time.get_ticks()
            self.clock.tick(self.fps)
            if self.player.spawn:
                self.player_objects[self.player.name] = self.player.rect_data
                self.player_colors[self.player.name] = self.player.color
            
            
            self.player_rects = []
            self.hard_rects = []
            self.static_rects = []
            self.goal_rects = []
            self.door_rects = {}

            self.draw_rects_dict(self.player_objects, 'p')
            self.draw_rects_dict(self.hard_objects[self.room], 'h')
            self.draw_rects_dict(self.level.map_doors[self.room], 'd')
            self.draw_rects_dict(self.goal_objects[self.room], 'g')
            self.draw_rects_dict(self.level.static_objects[self.room], 's')

            if self.physics_data:
                self.display_physics_data()

            if self.saving:
                sv_txt = self.font.render(f"save as: {self.save_name}", False, (255, 0, 0))    
                self.level.screen.blit(sv_txt, (200, 20))
            
            if self.paused:
                v = 10
                ps_txt = self.font.render(f"paused: enter a level name to change level", False, (255, 0, 0))
                chn_txt = self.font.render(f"new_level: {self.chng_lvl}", False, (255, 0, 0))
                lvls_txt = self.font.render(f"LEVELS", False, (255, 0, 0))
                self.level.screen.blit(ps_txt, (500, 20))
                self.level.screen.blit(chn_txt, (500, 40))
                self.level.screen.blit(lvls_txt, (870,10))
                for lvl in self.level.lvls:
                    v+=20
                    lvl_txt = self.font.render(f"{lvl.split('.js')[0]}", False, (255, 0, 0))
                    self.level.screen.blit(lvl_txt, (870,v))

            if self.win:
                win_txt = self.font.render(f"You won!", False, (255, 0, 0))    
                win2_txt = self.font.render(f"It took you {self.display_tick/1000} seconds.", False, (255, 0, 0))    
                self.level.screen.blit(win_txt, (self.res[0]/2, self.res[1]/2))
                self.level.screen.blit(win2_txt, (self.res[0]/2, self.res[1]/2+20))

            self.check_cooldowns(self.tick)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                
                if event.type == pygame.KEYDOWN:
                    if not self.saving and not self.paused and not self.paused2:
                        if event.key == pygame.K_q:
                            self.running = False

                        if event.key == pygame.K_SPACE:
                            if bool(self.player.jumps): # evals jump int to boolean : n > 0 returns True
                                self.ygrav = -self.ygrav
                                self.player.jumps -= 1
                                # self.player.double_jump = False
                                self.player.toj = pygame.time.get_ticks()

                        if event.key == pygame.K_F2:
                            self.physics_data = not self.physics_data
                        
                        if event.key == pygame.K_F3:
                            self.cheats = not self.cheats
                            self.update_display()
                        
                        if event.key == pygame.K_c:
                            self.hard_objects = {}
                            self.init_rooms(self.hard_objects)
                            self.player.boxs_placed = 0
                        
                        if event.key == pygame.K_z:
                            try:
                                del self.hard_objects[self.room][self.box_ids.pop()]
                                self.player.boxs_placed -= 1
                            except Exception as error:
                                pass
                        
                        if event.key == pygame.K_RETURN:
                            self.paused = True
                        if self.cheats:
                            if event.key == pygame.K_0:
                                self.ygrav = -self.ygrav
                            if event.key == pygame.K_MINUS:
                                self.ygrav-=1
                            if event.key == pygame.K_EQUALS:
                                self.ygrav+=1
                    else:
                        if self.saving:
                            if event.key == pygame.K_ESCAPE:
                                self.saving = not self.saving
                            if event.key == pygame.K_q:
                                    self.running = False
                            
                            if event.key == pygame.K_RETURN:
                                self.saving = not self.saving
                                for i in self.level.map_doors:
                                    self.level.static_objects[i].update(self.hard_objects[i])
                                self.level.map_data['level-name'] = self.save_name
                                json.dump(self.level.map_data, open(f"maps/{self.save_name}.json", 'w+'), indent=4)
                                self.hard_objects = {}
                                self.init_rooms(self.hard_objects)
                            else:
                                self.save_name += chr(event.key)

                            if event.key == pygame.K_BACKSPACE:
                                if self.save_name == '':
                                    pass
                                else:
                                    self.save_name = self.save_name[:-2]
                        elif self.paused:
                            if event.key == pygame.K_ESCAPE:
                                self.paused = not self.paused
                            if event.key == pygame.K_q:
                                    self.running = False 

                            if event.key == pygame.K_RETURN:
                                self.paused = not self.paused
                                self.load_data(f"maps/{self.chng_lvl}.json")
                                self.chng_lvl = ''
                                self.update_display()
                            else:
                                self.chng_lvl +=chr(event.key)
                            
                            if event.key == pygame.K_BACKSPACE:
                                if self.chng_lvl == '':
                                    pass
                                else:
                                    self.chng_lvl = self.chng_lvl[:-2]
                        elif self.paused2:
                            if event.key == pygame.K_ESCAPE:
                                self.paused2 = not self.paused2
                             
    
                if event.type == pygame.MOUSEBUTTONUP:
                    if not self.saving:
                        if event.button == 1:
                            x,y = pygame.mouse.get_pos()
                            bid = str(randint(1,1000)) + str(self.player.boxs_placed) + "-box"
                            self.box_ids.append(bid)
                            self.hard_objects[self.room][bid] = [x-(self.box_size/2), y-(self.box_size/2), self.box_size, self.box_size]
                            self.player.boxs_placed +=1

                        if event.button == 3:
                            x,y = pygame.mouse.get_pos()
                            did = str(randint(1,1000)) + str(self.player.boxs_placed) + "-door"

                
            if not self.saving and not self.paused:
                mice = pygame.mouse.get_pressed() # this will get constant feed of input, instead of waiting in the event queue 
                keys = pygame.key.get_pressed()   # allowing the player to hold a button and the action will continue until they let go

                if mice[0]:
                    x,y = pygame.mouse.get_pos()
                    rect = pygame.draw.rect(self.level.screen, self.grey, [x-(self.box_size/2), y-(self.box_size/2), self.box_size, self.box_size])

                if keys[pygame.K_a]:
                    self.xgrav -= 1

                if keys[pygame.K_d]:
                    self.xgrav += 1

                if keys[pygame.K_LEFTBRACKET]:
                    self.box_size-=1
                
                if keys[pygame.K_RIGHTBRACKET]:
                    self.box_size+=1
                
                if keys[pygame.K_LCTRL] and keys[pygame.K_s]:
                    self.saving = True

                if keys[pygame.K_LSHIFT] and self.player.teleport:
                    x,y = pygame.mouse.get_pos()
                    if self.check_collision(x,y):
                        self.player.xpos = x
                        self.player.ypos = y

                self.run_physics()
                self.player.update_rect_data()
            self.level.update_map()
    
    def init_rooms(self, dic):
        for i in self.level.map_doors:
            dic[i] = {}

    def update_display(self):
        pygame.display.set_caption(f"LEVEL: {self.level.level_name} | USER: {self.player.name} | CHEATS: {self.cheats}")

    def display_physics_data(self):
        boxsz_txt = self.font.render(f"box_size: {self.box_size}", False, (255,0,0))
        grav_txt = self.font.render(f"gravity {self.ygrav}", False, (255,0,0))
        vel_txt = self.font.render(f"velocity {self.xgrav}", False, (255,0,0))
        movs_txt = self.font.render(f"max-vel {self.max_vel}", False, (255,0,0))
        fps_txt = self.font.render('FPS: {0:.8}'.format(self.clock.get_fps()), False, (255, 0, 0))
        mos_txt = self.font.render(f"mouse_xy {pygame.mouse.get_pos()}", False, (255, 0, 0))
        py_txt = self.font.render(f"player_xy {self.player.xpos, self.player.ypos}", False, (255, 0, 0))
        # con_txt = self.font.render(f"connected:{client.connection_status}", False, (255,0,0))

        self.level.screen.blit(boxsz_txt, (890,10))
        self.level.screen.blit(grav_txt, (890,30))
        self.level.screen.blit(vel_txt, (890,50))
        self.level.screen.blit(movs_txt, (890,70))
        self.level.screen.blit(fps_txt, (20, 10))
        self.level.screen.blit(mos_txt, (20, 30))
        self.level.screen.blit(py_txt, (20, 50))
        # self.level.screen.blit(con_txt, (20,10))
    
    def run_physics(self):
        if self.xgrav > 0:
            self.xgrav-= self.friction
        elif self.xgrav < 0:
            self.xgrav+= self.friction

        if self.xgrav > self.max_vel:
            self.xgrav = self.max_vel
        elif self.xgrav < -self.max_vel:
            self.xgrav= -self.max_vel

        if self.check_collision(0,self.ygrav):
            self.player.ypos+=self.ygrav
        else:
            self.player.jumps = 2

        if self.check_collision(self.xgrav,0):
            self.player.xpos+=self.xgrav
        

    def check_collision(self, xoff, yoff):
        tup = self.player_objects[self.player.name]
        # print(tup)
        rect = pygame.Rect((tup[0]+xoff, tup[1]+yoff), (self.player.player_size,self.player.player_size))

        collisions = 0

        for h in self.hard_rects:
            if h.colliderect(rect):
                collisions+=1
            else:
                pass

        for s in self.static_rects:
            if s.colliderect(rect):
                collisions+=1
            else:
                pass
        
        for g in self.goal_rects:
            if g.colliderect(rect):
                self.win_tick = pygame.time.get_ticks()
                self.display_tick = self.win_tick - self.last_win
                self.last_win = self.win_tick
                self.room = self.level.start_room
                self.player.xpos = self.level.player_spawn[0]
                self.player.ypos = self.level.player_spawn[1]
                self.win = True
                self.player.update_rect_data()
            else:
                pass
        
        try:
            for s in self.level.map_doors[self.room]:
                rect2 = pygame.Rect(self.level.map_doors[self.room][s]['loc'])
                if rect2.colliderect(rect):
                    self.player.xpos = self.level.map_doors[self.room][s]['out-loc'][0]
                    self.player.ypos = self.level.map_doors[self.room][s]['out-loc'][1]
                    self.room = self.level.map_doors[self.room][s]['to']
                    self.player.update_rect_data()
                    return False
                else:
                    pass
        except Exception as error:
            print(self.level.map_doors)
            raise error

        if collisions > 0:
            # self.player.jump = True
            return False
        else:
            return True

    def check_cooldowns(self, tick):
        if self.player.toj > self.player.jump_cooldown:
            if self.cooldown_calc(tick, self.player.toj, self.player.jump_cooldown):
                self.ygrav = -self.ygrav
                self.player.toj = 0

        if self.player.tot > self.player.teleport_cooldown:
            if self.cooldown_calc(tick, self.player.tot, self.player.teleport_cooldown):
                self.player.teleport = True
                self.player.tot = 0

        if self.player.top > self.player.place_obj_cooldown:
            if self.cooldown_calc(tick, self.player.top, self.player.place_obj_cooldown):
                self.player.place_obj = True
                self.player.top = 0
        
        if self.win:
            if self.cooldown_calc(tick, self.win_tick, self.win_cooldown):
                self.win = False

    def cooldown_calc(self, t1, t2, c):
        if t1 - t2 >= c:
            return True
        else:
            False

    def draw_rects_dict(self, dic, typ):
        #use dict for color selection
        if typ == 'p':
            color = self.player_colors[list(dic.keys())[0]]
        elif typ == 'h':
            color = self.grey
        elif typ == 's':
            color = self.black
        elif typ == 'd':
            color = self.purple
        elif typ == 'g':
            color = self.gold
        for i in dic:
            if typ == 'd':
                rect = pygame.draw.rect(self.level.screen, color, dic[i]['loc'])
            else:
                rect = pygame.draw.rect(self.level.screen, color, dic[i])

            if typ == 'p':
                self.player_rects.append(rect)
            elif typ == 'h':
                self.hard_rects.append(rect)
            elif typ == 's':
                self.static_rects.append(rect)
            elif typ == 'g':
                self.goal_rects.append(rect)

class Player(object):
    def __init__(self, name):
        self.spawn = True

        self.jumps = 2
        self.double_jump = False
        self.teleport = True
        self.place_obj = True

        self.jump_cooldown = 85 # 85
        self.teleport_cooldown = 0
        self.place_obj_cooldown = 0

        self.player_size = 10
        self.boxs_placed = 0
        self.color = (255,0,0)

        self.xpos = 0
        self.ypos = 0

        self.toj = 0 #time of jump
        self.tot = 0 #time of teleport
        self.top = 0 #time of place object

        self.rect_data = (self.xpos, self.ypos, self.player_size, self.player_size)

        self.name = name

        # self.vars = {'j':self.jump, 't':self.teleport, 'po':self.place_obj, 'ps':self.player_size}
    
    def update_rect_data(self):
        self.rect_data = (self.xpos, self.ypos, self.player_size, self.player_size)

class Map(object):
    def __init__(self, map_path):
        self.lvls = self.get_lvls()
        self.map_data = None
        self.static_objects =None
        self.map_doors = None
        self.player_spawn = None
        self.map_grav = None
        self.map_vel = None
        self.map_friction = None
        self.level_name = None
        self.start_room = None
        self.goal = None
        self.screen = None

        self.load_map(map_path)
    
    def update_map(self):
        pygame.display.flip()
        self.screen.fill(self.map_data['fill'])
    
    def aquire_map(self, map_path):
        map_data = json.load(open(map_path, "r"))
        return map_data
    
    def get_lvls(self):
        ls = []
        for i in os.listdir("./maps"):
            if '.json' in i: ls.append(i)
        return ls
    
    def load_map(self,map_path):
        self.map_data = self.aquire_map(map_path)
        self.static_objects = self.map_data['static-objs']
        self.map_doors = self.map_data['doors']
        self.player_spawn = self.map_data['spawn']
        self.map_grav = self.map_data['ygrav']
        self.map_vel = self.map_data['max_vel']
        self.map_friction = self.map_data['friction']
        self.level_name = self.map_data['level-name']
        self.start_room = self.map_data['start-room']
        self.goal = self.map_data['goal']
        self.screen = pygame.display.set_mode( (self.map_data['res']) )


if __name__ == "__main__":
    game = Game(True, 200)
    game.start_game("maps/def.json")
