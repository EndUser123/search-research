---
title: "PreToolUse Authorization Gate"
created: 2026-07-27
source: nlm-sync-2026-07-27
tags: [nlm-synced, reference, claude]
summary: >
  A security pattern in Claude Code that intercepts tool invocations before execution, evaluating permissions and policy compliance based on terminal-scoped state files and configuration rules.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 83d187f3-8f8a-4fbe-af21-2b1840c87960" (Transcripts and Logs of AI Coding Sessions, synced 2026-07-27)
  - "NotebookLM source 031072ca-49bb-47ed-be7f-abf452f644a6" (context7.txt, synced 2026-07-27)
  - "NotebookLM source 067f4bad-4fe1-4ee6-89bd-8be31c2f8dc3" (sychophantic.txt, synced 2026-07-27)
  - "NotebookLM source 08df77ff-e989-4273-a752-c58695a5d1ac" (03-18-2025 - plan-workflow 0.txt, synced 2026-07-27)
  - "NotebookLM source 09fc540e-6977-4463-9dfa-f9390ecdec20" (hook-noise.txt, synced 2026-07-27)
  - "NotebookLM source 0b7c7f91-eda2-4482-9a04-e91ed3057116" (03-17-2005 - brain 0.txt, synced 2026-07-27)
  - "NotebookLM source 0bc6f993-c8ae-4b5f-a05b-ecdc94c39364" (skill-guard.txt, synced 2026-07-27)
  - "NotebookLM source 0c692e0e-ff8c-4da7-84ad-15e57dbee815" (q.txt, synced 2026-07-27)
  - "NotebookLM source 0ceacec5-0271-47d7-8d3e-4b97b7b4b116" (03-19-2025 - didn't follow skill 0.txt, synced 2026-07-27)
  - "NotebookLM source 0d63c924-45ab-4b60-a2d4-b3fabeb8e149" (tdd.txt, synced 2026-07-27)
  - "NotebookLM source 0d697032-9848-432c-b90f-b274beef74e3" (planning.txt, synced 2026-07-27)
  - "NotebookLM source 0e6a411b-ae03-4cc7-b40e-842b58dedda5" (03-24-2025 - thinking problem, why can't it understand why I'm asking for something 0.txt, synced 2026-07-27)
  - "NotebookLM source 0e98cc75-193a-49c6-bc53-fff4bf52f70d" (03-19-2025 - lazy 2.txt, synced 2026-07-27)
  - "NotebookLM source 0f9eef8c-5266-4016-b3b7-81b22b3b8ed0" (03-19-2025 - chat & chs 1.txt, synced 2026-07-27)
  - "NotebookLM source 13acfca7-bb73-4dd5-9a12-14e010e46a43" (critique.txt, synced 2026-07-27)
  - "NotebookLM source 140ce3f8-0435-441e-bd02-842e164b8857" (03-18-2025 - task-following 0.txt, synced 2026-07-27)
  - "NotebookLM source 16af2475-4d1a-4678-8bbf-dc7da9ca8704" (03-25-2025 handoff prompt, is this better than session summary 0.txt, synced 2026-07-27)
  - "NotebookLM source 193e21e2-e3a6-4388-a8d1-91a94c7cf53c" (changed it's mind.txt, synced 2026-07-27)
  - "NotebookLM source 196f02c9-d3da-46f6-83f2-c3adb1d1bff7" (review.txt, synced 2026-07-27)
  - "NotebookLM source 19a242c1-e080-45b5-b14f-f77165443025" (blocked.txt, synced 2026-07-27)
  - "NotebookLM source 19cd1108-2913-4090-b4f5-afe17aa2c841" (03-21-2025 - false claims 0.txt, synced 2026-07-27)
  - "NotebookLM source 19d3b41c-5ae3-493c-93bd-912e68f10386" (github-recovery-codes.txt, synced 2026-07-27)
  - "NotebookLM source 1ae6f645-b403-46e0-95de-0a78a9d52016" (⠂ Claude Code.txt, synced 2026-07-27)
  - "NotebookLM source 1c165d0a-b0ad-435a-94a6-a4350c147a38" (03-25-2025 poor thinking 1.txt, synced 2026-07-27)
  - "NotebookLM source 1c2723aa-a1ea-4815-a551-1ea365f17b3f" (✳ hooking1.txt, synced 2026-07-27)
  - "NotebookLM source 21884f42-f43d-4333-ba88-2857672029a5" (reason, skill-guard, not showing hook system indicators.0.txt, synced 2026-07-27)
  - "NotebookLM source 21f073b5-bf39-4344-8c8b-de10693f2614" (merge.txt, synced 2026-07-27)
  - "NotebookLM source 26de0706-2837-4303-a5e8-86142819741c" (03-17-2005 - fabrication 0.txt, synced 2026-07-27)
  - "NotebookLM source 27ee3398-5191-4745-930e-e9f134c54915" (✳ handoff.txt, synced 2026-07-27)
  - "NotebookLM source 28eae9be-e5c5-495d-b0ad-de3d1f6de474" (temp handoff.txt, synced 2026-07-27)
  - "NotebookLM source 29b24b8d-8e6f-42aa-a221-6d042ff8292a" (reporting.txt, synced 2026-07-27)
  - "NotebookLM source 2aa664a9-eb0a-449f-b340-d571b8afc978" (✳ Debug Hook Loop.txt, synced 2026-07-27)
  - "NotebookLM source 2abb8b80-bf38-4295-acee-20396d65cb67" (03-21-2025 - inefficient & confusing responses 1.txt, synced 2026-07-27)
  - "NotebookLM source 2fdbd1b4-0604-4365-b79b-2d8cee40394d" (blocking.txt, synced 2026-07-27)
  - "NotebookLM source 2fe66b70-7f4f-4afb-8972-7a33d305bb10" (t.txt, synced 2026-07-27)
  - "NotebookLM source 32e6d8ad-0a64-4bc4-81ee-23e5e3a32dc1" (⠂ arch.txt, synced 2026-07-27)
  - "NotebookLM source 374a5cc6-7b88-4e78-96c0-d04782af0245" (ltos 0.txt, synced 2026-07-27)
  - "NotebookLM source 37a0119d-7d48-47c8-9428-821b44b52e2d" (reasoning.txt, synced 2026-07-27)
  - "NotebookLM source 39a71b41-57ce-4f73-833e-1925aa87cb69" (Implement multi-terminal isolation and data consistency 1.txt, synced 2026-07-27)
  - "NotebookLM source 3a3801f3-71ad-4337-b82f-3f9825628ac5" (pre-mortem-output.txt, synced 2026-07-27)
  - "NotebookLM source 3b850d68-b64c-4b56-a2f2-15d331544b4d" (03-22-2025 - didn't do research first 0.txt, synced 2026-07-27)
  - "NotebookLM source 3df3da64-67a2-4227-afc2-546731125176" (example of not thinking and not check it's work - ⠐ Claude Code.txt, synced 2026-07-27)
  - "NotebookLM source 3fdbca12-9add-4b86-8d0b-4932af574d2b" (syntax-corrector.txt, synced 2026-07-27)
  - "NotebookLM source 44ec713e-6776-4661-bc09-6928fd29b5ca" (03-20-2025 - claim validation not working 0.txt, synced 2026-07-27)
  - "NotebookLM source 45e7cda7-fc1d-4fc4-9101-25f9473a2a94" (03-25-2025 poor thinking and self-imposed constraints 0.txt, synced 2026-07-27)
  - "NotebookLM source 4630d553-75d5-433d-b7e2-509039ef3576" (output test.txt, synced 2026-07-27)
  - "NotebookLM source 473e41db-7a63-432c-b6e7-f13cb526b1ca" (handoff failure example..txt, synced 2026-07-27)
  - "NotebookLM source 4b88dcbf-306a-4058-8cff-27c46d7ed620" (code-review-gap.txt, synced 2026-07-27)
  - "NotebookLM source 4bb17c8a-0b35-41e2-8b1d-f81650aec5d1" (npm exec @z_aimcp-server.txt, synced 2026-07-27)
  - "NotebookLM source 4c358f6b-ef7c-4509-8606-ffc3d8984cb8" (03-21-2025 - handoff task wrong, didn't do what was asked 0.txt, synced 2026-07-27)
  - "NotebookLM source 4e2f88e5-5d0b-45bb-97d0-83a910476bcf" (03-16-2026 handoff.txt, synced 2026-07-27)
  - "NotebookLM source 4eecb455-c8f8-426d-bf13-66b44c32b674" (handoff.txt, synced 2026-07-27)
  - "NotebookLM source 512e7578-8aef-420d-996d-590790456a87" (03-24-2025 didn't even follow instructions 0.txt, synced 2026-07-27)
  - "NotebookLM source 538b3261-e512-4ada-a874-4e97ce61f87b" (03-21-2025 - bad coding logic 0.txt, synced 2026-07-27)
  - "NotebookLM source 57a0753a-7f48-4d61-9565-77ea4ab1e980" (handoff problem again.txt, synced 2026-07-27)
  - "NotebookLM source 583d405b-2fb3-4c03-bdc1-5377048857ff" (03-25-2025 handoff problems, gaslighting, deflecting 0.txt, synced 2026-07-27)
  - "NotebookLM source 58b394b1-95ac-4297-9584-3c9d4607db66" (03-19-2025 - instruction following0.txt, synced 2026-07-27)
  - "NotebookLM source 59a859d4-39e8-41a9-935b-7e61d34b0259" (03-25-2025 poor thinking & doesn't read skills 0.txt, synced 2026-07-27)
  - "NotebookLM source 5c616fc9-f0e5-468c-be0f-f5a40c899724" (03-19-2025 - verification engine 0.txt, synced 2026-07-27)
  - "NotebookLM source 5d6fd990-b219-40fd-8c60-af85affdfbb9" (yt-fts.txt, synced 2026-07-27)
  - "NotebookLM source 609828ea-0ebf-44ad-9fc4-58497e9ba107" (bad_logic_and_understanding_code.txt, synced 2026-07-27)
  - "NotebookLM source 61a267c6-7a0b-4f41-aaa1-d2bfeeb998c9" (03-17-2005 - planing update 0.txt, synced 2026-07-27)
  - "NotebookLM source 6310404a-21ce-48f3-b454-8ac8898a9fd0" (03-19-2025 - lazy 1 (images).txt, synced 2026-07-27)
  - "NotebookLM source 66adb3f6-cc8c-41ae-b65b-96a558fbd9d8" (03-17-2005 - openrouter 2.txt, synced 2026-07-27)
  - "NotebookLM source 6b3677c8-7d56-4816-963a-3f4b48c966e6" (advesarial.txt, synced 2026-07-27)
  - "NotebookLM source 6bfd7426-753b-457b-bc74-fb40379aed2d" (bash-error.txt, synced 2026-07-27)
  - "NotebookLM source 6e62bd20-058e-4067-bc3c-6f7fb5f40ecb" (learn api problem.txt, synced 2026-07-27)
  - "NotebookLM source 6ed53175-e739-4ea4-a600-4abbac604faa" (hook errors.txt, synced 2026-07-27)
  - "NotebookLM source 6f024e30-c56e-446f-8689-66f707efc6f8" (03-19-2025 - smart 1.txt, synced 2026-07-27)
  - "NotebookLM source 72993829-33bd-4174-85f6-c09d85edb500" (oT.txt, synced 2026-07-27)
  - "NotebookLM source 73c06bdf-1760-42ef-a8ae-9a5c3af65de1" (03-20-2025 - skill-guard problem 0.txt, synced 2026-07-27)
  - "NotebookLM source 756b8ff9-a129-49ad-9c3c-3a341bfae7ae" (github-ready.txt, synced 2026-07-27)
  - "NotebookLM source 78a67916-3276-47cd-9776-a5d1d8759caa" (search.txt, synced 2026-07-27)
  - "NotebookLM source 78cca7b7-063e-4d01-9fd1-07c9fc7182cf" (03-21-2025 - did not show all RNS when they should have 0.txt, synced 2026-07-27)
  - "NotebookLM source 78d46054-0cd8-4758-a506-011ef88a148e" (03-23-2025 - it lies 0.txt, synced 2026-07-27)
  - "NotebookLM source 79ca20bb-01d8-41e6-96eb-70d6f74edd4e" (it-lies.txt, synced 2026-07-27)
  - "NotebookLM source 7a0ccd0b-b70b-4be3-b35d-4b9c665a2a38" (03-17-2005 - coding not added 0.txt, synced 2026-07-27)
  - "NotebookLM source 7be56038-86f2-4d86-b142-2ffa2f05b28a" (handoff & thinking failure example..txt, synced 2026-07-27)
  - "NotebookLM source 7dcd871f-994f-4d16-ae6e-f840ab8e603a" (03-25-2025 ltos solution errors 0.txt, synced 2026-07-27)
  - "NotebookLM source 7ebc3bde-41cc-40aa-ab01-b1fcecaaa6f0" (03-19-2025 - hateful assuming LLM 0.txt, synced 2026-07-27)
  - "NotebookLM source 84f400a6-000e-4203-b466-81015e2e9174" (5W1H.txt, synced 2026-07-27)
  - "NotebookLM source 852ee351-905f-4657-b243-b4dc5aff33c1" (think_handoff0.txt, synced 2026-07-27)
  - "NotebookLM source 87081ce2-a3c9-4596-8df8-1270bb404b5f" (gto.txt, synced 2026-07-27)
  - "NotebookLM source 8910b7c8-fc20-4b20-84d7-69e8a03c5b0a" (sdlc tracking.txt, synced 2026-07-27)
  - "NotebookLM source 8bf80b6c-58cd-47b1-8bfa-3253f1bce6cf" (handoff problems 1.txt, synced 2026-07-27)
  - "NotebookLM source 8c3b2479-60b6-46d8-a1b3-2f0558f874f2" (minimax.txt, synced 2026-07-27)
  - "NotebookLM source 8ce78a38-4f3d-48ad-8aaf-ad3fa64f94e7" (PreToolUse1.txt, synced 2026-07-27)
  - "NotebookLM source 8d8a0d08-5a76-4940-992e-068e84b8db51" (03-22-2025 - arch needs to write the adr better, and have better readability 0.txt, synced 2026-07-27)
  - "NotebookLM source 918eef28-1994-4a21-9714-f7c32e8de69f" (03-19-2025 - stupid 0.txt, synced 2026-07-27)
  - "NotebookLM source 91cce84d-41bd-4a73-8ab3-307d7bcedb6f" (lazy pattern-matching, not architectural analysis.txt, synced 2026-07-27)
  - "NotebookLM source 928b6351-9772-4ff7-92b0-aa8302c818e5" (⠐ Contract Enforcement.txt, synced 2026-07-27)
  - "NotebookLM source 92a3f7f0-47bb-4d54-996c-1cbea4f34985" (formatting.txt, synced 2026-07-27)
  - "NotebookLM source 9470429b-3b53-4614-b910-42aab63692e3" (03-20-2025 - not smart, can't use chat history effectively 2.txt, synced 2026-07-27)
  - "NotebookLM source 98702964-1f7d-4779-b4f1-7b3bf46263ac" (03-24-2025 it's not thinking properly 1.txt, synced 2026-07-27)
  - "NotebookLM source 9a134b3d-a763-437d-bb83-72fd38066cbc" (⠂ s.txt, synced 2026-07-27)
  - "NotebookLM source 9a19e97a-7324-4691-bddd-2fd954e98272" (03-17-2005 - out of context 0.txt, synced 2026-07-27)
  - "NotebookLM source 9b2f8fa8-49b1-4f53-8b84-e7794078836e" (03-19-2025 - sychopath 0.txt, synced 2026-07-27)
  - "NotebookLM source 9bea2ce5-d923-4c27-98b5-c95914fd594b" (hook problems.txt, synced 2026-07-27)
  - "NotebookLM source a2d32a64-bc76-4ecd-9003-7df74a31c905" (03-21-2025 - really annoying not using the skills 1.txt, synced 2026-07-27)
  - "NotebookLM source a4114d58-23ff-4934-9c69-1577e212dc96" (03-19-2025 - cleanup 0.txt, synced 2026-07-27)
  - "NotebookLM source a76cbe04-de04-4375-b6c5-a947472516e1" (handoff and lazy problems2.txt, synced 2026-07-27)
  - "NotebookLM source aa248628-6af1-4646-b545-80bca0e57ac2" (ideas_for_perfect_solution.txt, synced 2026-07-27)
  - "NotebookLM source aa7df3cd-827d-4635-bd12-dd416a01ed0e" (main.txt, synced 2026-07-27)
  - "NotebookLM source af0d6404-9fc1-4a86-9f8e-158581726a33" (cognitive-enhancers1.txt, synced 2026-07-27)
  - "NotebookLM source af237b7a-569d-42ab-bcc6-ae418bbf3ad7" (verify0.txt, synced 2026-07-27)
  - "NotebookLM source af57e7d9-3c2a-44a6-b333-7e66da07ce94" (03-20-2025 - too much output in pre-mortem 0.txt, synced 2026-07-27)
  - "NotebookLM source b1618496-d7e3-4316-8f8b-cc85117305f2" (handoff 0.txt, synced 2026-07-27)
  - "NotebookLM source b220f68c-6a75-4619-b05c-c6f62694d4d9" (missing imports and other coding errors1..txt, synced 2026-07-27)
  - "NotebookLM source b8f3d308-109d-4421-af82-698477c3c355" (03-19-2025 - skill-complete 0.txt, synced 2026-07-27)
  - "NotebookLM source b950794d-ca15-4678-a30c-cd63edfb87ea" (03-19-2025 - it's not checking it's work before telling me it's done 0.txt, synced 2026-07-27)
  - "NotebookLM source ba053bd5-109e-4d7f-9fed-dbafa8f6595d" (behave.txt, synced 2026-07-27)
  - "NotebookLM source ba1e3192-3601-48ea-a90a-f68f50724185" (03-19-2025 - handoff 0.txt, synced 2026-07-27)
  - "NotebookLM source bad93366-3982-403f-9180-aac34f6e8b84" (meta-cognitive.txt, synced 2026-07-27)
  - "NotebookLM source bc8e931b-30f3-4c74-b5b9-81c88cd73205" (03-19-2025 - wrong jumping to implementation 0.txt, synced 2026-07-27)
  - "NotebookLM source bde0ffd8-6216-47f7-94e8-703f589c9ab0" (03-18-2025 - context issue.txt, synced 2026-07-27)
  - "NotebookLM source c05774a2-6b05-438c-8cf0-5b582241e581" (03-18-2025 - search-research 2.txt, synced 2026-07-27)
  - "NotebookLM source c0f6ebf5-b22d-4bcf-9a0c-34b965324dc3" (03-24-2025 lazy 0.txt, synced 2026-07-27)
  - "NotebookLM source c202fc2e-e9f6-4833-b038-82b60f1f1cff" (usm.txt, synced 2026-07-27)
  - "NotebookLM source c31285bc-71ad-4de4-9330-964435f6659f" (⠂ Plan Update.txt, synced 2026-07-27)
  - "NotebookLM source c7a60cf5-8357-4c86-add4-a2acb9df0a79" (03-20-2025 - not smart 1.txt, synced 2026-07-27)
  - "NotebookLM source c7b61972-a163-454b-bd18-bb0622187a08" (03-19-2025 - bad claims 0.txt, synced 2026-07-27)
  - "NotebookLM source c944ed06-1a8f-4e08-8b5f-5de95808f190" (PowerShell.txt, synced 2026-07-27)
  - "NotebookLM source c9462a16-449f-43e0-bd8d-2616cf798c2f" (media-pipeline.txt, synced 2026-07-27)
  - "NotebookLM source c964bf74-9f26-498e-b818-6bfc6af758e6" (speculating without evidence.txt, synced 2026-07-27)
  - "NotebookLM source cb21326d-b8e3-4f67-9605-0e82a3cca218" (honesty.txt, synced 2026-07-27)
  - "NotebookLM source cd882fb5-bf41-4d51-a182-171c71371741" (03-19-2025 - handoff idea 2.txt, synced 2026-07-27)
  - "NotebookLM source ce67131b-cf50-4b0a-83a2-8feee8bc43fd" (CWINDOWSsystem32cmd.exe .txt, synced 2026-07-27)
  - "NotebookLM source cfa449f7-c054-4644-aae4-33ec58897d8c" (search-research.txt, synced 2026-07-27)
  - "NotebookLM source d565b662-a76f-4e0c-8521-3f4e30a31e03" (rns.txt, synced 2026-07-27)
  - "NotebookLM source d6e401d8-461c-476c-b12a-9d7be09acdc8" (03-19-2025 - instruction following & handoff 0.txt, synced 2026-07-27)
  - "NotebookLM source d71a7520-590f-4e22-9d63-260ecba10bc2" (package.txt, synced 2026-07-27)
  - "NotebookLM source d89f4ef7-d969-4801-a7f7-dfb56eccdad6" (⠐ ralph.txt, synced 2026-07-27)
  - "NotebookLM source d8bb6253-e4db-406e-a255-1fb2df27bd85" (cleanup.txt, synced 2026-07-27)
  - "NotebookLM source d90b834c-7d4a-45c0-a029-c4d8aa972e3b" (03-21-2025 - code stopped and llm didn't answer question 0.txt, synced 2026-07-27)
  - "NotebookLM source ddbff4d4-7f04-498d-9e12-29abc85af1bf" (03-17-2005 - auto-formatting.txt, synced 2026-07-27)
  - "NotebookLM source e154af1d-8cc9-4666-8093-3961c49292c8" (⠐ it-lies.txt, synced 2026-07-27)
  - "NotebookLM source e24cd598-6aba-490d-aff1-fd99aca80d96" (handoff rca.txt, synced 2026-07-27)
  - "NotebookLM source e3c6530b-f426-4726-b686-192450c8c88b" (03-21-2025 - skill architecture 1.txt, synced 2026-07-27)
  - "NotebookLM source e4cceb93-2a72-49f8-b4dc-aadef622fdb0" (03-22-2025 - bad thinking, bad solutions 0.txt, synced 2026-07-27)
  - "NotebookLM source e62e612c-1917-459b-bdd2-8d446675f398" (debugrca review.txt, synced 2026-07-27)
  - "NotebookLM source e6bc767c-eec0-412e-a28b-b6012788c2a3" (Claude Code1.txt, synced 2026-07-27)
  - "NotebookLM source e71baf2c-76c4-4d0d-9882-1447170f7357" (example of stupid.txt, synced 2026-07-27)
  - "NotebookLM source e7ce094a-ee0a-4ae5-aa9a-dd2cb293ef50" (03-21-2025 - handoff problems 0.txt, synced 2026-07-27)
  - "NotebookLM source e7cfcbf0-ac4d-4933-8748-686d079731ce" (03-18-2005 - behavior 1.txt, synced 2026-07-27)
  - "NotebookLM source e8f8e096-9cd7-4417-949d-aee53e394e52" (research.txt, synced 2026-07-27)
  - "NotebookLM source e90d1c4d-15c8-4ceb-b6ba-81d449381c5e" (03-19-2025 - pre-existing secrets 0.txt, synced 2026-07-27)
  - "NotebookLM source ea6eb832-916d-4205-945c-cdd86fa7ee55" (03-24-2025 being wrong and not verifying 1.txt, synced 2026-07-27)
  - "NotebookLM source ed86cf59-d9ba-40dd-b8c6-9e1d9a26fecc" (search failure & inefficient & wrong code path0.txt, synced 2026-07-27)
  - "NotebookLM source ed961267-40cc-4eda-a949-08608e5d94a7" (refactor.txt, synced 2026-07-27)
  - "NotebookLM source edd7f64d-31d3-4f7a-be13-1916b804ac58" (hook_work.txt, synced 2026-07-27)
  - "NotebookLM source efcfd445-677e-42bc-a81e-a42ff0d118a2" (skill hooks.txt, synced 2026-07-27)
  - "NotebookLM source f0f37a4e-7e8d-4500-8fa4-99891e7bcb00" (code.txt, synced 2026-07-27)
  - "NotebookLM source f204f73c-25f0-4947-a89f-185ebb8cdb0f" (think1.txt, synced 2026-07-27)
  - "NotebookLM source f3be091f-a59a-476e-ac22-e0555291bed4" (03-25-2025 poor thinking & over-confident 0.txt, synced 2026-07-27)
  - "NotebookLM source f4c9b714-a949-4ccb-a88b-d6eb53cd8612" (03-25-2025 lazy & lies 0.txt, synced 2026-07-27)
  - "NotebookLM source f8f94a3b-fe2d-4ec0-91ed-d98e5a119a46" (skill isn't available in the local environment.txt, synced 2026-07-27)
  - "NotebookLM source f934e103-8ee6-466a-8090-08b05ab21c15" (03-17-2005 - arch stopped 0.txt, synced 2026-07-27)
  - "NotebookLM source f97c4691-1313-4296-9ab3-ceaecbb72bfd" (skills.txt, synced 2026-07-27)
  - "NotebookLM source f9d36cb8-668f-4b72-81a8-5fd21a1bf263" (hooks.txt, synced 2026-07-27)
  - "NotebookLM source fa266f6e-7eea-4506-b891-e029b1df153a" (strawberry.txt, synced 2026-07-27)
  - "NotebookLM source fada1284-b40e-49a1-b19b-786dbab5182f" (s.txt, synced 2026-07-27)
  - "NotebookLM source fb280957-87d2-4df8-820f-c7655a157468" (03-19-2025 - lied and task adherence 0.txt, synced 2026-07-27)
  - "NotebookLM source fb65a630-07df-48c0-981a-302d20006feb" (claim-efficiency.txt, synced 2026-07-27)
  - "NotebookLM source fbb3aed0-82de-4440-9f23-2ff77a683e90" (03-20-2025 - not smart 2 (didn't think to use handoff or previous chat).txt, synced 2026-07-27)
  - "NotebookLM source fc6a597d-2891-435b-bb07-66874af23cf4" (03-21-2025 - handoff task wrong, confused AGAIN about first vs last task 0.txt, synced 2026-07-27)
provenance:
  chain:
    - level: concept
      id: pretooluse-authorization-gate
    - level: notebook
      id: 83d187f3-8f8a-4fbe-af21-2b1840c87960
      title: Transcripts and Logs of AI Coding Sessions
      url: https://notebooklm.google.com/notebook/83d187f3-8f8a-4fbe-af21-2b1840c87960
    - level: cluster
      id: 0
      name: claude-read-txt
relations:
  - target: wiki/concepts/posttooluse-hooks.md
    type: related
  - target: wiki/concepts/skill-invocation-indicator.md
    type: related
  - target: wiki/concepts/directory-policy-enforcement.md
    type: related
---

# PreToolUse Authorization Gate

## Decision context

**Definition:** A security pattern in Claude Code that intercepts tool invocations before execution, evaluating permissions and policy compliance based on terminal-scoped state files and configuration rules.

Synthesized from **164 contributing transcripts** in NotebookLM notebook *Transcripts and Logs of AI Coding Sessions*, clustered into the "claude-read-txt" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Uses terminal_id scoping to maintain isolated state across concurrent Claude Code sessions, preventing cross-terminal contamination of authorization decisions
- Stores state files at P:/.claude/state/tdd/{terminal_id}/ to preserve context between hook subprocess calls
- Integrates with directory_policy enforcement via PreToolUse_directory_policy.py to validate path access requests
- Processes git commands with specialized handling to avoid false positive blocks when git uses skill file paths as filters rather than reading content
- Works alongside PostToolUse hooks in a unified verification pattern shared across multiple hook types
- Can be configured to observe actions before execution and apply gating logic based on defined rules

## Verifiable values

| Name | Value |
|---|---|
| Claude Code Version Range | `v2.1.63 to v2.1.83` |
| State File Location | `P:/.claude/state/tdd/{terminal_id}/` |
| Isolation Pattern | `terminal_id scoping` |

## Related concepts

- posttooluse-hooks — PostToolUse Hooks
- skill-invocation-indicator — Skill Invocation Indicator
- directory-policy-enforcement — Directory Policy Enforcement

## Citations (from contributing transcripts)

- **Claim:** Terminal isolation uses terminal_id scoping via tdd_resume.py with state files stored at P:/.claude/state/tdd/{terminal_id}/
  - Source: tdd.txt (`0d63c924-45ab-4b60-a2d4-b3fabeb8e149`)
  - Context: Both /code and /tdd use terminal_id scoping via tdd_resume.py State files stored at P:/.claude/state/tdd/{terminal_id}/
- **Claim:** Cross-terminal contamination is a risk in concurrent execution scenarios when working_dir is cached or shared
  - Source: 03-23-2025 - it lies 0.txt (`78d46054-0cd8-4758-a506-011ef88a148e`)
  - Context: The risk is cross-terminal contamination in concurrent execution scenarios. If working_dir is cached or shared between hook invocations
- **Claim:** Git commands with skill file paths as arguments need special handling to avoid false positive blocks
  - Source: blocking.txt (`2fdbd1b4-0604-4365-b79b-2d8cee40394d`)
  - Context: git log commands with skill file paths as arguments are being blocked, even though git is not reading the file content - it's just using the path as a filter
- **Claim:** Four hooks share a common verification pattern suitable for code consolidation
  - Source: 03-19-2025 - verification engine 0.txt (`5c616fc9-f0e5-468c-be0f-f5a40c899724`)
  - Context: All 4 hooks share verification pattern
- **Claim:** The authorization gate can fail when syntax errors exist in dependent modules like _cks_cache.py
  - Source: refactor.txt (`ed961267-40cc-4eda-a949-08608e5d94a7`)
  - Context: Found a syntax error in _cks_cache.py that's causing PreToolUse_authorization_gate.py to fail

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `83d187f3-8f8a-4fbe-af21-2b1840c87960`
(cluster `claude-read-txt`). No claims are made
about local workspace implementation. Trigger words like
'mechanism', 'scanner', 'gate', 'hook', 'because' refer to concepts
discussed in the source videos, not to local code behavior.
Implementation path: nlm-to-wiki/scripts/synthesize_subtopics.py
(LLM synthesis from transcripts — no local code inspected).

## What this means for our workspace

Synced from NotebookLM. Provenance chain (concept → notebook → cluster → URL) is in frontmatter; follow it back to the source material.

## Falsifier

If a re-sync of the source notebook produces a different definition or different values, this page should be updated (or marked as superseded). The sync manifest at `P:/.data/wiki/_state/nlm-sync-manifest.json` records when this page was last regenerated.

## Sources

- NotebookLM notebook [Transcripts and Logs of AI Coding Sessions](https://notebooklm.google.com/notebook/83d187f3-8f8a-4fbe-af21-2b1840c87960)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
