
function usage(){
    echo "Usage:"
    echo "    ./collect-users.sh user machine1 [machine2] [machine3] [...]"
    exit 1
}

if [ $# -lt 2 ]; then
    usage
fi

user=$1
shift

all_entries=""

while [ $# -gt 0 ]; do
    machine=$1
    shift

    user_list="$(ssh "$user"@"$machine" users)"
    csv_entries="$(echo "$user_list" | awk -v machine="$machine" -v RS=" " '{{print "\x22" machine "\x22,\x22" $1 "\x22"}}')"
    all_entries="$all_entries$csv_entries"
done

all_entries="$(echo "$all_entries" | sort -u)"
echo "Machine,User"
echo "$all_entries"
