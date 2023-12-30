import sys

class Solution:
    def building_palindromes(self, n, q, letters, questions):
        totalCount = 0
        counts = [[False] * 26]

        # count; prefix sum implementation. has extra "base case"
        # where all frequencies are "0"
        for i, c in enumerate(letters):
            ind = ord(c) - ord('A')
            counts.append(counts[i][:]) # copy from previous
            counts[i+1][ind] = not counts[i+1][ind] # switch parity

        for l, r in questions:
            # use xor for subtraction
            # needed l-1 to offset for prefix sum
            sub = [counts[r][i] ^ counts[l-1][i] for i in range(26)]
            oddCount = 0
            for s in sub:
                if s: oddCount += 1
            if oddCount <= 1:
                totalCount += 1

        return totalCount

if __name__ == "__main__":
    test_file = open(sys.argv[1])
    tests = int(test_file.readline())
    output_file = open(sys.argv[2], 'w')
    s = Solution()

    for t in range(tests):
        n, q = [int(x) for x in test_file.readline().split(' ')]
        letters = test_file.readline().strip()
        questions = [[int(x) for x in test_file.readline().split(' ')] for _ in range(q)]

        ans = s.building_palindromes(n, q, letters, questions)
        output_file.write('Case #' + str(t+1) + ': ' + str(ans) + '\n')

    test_file.close()
    output_file.close()