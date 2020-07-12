#================================PREREQUISITES===============================
# I started with Raspbian Lite - bigger versions of Raspbian should be fine
#
# Ensure that the file at /boot/config.txt cobntains these two lines:
#		dtoverlay=hifiberry-dac
#		gpio=25=op,dh
# and put a hash before this line (as shown) to disable it:
#		#dtparam=audio=on
#
#  You need to install software and libraries as follows:
#		sudo apt-get update
#		sudo apt-get install python-rpi.gpio python-spidev python-pip python-pil python-numpy sox libsox-fmt-mp3
#		sudo pip install st7789
#
#  The code below also assumes that you have 
#	- an mp3 file called 'test.mp3' in the same folder as the program (see lines 140 and 144 of this file)
#	- a font file at /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf (see lines 70-73)
#  You can of course change thes locations within the code on the lines shown above.
#
#=========================END OF PREREQUISITES===============================

#================================BASIC SETUP=================================
#=======================================================
#Library imports
#=======================================================
# imports for screen
# documentation for PIL is at https://pillow.readthedocs.io/en/stable/reference/index.html
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from ST7789 import ST7789
#import os for beep
import os
#imports for buttons
import signal
import RPi.GPIO as GPIO
#import time so we can make a puase
import time

#=======================================================
# Set up the screen and image buffers
#=======================================================
#Set up screen
SPI_SPEED_MHZ = 80
screen = ST7789(
    rotation=90,  # Needed to display the right way up on Pirate Audio
    port=0,       # SPI port
    cs=1,         # SPI port Chip-select channel
    dc=9,         # BCM pin used for data/command
    backlight=13,
    spi_speed_hz=SPI_SPEED_MHZ * 1000 * 1000
)
# screen size details
width = screen.width
height = screen.height

# Create a few blank images.
# This lets us set up layouts/pictures, then send them easily to the acreen
# We set up an array of images and a corresponding array of draw objects, one for each image
image = [None] * 4
draw = [None] * 4
for i in range(4):
	image[i] = Image.new("RGB", (240, 240), (0, 0, 0))
	draw[i] = ImageDraw.Draw(image[i])

#=======================================================
# Set up a font to use when showing text
#=======================================================
# I've shown how to create two different sizes
# You need a font file in the appropriate directory.
# If using Raspbian lite, you'll need to create the directory and get a font from (eg) https://www.fontsquirrel.com/
font30 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
font60 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
	
#=======================================================	
# Create a 'beep' function - a simple noise to make sure sound is working at any stage 
#=======================================================
def beep():
	beepcmd = "play -n synth 0.3 sine A 2>/dev/null"
	os.system(beepcmd)

#=======================================================
# Set up the basics for buttons
#=======================================================
# The buttons on Pirate Audio are connected to pins 5, 6, 16 and 20
BUTTONS = [5, 6, 16, 20]

# These correspond to buttons A, B, X and Y respectively
LABELS = ['A', 'B', 'X', 'Y']

# Set up RPi.GPIO with the "BCM" numbering scheme
GPIO.setmode(GPIO.BCM)

# Buttons connect to ground when pressed, so we should set them up
# with a "PULL UP", which weakly pulls the input signal to 3.3V.
GPIO.setup(BUTTONS, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# NB: Further down, we'll set up the button handler which will tell teh pi what to do on each button pressed

#================================END OF THE BASIC SETUP======================

#=======================================================
# Set up our actual images
#=======================================================
# image 0 should already be a black screen as that's how we set them all up.  It's useful when we end the program
# image 1: get pi logo.  raspberrypi.png should be a 240x240 image in the same directory as the program
image[1] =Image.open("raspberrypi.png")

# image 2: draw a multicoloured series of small boxes over the display.  
# This uses the 'draw' object associated with image3
#draw.rectangle ((x0,y0,x1,y1),(r,g,b)) draws a box from x1,y1 to x2,y2, using r,g,b as colour values
for row in range(10):
        for cell in range(10):
                draw[2].rectangle((cell*24,row*24,cell*24+24,row*24+24), (cell*25, row*25, 0))
				
#image 3 uses drawing text to put a menu item next to each button
# let's have a function to do the repettitive stuff
def show_text(draw, message, x, y, font, ralign):
	size_x, size_y = draw.textsize(message, font)
	text_y = y - size_y
	text_x = x
	if ralign:
		text_x = x - size_x
	draw.text((text_x, text_y), message, font=font, fill=(255, 255, 255))
show_text(draw[3],"play", 0, 90, font30, False)
show_text(draw[3],"logo", 0, 200, font30, False)
show_text(draw[3],"colours", 240, 90, font30, True)
show_text(draw[3],"exit", 240, 200, font30, True)


#=======================================================
# Set up the button handler
#=======================================================
def handle_button(pin):
	label = LABELS[BUTTONS.index(pin)]
	print("Button press detected on pin: {} label: {}".format(pin, label))
	
	if label=='A':
		# button A - play the sound file, suppressing output by sending it to /dev/null
		# You'll need a file called 'test.mp3' in the same directory as the program
		# Show the blank image while the file is playing - this could be a different image, of course
		# NB: Showing the blank screen doesn't actually prevent button presses being made and stacked up
		screen.display(image[0])
		os.system("play test.mp3 2>/dev/null")
		screen.display(image[3])
		
	if label=='B':
		# button B - show the logo image, and pause for a second
		screen.display(image[1])
		time.sleep(1)
		screen.display(image[3])
		
	if label=='X':
		# button X - show the colour image, and pause for a second
		screen.display(image[2])
		time.sleep(1)
		screen.display(image[3])
		
	if label=='Y':
		# button Y - show the blank image, and exit
		screen.display(image[0])
		GPIO.cleanup()
		exit()
	
# Loop through out buttons and attach the "handle_button" function to each
# We're watching the "FALLING" edge (transition from 3.3V to Ground) and
# picking a generous bouncetime of 100ms to smooth out button presses.
for pin in BUTTONS:
    GPIO.add_event_detect(pin, GPIO.FALLING, handle_button, bouncetime=300)
	
# Now that we are all set up, show the menu screen (image 3)
screen.display(image[3])

# Finally, since button handlers don't require a "while True" loop,
# we pause the script to prevent it exiting immediately.
signal.pause()
