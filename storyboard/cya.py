"""
This is a script that attempts to parse a txt file and create images for each line,
audio for each line, and a video of the images and audio.
"""

import contextlib
import os
import subprocess
from gtts import gTTS
import scripts
import time
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import shutil
import av
from dataclasses import dataclass
import arrow


@dataclass
class Story:
    """
    A class that represents a story. It contains the text of the story, the
    images of the story, the audio of the story, and the video of the story.
    and all the other stuff
    """

    file_path: str
    file_prefix: str
    art_style: str
    text: str = None
    story_dict: list = None

    cached: bool = False
    cache_path: str = "storyboard/cache/"
    last_updated = arrow.now().isoformat()
    ignore_cache = False

    def get_text(self):
        """
        This function gets the text file and prepares it for parsing.
        Returns:
            list: a list of dictionaries with a text key and the value of each line.
        Example:
            [{'text': 'This is the first line.'}, {'text': 'This is the second line.'}]
        """
        # check if a cached story exists
        # if it does, return it
        # if not, get the text file and return it
        # import json
        # with contextlib.suppress(json.JSONDecodeError):
        #     if os.path.exists("storyboard/story.json"):
        #         # ensure the story is not empty
        #         with open("storyboard/story.json", "r") as story:
        #             story_dict = json.load(story)
        #         if story_dict:
        #             return story_dict

        print(f"Getting text from {self.file_path}")
        with open(self.file_path, "r") as text:
            story = [
                line[:-1]
                for line in text
                if not line.startswith("The AI response returned in")
                   and line not in ["", " "]
            ]

        story_dict = [{"text": line} for line in story if len(line) > 0 or line != b""]
        # remove any dictionaries that look like {"text": ""} or
        story_dict = [line for line in story_dict if line["text"] != ""]
        story_dict.append({"file_prefix": self.file_prefix, "file_path": self.file_path})
        # print("Caching story")
        # cache_story(story_dict)
        print("Text parsed")
        self.text = story
        self.story_dict = story_dict
        return story_dict

    def generate_audio(self):
        """
        This function takes the story dictionary and generates audio for each line using gTTS.
        Args:
            story_dict:

        Returns:
            list: a list of dictionaries with a text key and the value of each line with an audio key
            and the value of the audio file name.
        Example:
            [{'text': 'This is the first line.', 'audio': 'audio_0.mp3'}, {'text': 'This is the second line.', 'audio': 'audio_1.mp3'}]

        """
        # check if the audio folder exists
        # if not, create it
        print("Checking for audio folder")
        if not os.path.exists(f"storyboard/audio/{self.file_prefix}"):
            print("Audio folder not found, creating it")
            os.makedirs(f"storyboard/audio/{self.file_prefix}")
        print("Audio folder found")
        for index, line in enumerate(self.story_dict):
            # check if the audio file already exists
            # if it does, skip it
            # if not, generate the audio file
            # skip the last modified key
            if not line.get("audio"):
                print(f"Skipping {line} as there is no audio file for this index")
            if not self.ignore_cache:
                print(f"Checking for audio file for line {index}")
                if os.path.exists(f"storyboard/audio/{self.file_prefix}/audio_{index}.mp3"):
                    print(f"Audio file for line {index} found")
                    line["audio"] = f"audio_{index}.mp3"
                    continue

            try:
                print(f"Audio file for line {index} not found, generating it")
                tts = gTTS(text=line["text"], lang="en")
                tts.save(f"storyboard/audio/{self.file_prefix}/audio_{index}.mp3")
                line["audio"] = f"storyboard/audio/{self.file_prefix}/audio_{index}.mp3"
            except Exception as e:
                print(e)
                print(f"Audio file for line {index} could not be generated, {line}")
        print("Audio generated")
        self.cache_story()

    def cache_story(self):
        """
        This function takes the story dictionary and caches the story as a json file.

        Returns:
            None
        """
        import json
        import arrow

        print("let's cache this story")
        self.cache_path = f"storyboard/cache/{self.file_prefix}.json"
        if not os.path.exists(self.cache_path):
            print("Cache file not found, creating it")
            with open(self.cache_path, "w") as cache:
                json.dump(self.story_dict, cache)
        try:
            with open(self.cache_path, "w") as story:
                # find the last_updated key
                # if it exists, update it
                # if not, add it
                json.dump(self.story_dict, story)
            print("Story cached")
            self.last_updated = arrow.now().isoformat()
            self.cached = True
        except Exception as e:
            print(e)
            print("Story could not be cached")
            self.cached = False

    def generate_images(self):
        """
        This function uses scripts/txt2img.py to generate images for each line.

        Args:
            story_dict:
        example:
            [{'text': 'This is the first line.', 'audio': 'audio_0.mp3'},
            {'text': 'This is the second line.', 'audio': 'audio_1.mp3'}]

        Returns:
            [{'text': 'This is the first line.', 'audio': 'audio_0.mp3', 'image': 'image_0.png'},
            {'text': 'This is the second line.', 'audio': 'audio_1.mp3', 'image': 'image_1.png'}]
        """
        # check if the images folder exists
        # if not, create it

        for index, line in enumerate(self.story_dict):
            # check if the image file already exists
            # if it does, skip it
            # if not, generate the image file
            # skip the last modified key
            if not self.ignore_cache:
                print(f"Checking for image file for line {index}")
                if os.path.exists(
                        f"outputs/txt2img-samples/image_{self.file_prefix}_image_{index}.png"
                ):
                    print(f"Image file for line {index} found")
                    line[
                        "image"
                    ] = f"outputs/txt2img-samples/image_{self.file_prefix}_image_{index}.png"
                    continue
            try:
                print(f"Image file for line {index} not found, generating it")
                # run the txt2img.py script with the line text as the prompt
                filename = self.generate_path_from_script(
                    f'{line["text"]}, {self.art_style} art style'.replace(":", " "),
                    index,
                )
                line[
                    "image"
                ] = f"outputs/txt2img-samples/image_{self.file_prefix}_image_{index}.png"
                print(f"Image file for line {index} generated")
                # overlay the prompt on the image
                # save the image
                self.overlay_prompt(line["text"], filename)
            except Exception as e:
                print(e)
                print(f"Image file for line {index} could not be generated, {line}")

        self.cache_story()

    @staticmethod
    def overlay_prompt(text, file):
        """
        This function overlays the prompt on the image.
        Args:
            text: str the prompt to overlay
            file: str the path to the image file

        Returns:
            None
        Side Effects:
            Overlays the prompt on the image and saves it.
        """
        # load the image
        # create a font

        image = Image.open(file)
        draw = ImageDraw.Draw(image)
        font_size = 36
        font = ImageFont.truetype("Arial", font_size)

        textwidth, textheight = draw.textsize(text, font)

        image_width, image_height = image.size
        # Adjust font size if text is too wide
        while textwidth > image_width:
            font_size -= 1
            font = ImageFont.truetype("Arial", font_size)
            textwidth, textheight = draw.textsize(text, font)

        x = (image_width - textwidth) / 2
        y = 0

        draw.text((x - 1, y - 1), text, font=font, fill=(0, 0, 0))
        draw.text((x + 1, y - 1), text, font=font, fill=(0, 0, 0))
        draw.text((x - 1, y + 1), text, font=font, fill=(0, 0, 0))
        draw.text((x + 1, y + 1), text, font=font, fill=(0, 0, 0))
        draw.text((x, y), text, font=font, fill=(255, 255, 255))

        image.save(file)

    def generate_path_from_script(self, text, line_index):
        """
        This function runs the txt2img.py script with the line text as the prompt.
        Args:
            text: str the prompt to overlay
            line_index: int the index of the line in the story
        Returns:
            the path to the image file generated by the script
        """
        script_file = "scripts/txt2img.py"
        print(f"Running {script_file} with {text}")
        try:
            subprocess.run(
                [
                    "python",
                    script_file,
                    "--prompt",
                    text,
                    "--n_samples",
                    "1",
                    "--n_iter",
                    "1",
                    "--plms",
                    "--name",
                    f"{self.file_prefix}_image_{line_index}",
                ]
            )
        except Exception as e:
            print(e)
            print(f"Image file for {text} could not be generated")
            return None
        return (
            f"outputs/txt2img-samples/image_{self.file_prefix}_image_{line_index}.png"
        )

    def generate_video(self):
        """
        This function uses the story dictionary to generate a video using moviepy.
        Args:
            story_dict:
            [{'text': 'This is the first line.', 'audio': 'audio_0.mp3', 'image': 'image_0.png'},
            {'text': 'This is the second line.', 'audio': 'audio_1.mp3', 'image': 'image_1.png'}]

        Returns:
            video.mp4

        """
        # check if the video folder exists
        # if not, create it
        print("Checking for video folder")
        if not os.path.exists(f"storyboard/video/{self.file_prefix}"):
            print("Video folder not found, creating it")
            os.makedirs(f"storyboard/video/{self.file_prefix}")
        else:
            print("Video folder found")
        for index, line in enumerate(self.story_dict):
            line["video"] = f"storyboard/video/{index}.mp4"
            if line.get("last_updated"):
                continue
            if not self.ignore_cache:
                print(f"Checking for video file for line {index}")
                if os.path.exists(f"storyboard/video/{self.file_prefix}/{index}.mp4"):
                    print(f"Video file for line {index} found")
                    continue
            try:
                try:
                    audio_clip = AudioFileClip(f"storyboard/audio/{self.file_prefix}/{line['audio']}")
                except Exception as e:
                    audio_clip = AudioFileClip(line["audio"])
                image_clip = ImageClip(
                    line["image"], duration=audio_clip.duration
                ).set_audio(audio_clip)
                image_clip.write_videofile(f"storyboard/video/{self.file_prefix}/{index}.mp4", fps=24)
            except Exception as e:
                print(e)
                continue
        self.cache_story()

    def concatenate_videos(
            self

    ):
        """
        This function concatenates all the videos into one final video.
        Args:
            video_directory: str the directory containing the videos to concatenate
            output_file: str the path to the output file
        Returns:
            None
        """
        # Get a list of all the video files in the directory
        import re
        video_directory = f"storyboard/video/{self.file_prefix}/"
        output_path = f"storyboard/final_video/{self.file_prefix}"
        output_file = f"storyboard/final_video/{self.file_prefix}/final_video.mp4"
        video_files = [f for f in os.listdir(video_directory) if f.endswith(".mp4")]
        # ensure that the files are in order from storyboard/video/0.mp4 to n and retain the order and path
        # create the final video directory if it doesn't exist
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        video_files = sorted(
            video_files, key=lambda x: int(re.search(r"\d+", x).group())
        )
        # Create the concat demuxer file
        with open("concat_list.txt", "w") as f:
            for video_file in video_files:
                f.write(f"file {video_directory}/{video_file}'\n")
        concat_file = "concat_list.txt"

        # Use FFmpeg to combine the videos using the concat demuxer
        command = f"ffmpeg -f concat -safe 0 -i {concat_file} -c copy {output_file}"
        os.system(command)

    def check_if_final_video_exists(self):
        """
        This function checks if the final video exists.
        Args:
            None
        Returns:
            bool
        """
        breakpoint()
        return bool(
            os.path.exists(
                f"storyboard/final_video/{self.file_prefix}/final_video.mp4"
            )
        )


if __name__ == "__main__":
    print("Enter txt file path or press enter to use default file")
    default_file = (
        "storyboard/stories/Logans_Horror_Thriller_story_2022-09-04T10:29:14.971905.txt"
    )
    file_path = input()
    file_prefix = "logan"
    if not file_path:
        file_path = default_file
    else:
        file_prefix = file_path.split("/")[-1].split(".")[0].split("_")[0]
    if not os.path.exists(file_path):
        print("File not found")
        exit()
    art_style = input("Enter art style or press enter to use default style of Greg Rutkowski")
    if not art_style:
        art_style = "Greg Rutkowski"
    story = Story(file_path, file_prefix, art_style)
    if final_video := story.check_if_final_video_exists():
        print("Final video found, do you want to regenerate it?")
        regenerate = input("Enter y or n")
        if regenerate.lower().startswith("n"):
            print("Exiting")
            exit()
        else:
            story.ignore_cache = True

    print("Getting text...")
    story.get_text()
    print("Generating audio...")
    story.generate_audio()
    print("Generating images...")
    story.generate_images()
    print("Generating Video...")
    story.generate_video()
    print("Generating final video...")
    story.concatenate_videos()
