
function usage(){
    echo "Usage:"
    echo "    ./create-overlays.sh userlist"
    exit 1
}

if [ $# -lt 1 ]; then
    usage
fi

userlist=$1
shift

userlist="$(cat "$userlist")"

font="$(fc-match -f '%{file}' Monospace)"
text_options="-pointsize 32 -fill white -channel RGBA -font "$font""
background="-define gradient:vector=300,0,350,0 gradient:black-none"

while read user; do
    convert \
        -size 400x50 \
        -delay 100 -loop 0 \
        \( $background $text_options -draw "text 0,30 '$user'" \) \
        \( $background $text_options -draw "text 0,30 '$user|'" \) \
        -layers Optimize \
        foo.gif
done <<< "$userlist"

