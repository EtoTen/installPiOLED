#! /usr/bin/python3
# Copyright (c) 2017 Adafruit Industries
# Author: Tony DiCola & James DeVito
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# Portions copyright (c) NVIDIA 2019
# Portions copyright (c) JetsonHacks 2019

import time

from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306, ssd1325, ssd1331, sh1106
from random import randrange

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import subprocess


def get_network_interface_state(interface):
    return subprocess.check_output('cat /sys/class/net/%s/operstate' % interface, shell=True).decode('ascii')[:-1]


def get_ip_address(interface):
    if get_network_interface_state(interface) == 'down':
        return None
    cmd = "ifconfig %s | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1'" % interface
    return subprocess.check_output(cmd, shell=True).decode('ascii')[:-1]

# Return a string representing the percentage of CPU in use


def get_cpu_usage():
    # Shell scripts for system monitoring from here : https://unix.stackexchange.com/questions/119126/command-to-display-memory-usage-disk-usage-and-cpu-load
    cmd = "top -bn1 | grep load | awk '{printf \"CPU Load: %.2f\", $(NF-2)}'"
    CPU = subprocess.check_output(cmd, shell=True)
    return CPU

# Return a float representing the percentage of GPU in use.
# On the Jetson Nano, the GPU is GPU0


def get_gpu_usage():
    GPU = 0.0
    with open("/sys/devices/gpu.0/load", encoding="utf-8") as gpu_file:
        GPU = gpu_file.readline()
        GPU = int(GPU)/10
    return GPU

# 128x32 display with hardware I2C:
serial = i2c(port=1, address=0x3C)
disp = sh1106(serial, width=128, height=64, rotate=0)


# Turn on display
disp.show()

# Clear display.
disp.clear()

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image_stat = Image.new('1', (width, height))

# Get drawing object to draw on image.
draw_stat = ImageDraw.Draw(image_stat)

# Draw a black filled box to clear the image.
draw_stat.rectangle((0, 0, width, height), outline=0, fill=0)

# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height-padding

# Move left to right keeping track of the current x position for drawing shapes.
x = 0

# Load default font.
font = ImageFont.load_default()

def draw_stats():

    # Draw a black filled box to clear the image.
    draw_stat.rectangle((0, 0, width, height), outline=0, fill=0)

    # Shell scripts for system monitoring from here : https://unix.stackexchange.com/questions/119126/command-to-display-memory-usage-disk-usage-and-cpu-load
    cmd = "free -m | awk 'NR==2{printf \"Mem:  %.0f%% %s/%s M\", $3*100/$2, $3,$2 }'"
    MemUsage = subprocess.check_output(cmd, shell=True)
    cmd = "df -h | awk '$NF==\"/\"{printf \"Disk: %d/%dGB %s\", $3,$2,$5}'"
    Disk = subprocess.check_output(cmd, shell=True)

    # Print the IP address
    # Two examples here, wired and wireless
    draw_stat.text((x, top),       "eth0: " +
              str(get_ip_address('eth0')),  font=font, fill=255)
    # draw.text((x, top+8),     "wlan0: " + str(get_ip_address('wlan0')), font=font, fill=255)

    # Alternate solution: Draw the GPU usage as text
    # draw.text((x, top+8),     "GPU:  " +"{:3.1f}".format(GPU)+" %", font=font, fill=255)
    # We draw the GPU usage as a bar graph
    string_width, string_height = font.getsize("GPU:  ")
    # Figure out the width of the bar
    full_bar_width = width-(x+string_width)-1
    gpu_usage = get_gpu_usage()
    # Avoid divide by zero ...
    if gpu_usage == 0.0:
        gpu_usage = 0.001
    draw_bar_width = int(full_bar_width*(gpu_usage/100))
    draw_stat.text((x, top+8),     "GPU:  ", font=font, fill=255)
    draw_stat.rectangle((x+string_width, top+12, x+string_width +
                    draw_bar_width, top+14), outline=1, fill=1)

    # Show the memory Usage
    draw_stat.text((x, top+16), str(MemUsage.decode('utf-8')), font=font, fill=255)
    # Show the amount of disk being used
    draw_stat.text((x, top+25), str(Disk.decode('utf-8')), font=font, fill=255)

    # Display image.
    disp.display(image_stat)
    # 1.0 = 1 second; The divisor is the desired updates (frames) per second
    time.sleep(1.0/4)

def init_stars(num_stars, max_depth):
    stars = []
    for i in range(num_stars):
        # A star is represented as a list with this format: [X,Y,Z]
        star = [randrange(-25, 25), randrange(-25, 25), randrange(1, max_depth)]
        stars.append(star)
    return stars


def move_and_draw_stars(stars, max_depth):
    origin_x = device.width // 2
    origin_y = device.height // 2

    with canvas(device) as draw:
        for star in stars:
            # The Z component is decreased on each frame.
            star[2] -= 0.19

            # If the star has past the screen (I mean Z<=0) then we
            # reposition it far away from the screen (Z=max_depth)
            # with random X and Y coordinates.
            if star[2] <= 0:
                star[0] = randrange(-25, 25)
                star[1] = randrange(-25, 25)
                star[2] = max_depth

            # Convert the 3D coordinates to 2D using perspective projection.
            k = 128.0 / star[2]
            x = int(star[0] * k + origin_x)
            y = int(star[1] * k + origin_y)

            # Draw the star (if it is visible in the screen).
            # We calculate the size such that distant stars are smaller than
            # closer stars. Similarly, we make sure that distant stars are
            # darker than closer stars. This is done using Linear Interpolation.
            if 0 <= x < device.width and 0 <= y < device.height:
                size = (1 - float(star[2]) / max_depth) * 4
                if (device.mode == "RGB"):
                    shade = (int(100 + (1 - float(star[2]) / max_depth) * 155),) * 3
                else:
                    shade = "white"
                draw.rectangle((x, y, x + size, y + size), fill=shade)


def main():
    delay = 60 #60 second delay between stats and screensaver
    max_depth = 32
    stars = init_stars(512, max_depth)
    t_end = time.time() + delay
    screenSaver = False

    while True:
        if(time.time() > t_end):
           t_end = time.time() + 60
           screenSaver = not screenSaver

        if(screenSaver):
           move_and_draw_stars(stars, max_depth)
        else:
           draw_stats()

if __name__ == "__main__":
    try:
        device = disp
        main()
    except KeyboardInterrupt:
        pass
