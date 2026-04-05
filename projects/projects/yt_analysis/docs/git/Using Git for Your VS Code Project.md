<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" class="logo" width="120"/>

## Using Git for Your VS Code Project

Visual Studio Code (VS Code) has built-in Git integration, making it easy to manage version control for your project directly from the editor. Here’s a step-by-step guide to get you started:

**1. Prerequisites**

- **Install Git:** Make sure Git is installed on your system. You can check by opening the VS Code terminal and running `git --version`. If it's not installed, download it from the official site[^3][^1][^5].
- **Configure Git:** Set your username and email in Git (these appear in your commit history). In the terminal, run:

```
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

This only needs to be done once per machine[^3][^5].

**2. Initialize or Open a Git Repository**

- **For a new project:** Open your project folder in VS Code. Go to the Source Control view (icon on the Activity Bar or `Ctrl+Shift+G`). Click "Initialize Repository" to create a new Git repo in your folder. This is equivalent to running `git init` in the terminal[^1][^3].
- **For an existing repository:** If your folder already contains a `.git` directory, VS Code will automatically recognize it and enable Git features[^6].

**3. Basic Git Workflow in VS Code**

- **Stage Changes:** In the Source Control view, you’ll see a list of changed files. Click the "+" icon next to files to stage them, or use the "Stage All Changes" button[^1][^5].
- **Commit Changes:** Enter a commit message in the input box at the top, then click the checkmark icon to commit staged changes[^1][^5].
- **View History:** You can view commit history and diffs directly in VS Code. Click on files to see what’s changed, or use extensions like GitLens for more advanced history and blame features[^3].
- **Branches:** Switch or create branches by clicking the branch name in the lower left status bar. You can also create, delete, and merge branches from the Source Control view[^1][^5].

**4. Connecting to a Remote Repository (e.g., GitHub)**

- **Clone a repository:** Use `Ctrl+Shift+P` to open the Command Palette, then type `Git: Clone`. Paste the repository URL, choose a folder, and VS Code will clone it for you[^6][^5].
- **Add a remote:** If you initialized a local repo and want to push to GitHub, create a new repo on GitHub, copy its URL, then run:

```
git remote add origin <repository-URL>
git push -u origin main
```

You can do this from the terminal or use the VS Code Source Control UI[^4][^5].
- **Push and Pull:** Use the "Push" and "Pull" buttons in the Source Control view to sync changes with the remote repository[^1][^5].

**5. Using Extensions for Enhanced Workflow**

- **GitHub Pull Requests and Issues Extension:** Install this extension for advanced GitHub integration, including PR management and issue tracking from within VS Code[^7].
- **GitLens:** Adds powerful Git features like advanced blame, history, and visualization tools[^3].

**6. Tips and Best Practices**

- Commit frequently with clear messages.
- Pull before you start working to avoid conflicts.
- Use branches for new features or bug fixes.
- Resolve merge conflicts using VS Code’s built-in merge editor[^1].

**Summary Table: Key Git Actions in VS Code**


| Action | How to Do It in VS Code |
| :-- | :-- |
| Initialize repository | Source Control view → Initialize |
| Stage changes | Source Control view → "+" icon |
| Commit changes | Enter message → Checkmark icon |
| Push/Pull | Source Control view → Push/Pull |
| Switch branches | Click branch name in status bar |
| Clone repo | Ctrl+Shift+P → Git: Clone |

VS Code’s Git integration covers most common workflows, and you can always drop to the integrated terminal for advanced Git commands[^1][^3][^4].

<div style="text-align: center">⁂</div>

[^1]: https://code.visualstudio.com/docs/sourcecontrol/overview

[^2]: https://www.youtube.com/watch?v=i_23KUAEtUM

[^3]: https://www.gitkraken.com/blog/vs-code-git

[^4]: https://www.reddit.com/r/webdev/comments/1ciyc6j/using_github_and_vs_code/

[^5]: https://www.youtube.com/watch?v=EjHJNjLxE_U

[^6]: https://learn.microsoft.com/en-us/azure/developer/javascript/how-to/with-visual-studio-code/clone-github-repository

[^7]: https://code.visualstudio.com/docs/sourcecontrol/github

[^8]: https://git-scm.com/book/en/v2/Appendix-A:-Git-in-Other-Environments-Git-in-Visual-Studio-Code
