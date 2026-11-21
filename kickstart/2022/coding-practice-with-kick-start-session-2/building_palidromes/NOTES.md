# Building Palindromes

- **Contest:** kickstart 2022 coding-practice-with-kick-start-session-2
- **Date:** 2026-11-21
- **Outcome:** Accepted?   ·   **Time spent:** ~93 min
- **Topics:**

## My approach
I think I've told you my approach that finally got me there.

## Where I got stuck
The most stuck I got was with the time complexity. I knew I needed a count of all letters for each substring 0 to i, but at first I kept thinking about using a for loop to run through and check the parity of each count, then determining how many odds there were. If there were more than one 1s, then it's a no go, which was obvious but what wasn't obvious to me was how to do it more efficiently. I knew also that I could subtract the counts from b with a - 1 given the query a, b. All this is probably because I did remember something about prefix trees. Then I thought about it more, and I questioned my assumptions. Do I really need to keep the counts of each letter? Or maybe just the parity of each letter? That was when I realized I could use a bit sequence for each substring. Then, before then, I couldn't really figure out where XOR fit (I had been primed glancing at the previous solution), but then it was clear there. Then I didn't know how to count the number of 1s still efficiently until the tutor helped me.

## Compared with the analysis
I don't know since the page warned me "You've spent 93 mins on this problem. The plan is about 45 mins before reading the analysis, and reading it means this attempt is logged as E," so I didn't want to look.

## One-line takeaway
In a problem where I need to count by parity, I can use a bit sequence instead; also, prefix trees or preprocessing prefixes and then subtracting later when queried is a good way to save performance.

## Tutor review
<Filled in by Claude.>
