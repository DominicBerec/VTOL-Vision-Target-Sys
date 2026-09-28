# VTOL Target Tracking

This is the tracking layer I built for AIAA UCF's VTOL Vision Subteam, where I was the Computer Vision Lead (Feb 2026 to Apr 2026). It runs YOLOv8 on a live camera feed, finds a person, and drives a 2-axis pan/tilt gimbal to keep them centered in frame.

It's a bench prototype, not a finished flight system. The full design is below, along with what got done and what didn't.

## The bigger system

The goal was a target acquisition system for a VTOL aircraft. I designed the architecture and put together a 5-week roadmap and parts list (full doc in [`docs/roadmap.pdf`](/roadmap.pdf)).

```
CSI camera ──> Raspberry Pi 5 (YOLO + OpenCV) ──MAVLink over UART (TELEM2)──> Pixhawk (ArduPilot)
                                                                                 │
                                                          2-axis gimbal servos <─┘ (AUX outputs)
```

A few of the design calls and why I made them:

- **CSI camera instead of USB.** Lower latency, which matters when you're doing detection in real time.
- **Separate 5V 5A UBEC for the Pi.** The Pi 5 under load pulls more than the Pixhawk's 5V rail should be supplying. If that rail browns out you can take down the flight controller, which is the one thing that can't fail.
- **Two-layer control, gimbal first.** The gimbal handles fine tracking so the aircraft doesn't have to yaw for every small correction. The airframe only yaws when the gimbal gets near its limits.
- **SITL before hardware.** Test MAVLink commands in simulation first so a bug doesn't crash a real aircraft.

## What's in this repo

| File | What it does |
|---|---|
| `detect_track.py` | Main loop. Grabs frames, runs YOLOv8n, picks the highest-confidence `person` box, and hands its center to the servo code. |
| `servo_control.py` | Servo control. Sets up PWM on the Pi's GPIO, converts pixel offsets to angles, and moves the yaw and pitch servos. |
| `docs/roadmap.pdf` | The full roadmap, parts list, and cost breakdown. |

## How the tracking works

1. **Detect.** Run YOLOv8n on the frame and keep the single most confident `person` detection.
2. **Find the error.** Take the center of the bounding box and subtract the center of the frame. That offset in pixels is how far off target the camera is.
3. **Pixels to degrees.** `delta = (offset_px / frame_dim) * FOV`, using a 65° horizontal and 51° vertical field of view. So a target a quarter frame to the right is about 16° off.
4. **Move the gimbal.** Add the delta to the current yaw and pitch, clamp to 0 to 180°, and convert to a PWM duty cycle. At 50 Hz, `2.5 + (angle / 180) * 10` gives 2.5% to 12.5% duty, which is the standard 0.5 to 2.5 ms servo pulse.

## Hardware (from the roadmap)

| Part | Approx cost |
|---|---|
| Raspberry Pi 5 8GB Essentials Kit | ~$189 |
| Arducam Wide Camera Module 3 (CSI) | ~$57 |
| 5V 5A UBEC | ~$7 |
| JST-GH 6-pin to UART cable (Pixhawk TELEM2 to Pi) | ~$8 to $12 |
| 2-axis servo pan/tilt gimbal | ~$12 |
| TowerPro SG90 servos (x2) | ~$10 to $12 |
| Cables, connectors, heat shrink, fasteners | ~$20 to $30 |
| XT60 splitter | ~$8 |

Servos are wired to GPIO 17 (yaw) and GPIO 27 (pitch) in this prototype.

## Running it

```bash
pip install -r requirements.txt
python detect_track.py
```

`yolov8n.pt` downloads automatically the first time. Press `q` to quit.

## Status

Detection and gimbal tracking were the parts I got working on the bench. We never reached the MAVLink and SITL phases of the roadmap because the aircraft crashed and the team disbanded before we got there.

## Known limitations / what I'd do next

- **Servo moves block the loop.** `set_angle` sleeps 0.3 s per servo, so each frame with a target stalls for about 0.6 s. That caps tracking at a couple FPS. Next step would be making the servo moves non-blocking or cutting that delay way down.
- **Linear pixel-to-degree conversion.** It's an approximation. Using `atan` with the focal length would be exact, especially near the edges of the frame.
- **No smoothing or deadband.** It applies the full correction every step, so it can overshoot and oscillate. A gain below 1 and a small deadband around center would fix that.
- **USB webcam in the prototype.** The real design uses the CSI camera for lower latency.
- **Servos on the Pi's GPIO.** In the full design they move to the Pixhawk's AUX outputs and get commanded over MAVLink.
- **No custom training.** This uses the pretrained COCO `yolov8n` model with `person` as the target class.
