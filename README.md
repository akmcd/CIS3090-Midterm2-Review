# CIS*3090 midterm study site (MPI)

Notes, code walkthroughs, an interactive trapezoid trace and code-reading questions for the MPI part of CIS*3090.
Covers lectures 09 to 11 and textbook Chapter 3, sections 3.1 to 3.4.

**Study pages: https://akmcd.github.io/CIS3090-Midterm2-Review/**

Direct links:

- [Start here](https://akmcd.github.io/CIS3090-Midterm2-Review/)
- [Big ideas](https://akmcd.github.io/CIS3090-Midterm2-Review/concepts.html)
- [Send and receive](https://akmcd.github.io/CIS3090-Midterm2-Review/sendrecv.html)
- [Collective communication](https://akmcd.github.io/CIS3090-Midterm2-Review/collectives.html)
- [The trapezoidal rule](https://akmcd.github.io/CIS3090-Midterm2-Review/trapezoid.html)
- [Trapezoid trace](https://akmcd.github.io/CIS3090-Midterm2-Review/trace.html)
- [Code-reading questions](https://akmcd.github.io/CIS3090-Midterm2-Review/practice.html)
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
2. Add `("<slug>", "Sidebar label", "Group")` to `PAGES` in `build.py`
3. Run `python build.py` and commit the new `.html` files

Handy syntax inside the Markdown files:

- `{{code mpi_hello.c 23-64 hl=35,48}}` shows lines 23 to 64 of `examples/mpi_hello.c` with the real line numbers, highlighting lines 35 and 48 (indent it under a bullet to keep it in the list)
- `[[r0]]`, `[[r1]]`, `[[r2]]`, `[[r3]]`, `[[rx]]` make the coloured rank chips
- A practice question is a block that starts with `::: q`, has the question, a line with `---`, the answer, and ends with `:::`
- Fenced code blocks can be indented to stay inside a bullet

Colours and layout are in `style.base.css` (the build appends the code colours and writes `style.css`).

## Folders

- `content/`: the notes as Markdown (and `trace.html` for the interactive page)
- `examples/`: the course programs, unchanged
- `examples/extras/`: small programs written for this site to test pitfalls (hangs, reduce order, scatter and gather), not course material
- `trace.js`: the trapezoid simulator, which mirrors the C arithmetic

## Running the examples

    mpicc -std=c99 -Wall -o mpi_hello examples/mpi_hello.c
    mpiexec -n 4 ./mpi_hello
    echo "0 3 1024" | mpiexec -n 4 ./mpi_Bcast

All outputs shown on the site were produced with MPICH.
