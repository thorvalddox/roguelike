#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Thorvald
#
# Created:     22/07/2014
# Copyright:   (c) Thorvald 2014
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import numpy as np
import random

from itertools import product


def outwardSpiral(size):
    x,y = size//2,size//2
    yield x,y
    for dist in range(size):
        if dist%2:
            for _ in range(dist):
                x -= 1
                yield x,y
            for _ in range(dist):
                y-= 1
                yield x,y
        else:
            for _ in range(dist):
                x += 1
                yield x,y
            for _ in range(dist):
                y += 1
                yield x,y
    if size%2:
        for _ in range(size-1):
            x -= 1
            yield x,y
    else:
        for _ in range(size-1):
            x += 1
            yield x,y

def allborders(n,size):
    for i in n:
        for j in border(i,size):
            if not j in n:
                yield j



def growth(size):
    s = [(size//2,size//2)]
    yield s[0]
    Q = list(allborders(s,size))
    while Q:
        new = random.choice(Q)
        yield new
        s.append(new)
        Q = list(allborders(s,size))

def printgrowth(size):
    DIR = {}
    for i,n in enumerate(growth(size)):
        DIR[n] = i
    for x,y in product(range(size),repeat=2):
        if y==0:
            print(" ")
        try:
            print("{:>2} ".format(DIR[(x,y)]),end="")
        except KeyError:
            print("   ",end="")


def border(point,maxsize):
    x,y = point
    for rx,ry in ((-1,0),(1,0),(0,-1),(0,1)):
        nx,ny = x+rx,y+ry
        if not set((nx,ny)) & set((-1,maxsize)):
            yield nx,ny

def borderC(point1,point2):
    x1,y1 = point1
    x2,y2 = point2
    xb,yb = min(x1,x2),min(y1,y2)
    assert abs(x1-x2) + abs(y1-y2) == 1,"{},{} and {},{} don't border".format(x1,y1,x2,y2)
    t = abs(x1-x2) + 2*abs(y1-y2)
    return((xb,yb),t)

def genPath(size):
    """generates a numpy array of ints representing a maze
    0 = no path
    1 = path to right
    2 = path to bottom
    3 = path to right and bottom
    4+ important path to right
    8+ important path to bottom
    """
    s = np.array([[0]*size for _ in range(size)],np.bool)
    ret = np.array([[0]*size for _ in range(size)],np.int8)

    for x,y in growth(size):
        s[x,y] = True
        l = [(xb,yb) for xb,yb in border((x,y),size) if s[xb,yb]]
        if not l:
            continue
        conn = random.choice(l)
        (xn,yn),t = borderC(conn,(x,y))
        ret[xn,yn] = (t*0b101) | ret[xn,yn]
        if random.randrange(4):
            l = [(xb,yb) for xb,yb in border((x,y),size)]
            conn = random.choice(l)
            (xn,yn),t = borderC(conn,(x,y))
            ret[xn,yn] = t | ret[xn,yn]

    return(ret)


def draw_path(path):
    w,h = path.shape
    for y in range(h):
        l1 = []
        l2 = []
        for x in range(w):
            data = path[x,y]
            if 1 & data:
                l1.append("+--")
            else:
                l1.append("+  ")
            if 2 & data:
                l2.append("|  ")
            else:
                l2.append("   ")
        print("".join(l1))
        print("".join(l2))


def genRooms(maxsize,amsize,obl):
    """gives back a 3d array. The first to indices give to position, the last gives
        the data with resp (x1,y1,x2,y2)
        """
    ret = np.zeros((amsize,amsize,4), dtype=np.int32)

    for x,y in product(range(amsize),repeat=2):
        if random.random()<0.4 or obl[x,y]:
            x1 = random.randrange(2,maxsize//2-1)
            y1 = random.randrange(2,maxsize//2-1)
            x2 = random.randrange(maxsize//2+1,maxsize-2)
            y2 = random.randrange(maxsize//2+1,maxsize-2)
        else:
            x1 = random.randrange(2,maxsize-2)
            y1 = random.randrange(2,maxsize-2)
            x2 = x1
            y2 = y1
        ret[x,y,:] = (x1+x*maxsize,y1+y*maxsize,x2+x*maxsize,y2+y*maxsize)
    return(ret)

def genConn(size,rooms,paths):
    ret = np.zeros((size,size,2,6))
    draw_path(paths)
    for x,y in product(range(size),repeat=2):
        nx,ny = x+1,y+1
        if nx < size and 1 & paths[x,y]:
            lx1,ly1,lx2,ly2 = rooms[x,y,:]
            rx1,ry1,rx2,ry2 = rooms[nx,y,:]
            lst = random.randrange(ly1,ly2+1)
            rst = random.randrange(ry1,ry2+1)
            kn = random.randrange(lx2+2,rx1-1)
            ret[x,y,0,:] = lx2+1,rx1-1,lst,rst,kn,bool(4&paths[x,y])
        if ny < size and 2 & paths[x,y]:
            tx1,ty1,tx2,ty2 = rooms[x,y,:]
            bx1,by1,bx2,by2 = rooms[x,ny,:]
            tst = random.randrange(tx1,tx2+1)
            bst = random.randrange(bx1,bx2+1)
            kn = random.randrange(ty2+2,by1-1)
            ret[x,y,1,:] = ty2+1,by1-1,tst,bst,kn,bool(8&paths[x,y])
    return ret


def genObl(size,conn):
    s = np.ones((size,size),dtype=np.bool)
    for (x,y) in product(range(size),repeat=2):
        counter = 0
        if conn[x,y] & 1: counter+= 1
        if conn[x,y] & 2: counter+= 1
        if x>0 and conn[x-1,y] & 1:counter += 1
        if y>0 and conn[x,y-1] & 2:counter += 1
        if counter > 1:
            s[x,y] = 0
    return(s)


def genRoomField(maxsize,amsize):
    path = genPath(amsize)
    rooms = genRooms(maxsize,amsize,genObl(amsize,path))
    s = np.ones((amsize*maxsize,amsize*maxsize),dtype=np.int8)*2
    #ROOMS
    for x,y in product(range(amsize),repeat=2):
        x1,y1,x2,y2 = rooms[x,y,:]
        t,l,b,r = x1,y1,x2+1,y2+1
##        for (i,j) in product(range(x1,x2+1),range(y1,y2+1)):
##            s[i+maxsize*x,j+maxsize*y] = 0
        if (x1,y1) == (x2,y2):
            s[t:b,l:r] = 0
        else:
            s[t:b,l:r] = 1
    conn = genConn(amsize,rooms,path)

    #HORIZ PATHS
    for x,y in product(range(amsize),range(amsize)):

        lconn,rconn,lst,rst,Hkn,Rec = conn[x,y,0,:]
        if (lst,rst,Hkn) == (0,0,0):
            continue
        conntype = 0 if Rec else random.randrange(3)
        mst,hst = sorted((lst,rst))
        if conntype == 0:
            s[lconn:Hkn+1,lst] = 0
            s[Hkn:rconn+1,rst] = 0
            s[Hkn,mst:hst+1] = 0
        elif conntype == 1:
            s[lconn:rconn+1,mst:hst+1] = 5
        elif conntype == 2:
            s[lconn:rconn+1,mst:hst+1] = 0
            s[Hkn,mst:hst+1] = 4
        elif conntype == 3:
            s[lconn:rconn+1,mst:hst+1] = 0
    #VERT PATHS
    for x,y in product(range(amsize),range(amsize)):
        tconn,bconn,tst,bst,Vkn,Rec = conn[x,y,1,:]
        if (tst,bst,Vkn) == (0,0,0):
            continue
        conntype = 0 if Rec else random.randrange(3)
        mst,hst = sorted((tst,bst))
        if conntype == 0:
            s[tst,tconn:Vkn+1] = 0
            s[bst,Vkn:bconn+1] = 0
            s[mst:hst+1,Vkn] = 0
        elif conntype == 1:
            s[mst:hst+1,tconn:bconn+1] = 5
        elif conntype == 2:
            s[mst:hst+1,tconn:bconn+1] = 0
            s[mst:hst+1,Vkn] = 4
        elif conntype == 3:
            s[mst:hst+1,tconn:bconn+1] = 0

    return(s)



def roomsToFile(s):
    w,h = s.shape
    fff = open("grid.txt","w")
    for y in range(h):
        l1 = []
        for x in range(w):
            l1.append("*+  v~"[s[x,y]])
        fff.write("".join(l1)+"\n")


def main():
##    print(list(border((1,1),4)))
##    print(draw_path(genPath(4)))
    print(roomsToFile(genRoomField(10,4)))
##    printgrowth(4)
##    print(list(allborders([(0,1),(0,2),(3,4)],5)))

if __name__ == '__main__':
    main()