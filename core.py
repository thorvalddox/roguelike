import pygame
import numpy as np
import math
import time
from random import randrange

class Application():
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((480,320))
        self.view_window = pygame.Surface((50*32,50*32))
        self.info_window = pygame.Surface((480,80))

        self.grid = Grid("grid.txt")
        self.entities = []
        self.graphics = GraphicsLoader()
        self.player = Entity(self.grid,self.graphics("Soldier_5"),(8,8))
        self.player.lockscreen = True
        self.player.reveal_surroundings()
        self.entities.append(self.player)
        self.viewx = 0
        self.viewy = 0
        self.frame_rate=30
    def on_key_press(self, symbol, modifiers):
        mod = modifiers%16
        if symbol == pygame.K_UP:
            self.player.start_move(3,mod&1)
        elif symbol == pygame.K_DOWN:
            self.player.start_move(0,mod&1)
        elif symbol == pygame.K_LEFT:
            self.player.start_move(1,mod&1)
        elif symbol == pygame.K_RIGHT:
            self.player.start_move(2,mod&1)
    def on_key_release(self, symbol, modifiers):
        mod = modifiers%16
        if symbol == pygame.K_UP:
            self.player.stop_move(3)
        elif symbol == pygame.K_DOWN:
            self.player.stop_move(0)
        elif symbol == pygame.K_LEFT:
            self.player.stop_move(1)
        elif symbol == pygame.K_RIGHT:
            self.player.stop_move(2)

    def on_draw(self):
        #self.screen.fill((127,127,255))
        #self.view_window.fill((255,255,255))
        self.grid.on_draw(self.view_window,32)
        for e in self.entities:
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
        w,h = texture.get_size()
        texture = pygame.transform.scale(texture,(210,(210*h)//w))
        w,h = texture.get_size()
        self.width,self.height = w//3,h//4
        r = [(x*self.width,y*self.height,self.width,self.height) for y in range(4) for x in range(3)]

        self.textures = [pygame.Surface((self.width,self.height),flags=pygame.SRCALPHA) for _ in range(12)]
        for i,s in enumerate(r):

            self.textures[i].blit(texture,(0,0),s)
        del texture
    def __getitem__(self, item):
        return self.textures[item]

    def draw(self,dest,x,y,index):
        dest.blit(self.textures[index],(x,y))

class Entity:
    #0=down,1=left,2=up,3=right
    def __init__(self,grid,image,AI=False):
        self.lockscreen = False
        self.AI = AI
        self.grid = grid
        self.graph = image
        self.pos = (randrange(grid.width-8)+4,randrange(grid.height-8)+4)
        self.set_pos(self.pos)
        while not self.grid.data[self.pos] == 1:
            self.set_pos((randrange(grid.width-8)+4,randrange(grid.height-8)+4))
        print(self.pos)
        self.direction = 0
        self.movement = 0
        self.speed = 4 #squares/second
        self.command_queue = []


    def move_animation_frame(self):
        return [1,2,1,0][((math.floor(self.movement)//16)+2*(self.pos[0]+self.pos[1]))%4]
    def relative_movement_pos(self,dist=...):
        if dist == ...:
            dist = self.movement
        dist = int(math.floor(dist))
        if self.direction==0:
            return 0,dist
        elif self.direction == 1:
            return -dist,0
        elif self.direction == 3:
            return 0,-dist
        elif self.direction == 2:
            return dist,0
    def on_draw(self,dest,size):
        x,y = self.pixel_pos(size)
        if self.lockscreen:
            pass
        self.graph.draw(dest, x, y,self.move_animation_frame()+3*self.direction)
    @property
    def target_square(self):
        return tuple(old+rel for old,rel in zip(self.pos,self.relative_movement_pos(1)))
    def pixel_pos(self,size=32):
        return tuple(old*size -size//2 - size//2*parr+rel for old,rel,parr in zip(self.pos,self.relative_movement_pos(),(0,1)))
    def move_skip(self,dt):
        self.movement += dt*self.speed*32
        if self.lockscreen:
            sx,sy = self.pixel_pos()
            #arcade.window_commands.set_viewport(sx-240,sx+240,sy-200,sy+120)

    def move(self,dt):
        if self.move_valid():
            self.move_skip(dt)
    def move_valid(self):
        if not self.grid.passable(*self.target_square):
            return False
        elif self.grid.occupied[self.target_square]:
            return False
        else:
            return True
    @property
    def stopped(self):
        return self.movement == 0
    def stop(self):
        self.movement = 0
    def get_command(self): #overload this function to make AI-controlled monsters
        if self.command_queue:
            return self.command_queue[0]
    def do_frame(self,dt):
        if self.stopped:
            next_command = self.get_command()
            if next_command:
                self.direction,locked = next_command
                if not locked:
                    self.move(dt)
        else:
            self.move(dt)


        if self.movement > 32:
            self.set_pos(self.target_square)
            self.stop()
            if self.command_queue and self.direction in list(zip(*self.command_queue))[0]:
                self.move(dt)
    def start_move(self,direction,locked=False):
        self.command_queue.append((direction,bool(locked)))
    def stop_move(self,direction):
        self.command_queue = [x for x in self.command_queue if x[0]!= direction]
    def set_pos(self,newpos):
        self.grid.occupied[self.pos] = 0
        self.grid.occupied[newpos] = 1
        self.pos = newpos
        if self.lockscreen:
            self.reveal_surroundings()
    def reveal_surroundings(self,dist=2):
        x,y = self.pos
        for i in range(-dist,dist+1):
            for j in range(-dist,dist+1):
                self.grid.discover(x+i,y+j)





class Grid:
    def __init__(self,filename):
        self.tiles = pygame.image.load("dungeon_storeroom_main.png")
        import maze_gen
        self.data = maze_gen.genRoomField(10,5)
        width,height = self.data.shape
        self.occupied = np.zeros((width,height),np.int8)
        self.fogofwar = np.zeros((width,height),np.int8)

        self.texture_map = pygame.Surface((width*32,height*32))
        self.visible_map = pygame.Surface((width*32,height*32))
        self.texture_map.fill((0,255,255))
        self.visible_map.fill((127,127,127))
        self.minimap = pygame.Surface((100,100))
        it = np.nditer(self.data, flags=['multi_index'])
        #colors = [arcade.color.WHITE,arcade.color.RED]
        size = 32
        while not it.finished:
            c,(x,y) = it[0],it.multi_index
            if c == 0:
                arr = 1,9
            elif c==1:
                arr = 4,4
            elif c==2:
                try:
                    conn_index = (not self.wall(x,y-1))*4 + any(not self.wall(x-1,y+n) for n in range(3))*2\
                                 + any(not self.wall(x+1,y+n) for n in range(3))
                    arr = [(1,5),(0,12),(2,7),(5,7),(1,4),(2,4),(0,4),(3,4)][conn_index]

                    if not (self.wall(x,y+1) or self.wall(x,y-1)) or \
                       not (self.wall(x,y+1) or self.wall(x,y-2)) or \
                       not (self.wall(x,y+2) or self.wall(x,y-1)):
                        self.data[x,y] = 0
                        arr = 1,9

                    elif not self.wall(x,y+1):
                        self.data[x,y] = 3
                        arr = 1,8
                    elif not self.wall(x,y+2):
                        self.data[x,y] = 3
                        arr= 1,6


                except IndexError:
                    arr = 1,5
            #print(x,y,c)
            #arcade.draw_rectangle_filled(x*size+size//2, y*size+size//2, size, size, colors[c])
            cx,cy = arr
            self.texture_map.blit(self.tiles,(x*size,y*size),(cx*32,cy*32,32,32))
            it.iternext()
        self.width,self.height = width,height
    def on_draw(self,dest,size):
        dest.fill((0,255,0))
        dest.blit(self.visible_map,(0,0))
    def passable(self,x,y):
        return self.data[x,y] in (0,1)
    def wall(self,x,y):
        return self.data[x,y] in (2,3)
    def discover(self,x,y):
        if self.fogofwar[x,y]:
            return
        self.fogofwar[x,y] = True
        self.visible_map.blit(self.texture_map,(x*32,y*32),(x*32,y*32,32,32))
        color = [(255,255,255),(127,255,255),(0,0,0),(0,0,0)][self.data[x,y]]
        self.minimap.fill(color,(x*2,y*2,2,2))
        if self.data[x,y] == 1:
            for i in (-1,0,1):
                for j in (-1,0,1):
                    self.discover(x+i,y+j)
        if self.data[x,y] == 3:
            for i in (-1,1):
                self.discover(x,y+i)




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
    import cProfile
    cProfile.run('main()',"profile")




