Group 11
Joshua Ethridge
Rahul Verma
Harrison Termotto



***NECESSARY FILES***

Both the Server and Client are programmed using Python 3. This WILL NOT work with Python 2.

The only file that the server absolutely needs to run is "Server.py", but for there to be any functionality with the
server, a "groups.txt" files must also be included. If the Server.py file is run without the groups.txt file, the server
will still startup but will issue a warning that it's basically useless. The server creates the "groups" subfolder from
the given groups.txt file. The server will also create a "users.txt" file to keep track of the clients that connect.

The only file that the client absolutely needs is "Client.py". Everything else the client needs is created as it runs.

See the PERSISTENCE/IO section for more details.



***USAGE***:

Launching the server:
The server requires no special arguments to run. It can be run just the same as any other Python 3 script. It uses a
hardcoded port of 9966.

login <#> - Takes one argument, your user ID. Will log you into the server to access the forum. You must login before
you can access any of the other commands. Your user ID must be only alphanumerics.
help - Displays this help menu.
ag [<#>] - Has one optional argument. Returns a list of all existing discussion groups, N groups at a time. If the
argument is not provided, a default value of 5 will be used. When in ag mode,  the following subcommands are available.
	s - Subscribe to groups. Takes between 1 and N arguments. Subscribes to all groups listed in the argument.
	u - Unsubscribe to groups. Same functionality as s, but instead unsubscribes.
	n - Lists the next N discussion groups. If there are no more to display, exits ag mode.
	q - Exits from ag mode.
sg [<#>] - Has one optional argument. Returns a list of all subscribed groups, N groups at a time. If the argument is
not provided, then a default value of 5 will be used.
	u - Unsubscribe to groups. See ag.
	n - Lists the next N discussion groups. If there are no more to display, exits sg mode.
	q - Exits from sg mode.
rg <gname> [<#>] - Takes one mandatory argument and one optional argument. It displays the top N posts in a given
discussion group. The argument, 'gname' determines which group to display. If the optional argument is not provided,
then a default value of 5 will be used. After entering this command, the application will enter 'rg' mode, which uses
the following subcommands.
	[#] - The post number to display. Entering this mode will give even more subcommands.
		n - Display, at most, n more lines of content.
		q - Quit this read mode to return to normal rg mode
	r [#] - Marks the given post as read. If a single number is specified, then that single post will be marked as read.
	 You can use the format, 'n-m' to mark posts n through m as read.
	n - Lists the next n posts. If there are no more posts to display, exits rg mode.
	p - Post to the group. This subcommand will enter post mode.
		The application will request a title for the post. Then, the application will allow you to write the body of the
		 post. It will accept input until you enter a blank line, followed by a period, followed by another blank line.
		 After this command sequence is accepted, the post will be submitted and you will be returned to rg mode.
logout - Logs you out from the server, subsequently closing the application.



***PROTOCOL***:

The server and client communicate through various keywords. Here are all included keywords:
LOGIN
AG
SG
RG
LOGOUT
ERROR
SD
POST
The client and server communicate as follows:
1. A keyword is sent, followed by a space. On both ends, the messages are parsed by space, ignoring spaces between
''.
2. If the keyword has optional information sent along with it, then all of that information goes in the next few spaces.
Different arguments should be separated by spaces.
3. Both the client and server receive data until an End Of Message (EOM) is found. The EOM is determined by the
following sequence: '\r\n\r\n'. This includes the quotation marks. The quotation marks are necessary because of the way
the parser functions.

LOGIN sent from the client to the server must include the userID as a second argument.

RG Protocol
RG, since it has the most server functionality, has its own protocol for sending discussion posts to the client. When
the client sends an RG request, the server will respond with the RG keyword, followed by the number of total posts for
the group. The server will then send a message as follows: "RG_KEYWORD N FILE.TXT DATE AUTHOR TITLE CONTENTS EOM" where
N is the number of the post starting at 1 and going to the max number of discussion posts, DATE is the date the file was
 created, AUTHOR is the creator of the post, TITLE is the title, and FILE.TXT is the name of the file. CONTENTS is the
 content of the file, which can be sent across several messages based on the size of the post.

If the ERROR keyword is sent from the server to the client it will be accompanied by an error code number. Here is a
list of all error numbers and what they mean:
0 - Command not found
1 - Login invalid
10 - When using the RG command, group not found



***PERSISTENCE AND I/O***

All persistent information is stored in txt files. If a given file is not found, then it is created before it is first
used. Here is a list of all files used by the program:
Server files:
    users.txt
    groups.txt
Client files:
    Client files are stored in a folder that is named after their userId. This is why userIds can only be named with
    numbers and characters.
    Files that are stored in the user folder:
    subscription.txt