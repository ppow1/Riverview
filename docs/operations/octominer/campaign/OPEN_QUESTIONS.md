# Open Questions

- What causes the spontaneous Octo2 reboot behavior?
- Can PiKVM virtual mass storage reliably deliver BIOS candidates while HID remains usable?
- What exact stock boot-time distribution should define the firmware latency tolerance?
- Which high-MMIO firmware mechanism can increase P100 capacity without the previously observed boot delay?
- After a working solution is found, can the MMIO setting be exposed through BIOS Setup rather than remaining hard-coded?
- Why are unauthenticated requests currently reaching the Riverview Octo control API and receiving HTTP 401 responses?
