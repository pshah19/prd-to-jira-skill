Output assets/demo.gif

Set Shell "bash"
Set FontSize 15
Set Width 1200
Set Height 680
Set Theme "Dracula"
Set Padding 20
Set TypingSpeed 45ms
Set PlaybackSpeed 1.0

Type "cat examples/sample-prd.md | head -18"
Enter
Sleep 2500ms

Type "python3 skill/scripts/render_outputs.py examples/output/epics.json --outdir /tmp/prd-to-jira-demo"
Enter
Sleep 1500ms

Type "ls /tmp/prd-to-jira-demo"
Enter
Sleep 1500ms

Type "head -28 /tmp/prd-to-jira-demo/backlog.md"
Enter
Sleep 4000ms
