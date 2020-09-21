# Gaaaawr Guraaaa

Let's sing Aaaaaaaaaaaaaaaaaaaaaa! Transform the vocals of any song into a robotic version of Gawr Gura's 'A' sound.

Example: https://twitter.com/SheavinNou/status/1307907111641403392

## How to use

1. Clone or download repo

2. Unzip repo if downloaded
3. Install pip requirements using requirements.txt (<a href="https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/">I recommend creating a new environment</a>)
   <br/>
   <code>
   pip install -r requirements.txt
   </code>

4. Insert song into input_songs folder

5. Run:
   <code>
   spleeter separate -i ./input_songs/song_name.mp3 -o output
   </code>

Details on spleeter can be found <a href="https://github.com/deezer/spleeter">HERE</a>

6. Then run:
   <code>
   python ./main.py
   </code>

7. Input the vocals file generated by spleeter:
   <code>
   output/song_name/vocals.wav
   </code>

8. The new song is located at:
   <code>
   output/song_name/Aaa_song_name.mp3
   </code>

9. Enjoy a robotic Gura!

10. You can find the accomaniment.wav and vocal.wav file in the folder:
    <code>
    output/song_name/accompaniment
    </code>

Have fun mashing it together :3
