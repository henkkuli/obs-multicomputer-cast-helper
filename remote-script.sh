#!/bin/bash

# First get the arguments from the parent
user=$1
master_address=$2

# First find the correct display device
display=$(who | grep "$user" | awk '{{print $5}}' | tr -d "()" | grep ":[[:digit:]]*" | head -n1)
export DISPLAY=$display

# Then find the correct resolution
resolution=$(xdpyinfo | grep "dimensions:" | awk '{{print $2}}')

# And finally start streaming
ffmpeg \
    -video_size $resolution \
    -f x11grab \
    -i $display \
    -b:v 100M \
    -f mpegts $master_address < /dev/null
