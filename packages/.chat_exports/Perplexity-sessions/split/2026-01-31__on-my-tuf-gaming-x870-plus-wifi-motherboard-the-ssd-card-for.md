---
title: "On my TUF GAMING X870-PLUS WIFI motherboard, the SSD card for the M.2_4 slot, the latch doesn't want to latch. Am I doin"
date: "2026-01-31"
mode: "CONCISE"
uuid: "a1a847c5-6d91-4aac-9878-32cd94df8ade"
entry_count: 3
---

## Human

On my TUF GAMING X870-PLUS WIFI motherboard, the SSD card for the M.2_4 slot, the latch doesn't want to latch. Am I doing something wrong?

## Assistant

**The M.2 Q-Latch on your ASUS TUF GAMING X870-PLUS WIFI motherboard's M.2_4 slot is a tool-free mechanism designed for easy SSD installation, but it often requires specific technique to secure properly, especially with SSDs that have heatsinks.**[1][2]

## Installation Steps
Insert the SSD at a 30-degree angle into the M.2_4 slot (Key M, supports 2242/2260/2280/22110 PCIe 4.0 x4), ensuring the notch aligns with the connector.[1]
Push it down firmly and flat until fully seated, then rotate or push the Q-Latch (a small plastic lever or spinning mechanism) upward/clockwise to vertical position until it clicks over the SSD's notch or lip.[3][4][1]
Users report needing gentle but firm pressure or a slight twist on the latch, as it can be finicky and pop open if not fully engaged.[5][1]

## Common Issues and Fixes
- **SSD with heatsink**: Thick heatsinks prevent the latch from overlapping the notch properly; remove the SSD heatsink and use the motherboard's included M.2 heatsink (pre-installed or bundled), which is compatible with the Q-Latch.[6][1]
- **Not latching**: Ensure no obstructions, fully seat the SSD first, and avoid timid force—apply steady pressure without over-twisting to avoid damage.[5][6]
- If it still fails, the Q-Latch may be removable (check for screw at 2280 position); replace with a standoff screw from the package if needed, though tool-free is intended.[7][1]

## Verification
After latching, lightly tug upward—the SSD should not lift if secure.  Power on and check BIOS (Del key) for detection in M.2_4; note it disables PCIEX16(G4) slot.  If issues persist, confirm SSD compatibility via ASUS QVL.[2][1][5]

## Human

PCIe lane sharing effects of using M.2_4 slot on TUF X870-PLUS WIFI

## Assistant

**Using the M.2_4 slot on the ASUS TUF GAMING X870-PLUS WIFI disables the secondary PCIe 4.0 x16 slot (PCIEX16(G4), wired for x4), as they share the same chipset PCIe 4.0 x4 lanes.**[1][2][3]

## Slot Configuration
M.2_4 is a PCIe 4.0 x4 slot (Key M, sizes 2242/2260/2280/22110) connected to the AMD X870 chipset.[3][1]
It does not affect the primary PCIe 5.0 x16 GPU slot (PCIEX16(G5)), which only shares lanes with M.2_2.[4][5][3]

## Affected Components
| Component | Effect When M.2_4 Populated |
|-----------|-----------------------------|
| PCIEX16(G4) slot | Disabled [3][1][6] |
| Primary GPU slot (PCIEX16(G5)) | Unaffected (full x16) [4][5] |
| Other M.2 slots | No sharing with M.2_4 [3][1] |
| USB/SATA | No direct impact [5] |

## Performance Notes
PCIEX16(G4) is for expansion cards like additional storage adapters, but disabling it frees no additional lanes elsewhere.  Ideal for storage without GPU compromise, unlike M.2_2.[4][1][3]

## Human

I put a 1TB SSD card in the M.2_4 slot, and now my computer powers on but nothing displays, all my monitors are black.

## Assistant

**Your no-display issue after installing the 1TB SSD in M.2_4 is likely due to improper seating of the SSD, triggering a POST failure (check Q-LEDs: white for VGA, yellow-green for Boot if lit).**[1][2][3]
M.2_4 installation can halt boot if not fully latched, as the board halts on hardware errors during POST.[3][4]

## Immediate Troubleshooting
Power off, unplug PSU, and remove the M.2_4 SSD to test if display returns—this isolates if the SSD is the cause.[2][5]
Reseat the SSD: Insert at 30° angle, push firmly flat until seated (no gap), secure Q-Latch fully vertical/clicked (firm pressure needed).[4][3]
Check Q-LEDs (near 24-pin): Red=CPU, Yellow=DRAM, White=VGA, Green=Boot; lit LED indicates the failure stage.[1][3]

## Additional Checks
| Issue | Fix |
|-------|-----|
| Poor latch/seating | Tug lightly upward post-install; no lift if secure. Use mobo heatsink over SSD heatsink if thick. [4][3] |
| GPU/display | Confirm GPU in PCIEX16(G5), cables seated; try different cable/port/monitor. M.2_4 doesn't affect primary GPU. [1][6] |
| RAM/CPU | Reseat RAM in A2/B2 slots; clear CMOS via button/jumper if stuck. [7][3] |
| BIOS | Update via FlashBack if accessible without SSD. [3] |

Power cycle (hold power 10s unplugged) after changes; enter BIOS (Del) to verify SSD detection once booted.[5][3]
