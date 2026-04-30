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
        Potential = session.get(f"https://rscripts.net/_next/static/chunks/{Chunk}.js", headers=headers, proxy=proxy).text
        Action = re.search(r'"(\w+)",\w+\.callServer,void 0,\w+\.findSourceMapURL,"' + Name + '"', Potential)

        if Action != None:
            ActionR = Action.group(1)
            return True, ActionR
        else:
            if Chunk == Chunks[len(Chunks)-1]:
                return False, "No Next-Action found, this should not happen!"
    return False, "Unknown Failure"

base = "https://api.mail.tm"
rscripts = "https://rscripts.net/api"
reset = colorama.Fore.RESET

def randomString(n=20, all=False):
	letters = string.ascii_lowercase + string.digits
	if all:
		letters += string.ascii_uppercase
	return ''.join(random.choices(letters, k=n))

onboardingActionCache = None

def randomUsername():
	method = random.randint(1, 4)
	if method == 1:
		while True:
			res = requests.get("https://randomuser.me/api/?inc=name&nat=gb,us").json()
			first = res["results"][0]["name"]["first"]
			numberlength = random.randint(4, 10)
			if len(first) <= (20 - numberlength):
				return first + str(random.randint(int("1" + ("0" * (numberlength - 1))), int("9" * numberlength)))
	elif method == 2:
		return randomString(random.randint(14, 20))
	elif method == 3:
		numberlength = random.randint(4, 10)
		numstr = str(random.randint(int("1" + ("0" * (numberlength - 1))), int("9" * numberlength)))
		return randomString(random.randint(13, 20) - numberlength, True) + "_" + numstr
	else:
		return str(random.randint(10000000,9999999999))
	
def randomPfp():
	url = "https://picsum.photos/512"
	response = requests.get(url)
	if response.status_code == 200:
		with open("rikka.png", "wb") as f:
			f.write(response.content)
		print(f"[{colorama.Fore.GREEN}FINISHING{colorama.Fore.RESET}] Generated random PFP")
	else:
		print("Failed to fetch image:", response.status_code)

def generateAccount():
	global onboardingActionCache
	print("-------------- Generating Account --------------")
	with requests.get(f"{base}/domains") as domains:
		if domains.status_code != 200:
			print(f"{colorama.Fore.RED}Failed to get domains ({domains.status_code}){reset}")
			#exit()
			return None
	
		member = domains.json()["hydra:member"]
		with requests.get(base + member[0]["@id"]) as data:
			if data.status_code != 200:
				print(f"{colorama.Fore.RED}Failed to get data of domain ({data.status_code}){reset}")
				#exit()
				return None
	
			data = data.json()
			domain = data["domain"]
			username = randomString()
			password = randomString()
			authJson = {"address": f"{username}@{domain}", "password": password}
			print(f"[{colorama.Fore.BLUE}EMAIL{colorama.Fore.RESET}] Address: {authJson['address']}")
	
			with requests.post(f"{base}/accounts", json=authJson) as account:
				if account.status_code != 201:
					print(f"{colorama.Fore.RED}Failed to create account ({account.status_code}){reset}")
					#exit()
					return None
	
				token = requests.post(f"{base}/token", json=authJson)
				if token.status_code != 200:
					print(f"{colorama.Fore.RED}Failed to create token ({token.status_code}){reset}")
					#exit()
					return None
	
				headerAuth = {"Authorization": f"Bearer {token.json()['token']}"}
				
				def getIncomingMessages():
					messages = requests.get(f"{base}/messages?page=1", headers=headerAuth)
					if messages.status_code != 200:
						return []
					return messages.json()["hydra:member"]
	
				mainSession = newRscriptsSession()
				sendLink = mainSession.post(f"{rscripts}/auth/sign-in/magic-link", json={
					"email": authJson["address"],
					"callbackURL": "/dashboard?welcome=true",
					"newUserCallbackURL": "/onboarding"
				})
				if sendLink.status_code == 200:
					print(f"[{colorama.Fore.YELLOW}VERIFICATION{colorama.Fore.RESET}] Sent verify link (" + str(sendLink.status_code) + ")")
				else:
					print(f"{colorama.Fore.RED}Failed to send verify link ({sendLink.status_code}){reset}")
					return None
				isfound = False
				for _ in range(30):
					if isfound:
						break
					time.sleep(10)
					for msg in getIncomingMessages():
						with requests.get(base + msg["@id"], headers=headerAuth) as msgData:
							if msgData.status_code != 200:
								continue
	
							text = msgData.json()["text"]
							verify = re.search(r"https://rscripts\.net/api/auth/magic-link/verify\?[^\s\]]+", text).group()
							if verify != None:
								isfound = True
								break
	
					#print("Still checking ...")
	
				for _ in range(5):
					req = mainSession.get(verify)
					if req.status_code == 302:
						print(f"[{colorama.Fore.YELLOW}VERIFICATION{colorama.Fore.RESET}] Verified account")
						headers = req.headers
						cookie = headers["Set-Cookie"][0] + "; " + headers["Set-Cookie"][1]
						print(f"[{colorama.Fore.YELLOW}VERIFICATION{colorama.Fore.RESET}] Token: " + re.match("__Secure-better-auth.session_token=(.+)", cookie.split("; ")[0]).group(1))
						break
					else:
						print(f"Failure in verifying account ({req.status_code})")
	
				# update onboarding
				username = randomUsername()[:20]
				print(f"[{colorama.Fore.GREEN}FINISHING{colorama.Fore.RESET}] Username: {username}")
				if onboardingActionCache == None:
					nextResult, completeaction = GetNextAction("https://rscripts.net/onboarding", mainSession, "completeOnboarding", headers={
						"Cookie": cookie
					})
				else:
					nextResult, completeaction = True, onboardingActionCache
				if not nextResult:
					print(completeaction)
					return None
				if onboardingActionCache == None:
					#print("onboarding action: " + completeaction)
					onboardingActionCache = completeaction
					
				avatarKey = None
				randomPfp()
				with open("rikka.png", "rb") as f:
					boundary = b"--WebKitFormBoundary" + randomString(16).encode("utf-8")
					binary = f.read()
					body = b'----'+boundary+b'\r\nContent-Disposition: form-data; name="avatar"; filename="rikka.png"\r\nContent-Type: image/png\r\n\r\n'+binary+b'\r\n----'+boundary+b'--'
					open("testform.txt", "wb").write(body)
					pfpResult = mainSession.post("https://rscripts.net/api/upload/avatar", headers={
						"content-type": "multipart/form-data; boundary=--" + boundary.decode("utf-8")
					},data=body)
					if pfpResult.status_code == 200:
						json = pfpResult.json()
						avatarKey = json['url']
						print(f"[{colorama.Fore.GREEN}FINISHING{colorama.Fore.RESET}] Uploaded PFP")

				onboarding = mainSession.post("https://rscripts.net/onboarding", headers={
					"cookie": cookie,
					"next-action": completeaction
                }, json=[{
					"username": username,
					"avatarKey": avatarKey
                }])
				if onboarding.status_code == 200:
					print(f"[{colorama.Fore.GREEN}FINISHING{colorama.Fore.RESET}] Onboarding complete")
				else:
					print("Onboarding failed")
					return None

				return cookie

def addBot():
	now = int(time.time())
	cookie = generateAccount()
	if cookie:
		new = open("bots.txt", "r").read() + "\n" + cookie
		open("bots.txt", "w").write(new)
		cookies = [cookie for cookie in open("bots.txt", "r").read().splitlines() if cookie != "BOTS:"]
		print(f"[{colorama.Fore.MAGENTA}COMPLETE{colorama.Fore.RESET}] Wrote bot token to list. Total: " + str(len(cookies)))
		print(f"[{colorama.Fore.MAGENTA}COMPLETE{colorama.Fore.RESET}] Time taken to generate this account: {int(time.time()) - now}s")
	else:
		print("If you got 429 code, wait 45 seconds and generator will start again")
		time.sleep(30)

while True:
	addBot()
	time.sleep(15)