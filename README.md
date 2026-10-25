# COMP 262 Team 7

Project starter for **RoyianChow and Kekelani Dayo** using Amazon Gift Cards reviews.
The code includes a runnable data audit and lexicon baselines. The report and slides
are editable templates. Phase 2 machine learning, recommendations and local Hugging
Face tasks remain clearly marked workspaces to complete together.

## Project files

- [Code and setup instructions](<1 Code/README.md>)
- [Combined project report template](<2 Project Report.docx>)
- [Presentation template](<3 Presentation Slides.pptx>)

Both original review archives, provenance and starter outputs are included under
`1 Code`. The Word and PowerPoint files can be downloaded and opened in their
desktop applications. Fill in the student name, IDs and course dates before submission.

## Run the starter

Install Python 3.10 or newer and Git, then open PowerShell:

```powershell
git clone https://github.com/RoyianChow/comp262-team7.git
cd comp262-team7
cd "1 Code"
py -m venv .venv
.\.venv\Scripts\python.exe project_starter.py
```

The default audit runs offline using Python's standard library. For the two
lexicon baselines:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe project_starter.py --lexicons
```

See the code README for the proposed split, dataset details and remaining work.
The report and slides keep result placeholders for the team's interpretation.

## Working together on GitHub

This repository is public, so Kekelani can view, download or clone it immediately.
Public visibility does not grant direct push access. The owner can invite Kekelani
under **Settings > Collaborators > Add people**, using a GitHub username or email.
After accepting, Kekelani can push a working branch and open a pull request.
Until then, Kekelani can fork the repository and propose changes from the fork.

From the repository root, begin each task with an updated copy and a separate branch:

```powershell
git switch main
git pull --ff-only
git switch -c kekelani/phase2-models
# Edit and save the files for this task.
git add "1 Code/phase2_kekelani.py"
git commit -m "Add Phase 2 model implementation"
git push -u origin kekelani/phase2-models
```

Open a pull request on GitHub for the partner to review before merging. Use a new,
descriptive branch name for each later task. If working from a fork, `origin`
points to the fork, and the pull request targets this repository's `main` branch.

Agree who is editing the Word report or PowerPoint at a given time. Git stores
their versions, but it does not combine simultaneous edits to those binary files.
Close the document before committing, pull the latest version before editing,
and commit the specific saved file. Python files and Markdown can use normal
branch and pull request review.

Local changes appear on GitHub only after a commit and push. Keep the Git clone
as the working copy and coordinate contributions in the report's meeting log.

## Dataset attribution

Amazon Review Data 2018, Gift Cards, published by Jianmo Ni and collaborators.
Source: https://nijianmo.github.io/amazon/index.html

Ni, J., Li, J., and McAuley, J. (2019). *Justifying Recommendations using
Distantly-Labeled Reviews and Fine-Grained Aspects*. EMNLP.
The dataset retains its publisher's terms. See `1 Code/data/SOURCE.md` for archive
sources and checksums. No additional license is assigned by this starter.

GitHub collaboration reference:
https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/repository-access-and-collaboration/inviting-collaborators-to-a-personal-repository
