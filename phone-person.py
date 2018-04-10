#aplay test.wav --device=plughw:1,0 -Dplug:default
#arecord --device=plughw:0,0 --format S16_LE --rate 44100 -c1 test.wav
print("setting up")

#import modules

from subprocess import call
from time import sleep

call(['rm', '/home/pi/.asoundrc'])
call(['cp', '/home/pi/.Casoundrc', '/home/pi/.asoundrc'])
sleep(0.5)

import pyaudio
import speech_recognition as sr
import re
import os
import RPi.GPIO as gpio

speaker = '--device=plughw:1,0'
r = sr.Recognizer()
r.energy_threshold = 3000
fail = "fail z76487"
gpio.setmode(gpio.BCM)
red_led = 26
red_led_state = False
gpio.setup(red_led, gpio.OUT)
gpio.output(red_led, 0)

def play(file):
    print("playing %s" % file)
    call(['aplay', file, speaker])

def speak(text, voice='f'):
    print("speaking %s..." % text)
    if voice == 'f':
        call(['pico2wave', '-w', 'tempVoiceFile.wav', text])
        play('tempVoiceFile.wav')
        call(['rm', 'tempVoiceFile.wav'])
    if voice == 'r':
        call(['espeak', text])

def listen():
    try:
        with sr.Microphone(device_index = 1, chunk_size = 512) as source:
            print('listening...')
            audio = r.listen(source)
            print('processing...')
    except:
        with sr.Microphone(device_index = 2, chunk_size = 512) as source:
            print('listening...')
            audio = r.listen(source)
            print('processing...')
    try:
        message = (r.recognize_google(audio, language = 'en-us', show_all=False))
        print("you said %s" % message)
        return(message)
    except Exception as e:
        return(fail)
        print("not understood, Error:")
        print(e)

def waitforword(words, response='I did not understand that response...', voice='f', failresponse="", trysLeft=3):
    while trysLeft >= 0:
        speech = listen()
        for i in range(0, len(words)):
            regexp = re.compile(words[i])
            if not speech == fail:
                if regexp.search(speech):
                    print("Option %s spoken" % i)
                    return(i)
            else:
                print("failed to understand.")
                break
        if not trysLeft == 0:
            speak(response, voice)
        trysLeft -= 1
    speak(failresponse, voice)
    return(fail)

def programStart():
    print("phone person program running")
    #speak("Please speak the word: dial: into the phone: to connect your call, or: cancel: to turn off the phone.", 'r')
    status = waitforword([r'dial|call|connect|talk', r'cancel|shutdown|stop|shut down'],\
                         "Please speak the word: dial: into the phone: to connect your call, or: cancel: to turn off the phone.", "r", "Goodbye.", 10)
    if status == 1 or status == fail:
        stop('a')
    play('phone-ringing.wav')
    play('phone-ringing.wav')
    play('phone-pickup.wav')
    speak('Hello!! Thank you for calling me! Please be patient with me, I take a long time to answer.')
    howAreYou()


def howAreYou():
    speak('How are you today?')
    res = waitforword([r'bad|awful|terrible|horrible', r'well|good|great|awesome|wonderful|amazing'], "Could you say that again?", 'f', \
                      "I cant figure out if your good or not. I hope your good!", 3)
    if res == 1:
        speak('O thats great! I not bad either!')
    if res == 0:
        speak('O thats too bad. I hope your day gets better!')


class Words:
    goodbye = re.compile(r'goodbye|by|bye|I have to go')
    thankyou = re.compile(r'thank you')
    how_are_you = re.compile(r'how are you')
    shutdown = re.compile(r'shutdown|shut down|turn yourself off|power down|turn the phone off')
    hello = re.compile(r'hello|hi')
    ledOn = re.compile(r'turn the led|turn the light|turn on the|turn the|turn off the')
    hangup = re.compile(r'I hate you|you\'re the worst|your dum|dummy|stupid|go away|hang up|shut up')
    whatcanyoudo = re.compile(r'what can you do|what should I ask you|what can I')
    simonsays = re.compile(r'Simon Says|repeat after me|[could|can|will] you say|Simon says')
    takepicture = re.compile(r'take [a|an|another] [picture|photo|image]')
    yes = r'Yes|yes|yea|sure|great'
    no = r'No|no|nah|nope'

word = Words()

def stop(mode='r'):
    if mode == 'r':
        speak('goodbye!')
        play('phone-hangup.wav')
        print("RESTARTING...")
        sleep(1)
        programStart()
    else:
        print("stopping...")
        speak('turning phone off... goodbye.', 'r')
        gpio.cleanup()
        os.abort()
        
speak('program started', 'r')
programStart()
try:
    while True:
        speech = listen()
        if not speech == fail:
            if word.simonsays.search(speech):
                #speak("alright! say something and I'll repeat it")
                #sentence = listen()
                #if not sentence == fail:
                #    speak(sentence)
                #else:
                #    speak("sorry, I couldn't hear you...")
                try:
                    text = speech.split("Simon says" , 1)[1]
                    speak(text)
                except:
                    speak("Please say: Simon Says: plus whatever you want me to say")
            elif word.goodbye.search(speech):
                speak('You have to go? Ok!')
                stop()
            elif word.how_are_you.search(speech):
                speak("I'm good thank you,")
                howAreYou()
            elif word.thankyou.search(speech):
                speak('Your Welcome!')
            elif word.shutdown.search(speech):
                speak("goodbye")
                play('phone-hangup.wav')
                stop('a')
            elif word.hello.search(speech):
                speak("Hello! try asking me to turn on the l e d")
            elif word.ledOn.search(speech):
                if not red_led_state:
                    speak("I will turn the l e d on for you")
                    sleep(0.5)
                    gpio.output(red_led, 1);
                    red_led_state = True
                else:
                    speak("I will turn the l e d off for you")
                    sleep(0.5)
                    gpio.output(red_led, 0);
                    red_led_state = False
            elif word.hangup.search(speech):
                speak("I'm sorry.. would you like me to hang up?")
                res = waitforword([word.yes, word.no], 'would you like me to hang up?')
                if res == 0:
                    speak('o k.')
                    stop()
                if res == 1:
                    speak('o k.')
            elif word.takepicture.search(speech):
                speak("say cheese!")
                sleep(1)
                call(['fswebcam', 'tempImageFile.jpg'])
                play('camera.wav')
                call("geeqie tempImageFile.jpg -t -f &", shell=True)
                sleep(1)
                speak("look at you!")
                sleep(6)
                call(['pkill', 'geeqie'])
            elif word.whatcanyoudo.search(speech):
                speak("Try asking me to turn the light on, how I am, you can ask me to repeat after you, to shutdown or hang up,\
    you can even insult me or tell me to hang up!, and more.")
            
            else:
                speak("I don't know what that means.. try asking me: what can you do")
        else:
            print('not understood')
            speak("sorry, I didn't understand you. could you say that again?")
except Exception as e:
    print("Error:\n %s" % e)
    gpio.cleanup()
    
