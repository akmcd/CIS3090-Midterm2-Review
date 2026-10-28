title: Send and receive functions

- How a send finds its receive:
    - A send and a receive match when the communicator, the tag, the source and the destination all agree
    - The datatypes must agree too, and the receive count must be at least the send count
    - Only the receiver may use wildcards, and a sender must always name a destination and a tag
    - Messages from one sender to one receiver arrive in the order they were sent (**non-overtaking**)
    - The Send and receive page explains this with a lab

::: fn MPI_Send
Sends a message to one other process.

```c
int MPI_Send(const void* msg_buf_p, int msg_size, MPI_Datatype msg_type,
             int dest, int tag, MPI_Comm communicator);
```

| Argument | Meaning |
|---|---|
| `msg_buf_p` | where the data is |
| `msg_size` | how many elements to send (not bytes) |
| `msg_type` | the type of each element, like `MPI_INT` |
| `dest` | rank of the receiving process |
| `tag` | a non-negative int the receiver can use to tell messages apart |
| `communicator` | usually `MPI_COMM_WORLD` |

- It may copy the message into a system buffer and return at once, or wait until the receiver is ready
- Small messages are usually buffered and large ones usually wait, but the standard does not promise either
- When it returns, your send buffer is safe to reuse, but the message may not have arrived yet
- To send a string, send `strlen(s) + 1` characters so the `'\0'` goes too
- Used in the course: `mpi_hello.c` line 48, `mpi_SendRec.c` lines 73 and 115 to 117
:::

::: fn MPI_Recv
Receives one message. It waits until a matching message arrives.

```c
int MPI_Recv(void* msg_buf_p, int buf_size, MPI_Datatype buf_type,
             int source, int tag, MPI_Comm communicator, MPI_Status* status_p);
```

| Argument | Meaning |
|---|---|
| `msg_buf_p` | where to put the data |
| `buf_size` | how many elements the buffer can hold (not how many will arrive) |
| `buf_type` | the type of each element |
| `source` | rank to receive from, or `MPI_ANY_SOURCE` |
| `tag` | tag to match, or `MPI_ANY_TAG` |
| `communicator` | must be the same as the sender used |
| `status_p` | filled with details about the message, or `MPI_STATUS_IGNORE` |

- A receive with no matching send waits forever, so the program hangs
- If the message has more elements than `buf_size`, MPI reports a "Message truncated" error
- A buffer that is bigger than the message is fine
- Used in the course: `mpi_hello.c` line 54, `mpi_hello2.c` line 60, `mpi_SendRec.c` lines 78 and 120 to 124
:::

::: fn MPI_Ssend
A send that does not return until the receiver has started a matching receive.

```c
int MPI_Ssend(const void* msg_buf_p, int msg_size, MPI_Datatype msg_type,
              int dest, int tag, MPI_Comm communicator);
```

- It takes the same arguments as `MPI_Send`
- It never uses a system buffer, so it shows what the program does when sends have to wait
- Safety check: replace every `MPI_Send` with `MPI_Ssend`, and if the program hangs it was **unsafe** (it only worked because messages happened to be buffered)
- Used in this site: `head_to_head.c` in `examples/extras/`
:::

::: fn MPI_Sendrecv
Sends one message and receives another in a single call, in a way that cannot deadlock.

```c
int MPI_Sendrecv(const void* send_buf_p, int send_buf_size, MPI_Datatype send_buf_type,
                 int dest, int send_tag,
                 void* recv_buf_p, int recv_buf_size, MPI_Datatype recv_buf_type,
                 int source, int recv_tag, MPI_Comm communicator, MPI_Status* status_p);
```

- It is the fix for two processes that each want to send first and then receive
- The send buffer and the receive buffer must be different
- The course mentions it as a fix, and does not use it in the example programs
:::

::: fn MPI_Status
A struct that a receive fills in with details about the message it got.

```c
MPI_Status status;
MPI_Recv(buf, 100, MPI_CHAR, MPI_ANY_SOURCE, MPI_ANY_TAG, MPI_COMM_WORLD, &status);
int sender = status.MPI_SOURCE;
int tag    = status.MPI_TAG;
```

| Member | Meaning |
|---|---|
| `status.MPI_SOURCE` | rank of the sender |
| `status.MPI_TAG` | the tag the message was sent with |
| `status.MPI_ERROR` | error code |

- It matters most with wildcards, because then the receiver does not otherwise know who sent the message or with what tag
- The number of elements is not a member, because it depends on the datatype, so use `MPI_Get_count`
- If you do not need the details, pass `MPI_STATUS_IGNORE`
- Used in the course: `mpi_hello2.c` lines 59 to 62
:::

::: fn MPI_Get_count
Tells you how many elements a received message contained.

```c
int MPI_Get_count(const MPI_Status* status_p, MPI_Datatype type, int* count_p);
```

| Argument | Meaning |
|---|---|
| `status_p` | the status filled in by `MPI_Recv` |
| `type` | the datatype you received with |
| `count_p` | output: the number of elements |

- This is the actual message length, which can be smaller than the buffer size you passed to `MPI_Recv`
- Used in the course: `mpi_hello2.c` line 64, where a 30 character greeting reports 31 elements because the `'\0'` was sent too
:::

- Wildcards (receiver only):
    - `MPI_ANY_SOURCE`: accept a message from any sender
    - `MPI_ANY_TAG`: accept a message with any tag
    - There is no wildcard for the communicator
    - With `MPI_ANY_SOURCE`, the order messages are received in can change from run to run
