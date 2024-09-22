import json
import socket
import requests
import time
import os
from dateutil.relativedelta import relativedelta as relativeDelta

def FullPrint(*args, end="\n"):
    text = ""
    for i in args:
        text += str(i) + " "
    print(text + "\033[0K", end=end)

attrs = ['years', 'months', 'days', 'hours', 'minutes', 'seconds']

def human_readable(delta):
    deltaSeconds = relativeDelta(seconds=delta)
    result = []
    for attr in attrs:
        attr_value = getattr(deltaSeconds, attr)
        if attr_value:
            attr_value = round(attr_value)
        if attr_value:
            if attr_value > 1:
                attr_as_word = attr
            else:
                attr_as_word = attr[:-1]
            result += ['%d %s' % (attr_value, attr_as_word)]
    return " ".join(result)

print("\nParsing JSON... ")

# Checks if the json file is there
try:
    configFile = open("Config.json", "rt")
    configStr = configFile.read()
    configFile.close()
    if configStr == "":
        config = {}
    else:
        config = json.loads(configStr)
except FileNotFoundError:
    print("Config file created.")
    configFile = open("Config.json", "wt")
    configFile.close()
    config = {}

exampleDic = {
    "Token":"spauth.v1.{example_Token}",
    "Start ID" : 123456,
    "End ID" : 987654,
    "Student Identifier" : "@student.com",
    "Misc Identifiers" : {
        "teachers" : "@teacher.com",
        "kiosks" : "@kiosk.com"
    }
}

# Fills in keys that aren't there in the json file, and throws an error if any are missing
badFile = False
for i in exampleDic:
    if i not in config:
        config[i] = exampleDic[i]
        badFile = True

if badFile:
    configFile = open("Config.json", "wt")
    configStr = configFile.write(json.dumps(config, indent=4))
    configFile.close()
    raise ValueError(
        "\033[0;31mERROR: The file you provided does not contain all required parameters. We have added them to the file, please set their values accordingly.\33[0m"
    )

print("\033M\033[96mParsing Json... Done\033[0m")

# Pings google.com/generate_204 to check if you're connected to the internet
print("Checking internet connection...")
ip = socket.gethostbyname("google.com")
tSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tSock.settimeout(5)
try:
    tSock.connect((ip, 80))
except:
    raise ConnectionError(
        "\033[0;31mYou don't seem to be connected to the internet. Please reconnect and try again\33[0m"
    )

tSock.send(b"GET /generate_204 HTTP/1.1\r\nContent-Length: 0\r\n\r\n")
recv = tSock.recv(999)

# Throws an error if it couldn't understand google's response
if recv[:23] == b"HTTP/1.1 204 No Content":
    print("\033M\033[96mChecking internet connection... Done\033[0m")
else:
    raise RuntimeError("\033[0;31mCould not interpret server response.\33[0m")


print("\033[96mInit complete. Starting...\033[0m\n")

startID = int(config["Start ID"])
endID = int(config["End ID"])
cookie = {"smartpassToken" : config["Token"]}

# Makes a dictionary for all the categories (student, teacher, etc), with their identifier (@student.com, @teacher.com, etc), as well as a count, and for everyone but students, there is also a pointer to which ids they are located at
categoryData = {
    "students": {
        "Identifier": config["Student Identifier"],
        "Count": 0
    }
}
for i, j in config["Misc Identifiers"].items():
    categoryData[i] = {
        "Identifier": j,
        "Count": 0,
        "IDs": []
    }


print(f"Starting scrape from \033[96m{startID}\033[0m - \033[96m{endID}\033[0m with token \033[32m" + cookie["smartpassToken"] + "\033[0m")

responseTimeList = []
personDict = {}
print("_" * (os.get_terminal_size().columns - 1), end="\n" * (len(categoryData) + 2))

try:
    for i in range(startID, endID + 1):
        print("\033M" * (len(categoryData) + 1), end="")
        start = time.time()

        # Requests the id
        r = requests.get("https://smartpass.app/api/prod-us-central/v1/pass_limits/student_limit?student_id=" + str(i), cookies=cookie)
        if r.status_code == 500:
            print("\n" * (len(categoryData) + 2) + f"\033[0;31mThere are no id's past {i - 1}, skipping...\33[0m")
            break
        if r.status_code != 200:
            raise Exception(r.content)
        
        # Adds the id to a dictionary to output later
        response = json.loads(str(r.content, "latin-1"))["student"]
        tempDict = {
            "First Name": response["first_name"],
            "Last Name": response["last_name"],
            "User Name": response["username"],
            "Display Name": response["display_name"],
            "Email": response["primary_email"],
            "Profile Picture": response["profile_picture"]
        }
        personDict[response["id"]] = tempDict

        # Updating all the category counts
        for j, k in categoryData.items():
            if tempDict["Email"].find(k["Identifier"]) + 1:
                k["Count"] += 1
                if j != "students":
                    k["IDs"].append(i)

        # All the status stuff
        FullPrint(str(response["id"]) + ": " + tempDict["Display Name"] + ", " + tempDict["Email"])

        # Shows all the category counts underneath the current id display
        for j, k in categoryData.items():
            print("  ┝ " + j + ": " + str(k["Count"]))
        print("\033M\r  └")

        # Completion data
        fString = ""
        percentDone = (i - startID) / (endID - startID) # Num% Complete
        fString += str(round(percentDone * 100, 1)) + "% Complete "
        fString += str(i - startID) + "/" # finishedNum / TotalNum
        fString += str(endID - startID) + " ("
        if len(responseTimeList) > 150: # ETA, not accurate for the first 150
            reqSpeed = len(responseTimeList) / sum(responseTimeList)
            fString += str(round(reqSpeed, 1)) + " req/s) "
            timeLeft = round((endID - i + 1) / reqSpeed)
            fString += (human_readable(timeLeft) if timeLeft > 0 else "0 seconds") + " remaining. ["
        else:
            fString += "Calculating... ["
        progressBarMax = os.get_terminal_size().columns - 3 - len(fString)
        fString += "#" * round(percentDone * progressBarMax)
        fString += " " * round((1 - percentDone) * progressBarMax) + "]"
        print(fString, end="\r")

        # Used for getting the average request rate
        end = time.time()
        responseTimeList.append(end - start)
        if len(responseTimeList) > 500:
            del(responseTimeList[0])
    
    print("\n")
    print("\033[96mScrape complete.\033[0m")
    print("Final stats:")
    outputJSON = {"Total User Count": None}
    total = 0
    # For loop for displaying final counts, but also prepares output.json
    for i, j in categoryData.items():
        print("-" + i + ": " + str(j["Count"]))
        total += j["Count"]
        if i == "students":
            outputJSON["Student Count"] = j["Count"]
        else:
            outputJSON[i[0].upper() + i[1:] + " Count"] = j["Count"]
            outputJSON[i[0].upper() + i[1:] + " IDs"] = j["IDs"]

    print("\nGenerating output.json...")
    outputJSON["Total User Count"] = total
    outputJSON.update(personDict)
    file = open("Output.json", "wt")
    file.write(json.dumps(outputJSON, indent=4))
    file.close()
    print("\033M\033[96mGenerating output.json... Done\033[0m")
    print("Output.json has been created, exiting...")

except KeyboardInterrupt:
    print("\n" * (len(categoryData) + 2)+ "\033[0;31mOperation canceled.\33[0m")