#!/usr/bin/env python
# encoding: utf-8
"""
mutliwin

Created by See-ming Lee on 2011-11-01.
Copyright (c) 2011 See-ming Lee. All rights reserved.
"""
import pyglet
from pyglet.gl import *

def on_resize(width, height):
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60., width / float(height), 1., 100.)
    glMatrixMode(GL_MODELVIEW)

def setup():
    glClearColor(1, 1, 1, 1)
    glColor3f(.5, .5, .5)

def on_draw():
    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()
    glTranslatef(0, 0, -5)
    glRotatef(r, 0, 0, 1)
    glRectf(-1, -1, 1, 1)

r = 0
def update(dt):
    global r
    r += 1
    if r > 360:
        r = 0
pyglet.clock.schedule_interval(update, 1/20.)

wins = []

for i in range(10):
    side = 200+i*20
    win = pyglet.window.Window(side, side, caption="window %d" % i, resizable=True)
    win.on_resize = on_resize
    win.o_draw = on_draw
    win.switch_to()
    setup()
    wins.append(win)



pyglet.app.run()