# Distributed-Banking-Application
Used python and google's protocol buffer for marshalling and unmarshalling messages.
Implementation of Chandy-Lamport global snapshot algorithm.

## Requirenments 

- Python 2.7
- Google's protocol buffer

## Branch 
The distributed bank has multiple branches. Every branch knows about all other branches. 
A single TCP connection is setup between every pair of branches. Each branch starts with an initial balance. 
The branch then randomly selects another destination branch and sends a random amount of money to this destination branch 
at unpredictable times. 

Each branch will handle the following types of messages in a distributed bank:

- **InitBranch** this messages contains two pieces of information: the initial balance of a branch and a list of all
branches (including itself) in the distributed bank. Upon receiving this message, a branch will set its initial
balance and record the list of all branches.

- **Transfer** this message indicates that a remote, source branch is transferring money to the current, target branch.
The message contains an integer representing the amount of money being transferred. The branch receiving
the message should increase its balance by the amount of money indicated in the message.

Every branch is both a sender and a receiver. A sender can only send positive amount of money. It needs to
first decrease its balance, then send out a message containing the amount of money to a remote branch.
The amount of money will be drawn randomly between 1% and 5% of the branch’s initial balance.

- **InitSnapshot** upon receiving this message, a branch records its own local state (balance) and sends out Marker
messages to all other branches.  Upon receiving this message, the receiving branch
does the following:
  - if this is the first Marker message with the snapshot_id the receiving branch has seen, the re-
ceiving branch records its own local state (balance), records the state of the incoming channel from
the sender to itself as empty, immediately starts recording on other incoming channels, and sends out
Marker messages to all of its outgoing channels (i.e., all branches except itself).
  - otherwise, the receiving branch records the state of the incoming channel as the sequence of money
transfers that arrived between when it recorded its local state and when it received the Marker.
RetrieveSnapshot the controller sends retrieveSnapshot messages to all branches to collect snapshots. This mes-
sage will contain the snapshot_id that uniquely identifies a snapshot. A receiving branch should its
recorded local and channel states and return them to the caller (i.e., the controller) by sending a returnSnap-
shot message (next).

- **ReturnSnapshot** a branch returns the controller its captured local snapshot in this message. This message should
include the snapshot_id, captured local state, as well as all incoming channel states.

The branch executable will take two command line inputs. The first one is a human-readable name of the
branch, e.g., “branch1”. The second one specifies the port number the branch should runs on.

```
python branch.py branch1 9090

```

## Controller 

We rely on a controller to set a branch’s initial balance and notify every branch of all branches in
the distributed bank. This controller takes two command line inputs: the total amount of money in the distributed
bank and a local file that stores the names, IP addresses, and port numbers of all branches.


```
python controller.py 4000 branches.txt

```

The file (branches.txt) will contain a list of names, IP addresses, and ports, in the format “<name>
<public-ip-address> <port>”, of all of the running branches.

For example, if four branches with names: “branch1”, “branch2”, “branch3”, and “branch4” are running on
128.226.180.167 port 9090, 9091, 9092, and 9093, then branches.txt should contain:

```
branch1 128.226.180.167 9090
branch2 128.226.180.167 9091
branch3 128.226.180.167 9092
branch4 128.226.180.167 9093
```

The controller is fully automated. It periodically sends the InitSnapshot message with mono-
tonically increasing snapshot_id on a randomly selected branch and outputs to the console the aggregated
global snapshot retrieved from all branches in the correct format. 
In addition, the snapshot taken by branches is identified by their names: 
e.g., “branch1” to represent branch1’s local state, and “branch2->branch1” to represent the channel state. 

Sample controller output:

```
snapshot_id: 2
branch1: 1000, branch2->branch1: 0, branch3->branch1: 22
branch2: 1000, branch1->branch2: 0, branch3->branch2: 18
branch3: 960, branch1->branch3: 0, branch2->branch3: 0

```

## Messages transfer

File bank.proto defines the messages to be transmitted among processes in protocol buffer

```
protoc --python_out=./ bank.proto
```

The correctness of the Chandy-Lamport snapshot algorithm relies on FIFO message delivery of all communica-
tion channels among all branches (processes). A communication channel is a one way connection between two
branches. For example,  from “branch1” to “branch2” is one communication channel. From
“branch2” to “branch1” is another channel.
In order to ensure FIFO message delivery, we use TCP as the transport layer protocol for
branch communications. TCP ensures reliability and FIFO message delivery. TCP is also full duplex, allowing
messages to transmit in both directions. Each branch will set up exactly one TCP connection with every other
branches in the distributed bank.
This one single TCP connection will be used for transmitting banking messages between each other.




## References
- Distributed Snapshots: Determining Global States of Distributed Systems K. MANI CHANDY University of Texas at Austin and LESLIE LAMPORT Stanford Research Institute 
- Protobuf https://developers.google.com/protocol-buffers/

### Contact

[Kartik Deshpande](https://www.linkedin.com/in/kartik-deshpande/)

