import random, pygame, sys
from src.states.BaseState import BaseState
from src.constants import *
from src.Dependency import *
import src.CommonRender as CommonRender

class PlayState(BaseState):
    def __init__(self):
        super(PlayState, self).__init__()
        self.paused = False

    def Enter(self, params):
        
        self.paddle = params['paddle']
        self.bricks = params['bricks']
        self.health = params['health']
        self.score = params['score']
        self.high_scores = params['high_scores']
        self.ball = params['ball']
        self.level = params['level']
        self.powerups = []
        self.balls = []
        self.SPAWNRATE = random.randint(10,40)
        self.BOOM = False

        for b in self.bricks:
            if random.randint(0,100) <= self.SPAWNRATE: #Spawn rate
                p = PowerUp(b.x+24, b.y-1, 3)  # Adjusting for 48x48 size
                self.powerups.append(p)

        for x in range(10):
            b = Ball(5)
            b.rect.x = self.ball.rect.x
            b.rect.y = self.ball.rect.y
            b.dx = random.randint(-600, 600)
            b.dy = random.randint(-600, 600)
            self.balls.append(b)

        self.recover_points = 5000

        self.ball.dx = random.randint(-600, 600)  # -200 200
        self.ball.dy = random.randint(-220, -180)


    def update(self,  dt, events):
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                    gSounds['pause'].play()
                    #music_channel.play(sounds_list['pause'])
                if event.key == pygame.K_s:
                    gSounds['victory'].play()
                    g_state_manager.Change('victory', {
                        'level':self.level,
                        'paddle':self.paddle,
                        'health':self.health,
                        'score':self.score,
                        'high_scores':self.high_scores,
                        'ball':self.ball,
                        'recover_points':self.recover_points
                    })

        if self.paused:
            return
        else:
            pygame.mouse.set_pos(WIDTH/2,HEIGHT/2)
        #x = self.ball.rect.x - self.paddle.rect.width/2 #For bot purpose
        self.paddle.update(dt)
        self.ball.update(dt)
        for p in self.powerups:
            p.update(dt)
            # Check if power-up collides with the paddle
            if p.Collides(self.paddle):
                #self.health = min(3, self.health + 1)  # Example effect: gain health
                #gSounds['recover'].play()

                self.BOOM = True

                for b in self.balls:
                    b.rect.x = self.ball.rect.x
                    b.rect.y = self.ball.rect.y
                    b.dx = random.randint(-600, 600)
                    b.dy = random.randint(-600, 600)

                self.powerups.remove(p)  # Remove the power-up after collision
                # Remove power-up if it goes off-screen
                if self.SPAWNRATE > 10:
                    self.SPAWNRATE -= 10
                else:
                    self.SPAWNRATE = 10
            if p.rect.y > HEIGHT:
                self.powerups.remove(p)
                if self.SPAWNRATE > 10:
                    self.SPAWNRATE -= 10
                else:
                    self.SPAWNRATE = 10 

        if self.ball.Collides(self.paddle):
            # raise ball above paddle
            ####can be fixed to make it natural####
            self.ball.rect.y = self.paddle.rect.y - 24
            self.ball.dy = -self.ball.dy

            # half left hit while moving left (side attack) the more side, the faster
            if self.ball.rect.x + self.ball.rect.width < self.paddle.rect.x + (self.paddle.width / 2) and self.paddle.dx < 0:
                self.ball.dx = -150 + -(8 * (self.paddle.rect.x + self.paddle.width / 2 - self.ball.rect.x))
            # right paddle and moving right (side attack)
            elif self.ball.rect.x > self.paddle.rect.x + (self.paddle.width / 2) and self.paddle.dx > 0:
                self.ball.dx = 150 + (8 * abs(self.paddle.rect.x + self.paddle.width / 2 - self.ball.rect.x))
            gSounds['paddle-hit'].play()

        for k, brick in enumerate(self.bricks):
            if brick.alive and self.ball.Collides(brick):
                self.score = self.score + (brick.tier * 200 + brick.color * 25)
                brick.Hit()
                if not brick.alive:
                    self.bricks.remove(brick)

                for powerup in self.powerups:
                    if powerup.Collides(brick):
                        powerup.dy = 200

                # if self.score > self.recover_points:
                #     self.health = min(3, self.health + 1)
                #     self.recover_points = min(100000, self.recover_points * 2)

                #     gSounds['recover'].play()
                    #music_channel.play(sounds_list['recover'])

                if self.CheckVictory():
                    gSounds['victory'].play()

                    g_state_manager.Change('victory', {
                        'level':self.level,
                        'paddle':self.paddle,
                        'health':self.health,
                        'score':self.score,
                        'high_scores':self.high_scores,
                        'ball':self.ball,
                        'recover_points':self.recover_points
                    })

                # hit brick from left while moving right -> x flip
                if self.ball.rect.x + 6 < brick.rect.x and self.ball.dx > 0:
                    self.ball.dx = -self.ball.dx
                    self.ball.rect.x = brick.rect.x - 24

                # hit brick from right while moving left -> x flip
                elif self.ball.rect.x + 18 > brick.rect.x + brick.width and self.ball.dx < 0:
                    self.ball.dx = -self.ball.dx
                    self.ball.rect.x = brick.rect.x + 96

                # hit from above -> y flip
                elif self.ball.rect.y < brick.rect.y:
                    self.ball.dy = -self.ball.dy
                    self.ball.rect.y = brick.rect.y - 24

                # hit from bottom -> y flip
                else:
                    self.ball.dy = -self.ball.dy
                    self.ball.rect.y = brick.rect.y + 48

                # whenever hit, speed is slightly increase, maximum is 450
                if abs(self.ball.dy) < 450:
                    self.ball.dy = self.ball.dy * 1.02
                break

        if self.BOOM:
            for b in self.balls:
                b.dx = max(min(b.dx, 300), -300)  # Limit ball speed
                b.dy = max(min(b.dy, 300), -300)
                b.update(dt)  # Update the position of the extra balls

                # Now check collision of this extra ball with each brick
                for brick in self.bricks:
                    if brick.alive and b.Collides(brick):  # Use `b` instead of `self.ball`
                        self.score += (brick.tier * 200 + brick.color * 25)
                        brick.Hit()
                        if not brick.alive:
                            self.bricks.remove(brick)

                        for powerup in self.powerups:
                            if powerup.Collides(brick):
                                powerup.dy = 200

                        if self.CheckVictory():
                            gSounds['victory'].play()

                            g_state_manager.Change('victory', {
                                'level':self.level,
                                'paddle':self.paddle,
                                'health':self.health,
                                'score':self.score,
                                'high_scores':self.high_scores,
                                'ball':self.ball,
                                'recover_points':self.recover_points
                            })

                        # Collision response - flip the velocity of the ball based on where it hit
                        if b.rect.x + 6 < brick.rect.x and b.dx > 0:
                            b.dx = -b.dx
                            b.rect.x = brick.rect.x - 24
                        elif b.rect.x + 18 > brick.rect.x + brick.width and b.dx < 0:
                            b.dx = -b.dx
                            b.rect.x = brick.rect.x + 96
                        elif b.rect.y < brick.rect.y:
                            b.dy = -b.dy
                            b.rect.y = brick.rect.y - 24
                        else:
                            b.dy = -b.dy
                            b.rect.y = brick.rect.y + 48

                        # Speed boost after hit, but clamp it
                        if abs(b.dy) < 450:
                            b.dy *= 1.02
        
                    

                if b.Collides(self.paddle):
                    b.rect.y = self.paddle.rect.y - 24
                    b.dy = -b.dy

                        # half left hit while moving left (side attack) the more side, the faster
                    if b.rect.x + b.rect.width < self.paddle.rect.x + (self.paddle.width / 2) and self.paddle.dx < 0:
                        b.dx = -150 + -(8 * (self.paddle.rect.x + self.paddle.width / 2 - b.rect.x))
                        # right paddle and moving right (side attack)
                    elif b.rect.x > self.paddle.rect.x + (self.paddle.width / 2) and self.paddle.dx > 0:
                        b.dx = 150 + (8 * abs(self.paddle.rect.x + self.paddle.width / 2 - b.rect.x))
                    gSounds['paddle-hit'].play()
        
        #MAIN BALL FELL

        if self.ball.rect.y >= HEIGHT:
            self.health -= 1
            gSounds['hurt'].play()

            if self.health == 0:
                g_state_manager.Change('game-over', {
                    'score':self.score,
                    'high_scores': self.high_scores
                })
            else:
                g_state_manager.Change('serve', {
                    'level': self.level,
                    'paddle': self.paddle,
                    'bricks': self.bricks,
                    'health': self.health,
                    'score': self.score,
                    'high_scores': self.high_scores,
                    'recover_points': self.recover_points,
                    'powerups' : self.powerups
                })

    def Exit(self):
        pygame.mouse.set_visible(True)
        pass

    def render(self, screen):

        for p in self.powerups:
            p.render(screen)

        for brick in self.bricks:
            brick.render(screen)
        
        if self.BOOM:
            for b in self.balls:
                b.render(screen)

        self.paddle.render(screen)
        self.ball.render(screen)

        CommonRender.RenderScore(screen, self.score)
        CommonRender.RenderHealth(screen, self.health)

        if self.paused:
            pygame.mouse.set_visible(True)
            t_pause = gFonts['large'].render("PAUSED", False, (255, 255, 255))
            rect = t_pause.get_rect(center = (WIDTH/2, HEIGHT/2))
            screen.blit(t_pause, rect)
        else:
            pygame.mouse.set_visible(False)


    def CheckVictory(self):
        for brick in self.bricks:
            if brick.alive:
                return False

        return True
