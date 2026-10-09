# Architecture

## Camera assumption

One fixed phone behind the baseline, slightly above head height, with the whole
court in frame. Because the camera never moves, the court is calibrated once per
clip and the same mapping holds for every frame.

## Pipeline

1. **Court calibration** (`app/calibration.py`) - four court corners give a
   homography between image pixels and court metres. Manual clicks today;
   automatic line detection later.
2. **Ball detection** (`app/tracking/ball.py`) - a per-frame image position.
   Currently a motion + colour baseline behind the `BallDetector` interface.
3. **Player detection** - not built yet. A person detector, with each player's
   feet projected onto the court plane.
4. **Event detection** - not built yet. Hits and bounces show up as sharp
   changes of direction in the ball's image track.
5. **Stats** (`app/stats.py`) - speed and angle from ground-plane events.

## What a single camera can and cannot measure

The homography is only correct for points **on the ground**. A ball in flight
is above the court, so its pixel position does not map to one court position.

- **Angle**: reliable. Hit position (player's feet) and bounce position are both
  on the ground.
- **Speed**: v1 is the average horizontal speed between hit and bounce. That is
  lower than the speed off the racket, because the ball slows down in flight.
  The next step is to fit a 3D ballistic path (gravity + drag) through the
  image track, anchored at the bounce, which gives speed at any point.
- **Spin**: cannot be seen directly at phone frame rates. It will be estimated
  from the fitted path: topspin makes the ball dip faster than gravity alone,
  backspin makes it float, and the bounce angle changes too. Expect a
  classification (topspin / flat / slice) and a rough rpm, not a measurement.

Phone tips that help a lot: use a tripod, film at 60 fps or higher (slow-motion
modes give 120-240 fps), and lock exposure so the ball does not smear.

## Going live

The offline pipeline processes a file. Live mode will send frames over a
WebSocket (or WebRTC) and stream results back; it needs the ball detector to
keep up with the frame rate, so accuracy comes first and speed second.
