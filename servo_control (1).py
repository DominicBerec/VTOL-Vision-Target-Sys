import RPi.GPIO as GPIO
import time

SERVO_PIN_YAW   = 17
SERVO_PIN_PITCH = 27
PWM_FREQUENCY   = 50

MIN_ANGLE     = 0
MAX_ANGLE     = 180
CENTER_ANGLE  = 90

FOV_HORIZONTAL = 65
FOV_VERTICAL   = 51

current_yaw   = CENTER_ANGLE
current_pitch = CENTER_ANGLE

GPIO.setmode(GPIO.BCM)
GPIO.setup(SERVO_PIN_YAW,   GPIO.OUT)
GPIO.setup(SERVO_PIN_PITCH, GPIO.OUT)

pwm_yaw   = GPIO.PWM(SERVO_PIN_YAW,   PWM_FREQUENCY)
pwm_pitch = GPIO.PWM(SERVO_PIN_PITCH, PWM_FREQUENCY)
pwm_yaw.start(0)
pwm_pitch.start(0)


def angle_to_duty_cycle(angle: float) -> float:
    return 2.5 + (angle / 180.0) * 10.0


def set_angle(pwm_instance, angle: float) -> None:
    angle = max(MIN_ANGLE, min(MAX_ANGLE, angle))
    pwm_instance.ChangeDutyCycle(angle_to_duty_cycle(angle))
    time.sleep(0.3)
    pwm_instance.ChangeDutyCycle(0)


def pixel_offset_to_degrees(offset_px: float, frame_dim: int, fov: float) -> float:
    return (offset_px / frame_dim) * fov


def move_servos(cx: float, cy: float, frame_w: int, frame_h: int) -> tuple:
    global current_yaw, current_pitch

    offset_x = cx - (frame_w / 2)
    offset_y = cy - (frame_h / 2)

    delta_yaw   = pixel_offset_to_degrees(offset_x, frame_w, FOV_HORIZONTAL)
    delta_pitch = pixel_offset_to_degrees(offset_y, frame_h, FOV_VERTICAL)

    new_yaw   = current_yaw   + delta_yaw
    new_pitch = current_pitch + delta_pitch

    set_angle(pwm_yaw,   new_yaw)
    set_angle(pwm_pitch, new_pitch)

    current_yaw   = max(MIN_ANGLE, min(MAX_ANGLE, new_yaw))
    current_pitch = max(MIN_ANGLE, min(MAX_ANGLE, new_pitch))

    return current_yaw, current_pitch


def cleanup() -> None:
    pwm_yaw.stop()
    pwm_pitch.stop()
    GPIO.cleanup()
