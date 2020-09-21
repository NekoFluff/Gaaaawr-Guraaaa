import json
import re
import parselmouth
from parselmouth.praat import call

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import math

from pydub import AudioSegment
from pydub.playback import play
from PyInquirer import prompt
from pprint import pprint
import os

questions = [
    {
        'type': 'input',
        'name': 'sound_file',
        'message': 'What\'s the path of the sound file?',
    }
]
answers = prompt(questions)
# pprint(answers)

# Load the main sound
snd = parselmouth.Sound(answers['sound_file'])


def get_song_name():
    base_name = os.path.basename(answers['sound_file'])
    return base_name[:-4]


song_name = get_song_name()


def get_output_folder():
    folder_location = './output/{}'.format(song_name)
    if not os.path.exists(folder_location):
        os.mkdir(folder_location)
    # print('base_name', base_name[:-4])
    return folder_location


output_folder = get_output_folder()


def save_pitch_and_pulse(sound):
    manipulation = call(sound, "To Manipulation", 0.01, 75, 600)

    # Save pitch data
    pitch_tier = call(manipulation, "Extract pitch tier")
    pitch_tier_loc = '{}/vocals.PitchTier'.format(output_folder)
    pitch_tier.save_as_text_file(pitch_tier_loc)

    # Save pulse data
    pulse = call(manipulation, "Extract pulses")
    pulse_loc = '{}/vocals.Pulse'.format(output_folder)
    pulse.save_as_text_file(pulse_loc)


save_pitch_and_pulse(snd)


def change_pitch_by_shift(sound, shift):
    manipulation = call(sound, "To Manipulation", 0.01, 75, 600)

    pitch_tier = call(manipulation, "Extract pitch tier")
    print('Pitch Tier', pitch_tier)

    call(pitch_tier, "Shift frequencies", 0, 1000, shift, "Hertz")

    call([pitch_tier, manipulation], "Replace pitch tier")
    return call(manipulation, "Get resynthesis (overlap-add)")


def replace_pitch(sound, new_sound):
    # Get the pitch tier from the original sound
    manipulation = call(sound, "To Manipulation", 0.01, 75, 1500)
    pitch_tier = call(manipulation, "Extract pitch tier")

    # Get the manipulation object for the new sound
    manipulation2 = call(new_sound, "To Manipulation", 0.01, 75, 1500)

    # Replace the pitch tier of the new sound
    call([pitch_tier, manipulation2], "Replace pitch tier")
    return call(manipulation2, "Get resynthesis (overlap-add)")

# def change_pitch_by_factor(sound, factor):
#     manipulation = call(sound, "To Manipulation", 0.01, 75, 600)

#     pitch_tier = call(manipulation, "Extract pitch tier")
#     print('Pitch Tier', pitch_tier)

#     call(pitch_tier, "Multiply frequencies", sound.xmin, sound.xmax, factor)

#     call([pitch_tier, manipulation], "Replace pitch tier")
#     return call(manipulation, "Get resynthesis (overlap-add)")

# def generate_a():
#     song_duration = snd.duration
#     a_duration = a_snd.duration
#     a_count = math.ceil(song_duration/a_duration)
#     print('A count', a_count)
#     multiple_a = call(
#         [a_snd] * a_count, "Concatenate")
#     return multiple_a


def read_pitch(pitch_file):
    print('Reading Pitch Data...')

    f = open(pitch_file, "r")
    pitches = []
    data = f.read()
    # print('Read', data)
    time = re.findall('(?<=number = ).*', data)
    pitch = re.findall('(?<=value = ).*', data)

    time = list(map(lambda x: float(x), time))
    pitch = list(map(lambda x: float(x), pitch))

    f.close()
    return time, pitch


def read_pulse(pulse_file):
    print('Reading Pulse Data...')

    f = open(pulse_file, "r")

    data = f.read()
    # print('Read', data)
    pulse = re.findall('(?<=\] = )\d+\.\d+', data)
    pulse = list(map(lambda x: float(x), pulse))

    f.close()
    return pulse


def group_pulse_data(pulse):
    print('Grouping Pulse Data...')

    max_time_between_pulses = 0.3

    new_pulse = []
    start_group = 0
    end_group = None
    previous_pulse = None
    total_len = len(pulse)
    for idx, p in enumerate(pulse):
        print(idx, total_len)
        if previous_pulse is None:
            previous_pulse = p
            end_group = p

            # Create pause
            new_pulse.append(['silence', start_group, end_group - start_group])
            start_group = p
            continue
        else:
            if p - end_group > max_time_between_pulses:
                # Start new section
                duration = end_group - start_group

                # Create noise
                new_pulse.append(['sound', start_group, duration])

                # Set parameters
                previous_pulse = None
                start_group = end_group

            else:
                end_group = p

    # End section
    return new_pulse


def write_data(data, location):
    with open(location, 'w') as outfile:
        json.dump(data, outfile)


def read_data(location):
    with open(location) as json_file:
        return json.load(json_file)


# ---------------------------------------------------------------------- IF SAVING NEW DAYA
time, pitch = read_pitch("{}/vocals.PitchTier".format(output_folder))
write_data(time, "temp/pitch_p1.json")
write_data(pitch, "temp/pitch_p2.json")
pulse = read_pulse("{}/vocals.Pulse".format(output_folder))
write_data(pulse, "temp/pulse.json")

# ---------------------------------------------------------------------- LOAD DATA USING FILES BELOW (don't need to re-parse)
# time = read_data("temp/pitch_p1.json")
# pitch = read_data("temp/pitch_p2.json")
# pulse = read_data("temp/pulse.json")


# ---------------------------------------------------------------------- IF SAVING NEW DAYA
new_pulse = group_pulse_data(pulse)
# write_data(pulse, "temp/new_pulse.json")
print(new_pulse)

# Convert pulse into mp3_files
mp3_files = [] * 10
overflow = 0

for idx, pulse in enumerate(new_pulse):
    action, start, duration = pulse
    duration = duration * 1000

    # If silence
    if action == "silence":
        mp3_files.append(AudioSegment.silent(
            duration=max(duration + overflow, 0)))
        overflow = 0
    # Else make sound
    else:
        a_start = AudioSegment.from_wav("./a_sounds/a_short_start.wav")
        a_end = AudioSegment.from_wav("./a_sounds/a_short_end.wav")
        a = AudioSegment.from_wav("./a_sounds/a_short.wav")
        mp3_files.append(a_start)
        duration = duration - len(a_start)

        while (duration - len(a_end) > 0):
            # Add middle a sound
            mp3_files.append(a)
            duration = duration - len(a)

        mp3_files.append(a_end)
        duration = duration - len(a_end)
        overflow = duration


def save_song(mp3_files, save_location):
    first_mp3 = mp3_files[0]
    playlist = first_mp3

    for mp3 in mp3_files[1:]:
        playlist = playlist.append(mp3, crossfade=0)

    print("Song location:", save_location)

    with open(save_location, 'wb') as out_f:
        playlist.export(out_f, format='wav')


new_song_name = "Aaa_{}_no_pitch".format(song_name)
new_song_loc = "{}/{}.wav".format(output_folder, new_song_name)
print("Saving song without pitch...")
save_song(mp3_files, new_song_loc)

# Load it back into praat using parselmouth for pitch adjustment
new_snd = parselmouth.Sound(new_song_loc)
new_snd = replace_pitch(snd, new_snd)

print("Saving song with pitch...")
new_song_name = "Aaa_{}".format(song_name)
new_song_loc = "{}/{}.wav".format(output_folder, new_song_name)
new_snd.save(new_song_loc, parselmouth.SoundFileFormat.WAV)
print("Song location: ", new_song_loc)
