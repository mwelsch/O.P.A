# Offensive Pentesting Application

## A payload which connect to a server for remote access

## Roadmap:

- [ ] (Windows only) Keylogger 
- [ ] Access to Terminal or PowerShell
- [x] Stream device screen --> via pyautogui
- [ ] Server has easy-to-use web-interface
- [ ] Remote code execution with [rpyc](https://github.com/tomerfiliba-org/rpyc)
- [ ] Remote keyboard inputs --> via pyautogui
- [ ] Update the payload remotely
- [ ] File explorer with download, upload, create and delete features
- [ ] Integrate open source tools like:
  - [ ] (Windows, Linux, MacOS) https://github.com/peass-ng/PEASS-ng
  - [ ] (Probably deprecated because of the first tool; Windows) https://github.com/itm4n/PrivescCheck
  - [ ] (Windows) https://github.com/mandiant/SharPersist
  - [ ] (Windows) https://github.com/S3cur3Th1sSh1t/WinPwn
  - [ ] (Linux) https://github.com/liamg/traitor
  - [ ] (Linux) https://github.com/TH3xACE/SUDO_KILLER
  - [ ] ~~Tactics highlighted here https://attack.mitre.org/tactics/TA0003/ and here https://swisskyrepo.github.io/InternalAllTheThings/redteam/evasion/windows-amsi-bypass/#which-endpoint-protection-is-using-amsi~~ --> private repo
- [ ] Automatically generate report about system; including the above state open source tools checking for weaknesses
- [ ] Remote log viewer (for debugging)
- [ ] Server can handle multiple payloads connected to it in parallel
- [ ] Secure flask server [with password]
- [ ] (Optional) Payload can handle stuff via GMAIL and does not need a server
- [ ] (Optional) Server provides compiled executables via its webinterface
- [ ] (Optional) Leave no trace because everything is loaded into memory

This is the tool I want to run if I can execute a binary file on my target.
You might consider using https://github.com/n1nj4sec/pupy or https://github.com/tiagorlampert/CHAOS - this is a programming challenge for myself :)

## How to use

### Server

### Payload

You will need a serv

# Random design thoughts (probably not important for you):

Initially I thought I would hide the whole thing as a HTTP(S) app with no other traffic, to minimize detection.
~~But WebSockets seem to be mainstream now anyway, so I will use those for now. For better anti-detection a HTTP proxy can be used~~

I will do most communication through the HTTP(S) webserver. In case I want to live stream the screen I have multiple options:

- WebRTC
- Websockets
- Socket.IO (built on top of Websockets, but seems easier to handle)
- plain socket

I do want to take an easy and reliable approach: I tried using WebRTC with [this project](https://medium.com/@supersjgk/building-a-live-streaming-app-using-flask-opencv-and-webrtc-8cc8b521fa44#d598)
but honestly:

- I click on the link and the livestream takes forever to load.
- I cannot view it in multiple browser simultaniously (maybe that was because of the webcam api tho).
- It looks like a single stream and kind of difficult to built any other functionallity into the same site

Currently the project is therfore using sockets.io, with fallback methodes to simple HTTP requests

## Server

Handles multiple clients, should be able to

- receive & store/display
  - images (screenshots)
  - keyboard inputs
- send
  - keystrokes
  - maybe: commands to a powershell or something like that
- update the client script (for bugfixes, new functionality, etc.)

## Client

A payload, that:

- is a keylogger
- sends screenshots along with keylogs
  - ToDo find some kind of indicator of how often or when it is necessary to grab a screenshot
- can self-update
- can receive remote commands
  - keystrokes
  - maybe powershell commands
- if executed as admin: gain persistancy
- future: gain admin access or persistancy as normal user