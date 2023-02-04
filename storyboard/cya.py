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

def get_text():
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
    LOGANS_FILE = (
        "storyboard/stories/Logans_Horror_Thriller_story_2022-09-04T10:29:14.971905.txt"
    )
    print(f"Getting text from {LOGANS_FILE}")
    with open(LOGANS_FILE, "r") as text:
        story = [
            line[:-1]
            for line in text
            if not line.startswith("The AI response returned in")
               and line not in ["", " "]
        ]

    story_dict = [{"text": line} for line in story if len(line) > 0 or line != b'']
    # remove any dictionaries that look like {"text": ""} or
    story_dict = [line for line in story_dict if line["text"] != ""]
    # print("Caching story")
    # cache_story(story_dict)
    print("Text parsed")
    return story_dict


def generate_audio(story_dict):
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
    if not os.path.exists("storyboard/audio"):
        print("Audio folder not found, creating it")
        os.makedirs("storyboard/audio")
    print("Audio folder found")
    for index, line in enumerate(story_dict):
        # check if the audio file already exists
        # if it does, skip it
        # if not, generate the audio file
        # skip the last modified key
        print(f"Checking for audio file for line {index}")
        if os.path.exists(f"storyboard/audio/audio_{index}.mp3"):
            print(f"Audio file for line {index} found")
            line["audio"] = f"audio_{index}.mp3"
            continue
        try:
            print(f"Audio file for line {index} not found, generating it")
            tts = gTTS(text=line["text"], lang="en")
            tts.save(f"storyboard/audio/audio_{index}.mp3")
            line["audio"] = f"storyboard/audio/audio_{index}.mp3"
        except Exception as e:
            print(e)
            print(f"Audio file for line {index} could not be generated, {line}")
    print("Audio generated")
    cache_story(story_dict)
    return story_dict


def cache_story(wip_dict):
    """
    This function takes the story dictionary and caches the story as a json file.
    Args:
        wip_dict:

    Returns:
        None
    """
    import json
    import arrow
    print("let's cache this story")
    wip_dict.append({"last_updated": arrow.now().isoformat()})
    with open("storyboard/story.json", "w") as story:
        # find the last_updated key
        # if it exists, update it
        # if not, add it
        json.dump(wip_dict, story)
    print("Story cached")


def generate_images(story_dict):
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

    for index, line in enumerate(story_dict):
        # check if the image file already exists
        # if it does, skip it
        # if not, generate the image file
        # skip the last modified key

        print(f"Checking for image file for line {index}")
        if os.path.exists(f"outputs/txt2img-samples/image_logan_image_{index}.png"):
            print(f"Image file for line {index} found")
            line["image"] = f"outputs/txt2img-samples/image_logan_image_{index}.png"
            continue
        try:
            print(f"Image file for line {index} not found, generating it")
            # run the txt2img.py script with the line text as the prompt
            filename = generate_path_from_script(f'{line["text"]}, Greg Rutkowski art style'.replace(":", " "), index)
            line["image"] = f"outputs/txt2img-samples/image_logan_image_{index}.png"
            print(f"Image file for line {index} generated")
            # overlay the prompt on the image
            # save the image
            overlay_prompt(line["text"], filename)
        except Exception as e:
            print(e)
            print(f"Image file for line {index} could not be generated, {line}")

    cache_story(story_dict)
    return story_dict


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


def generate_path_from_script(text, line_index):
    """
    This function runs the txt2img.py script with the line text as the prompt.
    Args:
        text:

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
                '--prompt',
                text,
                "--n_samples",
                "1",
                "--n_iter",
                "1",
                "--plms",
                "--name",
                f"logan_image_{line_index}",
            ]
        )
    except Exception as e:
        print(e)
        print(f"Image file for {text} could not be generated")
        return None
    return f"outputs/txt2img-samples/image_logan_image_{line_index}.png"


def generate_video(story_dict):
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
    if not os.path.exists("storyboard/video"):
        print("Video folder not found, creating it")
        os.makedirs("storyboard/video")
    print("Video folder found")
    for index, line in enumerate(story_dict):
        line["video"] = f"storyboard/video/{index}.mp4"
        if line.get("last_updated"):
            continue
        print(f"Checking for video file for line {index}")
        if os.path.exists(f"storyboard/video/{index}.mp4"):
            print(f"Video file for line {index} found")
            continue
        audio_clip = AudioFileClip(f"storyboard/audio/{line['audio']}")
        image_clip = ImageClip(line["image"], duration=audio_clip.duration).set_audio(audio_clip)
        image_clip.write_videofile(f"storyboard/video/{index}.mp4", fps=24)
    cache_story(story_dict)

    return story_dict



def concatenate_videos(video_directory="storyboard/video", output_file="storyboard/final_video/final_video.mp4"):
    """
    This function concatenates all the videos into one final video.
    Args:
        dir_path: str the path to the directory containing the videos
    Returns:
        None
    """
    # Get a list of all the video files in the directory
    import re
    video_files = [f for f in os.listdir(video_directory) if f.endswith('.mp4')]
    # ensure that the files are in order from storyboard/video/0.mp4 to n and retain the order and path

    video_files = sorted(video_files, key=lambda x: int(re.search(r'\d+', x).group()))
    # Create the concat demuxer file
    with open('concat_list.txt', 'w') as f:
        for video_file in video_files:
            f.write(f"file {video_directory}/{video_file}'\n")
    concat_file = 'concat_list.txt'

    # Use FFmpeg to combine the videos using the concat demuxer
    command = f"ffmpeg -f concat -safe 0 -i {concat_file} -c copy {output_file}"
    os.system(command)





if __name__ == "__main__":
    print("Getting text...")
    story_dictionary = get_text()
    print("Generating audio...")
    story_with_audio = generate_audio(story_dictionary)
    print("Generating images...")
    story_with_images = generate_images(story_with_audio)
    print("Generating Video...")
    story_with_videos = generate_video(story_with_images)
    print("Generating final video...")
    concatenate_videos()

