# The Invisible Software Running the Internet's Video

*A summary of Lex Fridman Podcast #496 with Jean-Baptiste Kempf and Kieran Cunha*

---

Every time you watch a YouTube video, stream on Netflix, make a video call, or hit play in VLC, there's a piece of software doing an extraordinary amount of work completely out of sight. It's called FFmpeg. You've never thought about it. You've used it thousands of times.

Lex Fridman sat down with Jean-Baptiste Kempf — president of VideoLAN and lead developer behind VLC — and Kieran Cunha — codec engineer and the force behind the famously spicy FFmpeg Twitter account — for one of the most technically rich conversations in the podcast's history. Here's what they covered.

---

## What Is FFmpeg, Really?

FFmpeg is a collection of open-source libraries and command-line tools for decoding, encoding, transcoding, and streaming virtually any video or audio format ever invented. It powers YouTube, Netflix, Chrome, Discord, OBS, and basically every platform that touches video.

VLC, with over 6.5 billion downloads, is its most famous consumer — but VLC itself is just one of countless applications built on top of FFmpeg's engine.

What makes this remarkable is that both are built almost entirely by volunteers. The core FFmpeg team is 10–15 people. VLC's is five. Yet they collectively support more operating systems than Microsoft, Google, and Apple combined — including Windows XP, iOS 9, and OS/2 (yes, there are reportedly 10 people still running OS/2 and one of them maintains VLC for it).

---

## How Video Actually Works

When you press play, an enormous pipeline kicks off:

1. **Demuxing** — The container file (MP4, MKV, AVI) is split into separate audio, video, and subtitle tracks.
2. **Decoding** — Each track is decompressed using its respective codec. About 45% of files can't be hardware-decoded by the GPU, so they fall back to software.
3. **Rendering** — Raw frames are sent to the graphics card; raw audio to the sound card.

The key insight is how aggressive the compression is. MP3 compresses audio roughly 10x. Video codecs compress 100x to 200x — and they do it by deliberately degrading the signal in ways the human eye won't notice. They work in YUV color space rather than RGB, because human eyes are far more sensitive to brightness than to color. They use the discrete cosine transform to move image data into the frequency domain, quantize it, and discard what's imperceptible.

Each new generation of codecs achieves about 30% better compression at the same quality — but requires orders of magnitude more compute to encode.

---

## Containers vs. Codecs: The Industry's Great Confusion

People confuse MP4 with H.264. They're not the same thing. MP4 is a container (the box); H.264 is a codec (what's inside the box). Technically, H.264 is called MPEG-4 Part 10 — the naming is a mess by design, or at least by industry committee.

VLC and FFmpeg don't trust file extensions. They probe the actual bytes. A file labeled `.mp4` might be an MOV internally, or something entirely different. One of VLC's founding philosophies — born from its origins playing UDP network streams that could be corrupt or incomplete — is to never trust input and always try to play it anyway.

---

## The Open Source Philosophy

FFmpeg and VLC are licensed under the LGPL (with parts under GPL), which means companies can integrate them without open-sourcing their entire codebase — but must give back any modifications to the library itself.

The license is described as a social contract. It's the one thing the community agrees on, and it's what makes global collaboration between thousands of people with different backgrounds, politics, and religions possible. Changing it is nearly impossible: you have to track down every contributor and get their sign-off.

Jean-Baptiste did exactly this when relicensing VLC's core from GPL to LGPL. He contacted over 350 people. He traveled to meet them in person. In one case, he found himself at a factory explaining open-source licensing to a worker whose son — who had written the code — had passed away. It nearly brought him to tears.

---

## The Culture: Code Is Everything

The community is unapologetically meritocratic. Contributions are reviewed on the quality of the code alone. A senior engineer at a major company gets the same treatment as a teenager in a basement. The tone can be blunt. The standard is uncompromising. As JB put it:

> *"Maybe you're a dog. I don't care. I need to look at your code."*

This isn't elitism — it's necessity. The core maintainer group is tiny. Every line of code they accept is code they'll maintain for years. It has to be excellent.

Some of the most prolific contributors have been teenagers. Kieran highlighted 16-year-olds writing thousands of lines of handwritten assembly that outperform Google engineers' submissions. Andrew Kelly, creator of the Zig programming language, got his start in FFmpeg.

---

## Assembly: The Lost Art That Still Matters

One of the most heated topics in FFmpeg's Twitter presence is the debate over assembly language. Most engineers assume modern compilers, with auto-vectorization, can match or exceed handwritten assembly. FFmpeg's experience says otherwise — by a factor of 10x to 62x.

The specific technique is SIMD (Single Instruction, Multiple Data), which allows one CPU instruction to operate on 16 values simultaneously — ideal for pixel grids. The dav1d project, a software decoder for the AV1 codec, has 30,000 lines of C and **240,000 lines of handwritten assembly**. It was built because the Alliance for Open Media (Google, Netflix, Amazon) claimed software decoding of AV1 was impossible — that it required hardware. The FFmpeg/VideoLAN community proved them wrong.

The philosophy behind this obsession: hardware isn't getting faster the way it used to. Moore's law has slowed. The only way to keep up with demand is to extract more from the existing machine — sometimes using CPU instructions in ways their designers never intended, including cryptography instructions repurposed for video processing.

---

## The Corporate Exploitation Problem

FFmpeg and VLC collectively run on hundreds of millions of devices and power trillion-dollar companies. The financial support they receive is not commensurate with that.

A now-infamous incident: Microsoft Teams filed a bug report on FFmpeg's public tracker, labeled it "high priority," and name-dropped the Microsoft product to imply urgency — expecting volunteer maintainers to prioritize their commercial software's issue. When politely offered a support contract, Microsoft offered a one-time payment of a few thousand dollars.

This kind of dynamic is everywhere. Companies have entire products built on FFmpeg with zero contribution back. Many don't even know they're doing it — a product manager files a ticket on what they assume is a traditional vendor's JIRA, unaware they're demanding unpaid labor from hobbyists.

The response from the FFmpeg and VideoLAN teams has been to use Twitter/X as a pressure valve. A threatening tweet that VLC would be pulled from the Android Play Store over a year-long unresolved bug got a response from Google within days. "Spicy tweets" have driven more donations and more awareness than any formal outreach.

---

## Surveillance, Backdoors, and WikiLeaks

VLC has been implicated in two notable intelligence operations.

CIA's Vault 7 documents, released by WikiLeaks, revealed that a modified version of VLC had been distributed — identical to the official binary except for one additional DLL that exfiltrated data. VideoLAN's response was a press release reminding users to only download VLC from official sources.

When asked directly if intelligence agencies had ever approached VideoLAN to add a backdoor, JB confirmed they had. He declined. As he put it: *"If we had to compromise our software, we would shut it down."*

---

## FFmpeg on Mars

The Mars 2020 rover uses FFmpeg to compress images. The team behind the rover published a paper on it and specifically noted their preference for using commercial off-the-shelf technology wherever possible.

FFmpeg is also used at CERN to stream analog camera feeds across the 27-kilometer LHC ring. VLC monitors live feeds in Formula 1 paddocks, the European Space Agency, and SpaceX launch control.

---

## The Future: Smells, Brainwaves, and Archiving History

The conversation ended on a surprisingly expansive note. JB and Kieran see FFmpeg and VLC eventually handling volumetric video, brain-computer interface data (Neuralink formats), spatial audio, haptic feedback, and even smell — whatever the human sensorium requires.

VLC already has a haptic plugin for 4D cinemas. Spatial audio support is in active development. The framework is being designed so that adding new sensory modalities is an architecture problem, not a rebuild.

On the archiving side: a dedicated community of archivists uses FFmpeg and the lossless FFV1 codec to preserve the world's film and video heritage. They're making decisions about what survives. Physical tapes from the 1970s and 80s are degrading. There aren't enough tape heads in the world to read them all. What isn't archived now may be gone forever.

---

## Why It Matters

The most striking thing about this conversation isn't the technical depth — it's the philosophical point underneath all of it. Two people and a handful of volunteers built and maintain infrastructure that every person on Earth uses daily. The video you're watching right now passed through their work.

They didn't do it for money. They did it because they love movies, they love pushing compilers to their limits, and they believe that complex technology should be free for everyone.

> *"The world is a museum of passion projects."*

FFmpeg and VLC are two of the best exhibits in it.

---

*Watch the full episode: [Lex Fridman Podcast #496 — FFmpeg and VLC with Jean-Baptiste Kempf and Kieran Cunha](https://www.youtube.com/watch?v=nepKKz-MzFM)*
