import ctypes
import contextlib
import math
import os
import pygame
import random
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
  segments = radius * 5
  for i in range(segments + 1):
    glVertex2d(radius * math.cos(math.pi * 2 * i / segments), radius * math.sin(math.pi * 2 * i / segments))
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


def Length(x, y):
  return math.sqrt(x * x + y * y)


@contextlib.contextmanager
def Buffer(buf):
  glBindFramebuffer(GL_FRAMEBUFFER, buf)
  glViewport(0, 0, WIDTH * 2, HEIGHT * 2)
  yield
  glBindFramebuffer(GL_FRAMEBUFFER, 0)
  glViewport(0, 0, WIDTH, HEIGHT)


@contextlib.contextmanager
def Texture(tex):
  glEnable(GL_TEXTURE_2D)
  glBindTexture(GL_TEXTURE_2D, tex)
  yield
  glDisable(GL_TEXTURE_2D)


@contextlib.contextmanager
def Blending():
  glEnable(GL_BLEND)
  glBlendFunc(GL_ONE, GL_ONE)
  yield
  glDisable(GL_BLEND)


@contextlib.contextmanager
def Transform():
  glPushMatrix()
  yield
  glPopMatrix()


@contextlib.contextmanager
def Color(*rgba):
  glColor(*rgba)
  yield
  glColor(1, 1, 1, 1)


def ReadPixels(buf, x, y, w, h):
  glBindFramebuffer(GL_FRAMEBUFFER, buf)
  p = glReadPixels(x, y, w, h, GL_RED, GL_UNSIGNED_BYTE)
  glBindFramebuffer(GL_FRAMEBUFFER, 0)
  return p


def Collision(buf, x, y, radius):
  p = ReadPixels(buf, x * 2 + WIDTH - radius, y * 2 + HEIGHT - radius, radius, radius)
  return any(c != '\0' for c in p)


class Taxi(object):

  def __init__(self):
    self.phi = 90
    self.r = 200
    self.vphi = self.vr = 0
    self.light = Light(20, 100, 50)
    self.passenger = None

  def Update(self):
    pressed = pygame.key.get_pressed()
    if pressed[pygame.K_LEFT]:
      self.vphi += 10. / self.r
    if pressed[pygame.K_RIGHT]:
      self.vphi -= 10. / self.r
    if pressed[pygame.K_DOWN]:
      self.vr -= 0.1
    if pressed[pygame.K_UP]:
      self.vr += 0.1
    self.vr -= 0.02
    self.vphi *= 0.99
    self.vr *= 0.99
    self.phi += self.vphi
    self.r += self.vr
    self.x = self.r * math.cos(self.phi * math.pi / 180)
    self.y = self.r * math.sin(self.phi * math.pi / 180)
    if Collision(game.background, self.x, self.y, 5):
      with Buffer(game.background):
        glLoadIdentity()
        glTranslate(self.x, self.y, 0)
        with Color(0, 0, 0):
          Circle(50)
      self.phi = 90
      self.r = 200
      self.vphi = self.vr = 0
      if self.passenger:
        self.passenger = None
        game.objects = [o for o in game.objects if not isinstance(o, Destination)]
        game.Place(Guy)

  def Render(self):
    with Transform():
      glRotate(self.phi, 0, 0, 1)
      glTranslate(self.r, 0, 0)
      with Texture(self.light):
        with Blending():
          with Color(0.2, 0.2, 0.2):
            Quad(1024, 1024)
      color = (1, 1, 1) if not self.passenger else (0.5, 1, 0.2)
      with Color(*color):
        Quad(8, 30)
        glTranslate(8, 0, 0)
        Quad(8, 16)


class Guy(object):

  def __init__(self, x, y, phi):
    self.x = x
    self.y = y
    self.tx = x + 10 * math.cos(phi)
    self.ty = y + 10 * math.sin(phi)
    self.phi = phi * 180 / math.pi
    self.vx = 0
    self.vy = 0

  def Update(self):
    dx = self.tx - self.x
    dy = self.ty - self.y
    self.vx += 0.01 * dx
    self.vy += 0.01 * dy
    self.vx *= 0.9
    self.vy *= 0.9
    self.x += self.vx
    self.y += self.vy
    if not game.taxi.passenger:
      dx = game.taxi.x - self.x
      dy = game.taxi.y - self.y
      d2 = dx * dx + dy * dy
      if d2 < 1000:
        d = math.sqrt(d2)
        self.x += dx / d
        self.y += dy / d
        if d < 5:
          game.objects.remove(self)
          game.taxi.passenger = self
          game.Place(Destination)

  def Render(self):
    with Transform():
      glTranslate(self.x, self.y, 0)
      glRotate(self.phi, 0, 0, 1)
      dx = self.tx - self.x
      dy = self.ty - self.y
      d2 = dx * dx + dy * dy
      scale = 1.0 / (1.0 + 0.1 * d2)
      glScale(scale, scale, 1)
      with Color(0.5, 1, 0.2):
        Quad(15, 10)
        glTranslate(15, 0, 0)
        Circle(5)


class Destination(object):

  def __init__(self, x, y, phi):
    self.x = x
    self.y = y
    self.tx = x + 20 * math.cos(phi)
    self.ty = y + 20 * math.sin(phi)
    self.phi = phi * 180 / math.pi
    self.vx = 0
    self.vy = 0

  def Update(self):
    dx = self.tx - self.x
    dy = self.ty - self.y
    self.vx += 0.01 * dx
    self.vy += 0.01 * dy
    self.vx *= 0.9
    self.vy *= 0.9
    self.x += self.vx
    self.y += self.vy
    if game.taxi.passenger:
      dx = game.taxi.x - self.x
      dy = game.taxi.y - self.y
      d2 = dx * dx + dy * dy
      if d2 < 1000:
        d = math.sqrt(d2)
        self.x += dx / d
        self.y += dy / d
        if d < 5:
          game.objects.remove(self)
          game.taxi.passenger = None
          game.Place(Guy)

  def Render(self):
    with Transform():
      glTranslate(self.x, self.y, 0)
      glRotate(self.phi, 0, 0, 1)
      dx = self.tx - self.x
      dy = self.ty - self.y
      d2 = dx * dx + dy * dy
      scale = 1.0 / (1.0 + 0.1 * d2)
      glScale(scale, scale, 1)
      with Color(1, 0.7, 0.2):
        glRotate(45, 0, 0, 1)
        Quad(10, 10)


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
    self.background = glGenFramebuffers(1)
    with Buffer(self.background):
      glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, bg_tex, 0)
      glClear(GL_COLOR_BUFFER_BIT)
      Circle(100)
    clock = pygame.time.Clock()
    self.taxi = Taxi()
    self.objects = [self.taxi]
    self.Place(Guy)
    while True:
      clock.tick(60)
      for e in pygame.event.get():
        if e.type == pygame.QUIT or e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
          print 'fps:', clock.get_fps()
          pygame.quit()
          sys.exit(0)
      for o in self.objects[:]:
        o.Update()
      glClear(GL_COLOR_BUFFER_BIT)
      glLoadIdentity()
      with Texture(bg_tex):
        Quad(WIDTH, HEIGHT)
      for o in self.objects:
        o.Render()
      pygame.display.flip()

  def Place(self, cls):
    p = ReadPixels(self.background, 0, 0, WIDTH * 2, HEIGHT * 2)
    def Free(x, y):
      return p[int(x) * 2 + int(y) * 4 * WIDTH] == '\0'
    full = []
    for x in range(0, WIDTH, 10):
      for y in range(0, HEIGHT, 10):
        if not Free(x, y):
          full.append((x, y))
    random.shuffle(full)
    for x, y in full:
      phi = math.atan2(y - HEIGHT / 2, x - WIDTH / 2)
      r = Length(y - HEIGHT / 2, x - WIDTH / 2)
      fx = (r + 10) * math.cos(phi) + WIDTH / 2
      fy = (r + 10) * math.sin(phi) + HEIGHT / 2
      if Free(fx, fy):
        o = cls(float(x - WIDTH / 2), float(y - HEIGHT / 2), phi)
        self.objects.append(o)
        break

if __name__ == '__main__':
  game = Game()
  game.Loop()
