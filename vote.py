import requests
import colorama
import random
import string
import time
import re
import tls_client
import random
import uuid
import base64
import threading
import os

def newRscriptsSession():
	ChromeIdentifier = "chrome" + str(random.randint(112, 120))
	session = tls_client.Session(
			client_identifier=ChromeIdentifier,
			random_tls_extension_order=True,
			header_order=[
					"Accept",
					"Accept-Encoding",
					"Accept-Language",
					"Alt-Used",
					"Connection",
					"Host",
					"Priority",
					"Referer",
					"TE",
					"User-Agent",
			],
	)
	return session

def GetNextAction(link, session, Name, proxy=None, headers=None):
    Scraped = session.get(link, proxy=proxy).text
    Chunks = re.findall(r'src="/_next/static/chunks/(\w+).js"', Scraped)
    for Chunk in Chunks:
        #print(f"Chunk: {Chunk}")
        Potential = session.get(f"https://rscripts.net/_next/static/chunks/{Chunk}.js", headers=headers).text
        Action = re.search(r'"(\w+)",\w+\.callServer,void 0,\w+\.findSourceMapURL,"' + Name + '"', Potential)

        if Action != None:
            ActionR = Action.group(1)
            return True, ActionR
        else:
            if Chunk == Chunks[len(Chunks)-1]:
                return False, "No Next-Action found, this should not happen!"
    return False, "Unknown Failure"

def GetScriptIDFromLink(Link, Session):
    Scraped = Session.get(Link)
    Scraped = Scraped.text

    ScrapedIds = re.findall(r"\\\"scriptId\\\":\\\"(\w+)\\\"", Scraped) # absolutely insane method
    ScriptId = ScrapedIds[0]
    return ScriptId

def getCookies():
    return [cookie for cookie in open("bots.txt", "r").read().splitlines() if cookie != "BOTS:"]

cacheAction = None
cacheScriptId = None

def votePost(link, mode, amount=9999, startFrom=0):
    global cacheAction
    global cacheScriptId
    cookies = getCookies()
    done = 0
    actuallydone = 0
    for cookie in cookies:
        if done >= amount:
            break
        done += 1
        if done < startFrom:
            continue
        
        session = newRscriptsSession()
        if cacheAction != None:
            nextResult, voteAction = True, cacheAction
        else:
            nextResult, voteAction = GetNextAction(link, session, "toggleScriptVote")
        if nextResult:
            if cacheAction == None:
                print("Vote action: " + voteAction)
                cacheAction = voteAction

        else:
            print("Failed to get vote action")
            print(voteAction)
            return
        
        if cacheScriptId != None:
            scriptId = cacheScriptId
        else:
            scriptId = GetScriptIDFromLink(link, session)

        if not scriptId:
            print("Failed to get script id")
        else:
            if cacheScriptId == None:
                print("Script ID: " + scriptId)
                print("------------------------")
            cacheScriptId = scriptId

        def _func():
            voteRequest = session.post(link, headers={
                "next-action": voteAction,
                "cookie": cookie
            }, json=[scriptId, mode])
            if voteRequest.status_code == 200:
                print(mode + "d" + " script!")
                print(voteRequest.text)
            else:
                print("failed to " + mode + " script")

        threading.Thread(target=_func).start()
        actuallydone += 1
        print("thread #" + str(actuallydone))

def start():
    voting = False
    voteUrl = ""
    voteMode = ""
    voteAmount = 0
    voteStartFrom = 0

    followbot = False
    followUsername = ""

    commentbot = False
    commentUrl = ""
    commentList = []

    profilebot = False
    profileUsername = ""
    profileCommetList = []

    print(f"""                        ___.           __   
        _______  ______ ____\\_ |__   _____/  |_ 
        \\_  __ \\/  ___// ___\\| __ \\ /  _ \\   __\\
        |  | \\/\\___ \\  \\___| \\_\\ (  <_> )  |  
        |__|  /____  >\\___  >___  /\\____/|__|  
                    \\/     \\/    \\/             
                    Accounts: {len(getCookies())}

    {colorama.Fore.GREEN}[{colorama.Fore.RESET}1{colorama.Fore.GREEN}]{colorama.Fore.RESET} Account Generator   {colorama.Fore.GREEN}[{colorama.Fore.RESET}2{colorama.Fore.GREEN}]{colorama.Fore.RESET} Vote Bot
    {colorama.Fore.GREEN}[{colorama.Fore.RESET}3{colorama.Fore.GREEN}]{colorama.Fore.RESET} Follow Bot          {colorama.Fore.GREEN}[{colorama.Fore.RESET}4{colorama.Fore.GREEN}]{colorama.Fore.RESET} Script Comment Bot
    {colorama.Fore.GREEN}[{colorama.Fore.RESET}5{colorama.Fore.GREEN}]{colorama.Fore.RESET} Profile Comment Bot
        
    """)
    choice = input(" [Choice] > ")
    if choice == "1":
        os.system("py accountGenerator.py")
        exit()
    elif choice == "2":
        voting = True
        voteUrl = input(" [URL] > ")
        voteMode = input(" [Like/Dislike] > ").lower()
        voteAmount = int(input(" [Amount Of Bots] > "))
        _voteStartFrom = input(" [Optional - Start From X] > ")
        if _voteStartFrom != "":
            voteStartFrom = int(_voteStartFrom)
    elif choice == "3":
        followbot = True
        followUsername = input(" [Username] > ")
    elif choice == "4":
        commentbot = True
        commentUrl = input(" [URL] > ")
        commentList = input(" Enter the things you want to comment as a list, seperate by \"; \" (Semi-colon and space)\n Type here > ").split("; ")
    elif choice == "5":
        profileUsername = input(" [Username] > ")
        profileCommetList = input(" Enter the things you want to comment as a list, seperate by \"; \" (Semi-colon and space)\n Type here > ").split("; ")

    if voting:
        votePost(voteUrl, voteMode, voteAmount, voteStartFrom)

    if followbot:
        sesh = newRscriptsSession()
        _, act = GetNextAction("https://rscripts.net/@" + followUsername, sesh, "toggleFollowUser")
        cookies = getCookies()
        done = 0
        for cookie in cookies:
            def _func():
                voteRequest = sesh.post("https://rscripts.net/@" + followUsername, headers={
                    "next-action": act,
                    "cookie": cookie
                }, json=[followUsername])
                if voteRequest.status_code == 200:
                    print("followed")
                else:
                    print("failed to follow")
                    print(voteRequest.text)

            threading.Thread(target=_func).start()
            done += 1
            print("thread #" + str(done))
            if done % 15 == 0:
                    time.sleep(1)

    if commentbot:
        sesh = newRscriptsSession()
        _, act = GetNextAction(commentUrl, sesh, "submitComment")
        scripid = GetScriptIDFromLink(commentUrl, sesh)
        cookies = getCookies()
        print("cooks: " + str(len(cookies)))
        done = 0
        while True:
            for cookie in cookies:
                def _func():
                    voteRequest = sesh.post(commentUrl, headers={
                        "next-action": act,
                        "cookie": cookie
                    }, json=[scripid, random.choice(commentList), "$undefined"])
                    if voteRequest.status_code == 200:
                        print("commented")
                        print(voteRequest.text)
                    else:
                        print("failed to comment")

                threading.Thread(target=_func).start()
                done += 1
                print("thread #" + str(done))
                if done % 25 == 0:
                    time.sleep(2)

    if profilebot:
        sesh = newRscriptsSession()
        _, act = GetNextAction("https://rscripts.net/@" + profileUsername, sesh, "addProfileComment")
        cookies = getCookies()
        print("cooks: " + str(len(cookies)))
        done = 0
        while True:
            for cookie in cookies:
                def _func():
                    voteRequest = sesh.post("https://rscripts.net/@" + profileUsername, headers={
                        "next-action": act,
                        "cookie": cookie
                    }, json=[profileUsername, random.choice(profileCommetList)])
                    if voteRequest.status_code == 200:
                        print("commented")
                    else:
                        print("failed to comment")
                        print(voteRequest.text)

                threading.Thread(target=_func).start()
                done += 1
                print("thread #" + str(done))
                if done % 25 == 0:
                    time.sleep(2)

    os.system("cls")

start()