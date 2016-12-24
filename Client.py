# CSE 310 Project Group 11
# Rahul Verma
# Joshua Ethridge
# Harrison Termotto

from socket import *
import sys
import shlex
import os
import datetime
import errno
import time

EOM = "\"\r\n\r\n\""
EOP = "\n.\n"
LOGIN_KEYWORD = "LOGIN"
AG_KEYWORD = "AG"
SG_KEYWORD = "SG"
RG_KEYWORD = "RG"
LOGOUT_KEYWORD = "LOGOUT"
SD_KEYWORD = "SD"
ERROR_KEYWORD = "ERROR"
POST_KEYWORD = "POST"

AG_DEFAULT = 5
SG_DEFAULT = 5
RG_DEFAULT = 5

RG_DELAY = 0.001

CONNECT_ATTEMPTS = 5

loggedIn = False
userId = -1

subGroups = []

SUB_FILE = "subscriptions.txt"
USER_FILE = ""

def receiveData(socket):
    dataArgs = []
    while shlex.split(EOM)[0] not in dataArgs:
        try:
            dataRcv = socket.recv(1024)
        except:
            print("Timed out")
        dataRcv = dataRcv.decode()
        data = shlex.split(dataRcv)
        # Append the arguments to dataArgs
        # This way, it will keep accepting arguments until an EOM is found
        for i in data:
            dataArgs.append(i)
    return dataArgs


def printHelp():
    print("Help - Supported Commands: ")
    print("login <#> - Takes one argument, your user ID. Will log you into the server to access the forum. You must "
          "login before you can access any of the other commands. Your user ID must be only alphanumerics.")
    print("help - Displays this help menu.")
    print("ag [<#>] - Has one optional argument. Returns a list of all existing discussion groups, N groups at a time. "
          "If the argument is not provided, a default value of " + str(AG_DEFAULT) + " will be used. When in ag mode, "
          " the following subcommands are available.")
    print("\ts - Subscribe to groups. Takes between 1 and N arguments. Subscribes to all groups listed in the argument." )
    print("\tu - Unsubscribe to groups. Same functionality as s, but instead unsubscribes.")
    print("\tn - Lists the next N discussion groups. If there are no more to display, exits ag mode.")
    print("\tq - Exits from ag mode.")
    print("sg [<#>] - Has one optional argument. Returns a list of all subscribed groups, N groups at a time. If the "
          "argument is not provided, then a default value of " + str(SG_DEFAULT) + " will be used.")
    print("\tu - Unsubscribe to groups. See ag.")
    print("\tn - Lists the next N discussion groups. If there are no more to display, exits sg mode.")
    print("\tq - Exits from sg mode.")
    print("rg <gname> [<#>] - Takes one mandatory argument and one optional argument. It displays the top N posts in a "
          "given discussion group. The argument, 'gname' determines which group to display. If the optional argument is"
          " not provided, then a default value of " + str(RG_DEFAULT) + " will be used. After entering this command, the "
          "application will enter 'rg' mode, which uses the following subcommands.")
    print("\t[#] - The post number to display. Entering this mode will give even more subcommands.")
    print("\t\tn - Display, at most, n more lines of content.")
    print("\t\tq - Quit this read mode to return to normal rg mode")
    print("\tr [#] - Marks the given post as read. If a single number is specified, then that single post will be marked"
          " as read. You can use the format, 'n-m' to mark posts n through m as read.")
    print("\tn - Lists the next n posts. If there are no more posts to display, exits rg mode.")
    print("\tp - Post to the group. This subcommand will enter post mode.")
    print("\t\tThe application will request a title for the post. Then, the application will allow you to write the "
          "body of the post. It will accept input until you enter a blank line, followed by a period, followed by "
          "another blank line. After this command sequence is accepted, the post will be submitted and you will be "
          "returned to rg mode.")
    print("logout - Logs you out from the server, subsequently closing the application.")


# Takes two lists, groups and dataArgs. groups is the list of groups to subscribe to. dataArgs is the list of all groups
def subscribe(groups, dataArgs):
    for i in groups:
        groupName = dataArgs[int(i) - 1]
        if groupName in subGroups:
            print("You are already subscribed to " + str(groupName))
        else:
            subGroups.append(str(groupName))
            try:
                os.makedirs(USER_FILE + groupName)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
            print("Subscribed to " + str(dataArgs[int(i) - 1]))
    subFile = open(USER_FILE + SUB_FILE, "w")
    for i in subGroups:
        subFile.write(i + "\n")
    subFile.close()


# Takes two lists, groups and dataArgs. groups is the list of groups to unsub from. dataArgs is the list of all groups.
def unsub(groups, dataArgs):
    for i in groups:
        if dataArgs[int(i) - 1] in subGroups:
            subGroups.remove(str(dataArgs[int(i) - 1]))
            print("Unsubscribed to " + str(dataArgs[int(i) - 1]))
        else:
            print("You are not subscribed to " + str(dataArgs[int(i) - 1]))
    subFile = open(USER_FILE + SUB_FILE, "w")
    for i in subGroups:
        subFile.write(i + "\n")
    subFile.close()


# This is a helper method for createPost(). It detects when the user is finished composing their message.
def EOPFind(msg):
    for i in range(len(msg) - 2):
        if len(msg[i]) == 0 and msg[i+1] == "." and len(msg[i+2]) == 0:
            return True
    return False


# This method is used when creating a post to send to the server
def createPost(gname):
    messageDone = False
    fullMessage = []
    title = ""
    while len(title) < 1:
        title = input(str(userId) + "(Enter title)>>> ")
        if len(title) <= 1:
            print("A longer title is required.")
    while not messageDone:
        stdin = input(str(userId) + "(Compose Post)>>> ")
        if stdin == "/help":
            printHelp()
        else:
            fullMessage.append(stdin)
            messageDone = EOPFind(fullMessage)
    fullMessage.pop()
    fullMessage.pop()
    fullMessage.pop()
    print("Title: " + title)
    print("Content: ")
    for i in fullMessage:
        print(i)
    print("Submit this message?")
    userResponded = False
    userResponse = ""
    while not userResponded:
        answer = input(str(userId) + "(Y or N)>>> ")
        if answer == "Y" or answer == "N":
            userResponse = answer
            userResponded = True
        else:
            print("Unrecognized response")
    if userResponse == "Y":
        print("Submitting message...")
        clientSocket.send((POST_KEYWORD + " " + gname + " " + userId + " '" + title + "' ").encode("UTF-8"))
        for i in fullMessage:
            clientSocket.send(("\"" + i + "\n\"").encode("UTF-8"))
        time.sleep(RG_DELAY)
        clientSocket.send((" " + EOM).encode("UTF-8"))
    else:
        print("Message not submitted.")


def markPostAsRead(dataArgs, gname):
    # dataArgs format:
    #   0 - RG_KEYWORD
    #   1 - Number of message
    #   2 - Name of file
    #   3 - Date, in milliseconds, the post was created
    #   4 - Author of the post
    #   5 - Title of post
    #   6 - Content of post
    #   n - EOM
    # Add post to list of viewed posts along with some identifying information
    dateOfPost = datetime.datetime.fromtimestamp(int(dataArgs[3]))
    if os.path.exists(USER_FILE + gname + "/" + dataArgs[2]):
        print("File already read")
    else:
        f = open(USER_FILE + gname + "/" + dataArgs[2], "w+")
        f.write("Group: " + gname)
        f.write("\nSubject: " + dataArgs[5])
        f.write("\nAuthor: " + dataArgs[4])
        f.write("\nDate: " + str(dateOfPost))
        f.close()


# This method is used to view a given post from rg mode
def viewPost(dataArgs, gname, n):
    #   0 - RG_KEYWORD
    #   1 - Number of message
    #   2 - Name of file
    #   3 - Date, in milliseconds, the post was created
    #   4 - Author of the post
    #   5 - Title of post
    #   6 - Content of post
    #   n - EOM
    dateOfPost = datetime.datetime.fromtimestamp(int(dataArgs[3]))
    markPostAsRead(dataArgs, gname)
    # Print the post to the user
    print("Group: " + gname)
    print("Subject: " + dataArgs[5])
    print("Author: " + dataArgs[4])
    print("Date: " + str(dateOfPost))
    readStart = 6
    readEnd = 11
    if readEnd > len(dataArgs)-1:
        readEnd = len(dataArgs)-1
    read = True
    while(read):
        for i in range(readStart, readEnd):
            print(dataArgs[i])
            if readEnd < len(dataArgs)-1:
                readStart = readEnd
                stdin = input(str(userId) + "(View Mode)>>> ")
                if stdin == "n":
                    readEnd = readStart + int(stdin)
                    if readEnd > len(dataArgs)-1:
                        readEnd = len(dataArgs)-1
                elif stdin == "q":
                    read = False
            else:
                read = False


# This function handles the implementation of the ag command. It uses the submethods subscribe() and unsub()
def ag(n):
    clientSocket.send((AG_KEYWORD + " " + EOM).encode("UTF-8"))
    dataArgs = receiveData(clientSocket)
    currentMaxGroup = 2
    if dataArgs[0] == AG_KEYWORD:
        groupsLeft = int(dataArgs[1])
        while(groupsLeft > 0):
            # Make sure to avoid index out of array exception
            indexEnd = currentMaxGroup + n
            if groupsLeft - n < 0:
                indexEnd = indexEnd + (groupsLeft - n)

            # Iterate through the list, showing n groups at a time until no more groups are found
            for i in range(currentMaxGroup, indexEnd):
                if dataArgs[i] in subGroups:
                    print(str(i - 1) + ". (s) " + dataArgs[i])
                else:
                    print(str(i - 1) + ". ( ) " + dataArgs[i])
            currentMaxGroup = currentMaxGroup + n
            groupsLeft = groupsLeft - n
            nextSequence = False
            while(not nextSequence):
                stdin = ""
                while len(stdin) < 1:
                    stdin = input(str(userId) + "(AG Mode)>>> ")
                userInput = shlex.split(stdin)
                if userInput[0] == "s":
                    # Subscribe to group
                    groupsToSub = userInput[1:]
                    subscribe(groupsToSub, dataArgs[2:])
                elif userInput[0] == "u":
                    # Unsubscribe to group
                    groupsToUnsub = userInput[1:]
                    unsub(groupsToUnsub, dataArgs[2:])
                elif userInput[0] == "n":
                    nextSequence = True
                elif userInput[0] == "q":
                    groupsLeft = 0
                    nextSequence = True
                elif userInput[0] == "help":
                    printHelp()
                else:
                    print("Unsupported operation in ag mode.")
    print("Exiting AG Mode")


# This method handles the implementation of sg. It uses the submethod unsub()
def sg(n):
    clientSocket.send((SG_KEYWORD + " " + EOM).encode("UTF-8"))
    dataArgs = receiveData(clientSocket)
    dataArgs1 = dataArgs[:dataArgs.index("-")]
    groupPosts = dataArgs[dataArgs.index("-")+1:len(dataArgs)-1]
    dataArgs = dataArgs1
    currentMaxGroup = 0
    if dataArgs[0] == SG_KEYWORD:
        groupsLeft = len(subGroups)
        while(groupsLeft > 0):
            # Make sure to avoid index out of array exception
            indexEnd = currentMaxGroup + n
            if groupsLeft - n < 0:
                indexEnd = indexEnd + (groupsLeft - n)

            # Iterate through the list, showing n groups at a time until no more groups are found
            for i in range(currentMaxGroup, indexEnd):
                seenPosts = len(os.listdir(USER_FILE + str(subGroups[i])))
                newPosts = int(groupPosts[dataArgs.index(subGroups[i])-2]) - seenPosts
                if newPosts == 0:
                   print(str(i + 1) + ". \t\t" + subGroups[i])
                else:
                    print(str(i + 1) + ". \t" + str(newPosts) +"\t" + subGroups[i])
            currentMaxGroup = currentMaxGroup + n
            groupsLeft = groupsLeft - n
            nextSequence = False
            while(not nextSequence):
                stdin = ""
                while len(stdin) < 1:
                    stdin = input(str(userId) + "(SG Mode)>>> ")
                userInput = shlex.split(stdin)
                if userInput[0] == "u":
                    # Unsubscribe to group
                    # groups contains the number of the group according to subGroups
                    # This number needs to be translated to the number as it is used in dataArgs
                    groups = userInput[1:]
                    groupNamesToUnsub = []
                    for i in range(0, len(subGroups)+1):
                        if str(i) in groups:
                            groupNamesToUnsub.append(subGroups[i - 1])
                    groupsToUnsub = []
                    for i in range(0, len(dataArgs)):
                        for j in groupNamesToUnsub:
                            if j == dataArgs[i]:
                                groupsToUnsub.append(i - 1)
                    unsub(groupsToUnsub, dataArgs[2:])
                elif userInput[0] == "n":
                    nextSequence = True
                elif userInput[0] == "q":
                    groupsLeft = 0
                    nextSequence = True
                elif userInput[0] == "help":
                    printHelp()
                else:
                    print("Unsupported operation in sg mode.")
    print("Exiting SG Mode")

# This method handles the implementation of rg, which is "read group"
def rg(gname, n):
    gname = str(gname)
    if gname not in subGroups:
        print("You are not subscribed to " + gname)
        return
    clientSocket.send((RG_KEYWORD + " " + gname + " " + EOM).encode("UTF-8"))
    dataArgs = receiveData(clientSocket)
    if dataArgs[0] == RG_KEYWORD:
        print(gname + " found!")
        totalPosts = dataArgs[1]
        totalPosts = int(totalPosts)
        # allPosts is an array containing all the information about the post. That information is contained in an array
        # Yep, that means 2D arrays.
        allPosts = []
        for i in range(totalPosts):
            dataArgs = receiveData(clientSocket)
            dataArgs.reverse()
            reverseArgs = dataArgs[:]
            dataArgs.reverse()
            if reverseArgs.index(RG_KEYWORD) == len(reverseArgs) - 1:
                allPosts.append(dataArgs)
            else:
                while reverseArgs.index(RG_KEYWORD) != len(reverseArgs) - 1:
                    arg = reverseArgs[:reverseArgs.index(RG_KEYWORD)+1]
                    arg.reverse()
                    allPosts.insert(0, arg)
                    reverseArgs = reverseArgs[reverseArgs.index(RG_KEYWORD)+1:]
                arg = reverseArgs[:]
                arg.reverse()
                allPosts.insert(0, arg)
            if len(allPosts) == totalPosts:
                break
        allPosts.reverse()
        # Entering rg mode here
        # For use in this loop:
        #   0 - RG_KEYWORD
        #   1 - Number of message
        #   2 - Name of file
        #   3 - Date, in milliseconds, the post was created
        #   4 - Author of the post
        #   5 - Title of post
        #   6 - Content of post
        #   7 - EOM
        groupsLeft = len(allPosts)
        currentMaxGroup = 0
        while(groupsLeft > 0):
            # Make sure to avoid index out of array exception
            indexEnd = currentMaxGroup + n
            if groupsLeft - n < 0:
                indexEnd = indexEnd + (groupsLeft - n)

            # Iterate through the list, showing n groups at a time until no more groups are found
            for i in range(currentMaxGroup, indexEnd):
                #TODO Modify the date so it looks nicer
                dateOfPost = datetime.datetime.fromtimestamp(int(allPosts[i][3]))
                if os.path.exists(USER_FILE + gname + "/" + allPosts[i][2]):
                    print(str(i + 1) + ". \t\t" + str(dateOfPost) + "\t" + str(allPosts[i][5]))
                else:
                    print(str(i + 1) + ". \tN\t" + str(dateOfPost) + "\t" + str(allPosts[i][5]))
            currentMaxGroup = currentMaxGroup + n
            groupsLeft = groupsLeft - n
            nextSequence = False
            while(not nextSequence):
                stdin = ""
                while len(stdin) < 1:
                    stdin = input(str(userId) + "(RG Mode)>>> ")
                userInput = shlex.split(stdin)
                if userInput[0] == "n":
                    nextSequence = True
                elif userInput[0] == "q":
                    groupsLeft = 0
                    nextSequence = True
                elif userInput[0] == "help":
                    printHelp()
                elif userInput[0] == "r":
                    if userInput[1].isdigit() and int(userInput[1]) >= 1 and int(userInput[1]) <= len(allPosts):
                        post = int(userInput[1])
                        markPostAsRead(allPosts[post - 1], gname)
                    elif userInput[1][:userInput[1].index("-")].isdigit() and userInput[1][userInput[1].index("-")+1:len(userInput[1])].isdigit():
                        firstDigit = int(userInput[1][:userInput[1].index("-")])
                        secondDigit = int(userInput[1][userInput[1].index("-")+1:len(userInput[1])])
                        for i in range(firstDigit, secondDigit+1):
                            markPostAsRead(allPosts[i - 1],gname)
                    else:
                        print("That is an unacceptable post to mark as read.")
                elif userInput[0] == "p":
                    createPost(gname)
                elif userInput[0].isdigit():
                    post = int(userInput[0])
                    if post > len(allPosts) or post < 1:
                        print("That is an unacceptable post number.")
                    else:
                        viewPost(allPosts[post - 1], gname, n)
                else:
                    print("Unsupported operation in rg mode.")
        print("Exiting RG Mode")

    elif dataArgs[0] == ERROR_KEYWORD:
        print("Error in finding group.")
        if dataArgs[1] == str(10):
            print(gname + " not found.")

# ***Client starts here***

# Get system arguments to determine address and port
try:
    argv = sys.argv
    host = argv[1]
    port = argv[2]
    port = int(port)
except IndexError:
    print("Too few arguments given.")
    sys.exit()

# Attempt to connect to given address
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.settimeout(3)
print("Attempting to connect to " + str(host) + ":" + str(port))
i = 1
connect = False
while not connect:
    if i > CONNECT_ATTEMPTS:
        print("Connection aborted. Exiting program.")
        sys.exit()
    try:
        if i != 1:
            print("Attempting to connect. Attempt " + str(i) + " of " + str(CONNECT_ATTEMPTS))
        clientSocket.connect((host, port))
        connect = True
    except OSError:
        print("Connection refused")
        i += 1
keepRunning = True
print("Connection successful!")
try:
    while keepRunning:
        if loggedIn:
            stdin = input(str(userId) + ">>> ")
        else:
            stdin = input('>>> ')
        userInput = shlex.split(stdin)
        if userInput != []:
	        if not loggedIn:
	            if userInput[0] == "login":
	                # Login operations
	                if not loggedIn:
	                    # Login requires exactly 2 arguments
	                    if len(userInput) != 2:
	                        print("Incorrect number of arguments.")
	                        printHelp()
	                    else:
	                        print(userInput[1])
	                        clientSocket.send((LOGIN_KEYWORD + " '" + userInput[1] + "' " + EOM).encode("UTF-8"))

	                        # Receive data until EOM found
	                        dataArgs = receiveData(clientSocket)

	                        if dataArgs[0] == LOGIN_KEYWORD :
	                            print("Login successful! Welcome user " + str(dataArgs[1]))
	                            loggedIn = True
	                            userId = dataArgs[1]
	                            USER_FILE = userId + "/"
	                            try:
	                                os.makedirs(userId)
	                            except OSError as e:
	                                if e.errno != errno.EEXIST:
	                                    raise
	                            if os.path.exists(USER_FILE + SUB_FILE):
	                                subFile = open(USER_FILE + SUB_FILE, "r")
	                            else:
	                                subFile = open(USER_FILE + SUB_FILE, "w+")
	                            for i in subFile:
	                                group = i.rstrip()
	                                subGroups.append(group)
	                                try:
	                                    os.makedirs(USER_FILE + group)
	                                except OSError as e:
	                                    if e.errno != errno.EEXIST:
	                                        raise
	                            subFile.close()
	                        else:
	                            print("Login failed.")
	            elif userInput[0] == "help":
	                printHelp()
	            else:
	                print("Please login before issuing commands.")
	                printHelp()
	        else:
	            if userInput[0] == "login":
	                print("You are already logged in.")
	                printHelp()
	            elif userInput[0] == "help":
	                printHelp()
	            elif userInput[0] == "ag":
	                if len(userInput) == 2 and userInput[1].isdigit() and int(userInput[1]) > 0:
	                    ag(int(userInput[1]))
	                elif len(userInput) == 1:
	                    ag(AG_DEFAULT)
	                else:
	                    print("Incorrect usage for ag.")
	                    printHelp()
	            elif userInput[0] == "sg":
	                if len(userInput) == 2 and userInput[1].isdigit() and int(userInput[1]) > 0:
	                    sg(int(userInput[1]))
	                elif len(userInput) == 1:
	                    sg(SG_DEFAULT)
	                else:
	                    print("Incorrect usage for sg.")
	                    printHelp()
	            elif userInput[0] == "rg":
	                if len(userInput) == 2:
	                    rg(userInput[1], RG_DEFAULT)
	                elif len(userInput) == 3 and int(userInput[2]) > 0:
	                    rg(userInput[1], int(userInput[2]))
	                else:
	                    print("Incorrect usage for rg.")
	                    printHelp()
	            elif userInput[0] == "logout":
	                print("Logging out from the server...")
	                clientSocket.send((LOGOUT_KEYWORD + " " + EOM).encode("UTF-8"))
	                dataArgs = receiveData(clientSocket)
	                if(dataArgs[0] == LOGOUT_KEYWORD):
	                    print("Received from server: " + dataArgs[1])
	                break
	            elif userInput[0] == "EOM":
	                clientSocket.send("'\r\n\r\n'".encode("UTF-8"))
	                rcv = clientSocket.recv(1024)
	                print("Received: " + rcv.decode())
	            elif userInput[0] == "sd":
	                clientSocket.send((SD_KEYWORD + " " + EOM).encode("UTF-8"))
	            else:
	                print("Unrecognized command.")
	                printHelp()
except error as e:
    print("Unexpected error occured.")
    print(e)
    # try/catch blocks inside a try/catch block. Much python, such fancy. Wow.
    try:
        clientSocket.send((LOGOUT_KEYWORD + " " + EOM).encode("UTF-8"))
        dataArgs = receiveData(clientSocket)
        if(dataArgs[0] == LOGOUT_KEYWORD):
            print("Received from server: " + dataArgs[1])
    except:
        print("Server unexpectedly closed. Shutting down.")

    clientSocket.close()
if loggedIn:
    clientSocket.close()
