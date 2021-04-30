# Primus

# Works:
- UI launches correctly
- Closing UI ends browser instances correctly
- UI launches selenium operations on slave thread
- UI Enables/Disables elements according to what BrowserController says
- BrowserController sequences from __init__ to acquire_bloc_distribution (end sequence works aswell)
- BrowserController spawns multiple Browser instances, and the Browsers's methods are called over multiple threads (concurrent.futures) during BrowserController sequences

# Doesn't work
- BrowserController.main_extraction_sequence  (needs fixing, optimizing and making stuff a bit less shit...)
- Logins occure on all BrowserInstances at the same time. High likelyhood of instantly looking synchro access when creditentials are wrong
- Synchro itself lmao
