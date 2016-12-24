# CSE 310 Project Group 11
# Rahul Verma
# Joshua Ethridge
# Harrison Termotto
#
# ERRORS:
# 0     Command not found
# 1     Login invalid
# 10    rg group not found

from socket import *
import threading
import shlex
import os
import sys
import errno
import re
import time

DEFAULT_PORT = 9966

EOM = "\"\r\n\r\n\""

LOGIN_KEYWORD = "LOGIN"
AG_KEYWORD = "AG"
SG_KEYWORD = "SG"
RG_KEYWORD = "RG"
LOGOUT_KEYWORD = "LOGOUT"
ERROR_KEYWORD = "ERROR"
SD_KEYWORD = "SD"
POST_KEYWORD = "POST"

LOGOUT_SND = " 'Logging you out from the server.' "
NOCMD_SND = " 0 'That is not a recognized command.' "
RGGNF_SND = " 10 'Requested group not found.' "

USER_FILE = "users.txt"
GROUP_FILE = "groups.txt"
GROUPS_FOLDER = "groups"

# This is a hacky way of making sure linux doesn't bug out in rg mode because reasons
RG_DELAY = 0.01

serverRunning = False
loginThreadRunning = False

# ***Persistence functionality starts here***
# Users
# Check first to see if file exists
if os.path.exists(USER_FILE):
    print("User file found! Loading users...")
    userFile = open(USER_FILE, "r")
else:
    print("User file not found. Creating user file.")
    userFile = open(USER_FILE, "w+")
users = []
usersLock = threading.Lock()
for i in userFile:
    # Strip the Id of the trailing newline and any extra whitespace
    userId = i.rstrip()
    users.append(userId)
userFile.close()

# Groups
if os.path.exists(GROUP_FILE):
    print("Groups file found! Loading groups...")
    groupFile = open(GROUP_FILE, "r")
else:
    print("A groups file was not found and is necessary for safe operations.")
    print("A placeholder file will be made, but the server will not provide much functionality without any groups.")
    groupFile = open(GROUP_FILE, "w+")
groups = []
for i in groupFile:
    group = i.rstrip()
    groups.append(group)
groupFile.close()
# Hacky way of checking if a folder exists
try:
    os.makedirs(GROUP_FILE)
except OSError as e:
    if e.errno != errno.EEXIST:
        raise
for i in groups:
    # This is a very hacky way of making a bunch of folders inside the main groups folder
    try:
        os.makedirs(GROUPS_FOLDER + "/" + i)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
os.stat_float_times(False)


# ***Helper methods start here***

# This method receives data until an EOM is found.
def receiveData(socket):
    dataArgs = []
    while shlex.split(EOM)[0] not in dataArgs:
        dataRcv = socket.recv(2048)
        dataRcv = dataRcv.decode()
        data = shlex.split(dataRcv)
        # Append the arguments to dataArgs
        # This way, it will keep accepting arguments until an EOM is found
        for i in data:
            dataArgs.append(i)
    return dataArgs


# This method removes a thread from the array of threads
def removeThread(threadID):
    arrayLock.acquire()
    for i in threads:
        if(threadID == i.threadID):
            threads.remove(i)
            break
    arrayLock.release()


# This is a method which will handle a client logging in to the server
def clientLogin(socket, identity, args):
    print("Login received from " + identity)
    if ((args[1].isdigit()) and int(args[1]) == -1) or not re.match("^[\w\d]*$",args[1]):
        print("Invalid login from " + identity)
        socket.send((ERROR_KEYWORD + " 1 'Login invalid' " + EOM).encode("UTF-8"))
        return -1
    userFound = False
    for i in users:
        if i == args[1]:
            userFound = True
    if not(userFound):
        usersLock.acquire()
        users.append(args[1])
        userFile = open(USER_FILE, "a")
        userFile.write(args[1])
        userFile.write("\n")
        userFile.close()
        usersLock.release()
        print("New user found. Added user " + str(args[1]))
    socket.send((LOGIN_KEYWORD + " '" + args[1] + "' " + EOM).encode("UTF-8"))
    print("Valid login from " + identity + "(User: " + args[1] + ")")
    return args[1]


# This method returns all of the groups to the client that requested it.
def agSend(socket, identity):
    socket.send((AG_KEYWORD + " ").encode("UTF-8"))
    socket.send((str(len(groups)) + " ").encode("UTF-8"))
    for i in groups:
        socket.send((i + " ").encode("UTF-8"))
    socket.send((EOM).encode("UTF-8"))
    print("Sent all groups to " + identity)


# This method handles the sg functionality.
def sgSend(socket, identity):
    socket.send((SG_KEYWORD + " ").encode("UTF-8"))
    socket.send((str(len(groups)) + " ").encode("UTF-8"))
    groupPosts = []
    for i in groups:
        allFiles = os.listdir(GROUPS_FOLDER + "/" + i)
        numberOfFiles = str(len(allFiles))
        groupPosts.append(numberOfFiles)
        socket.send((i + " ").encode("UTF-8"))
    socket.send("- ".encode("UTF-8"))
    for i in groupPosts:
        socket.send((i + " ").encode("UTF-8"))
    socket.send((EOM).encode("UTF-8"))
    print("Sent all groups to " + identity + " for use with sg.")

def rgSend(socket, identity, dataArgs):
    # dataArgs (should) contain the following:
    # 0 - RG_KEYWORD
    # 1 - gname - the group of which to serve posts
    gname = dataArgs[1]
    if gname in groups:
        print("Group '" + gname + "' requested from " + identity)
        # This is the path to the folder for the requested group
        activeFolder = GROUPS_FOLDER + "/" + gname
        # allFiles holds an array of all files in the group folder.
        # The contents of the file will be sent, one file at a time, with the first message being the number of posts
        # overall to send.
        allFiles = os.listdir(activeFolder)
        socket.send((RG_KEYWORD + " " + str(len(allFiles)) + " " + EOM).encode("UTF-8"))
        time.sleep(RG_DELAY)
        i = 0
        for file in allFiles:
            activeFilePath = activeFolder + "/" + file
            activeFile = open(activeFilePath, "r")
            mTime = os.path.getmtime(activeFilePath)
            i += 1
            time.sleep(RG_DELAY)
            socket.send((RG_KEYWORD + " " + str(i) + " " + file + " " + str(mTime) + " ").encode("UTF-8"))
            content = []
            line = activeFile.readline()
            tuple = line.rpartition("-")
            socket.send(str(tuple[2]).encode("UTF-8"))
            content.append(str(tuple[0]))
            for line in activeFile:
                content.append(line.rstrip())
            for line in content:
                if len(line) == 0:
                    socket.send("\n".encode("UTF-8"))
                else:
                    socket.send(("\"" + line + "\n\"").encode("UTF-8"))
            socket.send(" ".encode("UTF-8"))
            socket.send(EOM.encode("UTF-8"))
            socket.send(" ".encode("UTF-8"))
            activeFile.close()
            time.sleep(RG_DELAY)
    else:
        # Group not found, send GNF error
        socket.send((ERROR_KEYWORD + RGGNF_SND + EOM).encode("UTF-8"))
        print("Unknown group, '" + gname + "' requested from " + identity)


# This method is called when a user submits a new post to the server.
# It takes that information and saves the post to the system.
def newPost(dataArgs, identity):
    # dataArgs array setup:
    # 0 - POST_KEYWORD
    # 1 - Group
    # 2 - Author name
    # 3 - Title
    # 4-(n-1) - Content
    # n - EOM
    print("New post received from " + identity)
    filePath = GROUPS_FOLDER + "/" + dataArgs[1]
    numberPosts = len(os.listdir(filePath))
    f = open(filePath + "/" + str(numberPosts) + ".txt", "w+")
    f.write(dataArgs[3] + "-" + dataArgs[2] + "\n\n")
    for i in range(4, len(dataArgs)-1):
        f.write(dataArgs[i])
    f.close()


# This method safely quits the server, closing all open files, threads, and such.
def quitServer():
    print("Quitting server!")
    for i in threads:
        print("Closing " + i.identity)
        try:
            i.socket.shutdown(SHUT_RDWR)
            i.socket.close()
        except:
            print("Issue closing socket attached to " + i.identity)
            print("Socket could have disconnected in a very unsafe manner or some other error could have occurred.")
    if loginThreadRunning:
        loginThread.serverSocket.close()
    sys.exit()


# ***This is the thread object***
# When Thread.start() is run, the run method will run. Upon return of the run method, the thread dies.
# This thread is to handle listening to the various clients
class ConnThread (threading.Thread):

    # This is the constructor for the thread.
    def __init__(self, threadID, socket, ip, port):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.socket = socket
        self.ip = ip
        self.port = port
        self.identity = "Thread" + str(self.threadID) + "@" + str(self.ip) + ":" + str(self.port)

    # This is what functionality the thread will perform while it's alive.
    def run(self):
        print("Running thread " + str(self.threadID) + " for " + str(self.ip) + ":" + str(self.port))
        keepRunning = True
        try:
            while(keepRunning):
                dataArgs = receiveData(self.socket)
                # Search for arguments
                if dataArgs[0] == LOGIN_KEYWORD:
                    # Perform login operations
                    loginStatus = clientLogin(self.socket, self.identity, dataArgs)
                    if loginStatus != -1:
                        self.identity = self.identity + "(User: " + loginStatus + ")"
                elif dataArgs[0] == AG_KEYWORD:
                    # Perform ag operations
                    agSend(self.socket, self.identity)
                elif dataArgs[0] == SG_KEYWORD:
                    # Perform sg operations
                    sgSend(self.socket, self.identity)
                elif dataArgs[0] == RG_KEYWORD:
                    # Perform rg operations
                    rgSend(self.socket, self.identity, dataArgs)
                elif dataArgs[0] == LOGOUT_KEYWORD:
                    # Perform logout operations
                    self.socket.send((LOGOUT_KEYWORD + LOGOUT_SND + EOM).encode("UTF-8"))
                    self.socket.close()
                    print("Client from " + self.identity + " has disconnected.")
                    keepRunning = False
                elif dataArgs[0] == SD_KEYWORD:
                    # Perform shutdown operations
                    # This is mostly for testing
                    # If this stays in, it must be password protected
                    keepRunning = False
                    quitServer()
                elif dataArgs[0] == POST_KEYWORD:
                    # User has submitted a new post
                    newPost(dataArgs, self.identity)
                else:
                    # Print non-recognized keyword
                    self.socket.send(ERROR_KEYWORD + NOCMD_SND + EOM)

        except (ConnectionAbortedError, ConnectionResetError):
            # If a client closes without using the logout functionality
            self.socket.close()
            print("Client from " + self.identity + " has disconnected unexpectedly.")

        # Client disconnected, remove thread from array of active threads
        print("Closing " + self.identity)
        removeThread(self.threadID)
    # End of run method, thread automatically ends


class LoginThread(threading.Thread):

    def __init__(self, serverSocket):
        threading.Thread.__init__(self)
        self.serverSocket = serverSocket

    def run(self):
        print("Login Thread running")
        freeThreadID = 0
        runServer = True
        # Functionality loop
        while runServer:
            try:
                self.serverSocket.listen(1)
                # Connection received from client
                clientSocket, addr = self.serverSocket.accept()
                print("Connection received from " + str(addr[0]) + ":" + str(addr[1]))
                thread = ConnThread(freeThreadID, clientSocket, addr[0], addr[1])
                freeThreadID += 1

                # Add the thread to the list of threads
                arrayLock.acquire()
                threads.append(thread)
                arrayLock.release()

                # Start the thread
                thread.start()
            except OSError:
                print("The socket in the login thread has closed.")
                print("If this was triggered by something other than a server shutdown, a critical error has occured.")
                runServer = False


# ***Server startup begins here***

# Prepare the socket
serverPort = DEFAULT_PORT
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(("", serverPort))

# Array to hold all threads
threads = []
# Threads will increment by 1, starting at 0, avoiding duplicates
# Semaphore for concurrency stuff
arrayLock = threading.Lock()

# Waiting for connection...
print("Beginning server.")
print("Listening on port " + str(serverPort))

# Create a thread for logging in
loginThread = LoginThread(serverSocket)
loginThread.start()
loginThreadRunning = True
# Wait for the login thread to end
try:
    loginThread.join()
except KeyboardInterrupt:
    quitServer()