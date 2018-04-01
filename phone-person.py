#aplay test.wav --device=plughw:1,0 -Dplug:default
#arecord --device=plughw:0,0 --format S16_LE --rate 44100 -c1 test.wav
print("setting up")

#import modules
from subprocess import call
import pyaudio
import speech_recognition as sr
import re
from time import sleep
import os
import RPi.GPIO as gpio

speaker = '--device=plughw:1,0'
r = sr.Recognizer()
r.energy_threshold = 4000
fail = "fail"
call(['cp', '~/.Casoundrc', '~/.asoundrc'])
gpio.cleanup()
gpio.setmode(gpio.BCM)
red_led = 26
red_led_state = False
gpio.setup(red_led, gpio.OUT)
gpio.output(red_led, 0)

def play(file):
    print("playing %s" % file)
    call(['aplay', file, speaker])

def speak(text, voice='f'):
    if voice == 'f':
        call(['pico2wave', '-w', 'tempVoiceFile.wav', text])
        play('tempVoiceFile.wav')
        call(['rm', 'tempVoiceFile.wav'])
    if voice == 'r':
        call(['espeak', text])

def listen():
    with sr.Microphone(device_index = 2, chunk_size = 512) as source:
        print('listening...')
        audio = r.listen(source)
        print('processing...')
    try:
        message = (r.recognize_google(audio, language = 'en-us', show_all=False))
        print("you said %s" % message)
        return(message)
    except Exception as e:
        print("not understood, Error:")
        print(e)

def waitforword(words, response='I did not understand that response...', voice='f', failresponse="", trysLeft=3):
    while trysLeft >= 0:
        speech = listen()
        for i in range(0, len(words)):
            regexp = re.compile(words[i])
            try:
                if regexp.search(speech):
                    print("Option %s spoken" % i)
                    return(i)
            except TypeError:
                print("failed to understand.")
                break
        if not trysLeft == 0:
            speak(response, voice)
        trysLeft -= 1
    speak(failresponse, voice)
    return(fail)

def programStart():
    print("phone person program running")
    speak('program started', 'r')
    status = waitforword([r'dial|call|connect|talk', r'cancel|shutdown|stop|shut down'],\
                         "Please speak the word: dial: into the phone: to connect your call, or: cancel: to cancel.", "r", "Goodbye.", 10)
    if status == 1 or status == fail:
        speak('goodbye!', 'r')
        gpio.cleanup()
        os.abort()
    speak('Hello!! Thank you for calling me!')
    howAreYou()


def howAreYou():
    speak('How are you today?')
    res = waitforword([r'bad|awful|terrible|horrible', r'well|good|great|awesome|wonderful|amazing'], "Could you say that again?", 'f', \
                      "I cant figure out if your good or not. I hope your good!", 3)
    if res == 1:
        speak('O thats great! I not bad either!')
    if res == 0:
        speak('O thats too bad. I hope your day gets better!')

programStart()

class Words:
    goodbye = re.compile(r'goodbye|by|bye|I have to go')
    thankyou = re.compile(r'thank you')
    how_are_you = re.compile(r'how are you')
    shutdown = re.compile(r'shutdown|shut down|turn yourself off|power down')
    hello = re.compile(r'hello|hi')
    ledOn = re.compile(r'turn the led|turn the light|turn on the|turn the|turn off the')

word = Words()

while True:
    speech = listen()
    try:
        if word.goodbye.search(speech):
            speak('You have to go? Ok! Goodbye!')
            print("RESTARTING")
            sleep(2)
            programStart()
        elif word.how_are_you.search(speech):
            speak("I'm good thank you,")
            howAreYou()
        elif word.thankyou.search(speech):
            speak('Your Welcome!')
        elif word.shutdown.search(speech):
            speak("goodbye")
            sleep(0.5)
            speak("goodbye", 'r')
            gpio.cleanup()
            os.abort()
        elif word.hello.search(speech):
            speak("Hello!")
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
        else:
            speak("Sorry, I don't know what that means yet...")
    except TypeError:
        print('not understood')
        speak("sorry, I didn't understand you. could you say that again?")


gpio.cleanup()
    
