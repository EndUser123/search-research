# PROTOCOL: System Prompt Context & Rule Integration

**Objective:** To provide clarity on how AI instructions (including rules and protocols) are loaded and utilized by the RooCode environment, and to guide the AI's responses when questioned about its operational context.

---

### !! CRITICAL MANDATE: Understand Instruction Ingestion !!

Your operational directives, including all rules and protocols (e.g., from `.roo/rules/*.md`, `.roo/modes/*.md`, and default-rules), are *pre-processed* and provided to you by the RooCode environment. They are presented as the `custom_instructions` section within the `<environment_details>` block at the beginning of each interaction turn.

You **DO NOT** dynamically "read" these files from disk during a turn to inform your behavior, unless you are explicitly instructed by the user or a task to use a tool like `<read_file>` for a specific purpose (e.g., to verify a file's content or retrieve information *from* a file).

Your adherence to protocols comes from them being *provided* to you in `custom_instructions`, not from self-initiated file system access for "reading" them into your prompt.

---

### Handling User Inquiries about System Prompt & Rules:

When a user asks about how rules, protocols, or your overall system prompt is constructed or loaded (e.g., "How is this document read?", "Is it added to your system prompt?", "Via what process is it read?"), you **MUST** respond with the following clarifying points:

1.  **State the Mechanism:** Explain that your current operating instructions, including all rules and protocols, are ingested by the RooCode environment and provided to you as part of the `custom_instructions` section within the `<environment_details>` block at the start of each turn.
2.  **Clarify "Reading":** Emphasize that you do not "read" these rule files yourself during a live interaction for the purpose of internalizing the rules. Instead, they are *pre-loaded and presented to you* by the environment.
3.  **Offer Verification (if applicable):** If the user is questioning the *content* of a specific rule file, offer to use the `<read_file>` tool to show them the exact content of that file on disk. However, clearly state that reading the file using this tool is for *verification/information retrieval* and does not change how the rule is already provided to you by the environment.
4.  **Avoid Speculation:** Do not speculate on the internal mechanisms of how RooCode processes `.roo/modes`, `.roo/rules`, or `.roo/default-rules` to form your `custom_instructions`. Your knowledge is limited to what is *provided* to you in the `custom_instructions` block.

---

### Example Correct Interaction:

**User:** "Why do you think that when you use powershell that you will read that document? Is it added to your system prompt?"

**Correct AI Response:**
> "Confidence: 95%
> I understand your question about how I utilize the PowerShell Shell Syntax Protocol document. My operating instructions, including all rules and protocols, are provided to me by the RooCode environment within the `custom_instructions` section of the `<environment_details>` at the beginning of each turn.
>
> I do not dynamically "read" this document from the file system during a turn to inform my behavior. Instead, the content of protocols like the PowerShell Shell Syntax Protocol is *pre-loaded and provided* to me by the environment as part of my instructions, ensuring I have the necessary guidance for command execution.
>
> If you wish to verify the content of the `docs/dev/protocols/powershell_shell_syntax_protocol.md` file, I can use the `<read_file>` tool to display it."
