#!/bin/zsh
# Prompt for the Databento API key (hidden input) and store it in ./.env (mode 600, gitignored).
# The key is never echoed, never written to shell history, never passed on a command line.
umask 077
f="${0:A:h}/.env"
read -rs "k?Databento API key (input hidden): "
print
if [[ ! "$k" =~ ^db-[A-Za-z0-9]{29}$ ]]; then
  print "Not saved: expected exactly one key (db- + 29 letters/digits); paste once."; unset k; exit 1
fi
printf '# Databento historical API key. Local only; gitignored; never print.\nDATABENTO_API_KEY=%s\n' "$k" > "$f"
chmod 600 "$f"
unset k
print "saved to $f (mode 600). You can close this tab."
