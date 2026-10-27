# CIS*3090 midterm 2 study site (MPI)

Built for reading and predicting MPI code. Each code page has a rank lens (pick a rank and only the lines it runs stay lit) and a message timeline you can step through. There are also two small labs (send/receive matching, collectives), a trapezoid trace and code-reading questions with got-it / missed-it marks.
Covers lectures 09 to 11 and textbook Chapter 3, sections 3.1 to 3.4.

**Study pages: https://akmcd.github.io/CIS3090-Midterm2-Review/**

Direct links:

- [Start here](https://akmcd.github.io/CIS3090-Midterm2-Review/)
- [Big ideas](https://akmcd.github.io/CIS3090-Midterm2-Review/concepts.html)
- [Reading MPI code](https://akmcd.github.io/CIS3090-Midterm2-Review/method.html)
- [Send and receive](https://akmcd.github.io/CIS3090-Midterm2-Review/sendrecv.html)
- [Collective communication](https://akmcd.github.io/CIS3090-Midterm2-Review/collectives.html)
- [The trapezoidal rule](https://akmcd.github.io/CIS3090-Midterm2-Review/trapezoid.html)
- [Code walkthroughs](https://akmcd.github.io/CIS3090-Midterm2-Review/hello.html)
- [Hangs and mix-ups](https://akmcd.github.io/CIS3090-Midterm2-Review/pitfalls.html)
- [Code-reading questions](https://akmcd.github.io/CIS3090-Midterm2-Review/practice.html)
- [Trapezoid trace](https://akmcd.github.io/CIS3090-Midterm2-Review/trace.html)
- [Cheat sheet](https://akmcd.github.io/CIS3090-Midterm2-Review/reference.html)

## How the site is published (GitHub Pages)

1. In the repository, open Settings, then Pages
2. Under Build and deployment choose "Deploy from a branch", pick the `main` branch and the `/ (root)` folder, then save
3. After a minute the site is live at the link above
4. Keep the `.nojekyll` file in the repository root

The pages are plain HTML files that are already built, so nothing else is needed.

## Editing and adding pages

The notes live in `content/*.md` as nested bullet lists. After editing, rebuild:

    pip install -r requirements.txt
    python build.py

To add a page (for example a new lecture):

1. Create `content/<slug>.md`, starting with a line like `title: Lecture 12`
2. Add `("<slug>", "Label", "Group", "One-line description")` to `PAGES` in `build.py`
3. Run `python build.py` and commit the new `.html` files

To add a code walkthrough:

1. Put the C file in `examples/`
2. Create `content/walk/<name>.json` (copy `hello.json`): the file, line range, who runs which lines (`who`), the line numbers each timeline step lights up (`refs`), notes under lines (`notes`) and the text shown for each rank (`summaries`)
3. Add `{{walk <name>}}` to a page
4. If the program sends different messages from the existing ones, add an event builder with the same `example` name to `EVENTS` in `assets/app.js`

Handy syntax inside the Markdown files:

- `{{walk NAME}}` rank lens plus message timeline, from `content/walk/NAME.json`
- `{{code mpi_hello.c 23-64 hl=35,48}}` a plain listing with real line numbers
- `{{lab match}}`, `{{lab collective}}`, `{{diagram memory}}`, `{{progress}}`, `{{map}}`
- `[[r0]]`, `[[rx]]` small rank labels
- `::: q` question, a `---` line, the answer, then `:::`
- `::: run Caption` real program output (a first line starting with `$ ` is styled as the command), `::: warn` and `::: note` callouts
- Fenced code blocks and the blocks above can be indented to stay inside a bullet

## Folders

- `content/`: the notes as Markdown (`trace.html` is hand-written)
- `content/walk/`: one JSON file per code walkthrough
- `assets/`: `style.css` and `app.js` (lens, timeline, labs, practice marks, trace)
- `examples/`: the course programs, unchanged
- `examples/extras/`: small programs written for this site to test pitfalls (hangs, reduce order, scatter and gather), not course material

## Running the examples

    mpicc -std=c99 -Wall -o mpi_hello examples/mpi_hello.c
    mpiexec -n 4 ./mpi_hello
    echo "0 3 1024" | mpiexec -n 4 ./mpi_Bcast

All outputs shown on the site were produced with MPICH.
