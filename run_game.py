import ctypes
import contextlib
import math
import os
import pygame
import sys
from OpenGL.GL import *

WIDTH, HEIGHT = 800, 600

def Light(radius, height, strength):
  r2 = float(radius * radius)
  h2 = float(height * height)
  data = ''
  if os.path.exists('light.data'):
    with file('light.data') as f:
      data = f.read()
  if len(data) != 3 * 1024 * 1024:
    data = (ctypes.c_char * (3 * 1024 * 1024))()
    i = 0
    for x in range(1024):
      x -= 512
      for y in range(1024):
        y -= 512
        d2 = h2 + x * x + y * y
        e2 = d2 - r2
        alpha = math.atan(math.sqrt(r2 / e2)) * 2 / math.pi
        c = chr(max(0, min(255, int(strength * 255 * alpha * alpha))))
        data[i * 3] = c
        data[i * 3 + 1] = c
        data[i * 3 + 2] = c
        i += 1
    with file('light.data', 'wb') as f:
      f.write(data)
  tex = glGenTextures(1)
  glBindTexture(GL_TEXTURE_2D, tex)
  glTexParameter(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
  glTexParameter(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
  glTexParameter(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
  glTexParameter(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
  glTexParameter(GL_TEXTURE_2D, GL_GENERATE_MIPMAP, GL_FALSE)
  glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, 1024, 1024, 0, GL_RGB, GL_UNSIGNED_BYTE, data)
  return tex


def Circle(radius):
  glBegin(GL_TRIANGLE_FAN)
  glVertex2d(0, 0)
  for i in range(61):
    glVertex2d(radius * math.cos(math.pi * i / 30), radius * math.sin(math.pi * i / 30))
  glEnd()


def Quad(width, height):
  glBegin(GL_TRIANGLE_STRIP)
  glTexCoord2d(0, 0)
  glVertex2d(-0.5 * width, -0.5 * height)
  glTexCoord2d(1, 0)
  glVertex2d(0.5 * width, -0.5 * height)
  glTexCoord2d(0, 1)
  glVertex2d(-0.5 * width, 0.5 * height)
  glTexCoord2d(1, 1)
  glVertex2d(0.5 * width, 0.5 * height)
  glEnd()


@contextlib.contextmanager
def Buffer(buf):
  glBindFramebuffer(GL_FRAMEBUFFER, buf)
  glViewport(0, 0, WIDTH * 2, HEIGHT * 2)
  yield
  glBindFramebuffer(GL_FRAMEBUFFER, 0)
  glViewport(0, 0, WIDTH, HEIGHT)


def Collision(buf, phi, r, radius):
  x = r * math.cos(phi)
  y = r * math.sin(phi)
  glBindFramebuffer(GL_FRAMEBUFFER, buf)
  p = glReadPixels(x * 2 + WIDTH - radius, y * 2 + HEIGHT - radius, radius, radius, GL_RED, GL_UNSIGNED_BYTE)
  glBindFramebuffer(GL_FRAMEBUFFER, 0)
  return any(c != '\0' for c in p)


class Game(object):

  def __init__(self):
    self.x = 0
    self.y = 200
    self.vx = 0
    self.vy = 0

  def Loop(self):
    pygame.init()
    pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 1)
    pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 4)
    pygame.display.set_caption('Satellite Taxi')
    pygame.display.set_mode((WIDTH, HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF | pygame.HWSURFACE)
    glViewport(0, 0, WIDTH, HEIGHT)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glScale(2./WIDTH, 2./HEIGHT, 1)
    glMatrixMode(GL_MODELVIEW)
    bg_tex = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, bg_tex)
    glTexParameter(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameter(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameter(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
    glTexParameter(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
    glTexParameter(GL_TEXTURE_2D, GL_GENERATE_MIPMAP, GL_FALSE)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, WIDTH * 2, HEIGHT * 2, 0, GL_RGB, GL_UNSIGNED_BYTE, None)
    background = glGenFramebuffers(1)
    with Buffer(background):
      glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, bg_tex, 0)
      glClear(GL_COLOR_BUFFER_BIT)
      Circle(100)
    light = Light(20, 100, 50)
    clock = pygame.time.Clock()
    while True:
      clock.tick(60)
      for e in pygame.event.get():
        if e.type == pygame.QUIT or e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
          pygame.quit()
          sys.exit(0)
      pressed = pygame.key.get_pressed()
      if pressed[pygame.K_LEFT]:
        self.vx -= 10. / self.y
      if pressed[pygame.K_RIGHT]:
        self.vx += 10. / self.y
      if pressed[pygame.K_DOWN]:
        self.vy -= 0.1
      if pressed[pygame.K_UP]:
        self.vy += 0.1
      self.vy -= 0.02
      self.vx *= 0.99
      self.vy *= 0.99
      self.x += self.vx
      self.y += self.vy
      if Collision(background, self.x, self.y, 1):
        print 'crash!', clock.get_fps()
        sys.exit(0)
      glClear(GL_COLOR_BUFFER_BIT)
      glLoadIdentity()
      glEnable(GL_TEXTURE_2D)
      glBindTexture(GL_TEXTURE_2D, bg_tex)
      Quad(WIDTH, HEIGHT)
      glDisable(GL_TEXTURE_2D)
      glRotatef(self.x, 0, 0, -1)
      glTranslatef(0, self.y, 0)
      Quad(30, 8)
      glTranslatef(0, 8, 0)
      Quad(16, 8)
      pygame.display.flip()

if __name__ == '__main__':
  Game().Loop()
