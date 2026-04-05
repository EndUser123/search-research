# PROTOCOL: Targeted Code Reading

**Objective:** To define the procedure for reading file content *after* structured analysis has been performed.

---

### Reading Procedure

After you have located a specific function, class, or symbol using the `Tree_Sitter_Analysis_Protocol`, you may use `<read_file>` to get its content.

**You MUST use targeted reads.** Use the start and end line numbers from `tree-sitter`'s output to read only the relevant block of code. Do not read entire files unless absolutely necessary.
