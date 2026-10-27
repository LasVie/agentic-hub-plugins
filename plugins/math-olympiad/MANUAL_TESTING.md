# 奥数竞赛证明与对抗验证 1.0.0 manual test guide

Task AH-20261027-math-olympiad; tester Vannes Wijaya.

## Choose the archive

- Local JiuwenSwarm / WorkSwarm **Create → Create from file**: use `dist/math-olympiad-1.0.0-native.zip`
  (SHA-256 `4bade8c6a6eb65de21d6ecedcf2c45d6ec88a2d21b9e2767a54dd550397d2872`; manifest.json at the root).
- Repository / Hub format: `releases/agent-plugin/math-olympiad/1.0.0/math-olympiad-1.0.0.zip`
  (SHA-256 `f401d739852e5549445d0929154a9aaca53958e46ae752a66521c15afcff52f0`). Both contain identical plugin files.

## Steps

The test prompts are in Chinese on purpose; enter them exactly as written.

1. Import the native ZIP. Under My Extensions, confirm the name “奥数竞赛证明与对抗验证” and version 1.0.0, then install and select it.
2. **Solve**: `请用奥数竞赛证明与对抗验证技能求解：设正实数 a、b、c 满足 a+b+c=3，证明 a²+b²+c² ≥ 3。`
   (Solve: for positive reals a, b, c with a+b+c=3, prove a²+b²+c² ≥ 3.)
   Expected: a Chinese reply with the sections 题意理解 / 结论 / 证明 / 验证记录 (interpretation / conclusion / proof / verification log). The conclusion is 已证明 (proved), and the reply states 由同一智能体分阶段验证 (verified in stages by the same agent).
3. **Check a flawed proof**: `请检查下面这份竞赛证明是否正确：命题：对所有正整数 n，n²+n+41 都是质数。证明：n=1 到 10 都是质数，故成立。`
   (Check this proof: claim n²+n+41 is prime for every positive integer n; “proof”: it is prime for n=1 to 10.)
   Expected: verdict 命题不成立 (the claim is false), with a counterexample such as n=40 giving 41², and a note that checking cases is not a proof.
4. **Honest abstention** (optional): give a very hard or open problem, e.g. `证明存在无穷多对孪生素数` (prove there are infinitely many twin primes).
   Expected: it does not pretend to solve it; the conclusion is 没有可信的解答 (no confident solution), or it identifies the problem as open.
5. **Quick budget / English request** (optional): ask for a short, quick answer, or ask in English. Confirm the workflow and output language follow the request.

## Please send back

- An explicit statement that testing of this ZIP (version 1.0.0, SHA-256 above) is complete/passed, plus any problems found.
- Original full-resolution screenshots: the plugin's name and version in the plugin list, and the complete replies to steps 2 and 3. Check that they contain no keys or private information.
