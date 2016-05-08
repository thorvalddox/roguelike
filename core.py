import pygame
import numpy as np
import math
import time
from random import randrange
import json
from collections import namedtuple
from functools import partial

class Application():
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((480,320))
        pygame.display.set_caption("Roguelike")
        self.view_window = pygame.Surface((50*32,50*32))
        self.info_window = pygame.Surface((480,80))

        self.grid = Grid("grid.txt")
        self.entities = []
        self.graphics = GraphicsLoader()
        self.player = Creature(self,Player)
        self.player.lockscreen = True
        self.player.reveal_surroundings()
        self.entities.append(self.player)
        self.create_enemies(Skeleton,8)
        self.viewx = 0
        self.viewy = 0
        self.frame_rate=30
    def create_enemies(self,type_,amount=1):
        for _ in range(amount):
            e = Enemy(self,type_)
            self.entities.append(e)

    def on_key_press(self, symbol, modifiers):
        mod = modifiers%16
        movelist = (pygame.K_DOWN,pygame.K_LEFT,pygame.K_RIGHT,pygame.K_UP)
        skilllist = (pygame.K_SPACE,pygame.K_q,pygame.K_s,pygame.K_d)
        if symbol in movelist:
            self.player.start_move(movelist.index(symbol),bool(mod&1))
        if symbol in skilllist:
            self.player.append_command(1,skilllist.index(symbol))

    def on_key_release(self, symbol, modifiers):
        mod = modifiers%16
        movelist = (pygame.K_DOWN,pygame.K_LEFT,pygame.K_RIGHT,pygame.K_UP)
        skilllist = (pygame.K_SPACE,pygame.K_q,pygame.K_s,pygame.K_d)
        if symbol in movelist:
            self.player.stop_move(movelist.index(symbol))
        if symbol in skilllist:
            self.player.remove_command(1,skilllist.index(symbol))


    def on_draw(self):
        #self.screen.fill((127,127,255))
        #self.view_window.fill((255,255,255))
        self.grid.on_draw(self.view_window,32)
        for e in sorted(self.entities,key=lambda x:x.pos[1]):
            e.on_draw(self.view_window,32)
        self.screen.blit(self.view_window,(0,0),(self.viewx,self.viewy,480,240))
        self.screen.blit(self.grid.minimap,(380,220))
        pygame.display.flip()
    def animate(self, dt):
        for e in self.entities:
            e.do_frame(dt)
            sx,sy = self.player.pixel_pos()
            self.viewx,self.viewy = sx-240,sy-100
    def run(self):
        current_time = time.time()
        counter = 0
        total_time = 0
        while True:
            counter += 1
            pygame.event.pump()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                elif event.type == pygame.KEYDOWN:
                    self.on_key_press(event.key,event.mod)
                elif event.type == pygame.KEYUP:
                    self.on_key_release(event.key,event.mod)
            new_time = time.time()
            lost_time = new_time - current_time

            if counter%100:
                total_time += lost_time
            else:
                print("FPS:",100/total_time)
                total_time = 0

            if lost_time < 1/self.frame_rate:
                time.sleep(1/self.frame_rate-lost_time)


            current_time = new_time
            self.animate(lost_time)
            self.on_draw()
    def find_entity(self,position):
        for i in self.entities:
            if i.pos == position:
                return i
    def destroy_entity(self,target):
        self.entities.remove(target)


class GraphicsLoader():
    def __init__(self):
        self.graphs = {}
    def __call__(self,name):
        if name not in self.graphs:
            self.graphs[name] = Graphic(name)
        return self.graphs[name]






class Graphic:
    def __init__(self,filename):
        texture = pygame.image.load(filename+".png")
        try:
            alttexture = pygame.image.load(filename+"_Pose.png")
        except pygame.error:
            alttexture = texture
        w,h = texture.get_size()
        texture = pygame.transform.scale(texture,(210,(210*h)//w))
        alttexture = pygame.transform.scale(alttexture,(210,(210*h)//w))
        w,h = texture.get_size()
        self.width,self.height = w//3,h//4
        r = [(x*self.width,y*self.height,self.width,self.height) for y in range(4) for x in range(3)]
        self.textures = [pygame.Surface((self.width,self.height),flags=pygame.SRCALPHA) for _ in range(24)]
        for i,s in enumerate(r):

            self.textures[i].blit(texture,(0,0),s)
        for i,s in enumerate(r):
            self.textures[i+12].blit(alttexture,(0,0),s)
        del texture
        del alttexture
    def __getitem__(self, item):
        return self.textures[item]

    def draw(self,dest,x,y,direction,pose,frame):
        dest.blit(self.textures[pose*12+direction*3+frame],(x,y))

class Entity:
    #0=down,1=left,2=up,3=right
    def __init__(self,parent,image):

        self.lockscreen = False
        self.grid = parent.grid
        self.graph = image
        self.pos = (randrange(self.grid.width-8)+4,randrange(self.grid.height-8)+4)
        self.set_pos(self.pos)
        while not self.grid.data[self.pos] == 1:
            self.set_pos((randrange(self.grid.width-8)+4,randrange(self.grid.height-8)+4))
        print(self.pos)
        self.direction = 0
        self.movement = 0
        self.cooldown = 0
        self.speed = 4 #squares/second
        self.command_queue = []
        self.passable_tiles = (0,1)


    def move_animation_frame(self):
        return [1,2,1,0][((math.floor(self.movement)//16)+2*(self.pos[0]+self.pos[1]))%4]
    def relative_movement_pos(self,dir=...,dist=...):
        if dist is ...:
            dist = self.movement
        if dir is ...:
            dir = self.direction
        dist = int(math.floor(dist))
        if dir==0:
            return 0,dist
        elif dir == 1:
            return -dist,0
        elif dir == 3:
            return 0,-dist
        elif dir == 2:
            return dist,0
    def on_draw(self,dest,size):
        if not self.visible():
            return
        x,y = self.pixel_pos(size)
        if self.lockscreen:
            pass
        if self.cooldown <= 0:
            self.graph.draw(dest, x, y,self.direction,0,self.move_animation_frame())
        else:
            self.graph.draw(dest, x, y,self.direction,1,0)
    def moveto_square(self,direction):
        return tuple(old+rel for old,rel in zip(self.pos,self.relative_movement_pos(direction,1)))
    @property
    def target_square(self):
        return self.moveto_square(self.direction)
    def pixel_pos(self,size=32):
        return tuple(old*size -size//2 - size//2*parr+rel for old,rel,parr in zip(self.pos,self.relative_movement_pos(),(0,1)))
    def move_skip(self,dt):
        self.movement += dt*self.speed*32
    def move(self,dt):
        if self.move_valid():
            self.reserve(True)
            self.move_skip(dt)
        else:
            self.stop()

    def move_valid(self,direction=...):
        if direction is ...:
            direction = self.direction
        if not self.grid.passable(self,*self.moveto_square(direction)):
            return False
        elif self.grid.occupied[self.moveto_square(direction)]:
            return False
        else:
            return True
    @property
    def stopped(self):
        return self.movement == 0
    def stop(self):
        self.movement = 0
    def get_command(self): #overload this function to make AI-controlled monsters
        """
        Overload this function to create AI monsters

        This returns a generator containing commands
        The commands are tuples with the following structure:
         (command, arg1,arg2, ...)
        command = 0:
            moves the target in a given direction
            arg1: direction (DOWN,LEFT,RIGHT,UP) = (0,1,2,3)
            arg2: locked
        command = 1:
            uses a skill
            arg1: skill index
            arg2: direction
        :return:
        """
        yield from self.command_queue
    def handle_command(self,dt):
        for next_command in self.get_command():
            command,*args = next_command
            if command==0:
                self.direction,locked = args
                if not locked and self.move_valid():

                    self.move(dt)
                    return
            elif command==1:
                index, = args
                self.use_skill(index)
                return
    def do_frame(self,dt):
        if self.cooldown > 0:
            self.cooldown -= dt
            return
        else:
            self.cooldown = 0
        if self.stopped:
            self.handle_command(dt)
        else:
            self.move_skip(dt)


        if self.movement > 32:
            self.set_pos(self.target_square)
            self.stop()
            if self.command_queue and self.direction in [x[1] for x in self.command_queue if x[0]==0]:
                self.move(dt)
    def start_move(self,direction,locked=False):
        self.append_command(0,direction,locked)
    def stop_move(self,direction):
        self.remove_command(0,direction,...)
    def append_command(self,command,*args):
        self.command_queue.append((command,)+args)
    def remove_command(self,command,*args):
        """
        Removes a command from the queue
        :param command:
        :param args: Use Ellipsys ... to set wildcards
        :return:
        """
        self.command_queue = [x for x in self.command_queue \
                              if not(x[0] == command and all(a in (b,...) for a,b in zip(args,x[1:])))]
    def reserve(self,occupy):
        self.grid.occupied[self.target_square] = occupy
    def set_pos(self,newpos):
        self.grid.occupied[self.pos] = 0
        self.grid.occupied[newpos] = 1
        self.pos = newpos
        if self.lockscreen:
            self.reveal_surroundings()
    def reveal_surroundings(self,dist=2):
        w,h = self.grid.data.shape
        for x in range(w):
            for y in range(h):
                self.grid.hide(x,y)
        x,y = self.pos
        for i in range(-dist,dist+1):
            for j in range(-dist,dist+1):
                self.grid.discover(x+i,y+j)
    def visible(self):
        return self.grid.fogofwar[self.pos] or self.grid.fogofwar[self.target_square]
    def wait(self,seconds):
        self.cooldown = seconds
    def use_skill(self,index):
        pass


Creature_stats = namedtuple('Creature_stats','face,health,damage')

Player = Creature_stats("Soldier_5",100,5)
Skeleton = Creature_stats("Skeleton",20,2)

class Creature(Entity):
    def __init__(self,parent,stats):
        Entity.__init__(self,parent,parent.graphics(stats.face))
        self.radar = parent.find_entity
        self.destroy = partial(parent.destroy_entity,self)
        self.health = stats.health
        self.maxhealth = stats.health
        self.damage = stats.damage

        self.skills = [(True,self.attack,0.7)] #Tuples: (active,method,cooldown)
    def see(self,direction):
        return(self.radar(self.moveto_square(direction)))
    def apply_damage(self,amount):
        self.health -= amount
        if self.health <= 0:
            self.die()
    def die(self):
        if self.lockscreen:
            print("The end")
            #to be fixed to display game over
        else:
            self.destroy()
            self.grid.occupied[self.pos] = False
    def attack(self):
        target = self.see(self.direction)
        if target and isinstance(target,Creature):
            target.apply_damage(self.damage)
            return True
        return False
    def use_skill(self,index):
        active,method,cooldown = self.skills[index]
        if active:
            if method():
                self.wait(cooldown)
    def on_draw(self,dest,size):
        if self.visible():
            x,y = self.pixel_pos(size)
            dest.fill((255,0,0),(x+35-size//2,y-4,size,4))
            dest.fill((0,255,0),(x+35-size//2,y-4,(size*self.health)//self.maxhealth,4))
            if self.cooldown > 0:
                dest.fill((127,127,127),(x+35-size//2,y,size,4))
                dest.fill((0,0,255),(x+35-size//2,y,(size*(2-self.cooldown))//2,4))
        Entity.on_draw(self,dest,size)



class Enemy(Creature):
    def __init__(self,parent,image):
        Creature.__init__(self,parent,image)
        self.target = parent.player
        self.speed = 2

    def get_command(self):
        for i in range(4):
            target = self.see(i)

            if target and target.lockscreen:
                if i != self.direction:
                    yield (0,i,1)
                yield (1,0)
        priordict = {k:self.get_moves_priority(k)  for k in range(4) if self.move_valid(k)}
        if not priordict:
            return None
        best_dirs = sorted(priordict.keys(),key=priordict.get)
        yield from ((0,b,0) for b in best_dirs)


    def get_moves_priority(self,direction):
        target = self.moveto_square(direction)
        x,y = target
        px,py = self.target.pos
        return math.sqrt((x-px)*(x-px)+(y-py)*(y-py))






TILES = "dungeon_storeroom_main.png;volcanic.png"


class Texturemap_loader:
    def __init__(self):
        with open("textures.json") as file:
            self.textures = json.load(file)
        self.tiles = [pygame.image.load(x) for x in TILES.split(";")]

    def add_texture(self,pack,name,dest,x,y):
        for tex,cx,cy in self.textures[pack][name]:
            dest.blit(self.tiles[tex],(x*32,y*32),(cx*32,cy*32,32,32))


class Grid:
    def __init__(self,filename):
        self.texturer = Texturemap_loader()
        self.cover_texture = pygame.Surface((32,32),flags=pygame.SRCALPHA)
        self.cover_texture.fill((0,0,0,191))
        import maze_gen
        self.data = maze_gen.genRoomField(10,5)
        width,height = self.data.shape
        self.occupied = np.zeros((width,height),np.int8)
        self.fogofwar = np.zeros((width,height),np.int8)

        self.texture_map = pygame.Surface((width*32,height*32))
        self.visible_map = pygame.Surface((width*32,height*32))
        self.texture_map.fill((0,255,255))
        self.visible_map.fill((0,0,0))
        self.minimap = pygame.Surface((100,100))
        it = np.nditer(self.data, flags=['multi_index'])
        #colors = [arcade.color.WHITE,arcade.color.RED]
        size = 32
        while not it.finished:
            c,(x,y) = it[0],it.multi_index
            tex = "walkable"
            if c == 0:
                tex = "walkable"
            elif c==1:
                tex = "room"
            elif c==2:
                try:
                    conn_index = (not self.wall(x,y-1))*4 + any(not self.wall(x-1,y+n) for n in range(3))*2\
                                 + any(not self.wall(x+1,y+n) for n in range(3))
                    tex = ["wall","wall_l","wall_r","wall_lr","wall_u","wall_ul","wall_ur","wall_ulr"][conn_index]


                    if not (self.wall(x,y+1) or self.wall(x,y-1)) or \
                       not (self.wall(x,y+1) or self.wall(x,y-2)) or \
                       not (self.wall(x,y+2) or self.wall(x,y-1)):
                        tex = "boulder"

                    elif not self.wall(x,y+1):
                        self.data[x,y] = 3
                        tex = "wall2"
                    elif not self.wall(x,y+2):
                        self.data[x,y] = 3
                        tex = "wall1"


                except IndexError:
                    tex = "wall"
            elif c==4:
                if self.data[x,y-1] == 4:
                    tex = "cliff"
                else:
                    tex = "cliff1"
            elif c==5:
                if self.data[x,y-1] == 5:
                    tex = "water"
                else:
                    tex = "water1"
            #print(x,y,c)
            #arcade.draw_rectangle_filled(x*size+size//2, y*size+size//2, size, size, colors[c])
            self.texturer.add_texture("default",tex,self.texture_map,x,y)
            it.iternext()
        self.width,self.height = width,height
    def on_draw(self,dest,size):
        dest.fill((0,255,0))
        dest.blit(self.visible_map,(0,0))
    def passable(self,entity,x,y):
        return self.data[x,y] in entity.passable_tiles
    def wall(self,x,y):
        return self.data[x,y] in (2,3)
    def discover(self,x,y):
        if self.fogofwar[x,y]:
            return
        self.fogofwar[x,y] = True
        self.visible_map.blit(self.texture_map,(x*32,y*32),(x*32,y*32,32,32))
        try:
            color = [(255,255,255),(255,255,255)][self.data[x,y]]
        except IndexError:
            color = (0,0,0)
        self.minimap.fill(color,(x*2,y*2,2,2))
        if self.data[x,y] == 1:
            for i in (-1,0,1):
                for j in (-1,0,1):
                    self.discover(x+i,y+j)
        if self.data[x,y] == 3:
            for i in (-1,):
                self.discover(x,y+i)
    def hide(self,x,y):
        if not self.fogofwar[x,y]:
            return
        self.fogofwar[x,y] = False
        self.visible_map.blit(self.cover_texture,(x*32,y*32))




def extract_ground_tile(filename):
    texture =  pygame.image.load(filename+".png")
    texture2 = pygame.Surface((32,32))
    texture2.blit(texture,(0,0),(16,48,32,32))
    del texture
    return texture2





def main():

    window = Application()
    window.run()

if __name__ == "__main__":
    main()





