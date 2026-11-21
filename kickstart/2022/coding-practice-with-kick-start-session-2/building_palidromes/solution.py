import sys


def preprocess(s):
    # algo:
    # 1. store a bit sequence for 0 - i
    # 2. for each sequence, 0 means the count for that letter is even; 1 odd
    mask = 0
    bits = [mask]
    for c in s:
        num = c - 65
        # How the counts are stored in reverse, but in the end doesn't matter anyway
        # since we only care about how many 1s there are.
        mask ^= 1 << num
        bits.append(mask)
    
    return bits
    

def main():
    it = iter(sys.stdin.buffer.read().split())
    nxt = lambda: next(it)
    ni  = lambda: int(next(it))
    
    t = ni()
    out = []
    
    for case in range(1, t + 1):
        n, q = ni(), ni()
        s = nxt()
        
        bit_seqs = preprocess(s)
        
        # When processing query pairs a, b:
        # 1. XOR bit sequences of b with a - 1
        # 2. if there are less than or equal to 1 ones, inc ans
        ans = 0
        for _ in range(q):
            a, b = ni(), ni()
            ans += (bit_seqs[b] ^ bit_seqs[a-1]).bit_count() <= 1
        
        out.append(f"Case #{case}: {ans}")
    
    sys.stdout.write("\n".join(out) + "\n")

main()
