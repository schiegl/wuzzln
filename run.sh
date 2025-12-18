image_name="wuzzln"
port="8501"

docker build -t "$image_name" .
mkdir -p "/home/$USER/tmp"

docker run \
    --name "$image_name" \
    --rm \
    --user 1000:1000 \
    --detach `# run in background` \
    --publish "$port":"$port" \
    --security-opt no-new-privileges `# after starting no new privileges` \
    --cap-drop all `# no linux capabilities` \
    --read-only `# read only filesystem` \
    -v "/home/$USER/database:/home/me/database:rw" `# mount database files` \
	-v "/home/$USER/tmp:/tmp:rw" `# uv run needs it` \
    "$image_name"
