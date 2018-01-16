
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

userlist="$(cat "$userlist" | cut -d'"' -f 6)"

font="$(fc-match -f '%{file}' Monospace)"
text_options="-pointsize 32 -fill white -channel RGBA -font "$font""
background="-define gradient:vector=300,0,350,0 gradient:black-none"

idx=1
while read user; do
    convert \
        -size 400x50 \
        \( $background $text_options -draw "text 0,30 '$user|'" \) \
        -layers Optimize \
        "user-overlays/user-$i.png"

    i=$((i+1))
done <<< "$userlist"

