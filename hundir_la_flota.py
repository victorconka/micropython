# Pong!
# Using emulated hardware i2c, we can push enough frames for
# rough animations. Performance for this project is reduced
# using chromium.

import machine
import framebuf
import time
import math
import pyb

SCREEN_WIDTH = 64
SCREEN_HEIGHT = 32

game_over = False #player gameover-lose status
game_win = False #player win status
score = 0 # game score
led_it = 0  # iterador de los leds
n_game = 0 #game counter
servo = pyb.Servo(1) #servo motor 
y12 = machine.Pin('Y12') #red LED 
y4 = machine.Pin('Y4') #adc input pin
adc = pyb.ADC(y4) #adc input object
i2c = machine.I2C('X') #i2c screen
fbuf = framebuf.FrameBuffer(bytearray(64 * 32 // 8), 64, 32, framebuf.MONO_HLSB)

def toggle_led():
    y12(0 if y12() else 1)

def toggle_leds(value):
    pyb.LED((value % 4) + 1).toggle()
    return (value+1) % 4


class Entity:
    def __init__(self, x, y, w, h, vx, vy):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.vx = vx
        self.vy = vy
        self.score = 0
        self.direction = 1

    def draw(self, fbuf):
        fbuf.fill_rect(int(self.x), int(self.y), self.w, self.h, 1)


class Ball(Entity):
    def update(self, angleRad, objetivo):
        global game_over
        global score
        global game_win
        # update x ---------------------------------------------
        self.x += self.vx * math.cos(angleRad)
        if (self.x <= 0 or self.x >= SCREEN_WIDTH - self.w):#left-right screen limits
            self.x = 0
            game_over = True
            score -= objetivo.score
        # update y ----------------------------------------------
        self.y += self.vy * math.sin(angleRad)
        if(self.y >= SCREEN_HEIGHT-self.w):#this should never happen
            self.y = SCREEN_HEIGHT-self.w
        if (self.y <= 1):
            self.y = 0
            if(self.x >= objetivo.x and self.x <= (objetivo.x + objetivo.w)):
                score += objetivo.score
                game_win = True
                for i in range(0,10):
                    toggle_led()
                    time.sleep_ms(500)
            else:
                game_over = True
                score -= objetivo.score

class Player(Entity):
    pass

class Barco(Entity):
    def move(self):
        newX = self.x + self.direction
        if(newX + self.w > SCREEN_WIDTH or newX < 0):
            self.direction *= -1
        self.x += self.direction
            
def random_objetivo(tick):
    objetivo = Barco((tick % (64-2)), 0, 2, 1, 0, 0)
    objetivo.score = 8
    if(tick % 3 == 0):
        objetivo = Barco((tick % (64-10)), 0, 10, 1, 0, 0)
        objetivo.score = 2
        print("portaaviones\n")
    elif(tick % 3 == 1):
        objetivo = Barco((tick % (64-5)), 0, 5, 1, 0, 0)
        objetivo.score = 5
        print("fragata\n")
    else:
        print("corbeta\n")
    return objetivo


def mapValue_radians(oldValue, newMin=180, newMax=0, oldMin=0, oldMax=255, integer=False):
    """[map value from one range to another]

    Arguments:
        oldValue {[int/float]} -- [initial range value(0..255) that will be mapped to radians]

    Keyword Arguments:
        newMin {int} -- [new min range] (default: {180})
        newMax {int} -- [new max range] (default: {0})
        oldMin {int} -- [old min range] (default: {0})
        oldMax {int} -- [old max range] (default: {255})
        integer {bool} -- [return integer or float] (default: {False})

    Returns:
        [int/float] -- [valor 0..255 mapeado a radianes]
    """
    return math.radians(mapValue(oldValue, newMin=newMin, newMax=newMax, oldMin=oldMin, oldMax=oldMax))


def mapValue(oldValue, newMin=-90, newMax=90, oldMin=0, oldMax=255, integer=False):
    """[map value from one range to another]

    Arguments:
        oldValue {[int/float]} -- [initial range value(0..255) that will be mapped to radians]

    Keyword Arguments:
        newMin {int} -- [new min range] (default: {180})
        newMax {int} -- [new max range] (default: {0})
        oldMin {int} -- [old min range] (default: {0})
        oldMax {int} -- [old max range] (default: {255})
        integer {bool} -- [return integer or float] (default: {False})

    Returns:
        [int/float] -- [oldValue mapped to radians]
    """
    oldRange = (oldMax - oldMin)
    if (oldRange == 0):
        newValue = newMin
    else:
        newRange = (newMax - newMin)
        newValue = (((oldValue - oldMin) * newRange) / oldRange) + newMin
    if (integer):
        newValue = int(newValue)
    return newValue

while(True):  # game has no end
    n_game += 1
    update_ball = False
    game_over = False
    game_win = False
    ball = Ball(32, 30, 1, 1, 2, -2)
    player = Player(31, 31, 3, 1, 0, 0)
    objetivo = random_objetivo(time.ticks_ms())
    
    fbuf.fill(0)
    fbuf.text('ROUND: %d' % n_game, 0, 0)
    fbuf.text('SCORE %d' % score, 0, 8)
    i2c.writeto(8, fbuf)
    time.sleep_ms(5000)

    while (not game_over and not game_win):
        objetivo.move()
        # leer valor adc
        adc_val = adc.read()
        # mapear posicion del servo
        servo.angle(mapValue(adc_val, integer=True), 100)
        # mapear angulo bola
        ball_angle = mapValue_radians(adc_val)
        if(pyb.Switch().value()):  # detectar disparo
            update_ball = True
        if(update_ball):  # actualizar posicion de bola solo despues del disparo
            # toggle led solo si se ha pulsado el boton
            led_it = toggle_leds(led_it)
            ball.update(ball_angle, objetivo)
        # dibujar los objetos
        fbuf.fill(0)
        ball.draw(fbuf)
        player.draw(fbuf)
        objetivo.draw(fbuf)
        i2c.writeto(8, fbuf)
        time.sleep_ms(300)  # velocidad del juego
    fbuf.fill(0)
    fbuf.text('ROUND: %d' % n_game, 0, 12)
    fbuf.text('SCORE %d' % score, 0, 22)
    if game_win:
        fbuf.text('YOU WIN', 0, 0)
    else:
        fbuf.text('YOU LOSE', 0, 0)
    i2c.writeto(8, fbuf)
    time.sleep_ms(5000)
