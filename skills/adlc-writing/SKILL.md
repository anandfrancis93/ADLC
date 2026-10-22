---
name: adlc-writing
description: Write plain English for people to read. Use for PR titles and bodies, commit messages, review comments, specs, AGENTS.md, READMEs, changelogs and chat replies. Not for code, identifiers, quotes or app UI text.
---
# ADLC Writing

These rules apply to prose that a person reads. They do not apply to code, identifiers,
command output, quotes, or the text inside an app's UI.

The rules are a target, not a gate. Aim to meet most of them. No CI check enforces them,
and a reviewer does not block a PR for style alone.

## Sentences

1. Write at most 20 words in an instruction.
2. Write at most 25 words in a description.
3. Give one instruction per sentence.
4. Write at most 6 sentences in a paragraph.
5. Use the active voice. Name who does the action: "CI runs the tests", not "the tests are run".
6. Put the main point first. Put the reason after it.

## Words

1. Use the plain word: "use", not "utilize"; "make sure", not "ensure"; "start", not "initiate".
2. Use one word for one thing. Do not switch between synonyms for the same thing.
3. Keep noun stacks to 3 words or fewer. Write "the tier of the change", not "change risk tier level".
4. Name the specific thing: the file, the command, the number. Avoid vague words like "stuff" or "some issues".
5. Write "I don't know" when you don't know. Do not guess.

## Structure

1. Use lists for steps and for more than 2 parallel items.
2. Use a table only to compare items across the same attributes.
3. Use a Mermaid diagram when a flow or sequence is hard to follow in words.
4. Cut what the reader doesn't need: preamble, restating the question, closing summaries.

These rules adapt the limits of ASD-STE100 Simplified Technical English, in our own words.
