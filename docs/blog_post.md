**[Support TailJLogs Development on GitHub](https://github.com/brianoflondon/tailjlogs)
[Follow me on Hive](https://hive.blog/@brianoflondon)**

***This is a value for value project: see the explanation in the footer.***

---

## TailJLogs: A Better Way to View Logs in Your Terminal

Developers spend more time reading logs than they probably care to admit. Whether you're debugging a production issue at 3 AM or tracking down a subtle bug in your application, the quality of your log viewing experience matters more than you'd think.

I've been frustrated with log viewing tools for years. Either they're too simplistic—just `tail` and `grep`—or they're overly complex GUI applications that take forever to open a massive log file. I needed something fast, powerful, and purpose-built for the reality of modern application logging, especially JSON logs.

That's why I built TailJLogs.


![TailJLogs](https://files.peakd.com/file/peakd-hive/brianoflondon/Eo6BoTCAqz5uSEgzXz9gWKtR5NDHQAhfFoMjpe7NyNgj1Crwsmv2dTt8c4fd583h3Ye.png)


### The Problem with Log Files Today

Modern applications don't just spit out plain text anymore. We've got JSON logs, structured logs, logs from Docker containers, logs from microservices running all over the place. When something goes wrong, you're usually looking at multiple log files simultaneously.

I found myself in a situation where I needed to:
- Open multi-gigabyte log files instantly (not wait for a file manager dialog)
- View JSON logs in a readable format without them being a wall of text
- Search and filter logs without switching between different tools
- Tail multiple files at the same time, understanding which service each line came from
- Drill down into the full JSON detail of a log entry without leaving the terminal

The existing tools didn't do all of this well. Enter TailJLogs.


![image.png](https://files.peakd.com/file/peakd-hive/brianoflondon/23swkTX4yLzZtadBFe1jUthFhprWQzhjHxXFnuBkJWA7BmEEHg4LLVsWoJ3ipr1bVuQ3K.png)


### Based on Something Good

I didn't start from scratch. TailJLogs is built on the excellent [Toolong](https://github.com/Textualize/toolong) project by Will McGugan—an incredibly clean implementation of a terminal-based log viewer using the [Textual](https://textual.textualize.io/) framework.

But Toolong wasn't specifically designed for JSON logs. I saw an opportunity: take something great and optimize it for the logging reality of 2024/2025—where JSON is king.

### What Makes TailJLogs Different

#### JSONL Compact Format

Instead of displaying JSON logs as an unreadable wall of braces and quotes, TailJLogs parses them and shows:

```
01-15T09:36:38.194 INFO module 39 : message
```

This is readable. Your eyes can scan it. You can actually understand what's happening without having to expand every single line. When you want to see the full JSON? Press Enter. The entire JSON object displays beautifully formatted in a detail panel below. You can also copy the JSON to your clipboard with `⌘C` (macOS) or `Ctrl+Shift+C`, and press `y` to toggle between **Pretty** and **Raw** copy modes (default is Pretty).

![Side by side](https://files.peakd.com/file/peakd-hive/brianoflondon/23tGTggBu4XCvJFe8g3cJDjRtKQryCHWefai3waca6ofEnmZA3FmRhsGp1rCDQ1TMaxwQ.png)

#### Smart Filtering Without Leaving Your Flow

Press `\` and you get a filter dialog. This isn't just "find and highlight"—it actually hides lines that don't match. You can quickly drill down to just the errors, or just the messages from a specific service, then back out and see everything again. Fast. Intuitive.

#### Merge Multiple Files with Visual Distinction

Using `--merge`, you can tail multiple log files at the same time. Each line gets a colored filename prefix so you always know which file/service it came from. Want to see exactly how your API logs interleave with your database logs? Now you can. It's like `docker-compose logs` but for any files you throw at it.

#### Handle Real File Structures

Logs rotate. Files get compressed as `.bz` or `.bz2`. Logs live in deeply nested directory structures. TailJLogs handles this:

- Glob patterns: `*.jsonl`, `logs/**/*.log`, you name it
- Automatic decompression of compressed files
- Directory expansion to find all log files automatically

<div class="pull-right">


![Summary](https://files.peakd.com/file/peakd-hive/brianoflondon/23tGRUVGnEf7A3Edzfo5pZW9zBUwQWk7GwJXoQcUacKJoHvqAK8kcJxNSgzVjk6C7Hue6.png)

</div>

### New in v2.4: Summary Mode

Sometimes you just need to understand what's in your logs without reading through all of them. The new `--summary` mode scans a directory (or a set of rotated log files) and tells you:

- When the logs start and end
- How long they span
- How many log entries at each level (ERROR, WARN, INFO, etc.)
- Available in plain text or JSON output

Perfect for understanding the scope of a problem before you dive in.

### Built for Developers, By a Developer

Everything about TailJLogs is designed around actual developer workflows:

- **Fast startup**: No waiting around. It opens huge files instantly.
- **Keyboard-first**: Everything accessible from the keyboard. Navigate with arrow keys, press `/` to find, `\` to filter.
- **In the terminal**: No separate window. No context switching. It works wherever you work.
- **Modern foundation**: Built on Textual, which means it works smoothly on macOS, Linux, and Windows.

### How to Get Started

```bash
# Using pip
pip install tailjlogs

# Using uv (recommended)
uv tool install tailjlogs

# Using pipx
pipx install tailjlogs
```

Then just:

```bash
# View a single file
tailjlogs app.jsonl

# View multiple files side by side
tl access.log error.log app.jsonl

# Merge and tail (great for microservices)
tl --merge *.jsonl

# Get a summary of your logs
tl --summary /var/log/myapp/
```


![--help](https://files.peakd.com/file/peakd-hive/brianoflondon/Eo1vTqKnAyEsbUq11MqdG52JmCkDBkGvqhwC9azYm42dV6Uz6EGcu1MxTDNQ7La5Hdz.png)


### The Vision

TailJLogs is part of a broader commitment I have to building tools that work with Hive. This particular project is open source and free to use, but it represents the same philosophy I apply to everything I build: make things useful, make them fast, and make them a pleasure to use.

If you're debugging logs in the terminal, I believe TailJLogs will become indispensable to your workflow. Try it. I think you'll be surprised by how much faster and cleaner your debugging becomes.

---

## Value for Value

If you find TailJLogs useful, I'd appreciate your support in any form:

- **Star the repository** on GitHub — it helps others discover the project
- **Upvote this post** on Hive if you found it valuable
- **Direct support**: You can send me tips directly (look for the Lightning Address or tip button on Hive)

I build because I love building. Your support helps me dedicate more time to making tools like this better.

**[Support Brianoflondon's Witness KeyChain or HiveSigner](https://vote.hive.uno/@brianoflondon)**

---

- [Find me on Telegram](https://t.me/brianoflondon)
- [TailJLogs on GitHub](https://github.com/brianoflondon/tailjlogs)
- [TailJLogs on PyPI](https://pypi.org/project/tailjlogs/)
- [Vote for Brianoflondon's Witness KeyChain or HiveSigner](https://vote.hive.uno/@brianoflondon)
- [Follow me on Hive](https://hive.blog/@brianoflondon)
