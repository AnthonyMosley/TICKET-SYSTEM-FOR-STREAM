
# Ticket Tracker (Because You Can’t Do Everything at Once)

So, you decided to keep track of tickets during your stream. You’ll still get overwhelmed, but now you’ll have a window to watch the chaos unfold in real time. Welcome to **Ticket Tracker**.

## Features
- **Dark Mode**: Because who doesn’t have a headache already?
- **Ticket Stages**: The system manages tickets through the stages of **Open**, **In Progress**, and **Complete**. It’s like watching grass grow, but with more text.
- **Priority Levels**: High-priority tickets are marked in red, as if you could actually get to them any faster. (Priority is automatically determined by it being a Subscriber by default)
- **Comments Section**: Every ticket has a comments section, because everyone needs more scrolling in their life.

## Installation
1. Make sure you have Python installed. (Or don’t. This probably won’t work if you don’t.)
2. Grab the dependencies (it’s just `tkinter`, so maybe you’re lucky):
   ```bash
   pip install tk
   ```

3. Run the tracker:
   ```bash
   python ticket_tracker.py
   ```

## Usage
1. **Open the app** and behold the thrill of incoming tickets.
2. Use the **spacebar** to move selected tickets along, because who has time to click buttons.
3. When you’re ready to pretend you’re on top of things, watch those tickets crawl from **Open** ➡️ **In Progress** ➡️ **Complete**.

## Ticket Life Cycle
The journey:
1. **Open**: Tickets start here, full of hope.
2. **In Progress**: This stage tells you you’re working on it, even if you forgot five minutes ago.
3. **Complete**: The ticket’s final resting place, where we pretend it was done on time.

## Pro Tips
- **Don't ignore high-priority tickets**. They’re in red to help you forget them slightly less often.
- **Comments** are there for your thoughts and updates, in case you forget what the ticket was about five minutes later.
- **Save regularly**. Or don’t, and let fate decide.

## Why This Exists
Some systems keep track of everything effortlessly. This isn’t one of them, but it tries. Sort of.

## Post notes
Working on developing a dynamic website for this.
Tickets are inserted by CSV for now, Plans to move to tinydb or something similar.
I use SAMMI to capture the tickets.
