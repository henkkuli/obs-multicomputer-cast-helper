from obswebsocket import obsws, events, requests

class Obs:

    def __init__(self, url, port, password, queue):
        self.__ws = obsws(url, port, password)
        self.currently_streaming = []
        self.__queue = queue


    def get_currently_streaming_computers(self):
        ws = self.__ws

        # First request a list of scenes
        scenes = ws.call(requests.GetSceneList())
        current_scene = scenes.getCurrentScene()
        scenes = scenes.getScenes()

        logger.info("Finding out currently streaming computers")
        
        # Then organize them by name
        scenes = {scene['name']: scene for scene in scenes}

        streaming_computers = []
        def handle_scene(scene):
            for source in scene['sources']:
                type = source['type']
                if type == 'ffmpeg_source':
                    name = source['name']
                    if name.startswith(source_prefix):
                        index = int(name[len(source_prefix):])
                        streaming_computers.append(index)
                elif type == 'scene':
                    handle_scene(scenes[source['name']])

        handle_scene(scenes[current_scene])

        self.currently_streaming = streaming_computers
