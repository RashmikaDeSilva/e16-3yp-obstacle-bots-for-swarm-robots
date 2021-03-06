import cv2
import numpy as np
import random
import math
import imgFunctions as img


bots = list()
BOT_COUNT = 50
RADI = 50
GRID_SIZE = 20
dS = 0.1
WINDOW_SIZE = 1000  # square window, height = width
CELL_SIZE = 100 

backg_H = 0
backg_W = 0
bot_H = 0
bot_W = 0

mouse_pos = [0, 0]
mouse_state = 0

paused = False
set_dest = False


# class to make a bot
class Bot:
    def __init__(self, ID):

        # state = -1, 0, 1 (-1:stoped, 0:success, 1:moving)
        self.state = -1
        self.ID = ID
        self.clicked = False

        # current position
        self.x = 0
        self.y = 0
        self.angle = 0

        # destination position
        self.dest_x = int(-1)
        self.dest_y = int(-1)
        self.dest_angle = 0

    def isClicked(self):
        mouse_dist = np.sqrt(
            np.square(mouse_pos[0] - self.x) + np.square(mouse_pos[1] - self.y))
        if (mouse_dist < 50) and (mouse_state == cv2.EVENT_LBUTTONDOWN):
            self.clicked = not self.clicked
            return True
        return False

    def setImgs(self, imgs):
        self.bot_imgs = imgs

    def setDest(self, x, y, angle):
        self.dest_x = int(x)
        self.dest_y = int(y)
        self.dest_angle = angle

    def setPos(self, x, y, angle):

        # check for the overflow of the x , y values over the backgrounf image
        self.x = (bot_W/2 if (x < bot_W/2) else ((backg_W - bot_W/2)
                                                 if x > (backg_W - bot_W/2) else x))
        self.y = (bot_H/2 if (y < bot_H/2) else ((backg_H - bot_H/2)
                                                 if y > (backg_H - bot_H/2) else y))
        self.angle = angle

    def getState(self, bots):
        min = WINDOW_SIZE
        for i, bot in enumerate(bots):
            if self.ID != i:
                dist = math.sqrt((self.x - bot.x)*(self.x -
                                                   bot.x) + (self.y - bot.y)*(self.y - bot.y))
                # angle = math.atan((self.y - bot.y)/(self.x - bot.x))
                if min > dist:
                    min = dist

        if min < 100:
            self.state = -1
        else:
            self.state = 0


def update(bots):
    if len(bots) == 0:
        for i in range(BOT_COUNT):
            imgs = bot_pngs.copy()
            bot = Bot(i)
            bot.setPos(random.randint(0, backg_H), random.randint(
                0, backg_H), random.randint(0, 360))
            bot.setImgs(imgs)
            bots.append(bot)

    else:
        # if the motion update is not paused
        if not paused:
            for bot in bots:
                # move the bot if there is a destinatiom
                # info: -1 for the destination represents that the bot has no destination
                if bot.dest_x != -1:
                    x = bot.x + dS*(bot.dest_x - bot.x)
                    y = bot.y + dS*(bot.dest_y - bot.y)
                    angle = bot.angle + 0.8
                    bot.setPos(x, y, angle)


""" draw bot images in the overlay canvas
    return : overlay(4 dims with the alpha layer)"""


def draw_bots(bots):
    # create a overlay layer to draw all the robots with the alpha
    overlay = np.zeros((backg_H, backg_W, 4), dtype="uint8")
    for bot in bots:
        x = bot.x
        y = bot.y
        angle = bot.angle
        x_start = int(x - bot_W/2)
        y_start = int(y - bot_H/2)

        #  set the state of the bot acording to the neighbour bots distatnce
        bot.getState(bots)

        # add the additional status color bar to the basic bot png
        if (bot.state == 0) and (bot.clicked == 0):
            addon = bot.bot_imgs['blue']
        else:
            addon = bot.bot_imgs['red']

        # ---------------------Draw destination lines and rectangles -----------------------
        if bot.dest_x != -1:
            cv2.line(overlay, (int(bot.x), int(bot.y)),
                     (bot.dest_x, bot.dest_y), (0, 200, 200, 255), 2)


            cv2.rectangle(overlay, (bot.dest_x-int(CELL_SIZE/2), bot.dest_y-int(CELL_SIZE/2)),
                      (bot.dest_x+int(CELL_SIZE/2), bot.dest_y+int(CELL_SIZE/2)), color, 2)

        bot_img = cv2.add(bot.bot_imgs['bot'], addon)
        bot_img = img.rotate_image(bot_img, angle)
        roi = overlay[y_start:y_start+bot_W,
                      x_start:x_start+bot_W]  # region of interest
        overlay[y_start:y_start+bot_W, x_start:x_start+bot_W] = roi + bot_img

    return overlay


def mosueEvent(event, x, y, flags, param):
    global mouse_pos, mouse_state, bots, set_dest

    mouse_pos = [x, y]
    mouse_state = event

    # In a event of left down click
    #   - if the current state of destination mode is set
    if not set_dest:
        for bot in bots:
            if bot.isClicked():
                set_dest = True
                bot.setDest(-1, -1, 0)
                break

    elif event == cv2.EVENT_LBUTTONDOWN:
        for bot in bots:
            if bot.clicked:
                bot.clicked = False

                # convert the mouse point to the center clicked cell
                x_cell, y_cell, cell_size = getCell(x,y)
                x_cell = x_cell + int(cell_size/2)
                y_cell = y_cell + int(cell_size/2)

                bot.setDest(x_cell, y_cell, 0)
                set_dest = False


def getCell(x, y):
    cell_size = int(WINDOW_SIZE/GRID_SIZE)
    x_cell = int(mouse_pos[0]/cell_size)*cell_size
    y_cell = int(mouse_pos[1]/cell_size)*cell_size

    return x_cell, y_cell, cell_size


if __name__ == "__main__":

    # load backgroug image according to the grid size
    backg_H, backg_W, background = img.loadBackground(GRID_SIZE, WINDOW_SIZE)
    bot_H, bot_W, bot_pngs = img.loadBotImgs(
        GRID_SIZE, WINDOW_SIZE)  # load all pngs of the bot to a dict
    bot_png = bot_pngs['bot']  # get the bot image

    print(backg_H, backg_W)
    print(bot_H, bot_W)

    cv2.namedWindow("image")
    cv2.setMouseCallback("image", mosueEvent)

    while True:
        update(bots)

        # ------------Draw bots ------------------------------
        # get a overlay that contains the vector with aplha which has the current orientation of bots
        overlay = draw_bots(bots)
        # mask the background with the overlay
        masked_backg = cv2.bitwise_and(background, background, mask=cv2.bitwise_not(overlay[:, :, 3]))
        # add the overlay and the background
        finalImg = cv2.add(overlay[:, :, :3], masked_backg)

        # ------------Draw rect on selected cell --------------
        x_cell, y_cell, CELL_SIZE = getCell(mouse_pos[0], mouse_pos[1])
        
        color = (125, 0, 100) if mouse_state == cv2.EVENT_LBUTTONDOWN else (125, 255, 0)
        cv2.rectangle(finalImg, (x_cell, y_cell),
                      (x_cell+CELL_SIZE, y_cell+CELL_SIZE), color, 2)

        cv2.imshow('image', finalImg)

        key = cv2.waitKey(5)

        if key == 27:
            break
        elif key == 32:
            paused = not paused
