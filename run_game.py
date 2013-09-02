import math
import pygame
import sys
from OpenGL.GL import *

WIDTH, HEIGHT = 800, 600

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
    glBindFramebuffer(GL_FRAMEBUFFER, background)
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, bg_tex, 0)
    glViewport(0, 0, WIDTH * 2, HEIGHT * 2)
    glClear(GL_COLOR_BUFFER_BIT)
    Circle(100)
    glBindFramebuffer(GL_FRAMEBUFFER, 0)
    glViewport(0, 0, WIDTH, HEIGHT)
    clock = pygame.time.Clock()
    while True:
      clock.tick(40)
      for e in pygame.event.get():
        if e.type == pygame.QUIT or e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
          pygame.quit()
          sys.exit(0)
      pressed = pygame.key.get_pressed()
      if pressed[pygame.K_LEFT]:
        self.vx -= 0.1
      if pressed[pygame.K_RIGHT]:
        self.vx += 0.1
      if pressed[pygame.K_DOWN]:
        self.vy -= 0.1
      if pressed[pygame.K_UP]:
        self.vy += 0.1
      self.vy -= 0.02
      self.vx *= 0.99
      self.vy *= 0.99
      self.x += self.vx
      self.y += self.vy
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
      Quad(12, 8)
      pygame.display.flip()

if __name__ == '__main__':
  Game().Loop()
