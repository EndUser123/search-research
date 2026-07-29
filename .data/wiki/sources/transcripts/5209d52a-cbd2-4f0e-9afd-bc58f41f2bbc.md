---
source_id: "5209d52a-cbd2-4f0e-9afd-bc58f41f2bbc"
title: "So we're doing loops now"
notebook_id: 06717c64-8597-4a59-a5e3-871e841585af
url: null
type: youtube
exported: 2026-07-27
---

# So we're doing loops now
so what is a loop so what is a loop so what is a loop you know the workflow you prompt your agent your agent writes the code for you you wait for it to be done and then you prompt it again loops are what change this you're giving your agent a goal and the agent will not only start itself but will continue until that goal is met so a loop really only needs two things it needs some kind of trigger and some kind of goal the goal must be verifiable in some way it can be done with deterministic goals so when all the tests pass or non-deterministic goals we have the trigger and we have the goal let me show you what it actually looks like in practice in cursor there's this tab called automations click that and you can set up a new automation i've already set one up and i've said every time i open up a pr in astrohub i want this automation to trigger then i give the agent the instruction to review the pr and look for any potential issues fix them automatically and commit back to the same pr make sure all tests pass and if they don't fix them make sure all other ci is green and that's it
