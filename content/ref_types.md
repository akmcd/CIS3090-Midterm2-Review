title: Datatypes, operators and constants

- Datatypes:
    - MPI needs the type of the data as an `MPI_Datatype` value, and it must match the C type of the variable
    - `count` arguments are numbers of elements, never bytes

| C type | MPI datatype |
|---|---|
| `char` | `MPI_CHAR` |
| `signed char` | `MPI_SIGNED_CHAR` |
| `unsigned char` | `MPI_UNSIGNED_CHAR` |
| `short` | `MPI_SHORT` |
| `int` | `MPI_INT` |
| `unsigned` | `MPI_UNSIGNED` |
| `long` | `MPI_LONG` |
| `long long` | `MPI_LONG_LONG` |
| `float` | `MPI_FLOAT` |
| `double` | `MPI_DOUBLE` |
| `long double` | `MPI_LONG_DOUBLE` |
| raw bytes | `MPI_BYTE` |

- Reduction operators (textbook Table 3.2):
    - Used as the `operator` argument of `MPI_Reduce` and `MPI_Allreduce`

| Operator | Meaning |
|---|---|
| `MPI_SUM`, `MPI_PROD` | sum, product |
| `MPI_MAX`, `MPI_MIN` | maximum, minimum |
| `MPI_MAXLOC`, `MPI_MINLOC` | extreme value and where it is |
| `MPI_LAND`, `MPI_LOR`, `MPI_LXOR` | logical and, or, exclusive or |
| `MPI_BAND`, `MPI_BOR`, `MPI_BXOR` | bitwise and, or, exclusive or |

- Constants:

| Constant | Meaning |
|---|---|
| `MPI_COMM_WORLD` | the communicator with every process |
| `MPI_ANY_SOURCE` | wildcard for the source of a receive |
| `MPI_ANY_TAG` | wildcard for the tag of a receive |
| `MPI_STATUS_IGNORE` | pass instead of a status when you do not need one |
| `MPI_SUCCESS` | the return value of a call that worked |

- Common errors and what they mean:

| What you see | Usual cause |
|---|---|
| The program hangs | a receive or collective with no partner, or two blocking sends facing each other |
| "Message truncated" | the receive count is smaller than the message |
| Right answer on rank 0, garbage elsewhere | the output of `MPI_Reduce` is only valid on the destination |
| Wrong total with no error | `n` is not divisible by `comm_sz`, so some trapezoids are skipped |
