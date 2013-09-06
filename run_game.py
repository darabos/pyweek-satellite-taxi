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


def Ring(radius):
  glBegin(GL_LINES)
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
def Blending(src, dst):
  glEnable(GL_BLEND)
  glBlendFunc(src, dst)
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


class Taxi(object):
  light = None

  def __init__(self):
    self.phi = 90
    self.r = 200
    self.x = self.r * math.cos(self.phi * math.pi / 180)
    self.y = self.r * math.sin(self.phi * math.pi / 180)
    self.engine = 1
    self.shields = 0
    self.bombs = 0
    self.vphi = self.vr = 0
    if Taxi.light == None:
      Taxi.light = Light(20, 100, 50)
    self.passenger = None
    self.bonus = 0
    self.shop_timer = 0

  def Update(self):
    pressed = pygame.key.get_pressed()
    if pressed[pygame.K_LEFT]:
      self.vphi += self.engine * 10. / self.r
    if pressed[pygame.K_RIGHT]:
      self.vphi -= self.engine * 10. / self.r
    if pressed[pygame.K_DOWN]:
      self.vr -= self.engine * 0.1
    if pressed[pygame.K_UP]:
      self.vr += self.engine * 0.1
    self.vr -= 0.02
    self.vphi *= 0.99
    self.vr *= 0.99
    self.phi += self.vphi
    self.r += self.vr
    self.x = self.r * math.cos(self.phi * math.pi / 180)
    self.y = self.r * math.sin(self.phi * math.pi / 180)
    if self.bonus > 20.2:
      self.bonus -= 0.1

    pixels = ReadPixels(game.background, self.x * 2 + WIDTH - 5, self.y * 2 + HEIGHT - 5, 10, 10)
    if any(c == '\xff' for c in pixels):
      self.shields -= 1
      self.vphi *= -1
      self.vr *= -1
      if self.shields < 0:
        with Buffer(game.background):
          glLoadIdentity()
          with Transform():
            glTranslate(self.x, self.y, 0)
            with Color(0, 0, 0):
              Circle(50)
          Circle(50)
        if self.passenger:
          self.passenger = None
          game.objects = [o for o in game.objects if not isinstance(o, Destination)]
          game.Soon(lambda: game.Place(Guy))
        game.objects.remove(self)
        game.Soon(game.NewTaxi)
        game.TakeMoney(100)
    for c in pixels:
      for k, v in SHOPS.items():
        if c == chr(k[0]):
          if game.money < 100:
            if game.money_pos < 1:
              game.money_v = 1
            break
          self.shop_timer += 1
          if self.shop_timer == 180:
            if v == 'Pay Back Debt':
              game.TakeMoney(100)
              game.debt_v += 1
              game.debt -= 100
            elif v == 'Upgrade Engine':
              game.TakeMoney(100)
              self.engine += 1
            elif v == 'Buy Shields':
              game.TakeMoney(100)
              self.shields += 1
            elif v == 'Buy Bomb':
              game.TakeMoney(100)
              self.bombs += 1
          break
      else:
        continue
      break
    else:
      self.shop_timer = 0

  def Render(self):
    with Transform():
      glRotate(self.phi, 0, 0, 1)
      glTranslate(self.r, 0, 0)
      with Texture(self.light):
        with Blending(GL_ONE, GL_ONE):
          f = self.shop_timer / 180. if self.shop_timer < 180 else 0
          f = 0.8 * f
          with Color(0.2 + 0.2 * f, 0.2 + 0.7 * f, 0.2 + f):
            Quad(1024, 1024)
      color = (1, 1, 1) if not self.passenger else (0.5, 1, 0.2)
      for i in range(self.shields):
        Ring(20 + i * 5)
      with Color(*color):
        glTranslate(-4, 0, 0)
        Quad(8, 30)
        glTranslate(8, 0, 0)
        Quad(8, 16)


class Popup(object):
  dist = 10

  def __init__(self, x, y, phi):
    self.x = x
    self.y = y
    self.tx = x + self.dist * math.cos(phi)
    self.ty = y + self.dist * math.sin(phi)
    self.phi = phi * 180 / math.pi
    self.vx = 0
    self.vy = 0
    self.scale = 0

  def Update(self):
    dx = self.tx - self.x
    dy = self.ty - self.y
    self.vx += 0.01 * dx
    self.vy += 0.01 * dy
    self.vx *= 0.9
    self.vy *= 0.9
    self.x += self.vx
    self.y += self.vy
    d2 = dx * dx + dy * dy
    self.scale = 1.0 / (1.0 + 0.1 * d2)


class Guy(Popup):

  def Update(self):
    super(Guy, self).Update()
    if not game.taxi.passenger and game.taxi in game.objects:
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
          game.taxi.bonus = 100

  def Render(self):
    with Transform():
      glTranslate(self.x, self.y, 0)
      glRotate(self.phi, 0, 0, 1)
      glScale(self.scale, self.scale, 1)
      with Color(0.5, 1, 0.2):
        Quad(15, 10)
        glTranslate(15, 0, 0)
        Circle(5)


class Destination(Popup):
  dist = 20

  def Update(self):
    super(Destination, self).Update()
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
          game.Place(Building)
          game.Soon(lambda: game.Place(Guy))
          game.GiveMoney(int(game.taxi.bonus))
          game.taxi.bonus = 0

  def Render(self):
    with Transform():
      glTranslate(self.x, self.y, 0)
      glRotate(self.phi, 0, 0, 1)
      glScale(self.scale, self.scale, 1)
      with Color(1, 0.7, 0.2):
        glRotate(45, 0, 0, 1)
        Quad(10, 10)

SHOPS = {
  (50, 179, 255): 'Upgrade Engine',
  (51, 179, 255): 'Pay Back Debt',
  (52, 179, 255): 'Buy Shields',
  (53, 179, 255): 'Buy Bomb',
}

class Building(Popup):

  def __init__(self, x, y, phi):
    super(Building, self).__init__(x, y, phi)
    self.w = 20 + max(0, random.gauss(20, 20))
    self.h = 40 + max(0, random.gauss(40, 40))
    self.color = 255, 255, 255
    if random.random() < 0.2:
      self.color = random.choice(SHOPS.keys())
      self.w = max(self.w, 80)
      self.h = max(self.h, 80)

  def Update(self):
    super(Building, self).Update()
    if Length(self.tx - self.x, self.ty - self.y) < 1:
      with Buffer(game.background):
        self.Render()
      game.objects.remove(self)

  def Render(self):
    with Transform():
      glTranslate(self.x, self.y, 0)
      glRotate(self.phi - 90, 0, 0, 1)
      glScale(self.scale, self.scale, 1)
      with Color([c / 255. for c in self.color]):
        Quad(self.w, self.h)
      if self.color in SHOPS:
        text = SHOPS[self.color].split()
        for i, w in enumerate(text):
          game.smallfont.Render(0, (len(text) * 0.5 - 0.5 - i) * 20, w, (0, 0, 0), 'center')


class Font(object):

  def __init__(self, size):
    self.font = pygame.font.Font('OpenSans-ExtraBold.ttf', size)
    self.cache = {}

  def Render(self, x, y, text, color, align):
    if text not in self.cache:
      surface = self.font.render(text, True, (255, 255, 255), (0, 0, 0))
      data = pygame.image.tostring(surface, 'RGBA', 1)
      tex = glGenTextures(1)
      width = surface.get_width()
      height = surface.get_height()
      glBindTexture(GL_TEXTURE_2D, tex)
      glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
      glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
      glTexParameter(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
      glTexParameter(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
      glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
      if len(self.cache) > 200:
        self.DropCache()
      self.cache[text] = width, height, tex
    width, height, tex = self.cache[text]
    with Transform():
      if align == 'left':
        glTranslate(x + width / 2, y, 0)
      elif align == 'right':
        glTranslate(x - width / 2, y, 0)
      elif align == 'center':
        glTranslate(x, y, 0)
      else:
        assert False, align
      with Texture(tex):
        with Blending(GL_ZERO, GL_ONE_MINUS_SRC_COLOR):
          Quad(width, height)
        with Blending(GL_ONE, GL_ONE):
          with Color(*color):
            Quad(width, height)

  def DropCache(self):
    for w, h, tex in self.cache.values():
      glDeleteTextures(tex)
    self.cache = {}


class Game(object):

  def __init__(self):
    self.x = 0
    self.y = 200
    self.vx = 0
    self.vy = 0
    self.timers = []
    self.time = 0
    self.objects = []
    self.money = 0
    self.debt = 1000
    self.debt_pos = 30
    self.debt_v = 0
    self.money_pos = 30
    self.money_v = 0

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
    self.NewTaxi()
    self.taxi.shields = 1
    self.Place(Guy)
    pygame.font.init()
    self.smallfont = Font(12)
    self.font = Font(16)
    self.bigfont = Font(20)

    while True:
      clock.tick(60)
      self.time += 1
      while self.timers and self.timers[0][0] == self.time:
        t, f = self.timers.pop(0)
        f()
      for e in pygame.event.get():
        if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
          # DEBUG
          self.Place(Building)
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
      self.HUD()
      pygame.display.flip()

  def HUD(self):
    self.debt_v -= 0.05 * self.debt_pos
    self.debt_v *= 0.85
    self.debt_pos += self.debt_v
    self.money_v -= 0.05 * self.money_pos
    self.money_v *= 0.85
    self.money_pos += self.money_v
    self.font.Render(-WIDTH / 2 + 20, HEIGHT / 2 - 20 + self.debt_pos, 'DEBT:', (1.0, 1.0, 1.0), 'left')
    self.bigfont.Render(-WIDTH / 2 + 130, HEIGHT / 2 - 20 + self.debt_pos, str(self.debt), (1.0, 0.7, 0.2), 'right')
    self.font.Render(WIDTH / 2 - 130, HEIGHT / 2 - 20 + self.money_pos, 'CASH:', (1.0, 1.0, 1.0), 'left')
    self.bigfont.Render(WIDTH / 2 - 20, HEIGHT / 2 - 20 + self.money_pos, str(self.money), (0.5, 1.0, 0.2), 'right')
    if self.taxi.bonus:
      self.font.Render(WIDTH / 2 - 20, HEIGHT / 2 - 40, '+%d' % self.taxi.bonus, (0.5, 1.0, 0.2), 'right')

  def Place(self, cls):
    p = ReadPixels(self.background, 0, 0, WIDTH * 2, HEIGHT * 2)
    def Free(x, y):
      return p[int(x) * 2 + int(y) * 4 * WIDTH] == '\0'
    full = []
    for x in range(0, WIDTH, 10):
      for y in range(0, HEIGHT, 10):
        if Length(game.taxi.x - x + WIDTH / 2, game.taxi.y - y + HEIGHT / 2) < 100:
          continue
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

  def Soon(self, f):
    self.timers.append((self.time + 50, f))
    self.timers.sort()

  def NewTaxi(self):
    self.taxi = Taxi()
    self.objects.append(self.taxi)

  def GiveMoney(self, m):
    game.money += m
    game.money_v += 1

  def TakeMoney(self, m):
    game.money -= m
    if game.money >= 0:
      game.money_v += 1
    else:
      game.debt -= game.money
      game.debt_v += 1
      if game.money != -m:
        game.money_v += 1
      game.money = 0


if __name__ == '__main__':
  game = Game()
  game.Loop()
