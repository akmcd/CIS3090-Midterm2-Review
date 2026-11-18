# CIS*3090 Midterm 2 Review

**Live site: https://akmcd.github.io/CIS3090-Midterm2-Review/**

A static study site for CIS*3090 Parallel Programming midterm 2, covering lectures 09 to 17. Same layout as the [CIS*4020 midterm review site](https://akmcd.github.io/CIS4020-Midterm-Review/), plus code pages that walk through the course programs rank by rank.

- **Read** (`read.html`): 11 sections built from the lecture slides, each starting from the idea, with worked examples, exam traps, two labs (send/receive matching, collectives) and a cheat sheet.
- **Code** (`code.html`): the course programs with a rank lens (pick a rank and only the lines it runs stay lit) and a message timeline you can step through: `mpi_hello.c`, `mpi_hello2.c`, `mpi_SendRec.c`, `mpi_Bcast.c`, `heatDiffusionMpi.c`, three small programs that hang, and a trapezoid trace.
- **Quizzes** (`quiz.html`): 94 multiple-choice questions, one quiz per section, with an explanation after every answer.
- **Short answers** (`short.html`): 41 code-reading and explain-why prompts with model answers hidden until you open them.
- **Flashcards** (`flashcards.html`): 137 definitions, by section.
- **Practice exam** (`exam.html`): 40 questions with a 50- or 75-minute timer, or none. Exam A is 40 questions not used anywhere else; Exam B draws 40 from the quiz bank.
- **Reference** (`ref_index.html`): every MPI function used in the course, with its signature, arguments and the mistakes to avoid.

Progress is saved in your browser's local storage. Nothing is sent anywhere.

## How the site is published (GitHub Pages)

1. In the repository, open Settings, then Pages
2. Under Build and deployment choose "Deploy from a branch", pick the `main` branch and the `/ (root)` folder, then save
3. Keep the `.nojekyll` file in the repository root

The pages are plain HTML files that are already built, so nothing else is needed.

## Editing

Rebuild after any change:

    pip install -r requirements.txt
    python build.py

- Reading notes: `content/<section>.md` as nested bullet lists. The first lines are `title:`, `source:` and `lead:` (shown under the section heading). Section order and groups: `READ` in `build.py`.
- Quiz questions: `content/data_src/bank.py`
- Practice Exam A: `content/data_src/exam.py`
- Flashcards: `content/data_src/cards.py`
- Short answers: the `::: q` blocks in `content/practice.md` and `content/practice2.md` (`SHORT_SOURCES` in `build.py` gives each one its section)
- Code pages: `CODE` in `build.py`, `content/<slug>.md`, and `content/walk/<name>.json` for each walkthrough
- Reference pages: `REF` in `build.py` and `content/ref_*.md`
- Section names for quizzes and flashcards: `TOPICS` in `assets/common.js` (keys must match the section slugs)

`build.py` runs `content/data_src/make_data.py` first, which checks every question (valid answer index, no duplicate options, known section) and writes `data/bank.js`, `data/exam.js` and `data/flashcards.js`. `quiz.html`, `short.html`, `flashcards.html` and `exam.html` are hand-written and read those files.

In questions, `answer` is the index of the correct option, or a list of indices for "select all that apply". Options are shuffled when shown. Wrap code words in backticks and use `**bold**` for emphasis; put a code listing in `code=`.

After editing `assets/`, bump `VER` in `build.py` and the `?v=...` tags in the four hand-written pages so browsers fetch the new files.

To add a code walkthrough:

1. Put the C file in `examples/`
2. Create `content/walk/<name>.json` (copy `hello.json`): the file, line range, who runs which lines (`who`), the line numbers each timeline step lights up (`refs`), notes under lines (`notes`) and the text shown for each rank (`summaries`)
3. Add `{{walk <name>}}` to a page
4. If the program sends different messages from the existing ones, add an event builder with the same `example` name to `EVENTS` in `assets/app.js`

Handy syntax inside the Markdown files:

- `::: eg Title` amber worked example, `::: warn Title` red exam trap, `::: note Title` blue note, each closed with `:::`
- `::: run Caption` real program output (a first line starting with `$ ` is styled as the command)
- `{{walk NAME}}` rank lens plus message timeline
- `{{code mpi_hello.c 23-64 hl=35,48}}` a plain listing with real line numbers
- `{{lab match}}`, `{{lab collective}}`, `{{diagram memory}}`, `{{fnindex}}`
- `[[r0]]`, `[[rx]]` small rank labels
- `::: fn MPI_Name` a reference entry (first line is the one-line purpose, then a fenced signature, an arguments table and bullets)
- Fenced code blocks and the blocks above can be indented to stay inside a bullet. A table or block placed between two bullets folds with the subsection above it

Old page names from the first version of the site (`concepts.html`, `practice.html` and so on) are kept as redirects.

## Folders

- `content/`: the notes as Markdown (`trace.html` is hand-written), `walk/` for code walkthroughs, `data_src/` for the question and flashcard lists
- `data/`: generated quiz, exam, flashcard and short-answer files
- `assets/`: `style.css`, `common.js` (header, storage, question helpers), `site.js` (folding, contents), `home.js`, `app.js` (rank lens, timeline, labs, trace)
- `examples/`: the course programs, unchanged (`heatDiffusionMpi.c` is from `heatDiffusion.zip`)
- `examples/extras/`: small programs written for this site to test pitfalls, not course material. `arrAdd.py` is the lecture 15 Warp example put together from the slide code

## Running the examples

    mpicc -std=c99 -Wall -o mpi_hello examples/mpi_hello.c
    mpiexec -n 4 ./mpi_hello
    echo "0 3 1024" | mpiexec -n 4 ./mpi_Bcast
    mpicc -O2 -Wall -o heatDiffusionMpi examples/heatDiffusionMpi.c -lm
    mpirun -np 4 ./heatDiffusionMpi 16 6 1e-4 50000 1 frames txt
    pip install warp-lang==1.16.0 && python3 examples/extras/arrAdd.py

The outputs for lectures 09 to 11 were produced with MPICH. The heat diffusion runs were checked with Open MPI, and the Warp example with Warp 1.16.0 on the CPU.

## Sources and caveats

Written from the CIS*3090 slides and *An Introduction to Parallel Programming* (Pacheco and Malensek, 2nd ed.). `mpi_odd_even.c` and `arrAdd.py` were not in the posted files, so those sections use the code shown on the slides. The pthreads lectures (01 to 08) are not covered.
