"use strict";
const demos = {
  inspect: {title:"foundry / inspect", note:"Bounded inspection. No repository commands executed.", code:`$ foundry.py inspect --root ./project

{
  "status": "completed",
  "data": {
    "native_manifests": [
      { "path": "Cargo.toml", "ecosystem": "rust" }
    ],
    "truncated": false,
    "instructions_present": true
  }
}`},
  contract: {title:".agent / repository.json", note:"Your real commands. Explicit arguments. No guessed test runner.", code:`{
  "schema_version": "1.0.0",
  "name": "my-rust-library",
  "commands": [{
    "id": "test",
    "argv": ["cargo", "test", "--locked"],
    "cwd": ".",
    "purpose": "Run this library's tests"
  }],
  "verification": ["test"]
}`},
  skill: {title:"skills / your-skill", note:"A focused procedure. Supporting resources only when useful.", code:`your-skill/
├── SKILL.md
│   ├── Precise task description
│   ├── Inputs and applicability
│   ├── The actual procedure
│   └── Completion and recovery
├── references/    optional knowledge
├── scripts/       deterministic helpers
└── assets/        output schemas

Load the entry point first.
Read only the relevant references.`}
};
const tabs = [...document.querySelectorAll("[data-demo]")];
function activateDemo(tab) {
  const demo = demos[tab.dataset.demo];
  for (const item of tabs) {
    const active = item === tab;
    item.classList.toggle("active", active);
    item.setAttribute("aria-selected", String(active));
    item.tabIndex = active ? 0 : -1;
  }
  document.getElementById("demo-panel").setAttribute("aria-labelledby", tab.id);
  document.getElementById("demo-title").textContent = demo.title;
  document.getElementById("demo-code").textContent = demo.code;
  const note = document.getElementById("demo-note");
  note.replaceChildren();
  const dot = document.createElement("span"); dot.className = "status-dot";
  note.append(dot, document.createTextNode(demo.note));
}
tabs.forEach((tab,index) => {
  tab.addEventListener("click", () => activateDemo(tab));
  tab.addEventListener("keydown", event => {
    let next;
    if (event.key === "ArrowDown") next = (index+1)%tabs.length;
    if (event.key === "ArrowUp") next = (index-1+tabs.length)%tabs.length;
    if (event.key === "Home") next = 0;
    if (event.key === "End") next = tabs.length-1;
    if (next !== undefined) {event.preventDefault();activateDemo(tabs[next]);tabs[next].focus();}
  });
});
const hostButtons = [...document.querySelectorAll("[data-host]")];
const hosts = {
  codex: {invoke:"Use $agent-foundry to inspect this repository.", note:"Installs into your Codex skills directory. Available on your next turn; refresh the session if needed."},
  claude: {invoke:"/agent-foundry Inspect this repository.", note:"Targets ~/.claude/skills. Check discovery in your Claude Code session; host behavior differs."},
  agents: {invoke:"Use the agent-foundry skill to inspect this repository.", note:"Targets ~/.agents/skills. Choose this only when your host discovers that shared location."}
};
hostButtons.forEach(button => button.addEventListener("click", () => {
  const host = button.dataset.host;
  hostButtons.forEach(item => {item.classList.toggle("active", item===button);item.setAttribute("aria-pressed",String(item===button));});
  document.getElementById("install-code").textContent = `git clone https://github.com/AleksanderAmid/agent-foundry.git\ncd agent-foundry\npython skills/agent-foundry/scripts/foundry.py install --host ${host} --apply`;
  document.getElementById("invoke-code").textContent = hosts[host].invoke;
  document.getElementById("install-note").textContent = hosts[host].note;
  document.getElementById("copy-install").textContent = "Copy commands ⧉";
}));
document.getElementById("copy-install").addEventListener("click", async event => {
  const button = event.currentTarget;
  const status = document.getElementById("copy-status");
  try {
    await navigator.clipboard.writeText(document.getElementById("install-code").textContent);
    button.textContent = "Copied ✓";
    status.textContent = "Installation commands copied to your clipboard.";
  } catch {
    status.textContent = "Clipboard unavailable. Select and copy the visible commands.";
    document.getElementById("copy-install").textContent = "Select text to copy";
  }
});
